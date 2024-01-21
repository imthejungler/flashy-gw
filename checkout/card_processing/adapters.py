import abc
import decimal
import enum
from typing import List

import pydantic

from checkout.standard_types import card, money


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


class TransactionPackage(pydantic.BaseModel):
    franchise: card.Franchise


class TransactionRouter(abc.ABC):
    @abc.abstractmethod
    def get_acquiring_processing_providers(self, package: TransactionPackage) -> List[AcquiringProcessorProvider]:
        ...


class DefaultTransactionRouter(TransactionRouter):
    def get_acquiring_processing_providers(self, package: TransactionPackage) -> List[AcquiringProcessorProvider]:
        pass
