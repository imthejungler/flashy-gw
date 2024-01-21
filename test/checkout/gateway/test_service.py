import time
from unittest import mock

from checkout.gateway import services
from test.checkout.gateway import faker


@mock.patch("checkout.standard_types.helpers.time_ns", return_value=time.time_ns())
def test_should_approve_a_payment_when_the_card_processor_approves_the_transaction(time_ns_mock: int) -> None:
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


@mock.patch("checkout.standard_types.helpers.time_ns", return_value=time.time_ns())
def test_should_reject_a_payment_when_the_card_processor_rejects_the_transaction(time_ns_mock: int) -> None:
    request = faker.PaymentRequestFaker.with_merchant_id(
        merchant_id="fake-merchant-id"
    )
    payment_response = services.process_payment(
        request=request,
        repository=faker.CardNotPresentRepository(ids=["1"]),
        processor=faker.StubRejectedTransactionCardNotPresentProvider())
    expected_response = faker.PaymentResponseFaker.with_rejected_transaction(payment_id="1")
    assert payment_response == expected_response


@mock.patch("checkout.standard_types.helpers.time_ns", return_value=time.time_ns())
def test_should_save_the_transaction_result(time_ns_mock: mock.MagicMock) -> None:
    request = faker.PaymentRequestFaker.with_merchant_id(
        merchant_id="fake-merchant-id"
    )

    repository = faker.CardNotPresentRepository(ids=["1"])
    expected_payment = faker.StubApprovedCardNotPresentPayment.with_attrs(
        payment_id="1", merchant_id="fake-merchant-id",
        approval_number="000000123456", time_ns=time_ns_mock.return_value)

    services.process_payment(
        request=request,
        repository=repository,
        processor=faker.StubApprovedTransactionCardNotPresentProvider(
            approval_number="000000123456"
        ))

    assert expected_payment == repository.find_by_id(payment_id="1")
