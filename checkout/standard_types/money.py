import decimal
import enum

import pydantic


class Currency(enum.Enum):
    EUR = "EUR"
    USD = "USD"


class TaxType(enum.Enum):
    VAT = "VAT"


class Tax(pydantic.BaseModel):
    type: TaxType
    base: decimal.Decimal
    value: decimal.Decimal
