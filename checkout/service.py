import decimal

import pydantic


class PaymentResponse(pydantic.BaseModel):
    amount: decimal.Decimal
    amount: decimal.Decimal
    status: str


def process_payment(amount: decimal.Decimal) -> PaymentResponse:
    return PaymentResponse(status="APPROVED", amount=amount)
