from checkout import service as payment_service


def test_a_payment() -> None:
    payment = payment_service.process_payment(amount=100)
    assert payment.status == "APPROVED"
