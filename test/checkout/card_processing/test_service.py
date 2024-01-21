import pytest

from checkout.card_processing import services, adapters
from test.checkout.card_processing import faker


@pytest.mark.parametrize(
    "router, expected_attempts, expected_status",
    [(faker.StubApprovedTransactionRouter(), 0, services.TransactionStatus.APPROVED),
     (faker.StubRetryableApprovedTransactionRouter(), 1, services.TransactionStatus.APPROVED),
     (faker.StubRejectedTransactionRouter(), 0, services.TransactionStatus.REJECTED),
     (faker.StubRetryableRejectedTransactionRouter(), 1, services.TransactionStatus.REJECTED),
     (faker.StubAllRetryableRejectedTransactionRouter(), 2, services.TransactionStatus.REJECTED),
     ]
)
def test_should_process_transaction_accordingly(
        router: adapters.TransactionRouter, expected_attempts: int,
        expected_status: services.TransactionStatus) -> None:
    request = faker.TransactionFake.fake()
    transaction_response = services.process_sale(
        request=request,
        router=router,
        account_range_provider=faker.StubAccountRangeProvider(),
        repo=faker.FakeCardNotPresentTransactionRepository(ids=["1", "2", "3"])
    )
    assert transaction_response.status == expected_status
    assert transaction_response.attempts == expected_attempts


def test_franchise_not_supported() -> None:
    ...


def test_approved_transaction() -> None:
    ...


def test_fraudulent_transaction() -> None:
    ...
