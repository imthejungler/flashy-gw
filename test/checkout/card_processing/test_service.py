from checkout.card_processing import services, adapters
from test.checkout.card_processing import faker


def test_should_approve_a_transaction_when_the_acquiring_processor_approves() -> None:
    transaction = faker.TransactionFake.fake()
    transaction_response = services.process_sale(
        transaction=transaction,
        router=faker.StubApprovedTransactionRouter()
    )
    assert transaction_response.status == services.TransactionStatus.APPROVED


def test_should_reject_a_transaction_when_the_acquiring_processor_approves() -> None:
    transaction = faker.TransactionFake.fake()
    transaction_response = services.process_sale(
        transaction=transaction,
        router=faker.StubRejectedTransactionRouter()
    )
    assert transaction_response.status == services.TransactionStatus.REJECTED


def test_franchise_not_supported() -> None:
    ...


def test_retry_transaction() -> None:
    ...


def test_approved_transaction() -> None:
    ...


def test_fraudulent_transaction() -> None:
    ...
