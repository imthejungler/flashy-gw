import abc
import decimal
import enum
import os
from typing import Optional, List

import psycopg2
import pydantic

from checkout.card_processing import services, adapters
from checkout.gateway import model
from checkout.gateway.model import CardNotPresentPayment
from checkout.standard_types import money, helpers


# CARD PROCESSING ADAPTER #########################################
class Card(pydantic.BaseModel):
    cardholder_name: str
    expiration_month: int
    expiration_year: int
    pan: pydantic.SecretStr
    cvv: pydantic.SecretStr


class Transaction(pydantic.BaseModel):
    client_id: str = "FLASHY_GW"
    client_reference_id: str
    merchant_id: str
    currency: money.Currency
    total_amount: decimal.Decimal
    tip: decimal.Decimal
    vat: decimal.Decimal
    card: Card


class TransactionStatus(enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class TransactionResponse(pydantic.BaseModel):
    network: str
    response_code: str
    response_message: str
    approval_code: str
    status: TransactionStatus


class CardNotPresentProvider(abc.ABC):
    @abc.abstractmethod
    def sale(self, transaction: Transaction) -> TransactionResponse:
        """
        Authorizes and captures a transaction in one step:
        - Validates the card data,
        - Checks the card's restrictions,
        - Evaluates the transaction against an anti-fraud system,

        if any of these conditions fails, returns a rejected transaction.

        Otherwise, returns the response of the Acquiring processor.
        :return:
        TransactionResponse
        """


class FlashyCardNotPresentProvider(CardNotPresentProvider):
    def sale(self, transaction: Transaction) -> TransactionResponse:
        response = services.process_sale(
            request=FlashyCardNotPresentProvider._transaction_to_request(transaction=transaction),
            router=adapters.FlashyTransactionRouter(),
            account_range_provider=adapters.FlashyAccountRangeProvider(),
            repo=adapters.PostgresCardNotPresentTransactionRepository()
        )

        return TransactionResponse(
            network=response.network,
            response_code=response.response_code,
            response_message=response.response_message,
            approval_code=response.approval_code,
            status=TransactionStatus[response.status.value],
        )

    @staticmethod
    def _transaction_to_request(transaction: Transaction) -> services.TransactionRequest:
        return services.TransactionRequest(
            client_id=transaction.client_id,
            client_reference_id=transaction.client_reference_id,
            merchant_id=transaction.merchant_id,
            currency=transaction.currency,
            total_amount=transaction.total_amount,
            tip=transaction.tip,
            vat=transaction.vat,
            card=services.Card(
                cardholder_name=transaction.card.cardholder_name,
                expiration_month=transaction.card.expiration_month,
                expiration_year=transaction.card.expiration_year,
                pan=transaction.card.pan,
                cvv=transaction.card.cvv,
            ),
        )


# PAYMENT REPOSITORY #########################################
class CardNotPresentPaymentRepository(abc.ABC):

    @abc.abstractmethod
    def generate_id(self) -> str:
        ...

    @abc.abstractmethod
    def get_payments(self, merchant_id: str) -> List[model.CardNotPresentPayment]:
        ...

    @abc.abstractmethod
    def find_payment(self, merchant_id: str, payment_id: str) -> Optional[model.CardNotPresentPayment]:
        ...

    @abc.abstractmethod
    def create_payment(self, payment: model.CardNotPresentPayment) -> model.CardNotPresentPayment:
        ...

    @abc.abstractmethod
    def update_payment(self, payment: model.CardNotPresentPayment) -> model.CardNotPresentPayment:
        ...


class PostgresCardNotPresentPaymentRepository(CardNotPresentPaymentRepository):

    def generate_id(self) -> str:
        return helpers.IDGenerator.hex_uuid()

    def get_payments(self, merchant_id: str) -> List[model.CardNotPresentPayment]:
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                    SELECT merchant_id, payment_id, 
                    currency, total_amount, tip, vat, 
                    receipt_response_code, receipt_response_message, receipt_approval_code, 
                    status, card_masked_pan, payment_date 
                    FROM payments 
                    WHERE merchant_id = %s
                """,
                (merchant_id,))

            rows = cursor.fetchall()
            payments = []
            for row in rows:
                payments.append(CardNotPresentPayment(
                    merchant_id=merchant_id,
                    payment_id=row[1],
                    currency=money.Currency[row[2]],
                    total_amount=row[3],
                    tip=row[4],
                    vat=row[5],
                    receipt=model.Receipt(
                        response_code=row[6],
                        response_message=row[7],
                        approval_code=row[8]),
                    status=model.PaymentStatus[row[9]],
                    card=model.NotPresentCard(
                        masked_pan=row[10]),
                    payment_date=row[11],
                ))
            cursor.close()
            return payments
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            raise
        finally:
            if conn is not None:
                conn.close()

    def find_payment(self, merchant_id: str, payment_id: str) -> Optional[model.CardNotPresentPayment]:
        conn = None
        payment = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                    SELECT merchant_id, payment_id, 
                    currency, total_amount, tip, vat, 
                    receipt_response_code, receipt_response_message, receipt_approval_code, 
                    status, card_masked_pan, payment_date 
                    FROM payments 
                    WHERE merchant_id = %s AND payment_id = %s
                """,
                (merchant_id, payment_id))

            row = cursor.fetchone()
            if row is not None:
                payment = CardNotPresentPayment(
                    merchant_id=merchant_id,
                    payment_id=payment_id,
                    currency=money.Currency[row[2]],
                    total_amount=row[3],
                    tip=row[4],
                    vat=row[5],
                    receipt=model.Receipt(
                        response_code=row[6],
                        response_message=row[7],
                        approval_code=row[8]),
                    status=model.PaymentStatus[row[9]],
                    card=model.NotPresentCard(
                        masked_pan=row[10]),
                    payment_date=row[11],
                )
            cursor.close()
            return payment
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            raise
        finally:
            if conn is not None:
                conn.close()

    def create_payment(self, payment: model.CardNotPresentPayment) -> model.CardNotPresentPayment:
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                    INSERT INTO payments (
                    merchant_id, payment_id, 
                    currency, total_amount, tip, vat, 
                    receipt_response_code, receipt_response_message, receipt_approval_code, 
                    status, card_masked_pan, payment_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (payment.merchant_id, payment.payment_id,
                 payment.currency.value, payment.total_amount, payment.tip, payment.vat,
                 payment.receipt.response_code, payment.receipt.response_message, payment.receipt.approval_code,
                 payment.status.value, payment.card.masked_pan, payment.payment_date))
            conn.commit()
            cursor.close()
            return payment
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            raise
        finally:
            if conn is not None:
                conn.close()

    def update_payment(self, payment: model.CardNotPresentPayment) -> model.CardNotPresentPayment:
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                    UPDATE payments SET 
                    receipt_response_code = %s, receipt_response_message = %s, 
                    receipt_approval_code = %s, status = %s
                    WHERE merchant_id = %s AND payment_id = %s
                """,
                (payment.receipt.response_code, payment.receipt.response_message, payment.receipt.approval_code,
                 payment.status.value, payment.merchant_id, payment.payment_id))
            conn.commit()
            cursor.close()

            return payment
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            raise
        finally:
            if conn is not None:
                conn.close()

    def _get_connection(self):
        return psycopg2.connect(
            host=os.environ.get("POSTGRES_HOST"),
            dbname=os.environ.get("POSTGRES_DATABASE"),
            user=os.environ.get("POSTGRES_USER"),
            password=os.environ.get("POSTGRES_PASSWORD"),
        )
