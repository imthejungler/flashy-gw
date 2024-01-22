import abc
import decimal
import enum
from collections.abc import Iterator
from typing import List, Optional, Dict

import pydantic

from checkout.card_processing import model
from checkout.standard_types import card, money


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
class FinancialMessage(pydantic.BaseModel):
    merchant_id: str
    currency: money.Currency
    total_amount: decimal.Decimal
    tip: decimal.Decimal
    taxes: List[money.Tax]


class FinancialMessageResult(pydantic.BaseModel):
    network: card.AcquiringNetwork
    response_code: str
    response_message: str
    interchange_rate: decimal.Decimal


class ApprovedCapture(FinancialMessageResult):
    approval_code: str


class RejectedCapture(FinancialMessageResult):
    is_retryable: bool


class CaptureMessage(FinancialMessage):
    cardholder_name: str
    expiration_month: int
    expiration_year: int
    pan: pydantic.SecretStr
    cvv: pydantic.SecretStr


class ServiceType(enum.Enum):
    INTERCHANGE = enum.auto()
    INTERNATIONAL_ROUTING = enum.auto()
    ANTI_FRAUD_EVALUATION = enum.auto()
    OTHER = enum.auto()


class ProcessingCost(pydantic.BaseModel):
    service_type: ServiceType
    cost: decimal.Decimal


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
            approval_code="ABCDEFG1234",
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
        pass

    def find_by_id(self, transaction_id: str) -> Optional[model.CardNotPresentTransaction]:
        pass

    def register_transaction(self, transaction: model.CardNotPresentTransaction) -> model.CardNotPresentTransaction:
        pass

    def update_transaction(self, transaction: model.CardNotPresentTransaction) -> model.CardNotPresentTransaction:
        pass
