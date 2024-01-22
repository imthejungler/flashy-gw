import abc
import decimal
import enum
import os
from typing import Optional

import psycopg2
import pydantic

from checkout.card_processing import services, adapters
from checkout.gateway import model
from checkout.standard_types import money


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
    currency: money.Currency
    total_amount: decimal.Decimal
    tip: decimal.Decimal
    vat: decimal.Decimal
    card: Card


class TransactionStatus(enum.Enum):
    PENDING = enum.auto()
    APPROVED = enum.auto()
    REJECTED = enum.auto()


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
        return services.process_sale(
            request=FlashyCardNotPresentProvider._transaction_to_request(transaction=transaction),
            router=adapters.FlashyTransactionRouter(),
            account_range_provider=adapters.FlashyAccountRangeProvider(),
            repo=adapters.PostgresCardNotPresentTransactionRepository()
        )

    @staticmethod
    def _transaction_to_request(transaction: Transaction) -> services.TransactionRequest:
        return services.TransactionRequest(
            client_id=transaction.client_id,
            client_reference_id=transaction.client_reference_id,
            merchant_id=transaction.merchant_id,
            merchant_economic_activity=transaction.merchant_economic_activity,
            currency=transaction.currency,
            total_amount=transaction.total_amount,
            tip=transaction.tip,
            taxes=transaction.taxes,
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
    def find_by_id(self, payment_id: str) -> Optional[model.CardNotPresentPayment]:
        ...

    @abc.abstractmethod
    def create_payment(self, payment: model.CardNotPresentPayment) -> model.CardNotPresentPayment:
        ...

    @abc.abstractmethod
    def update_payment(self, payment: model.CardNotPresentPayment) -> model.CardNotPresentPayment:
        ...


class PostgresCardNotPresentPaymentRepository(CardNotPresentPaymentRepository):
    def generate_id(self) -> str:
        pass

    def find_by_id(self, payment_id: str) -> Optional[model.CardNotPresentPayment]:
        pass

    def create_payment(self, payment: model.CardNotPresentPayment) -> model.CardNotPresentPayment:
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                    INSERT INTO payments (merchant_id, payment_id, currency, total_amount, tip, vat, receipt, status, card_masked_pan, payment_date),
                    VALUES (%s, %s, %s, %s, %s)
                """,
                payment.merchant_id, payment.payment_id, payment.currency.value, payment.total_amount, payment.tip,
                payment.vat, payment.receipt, payment.status.value, payment.card.masked_pan, payment.payment_date)
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
                         
                        receipt=%s, status=%s),
                    VALUES (%s, %s, %s, %s, %s)
                """,
                payment.merchant_id, payment.payment_id, payment.currency.value, payment.total_amount, payment.tip,
                payment.vat, payment.receipt, payment.status.value, payment.card, payment.payment_date)
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
