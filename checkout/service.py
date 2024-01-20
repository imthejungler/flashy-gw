import decimal
from typing import List

import pydantic

from checkout.standard_types import money


class CardRequest(pydantic.BaseModel):
    cardholder_name: str
    expiration_month: int
    expiration_year: int
    pan: pydantic.SecretStr
    cvv: pydantic.SecretStr


class PaymentRequest(pydantic.BaseModel):
    total_amount: decimal.Decimal
    tip: decimal.Decimal
    taxes: List[money.Tax]
    card: CardRequest
    currency: money.Currency


class PaymentResponse(pydantic.BaseModel):
    status: str


def process_payment(request: PaymentRequest) -> PaymentResponse:
    return PaymentResponse(status="APPROVED")
