from checkout.card_processing import services, adapters
from test.checkout.card_processing import faker


def test_card_processing() -> None:
    transaction = faker.TransactionFake.fake()
    transaction_response = services.process_sale(
        transaction=transaction,
        router=faker.StubApprovedTransactionRouter()
    )
    assert transaction_response.status == services.TransactionStatus.APPROVED


def test_franchise_not_supported() -> None:
    ...


def test_retry_transaction() -> None:
    ...


def test_approved_transaction() -> None:
    ...


def test_rejected_transaction() -> None:
    ...


def test_fraudulent_transaction() -> None:
    ...
