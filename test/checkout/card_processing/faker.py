import decimal
from collections.abc import Iterator
from datetime import datetime

from checkout.card_processing import services, adapters
from checkout.standard_types import money, card


class TransactionFake:
    @staticmethod
    def fake() -> services.Transaction:
        return services.Transaction(
            merchant_id="fake-merchant-id",
            merchant_economic_activity="fake-merchant-economic-activity",
            client_id="fake-client-id",
            client_reference_id="fake-client-reference-id",
            currency=money.Currency.EUR,
            total_amount=decimal.Decimal("100.00"),
            tip=decimal.Decimal("0.00"),
            taxes=[],
            card=services.Card(
                cardholder_name="fake-cardholder-name",
                expiration_month=datetime.today().month,
                expiration_year=datetime.today().year,
                pan="1234567890123456",
                cvv="000",
            ),
        )


class StubApprovedAcquiringProcessorTransactionProvider(adapters.AcquiringProcessorProvider):
    def capture(self, message: adapters.CaptureMessage) -> adapters.FinancialMessageResult:
        return adapters.ApprovedCapture(
            network=card.AcquiringNetwork.CKO,
            response_code="00",
            response_message="Approved or completed successfully",
            interchange_rate=decimal.Decimal("0.10"),
            approval_code="ABCDEFG1234",
        )


class StubRejectedAcquiringProcessorTransactionProvider(adapters.AcquiringProcessorProvider):
    def capture(self, message: adapters.CaptureMessage) -> adapters.FinancialMessageResult:
        return adapters.RejectedCapture(
            network=card.AcquiringNetwork.CKO,
            response_code="43",
            response_message="Stolen card, pick up",
            interchange_rate=decimal.Decimal("0.10"),
            is_retryable=False
        )


class StubRetryableRejectedAcquiringProcessorTransactionProvider(adapters.AcquiringProcessorProvider):
    def capture(self, message: adapters.CaptureMessage) -> adapters.FinancialMessageResult:
        return adapters.RejectedCapture(
            network=card.AcquiringNetwork.CKO,
            response_code="19",
            response_message="Re-enter transaction",
            interchange_rate=decimal.Decimal("0.10"),
            is_retryable=True
        )


class StubApprovedTransactionRouter(adapters.TransactionRouter):
    def get_acquiring_processing_providers(
            self, package: adapters.TransactionPackage) -> Iterator[adapters.AcquiringProcessorProvider]:
        yield StubApprovedAcquiringProcessorTransactionProvider()


class StubRejectedTransactionRouter(adapters.TransactionRouter):
    def get_acquiring_processing_providers(
            self, package: adapters.TransactionPackage) -> Iterator[adapters.AcquiringProcessorProvider]:
        yield StubRejectedAcquiringProcessorTransactionProvider()


class StubRetryableRejectedTransactionRouter(adapters.TransactionRouter):
    def get_acquiring_processing_providers(
            self, package: adapters.TransactionPackage) -> Iterator[adapters.AcquiringProcessorProvider]:
        yield StubRetryableRejectedAcquiringProcessorTransactionProvider()
        yield StubRejectedAcquiringProcessorTransactionProvider()


class StubRetryableApprovedTransactionRouter(adapters.TransactionRouter):
    def get_acquiring_processing_providers(
            self, package: adapters.TransactionPackage) -> Iterator[adapters.AcquiringProcessorProvider]:
        yield StubRetryableRejectedAcquiringProcessorTransactionProvider()
        yield StubApprovedAcquiringProcessorTransactionProvider()
