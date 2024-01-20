from checkout import service as payment_service
import decimal


def test_should_approve_a_payment() -> None:
    payment_response = payment_service.process_payment(amount=decimal.Decimal("100.00"))
    assert payment_response.status == "APPROVED"
