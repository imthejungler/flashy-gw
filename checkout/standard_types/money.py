import decimal

import pydantic
import enum


class Currency(enum.Enum):
    EUR = "EUR"
    USD = "USD"


class TaxType(enum.Enum):
    VAT = enum.auto()


class Tax(pydantic.BaseModel):
    type: TaxType
    base: decimal.Decimal
    value: decimal.Decimal
