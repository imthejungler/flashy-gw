from checkout.gateway import services
from checkout.standard_types import money
from test.checkout.gateway import faker
import decimal


def test_should_approve_a_payment_when_the_card_processor_approves_the_transaction() -> None:
    request = faker.PaymentRequestFaker.with_merchant_id(
        merchant_id="fake-merchant-id"
    )
    payment_response = services.process_payment(
        request=request,
        repository=faker.CardNotPresentRepository(ids=["1"]),
        processor=faker.StubApprovedTransactionCardNotPresentProvider(
            approval_number="000000123456"
        ))
    expected_response = faker.PaymentResponseFaker.with_approved_transaction(
        payment_id="1",
        approval_number="000000123456")
    assert payment_response == expected_response


def test_should_reject_a_payment_when_the_card_processor_rejects_the_transaction() -> None:
    request = faker.PaymentRequestFaker.with_merchant_id(
        merchant_id="fake-merchant-id"
    )
    payment_response = services.process_payment(
        request=request,
        repository=faker.CardNotPresentRepository(ids=["1"]),
        processor=faker.StubRejectedTransactionCardNotPresentProvider())
    expected_response = faker.PaymentResponseFaker.with_rejected_transaction(payment_id="1")
    assert payment_response == expected_response


def test_should_save_the_transaction_result() -> None:
    request = faker.PaymentRequestFaker.with_merchant_id(
        merchant_id="fake-merchant-id"
    )

    repository = faker.CardNotPresentRepository(ids=["1"])
    expected_payment = faker.StubPendingCardNotPresentPayment.with_payment_id_and_merchant_id(
        payment_id="1", merchant_id="fake-merchant-id")

    services.process_payment(
        request=request,
        repository=repository,
        processor=faker.StubRejectedTransactionCardNotPresentProvider())

    assert expected_payment == repository.find_by_id(payment_id="1")
