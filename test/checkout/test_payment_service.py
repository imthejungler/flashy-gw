from checkout import service
from checkout.standard_types import money
from test.checkout import faker
import decimal


def test_should_approve_a_payment() -> None:
    request = faker.PaymentRequestFaker.with_amount_and_currency(
        total_amount=decimal.Decimal("100.00"),
        currency=money.Currency.EUR
    )
    payment_response = service.process_payment(request=request)
    assert payment_response.status == "APPROVED"
