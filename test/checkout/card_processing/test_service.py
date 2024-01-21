from checkout.card_processing import services, adapters
from test.checkout.card_processing import faker


def test_should_approve_a_transaction_when_the_acquiring_processor_approves() -> None:
    transaction = faker.TransactionFake.fake()
    transaction_response = services.process_sale(
        transaction=transaction,
        router=faker.StubApprovedTransactionRouter()
    )
    assert transaction_response.status == services.TransactionStatus.APPROVED


def test_should_reject_a_transaction_when_the_acquiring_processor_rejects() -> None:
    transaction = faker.TransactionFake.fake()
    transaction_response = services.process_sale(
        transaction=transaction,
        router=faker.StubRejectedTransactionRouter()
    )
    assert transaction_response.status == services.TransactionStatus.REJECTED
    assert transaction_response.attempts == 0


def test_should_reject_and_retry_a_transaction_when_id_rejected_by_one_processor_but_both_rejected() -> None:
    transaction = faker.TransactionFake.fake()
    transaction_response = services.process_sale(
        transaction=transaction,
        router=faker.StubRetryableRejectedTransactionRouter()
    )
    assert transaction_response.status == services.TransactionStatus.REJECTED
    assert transaction_response.attempts == 1


def test_should_reject_and_retry_a_transaction_when_id_rejected_by_one_processor_and_the_last_approved() -> None:
    transaction = faker.TransactionFake.fake()
    transaction_response = services.process_sale(
        transaction=transaction,
        router=faker.StubRetryableApprovedTransactionRouter()
    )
    assert transaction_response.status == services.TransactionStatus.APPROVED
    assert transaction_response.attempts == 1


def test_franchise_not_supported() -> None:
    ...


def test_approved_transaction() -> None:
    ...


def test_fraudulent_transaction() -> None:
    ...
