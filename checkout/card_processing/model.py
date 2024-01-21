import decimal
import enum
from typing import List

import pydantic

from checkout.standard_types import money


class TransactionTypes(enum.Enum):
    AUTHORIZATION = enum.auto()
    CAPTURE = enum.auto()
    REVERSAL = enum.auto()
    VOID = enum.auto()


class PCIComplianceCard(pydantic.BaseModel):
    cardholder_name: str
    franchise: str
    category: str
    bin: str
    masked_pan: str
    expiration_month: int
    expiration_year: int
    ttl: int


class TransactionStatus(enum.Enum):
    PENDING = enum.auto()
    APPROVED = enum.auto()
    REJECTED = enum.auto()


class CardNotPresentTransaction(pydantic.BaseModel):
    transaction_id: str
    client_id: str
    client_reference_id: str
    merchant_id: str
    merchant_economic_activity: str
    transaction_type: TransactionTypes
    currency: money.Currency
    total_amount: decimal.Decimal
    tip: decimal.Decimal
    taxes: List[money.Tax]
    card: PCIComplianceCard
    status: TransactionStatus

