import decimal

import pydantic

from checkout.standard_types import money
from checkout.gateway import service


class PaymentRequestFaker:
    @staticmethod
    def with_amount_and_currency(total_amount: decimal.Decimal, currency: money.Currency) -> service.PaymentRequest:
        return service.PaymentRequest(
            merchant_id="ABCDEFG",
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


class PaymentResponseFaker:
    @staticmethod
    def with_approved_transaction_and_approval_number(
            approval_number: str) -> service.PaymentResponse:
        return service.PaymentResponse(
            approval_number=approval_number,
            status="APPROVED"
        )

    @staticmethod
    def with_rejected_transaction() -> service.PaymentResponse:
        return service.PaymentResponse(
            approval_number="",
            status="APPROVED"
        )
