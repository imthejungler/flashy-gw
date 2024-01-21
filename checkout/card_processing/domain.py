import decimal
import enum
from typing import List

import pydantic

from checkout.standard_types import money


class TransactionTypes(enum.Enum):
    SALE = enum.auto()
    AUTHORIZATION = enum.auto()
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


class CardNotPresentTransaction(pydantic.BaseModel):
    client_id: str
    client_reference: str
    transaction_id: str
    transaction_type: TransactionTypes
    currency: money.Currency
    total_amount: decimal.Decimal
    tip: decimal.Decimal
    taxes: List[money.Tax]
    card: PCIComplianceCard
