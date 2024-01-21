from checkout.gateway import service
from checkout.gateway import adapter
from checkout.standard_types import money
from test.checkout import faker
import decimal


def test_should_approve_a_payment_when_the_card_processor_approves_the_transaction() -> None:
    request = faker.PaymentRequestFaker.with_amount_and_currency(
        total_amount=decimal.Decimal("100.00"),
        currency=money.Currency.EUR
    )
    payment_response = service.process_payment(
        request=request,
        card_processing_adapter=adapter.FakeCardProcessingAdapter(
            approval_number="000000123456"
        ))
    expected_response = faker.PaymentResponseFaker.with_approved_transaction_and_approval_number(
        approval_number="000000123456")
    assert payment_response == expected_response


def test_should_reject_a_payment_when_the_merchant_is_valid() -> None:
    request = faker.PaymentRequestFaker.with_amount_and_currency(
        total_amount=decimal.Decimal("100.00"),
        currency=money.Currency.EUR
    )
    payment_response = service.process_payment(
        request=request,
        card_processing_adapter=adapter.FakeCardProcessingAdapter())
    expected_response = faker.PaymentResponseFaker.with_rejected_transaction()
    assert payment_response == expected_response
