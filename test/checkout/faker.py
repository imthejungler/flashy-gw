import decimal

import pydantic

from checkout.standard_types import money
from checkout import service


class PaymentRequestFaker:
    @staticmethod
    def with_amount_and_currency(total_amount: decimal.Decimal, currency: money.Currency) -> service.PaymentRequest:
        return service.PaymentRequest(
            currency=currency,
            total_amount=total_amount,
            tip=decimal.Decimal("0"),
            taxes=[],
            card=service.CardRequest(
                cardholder_name="Fulanito de tal",
                expiration_month=1,
                expiration_year=2002,
                pan=pydantic.SecretStr("12345678790123456"),
                cvv=pydantic.SecretStr("123"),
            )
        )


class PaymentResponseFake:
    @staticmethod
    def approved_payment() -> service.PaymentRequest:
        return service.PaymentResponse(
            status="APPROVED"
        )
