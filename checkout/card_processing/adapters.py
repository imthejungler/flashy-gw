import abc
import decimal
import enum
from collections.abc import Iterator
from typing import List, Optional

import pydantic

from checkout.card_processing import model
from checkout.standard_types import card, money


# CARD INFO #########################################
class CardInfo(pydantic.BaseModel):
    country: str
    franchise: card.Franchise
    category: str


class CardInfoAdapter(abc.ABC):
    @abc.abstractmethod
    def get_pan_info(self, pan: str) -> CardInfo:
        ...


class DefaultCardInfoAdapter(CardInfoAdapter):
    def get_pan_info(self, pan: str) -> CardInfo:
        pass


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
    def capture(self, message: CaptureMessage) -> FinancialMessageResult:
        pass


class NoAcquiringProcessorProviderAvailable(AcquiringProcessorProvider):

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


class DefaultTransactionRouter(TransactionRouter):
    def get_acquiring_processing_providers(self, package: TransactionPackage) -> Iterator[AcquiringProcessorProvider]:
        pass


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


class DefaultCardNotPresentTransactionRepository(CardNotPresentTransactionRepository):
    def generate_id(self) -> str:
        pass

    def find_by_id(self, transaction_id: str) -> Optional[model.CardNotPresentTransaction]:
        pass

    def register_transaction(self, transaction: model.CardNotPresentTransaction) -> model.CardNotPresentTransaction:
        pass

    def update_transaction(self, transaction: model.CardNotPresentTransaction) -> model.CardNotPresentTransaction:
        pass
