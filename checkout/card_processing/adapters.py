import abc
import decimal
import os
import random
import string
from collections.abc import Iterator
from typing import Optional, Dict

import psycopg2
import pydantic

from checkout.card_processing import model
from checkout.standard_types import card, money, helpers


# ACCOUNT RANGES #########################################
class PANInfo(pydantic.BaseModel):
    country: str
    category: str
    franchise: str
    issuer: str


class UnknownPANInfo(PANInfo):
    country: str = "ZZ"
    franchise: str = "UNRECOGNIZED"
    category: str = "UNKNOWN"
    issuer: str = "UNKNOWN"


class AccountRangeProvider(abc.ABC):
    @abc.abstractmethod
    def get_pan_info(self, pan: pydantic.SecretStr) -> PANInfo:
        """
           Uses account ranges, better than using only bins due as it uses 10 digits of the pan
           in order to get the Franchise, country and most of the time, the category,
           :param pan: from 15 to 19 digits number representing the identifier of the card.
           :return: detailed information about the card
        """
        ...


class FlashyAccountRangeProvider(AccountRangeProvider):
    _ACCOUNT_RANGE_SERVICE: Dict[str, PANInfo] = {
        "4444444444": PANInfo(country="FR", franchise="VISA", category="BLACK", issuer="LCL"),
        "5555555555": PANInfo(country="VE", franchise="MASTER_CARD", category="BLACK", issuer="Banco de Venezuela"),
        "4444455555": PANInfo(country="UK", franchise="VISA", category="BLACK", issuer="HSBC")
    }

    def get_pan_info(self, pan: pydantic.SecretStr) -> PANInfo:
        return self._ACCOUNT_RANGE_SERVICE.get(pan.get_secret_value()[:10], UnknownPANInfo())


# ACQUIRING PROCESSORS #########################################

class FinancialMessageResult(pydantic.BaseModel):
    network: card.AcquiringNetwork
    response_code: str
    response_message: str
    interchange_rate: decimal.Decimal


class ApprovedCapture(FinancialMessageResult):
    approval_code: str


class RejectedCapture(FinancialMessageResult):
    is_retryable: bool


class CaptureMessage(pydantic.BaseModel):
    merchant_id: str
    currency: money.Currency
    total_amount: decimal.Decimal
    tip: decimal.Decimal
    vat: decimal.Decimal
    cardholder_name: str
    expiration_month: int
    expiration_year: int
    pan: pydantic.SecretStr
    cvv: pydantic.SecretStr


class AcquiringProcessorProvider(abc.ABC):
    @abc.abstractmethod
    def capture(self, message: CaptureMessage) -> FinancialMessageResult:
        ...


class CKOAcquiringProcessorProvider(AcquiringProcessorProvider):
    _ACQUIRING_SERVICE: Dict[str, FinancialMessageResult] = {
        "5555555555555555": RejectedCapture(
            network=card.AcquiringNetwork.CKO,
            response_code="43",
            response_message="Stolen card, pick up",
            interchange_rate=decimal.Decimal("0.10"),
            is_retryable=False
        )
    }

    def capture(self, message: CaptureMessage) -> FinancialMessageResult:
        return self._ACQUIRING_SERVICE.get(message.pan.get_secret_value(), ApprovedCapture(
            network=card.AcquiringNetwork.CKO,
            response_code="00",
            response_message="Approved or completed successfully",
            interchange_rate=decimal.Decimal("0.10"),
            approval_code="ABCDEFG1234",
        ))


class OTHERAcquiringProcessorProvider(AcquiringProcessorProvider):
    _ACQUIRING_SERVICE: Dict[str, FinancialMessageResult] = {
        "4444444444444444": RejectedCapture(
            network=card.AcquiringNetwork.CKO,
            response_code="19",
            response_message="Re-enter transaction",
            interchange_rate=decimal.Decimal("0.10"),
            is_retryable=True
        )
    }

    def capture(self, message: CaptureMessage) -> FinancialMessageResult:
        return self._ACQUIRING_SERVICE.get(message.pan.get_secret_value(), ApprovedCapture(
            network=card.AcquiringNetwork.CKO,
            response_code="00",
            response_message="Approved or completed successfully",
            interchange_rate=decimal.Decimal("0.20"),
            approval_code="".join(random.SystemRandom().choices(string.ascii_uppercase + string.digits, k=10)),
        ))


class NoProcessorAvailable(AcquiringProcessorProvider):

    def __init__(self, last_financial_message_result: Optional[FinancialMessageResult] = None) -> None:
        self._last_result: FinancialMessageResult = last_financial_message_result
        if last_financial_message_result:
            self._last_result = RejectedCapture(
                network=last_financial_message_result.network,
                response_code=last_financial_message_result.response_code,
                response_message=last_financial_message_result.response_message,
                interchange_rate=last_financial_message_result.interchange_rate,
                is_retryable=False
            )

    def capture(self, message: CaptureMessage) -> FinancialMessageResult:
        return self._last_result if self._last_result else RejectedCapture(
            network=card.AcquiringNetwork.CKO,
            response_code="F99",
            response_message="No Acquiring Processor Available",
            interchange_rate=decimal.Decimal("0.0"),
            is_retryable=False
        )


# ROUTER #########################################
class TransactionPackage(pydantic.BaseModel):
    franchise: card.Franchise


class TransactionRouter(abc.ABC):
    @abc.abstractmethod
    def get_acquiring_processing_providers(self, package: TransactionPackage) -> Iterator[AcquiringProcessorProvider]:
        ...


class FlashyTransactionRouter(TransactionRouter):
    _ROUTING_SYSTEM: Dict[card.Franchise, AcquiringProcessorProvider] = {
        card.Franchise.MASTER_CARD: CKOAcquiringProcessorProvider(),
        card.Franchise.VISA: OTHERAcquiringProcessorProvider()
    }

    def get_acquiring_processing_providers(self, package: TransactionPackage) -> Iterator[AcquiringProcessorProvider]:
        if package.franchise == card.Franchise.MASTER_CARD:
            yield CKOAcquiringProcessorProvider()
        elif package.franchise == card.Franchise.VISA:
            yield OTHERAcquiringProcessorProvider()
        else:
            yield CKOAcquiringProcessorProvider()
            yield OTHERAcquiringProcessorProvider()


# CARD NOT PRESENT TRANSACTION REPOSITORY #########################################
class CardNotPresentTransactionRepository(abc.ABC):

    @abc.abstractmethod
    def generate_id(self) -> str:
        ...

    @abc.abstractmethod
    def find_by_id(self, transaction_id: str) -> Optional[model.CardNotPresentTransaction]:
        ...

    @abc.abstractmethod
    def register_transaction(self, transaction: model.CardNotPresentTransaction) -> model.CardNotPresentTransaction:
        ...

    @abc.abstractmethod
    def update_transaction(self, transaction: model.CardNotPresentTransaction) -> model.CardNotPresentTransaction:
        ...


class PostgresCardNotPresentTransactionRepository(CardNotPresentTransactionRepository):
    def generate_id(self) -> str:
        return helpers.IDGenerator.hex_uuid()

    def find_by_id(self, transaction_id: str) -> Optional[model.CardNotPresentTransaction]:
        pass

    def register_transaction(self, transaction: model.CardNotPresentTransaction) -> model.CardNotPresentTransaction:
        conn = None
        print("transaction.transaction_id ", transaction.transaction_id)
        print("transaction.client_id ", transaction.client_id)
        print("transaction.client_reference_id ", transaction.client_reference_id)
        print("transaction.merchant_id ", transaction.merchant_id)
        print("transaction.transaction_type.value ", transaction.transaction_type.value)
        print("transaction.currency.value ", transaction.currency.value)
        print("transaction.total_amount ", transaction.total_amount)
        print("transaction.tip ", transaction.tip)
        print("transaction.vat ", transaction.vat)
        print("transaction.card_data.cardholder_name ", transaction.card_data.cardholder_name)
        print("transaction.card_data.franchise ", transaction.card_data.franchise)
        print("transaction.card_data.category ", transaction.card_data.category)
        print("transaction.card_data.country ", transaction.card_data.country)
        print("transaction.card_data.masked_pan ", transaction.card_data.masked_pan)
        print("transaction.card_data.expiration_month ", transaction.card_data.expiration_month)
        print("transaction.card_data.expiration_year ", transaction.card_data.expiration_year)
        print("transaction.status.value ", transaction.status.value)
        print("transaction.network_response.response_code ", transaction.network_response.response_code)
        print("transaction.network_response.response_message ", transaction.network_response.response_message)
        print("transaction.network_response.approval_code ", transaction.network_response.approval_code)
        print("transaction.transaction_date ", transaction.transaction_date)
        print("transaction.network_response.attempt ", transaction.network_response.attempt)
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                    INSERT INTO transactions (
                    transaction_id,
                    client_id,
                    client_reference_id,
                    merchant_id,
                    transaction_type,
                    currency,
                    total_amount,
                    tip,
                    vat,
                    card_data_cardholder_name,
                    card_data_franchise,
                    card_data_category,
                    card_data_country,
                    card_data_masked_pan,
                    card_data_expiration_month,
                    card_data_expiration_year,
                    status,
                    response_code,
                    response_message,
                    approval_code,
                    transaction_date,
                    attempt)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    transaction.transaction_id,
                    transaction.client_id,
                    transaction.client_reference_id,
                    transaction.merchant_id,
                    transaction.transaction_type.value,
                    transaction.currency.value,
                    transaction.total_amount,
                    transaction.tip,
                    transaction.vat,
                    transaction.card_data.cardholder_name,
                    transaction.card_data.franchise,
                    transaction.card_data.category,
                    transaction.card_data.country,
                    transaction.card_data.masked_pan,
                    transaction.card_data.expiration_month,
                    transaction.card_data.expiration_year,
                    transaction.status.value,
                    transaction.network_response.response_code,
                    transaction.network_response.response_message,
                    transaction.network_response.approval_code,
                    transaction.transaction_date,
                    transaction.network_response.attempt,
                ))
            conn.commit()
            cursor.close()
            return transaction
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            raise
        finally:
            if conn is not None:
                conn.close()

    def update_transaction(self, transaction: model.CardNotPresentTransaction) -> model.CardNotPresentTransaction:
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                    UPDATE transactions SET 
                    response_code = %s, response_message = %s, 
                    approval_code = %s, status = %s, 
                    attempt = %s
                    WHERE client_id = %s AND transaction_id = %s
                """,
                (transaction.network_response.response_code, transaction.network_response.response_message,
                 transaction.network_response.approval_code, transaction.status.value,
                 transaction.network_response.attempt,
                 transaction.client_id, transaction.transaction_id))
            conn.commit()
            cursor.close()

            return transaction
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
