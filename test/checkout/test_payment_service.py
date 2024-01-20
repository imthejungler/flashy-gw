import pydantic

from checkout import service
from checkout.standard_types import money
import decimal


def test_should_approve_a_payment() -> None:
    request = service.PaymentRequest(
        currency=money.Currency.USD,
        total_amount=decimal.Decimal("100.00"),
        tip=decimal.Decimal("100.00"),
        taxes=[
            money.Tax(
                type=money.TaxType.VAT,
                base=decimal.Decimal("90.00"),
                value=decimal.Decimal("10.00")
            )
        ],
        card=service.CardRequest(
            cardholder_name="Fulanito de tal",
            expiration_month=1,
            expiration_year=2002,
            pan=pydantic.SecretStr("12345678790123456"),
            cvv=pydantic.SecretStr("123"),
        )
    )
    payment_response = service.process_payment(request=request)
    assert payment_response.status == "APPROVED"
