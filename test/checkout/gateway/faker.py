import decimal
from typing import Optional, Dict, List

import pydantic

from checkout.gateway import adapters, model
from checkout.gateway import services
from checkout.standard_types import money, helpers


class PaymentRequestFaker:
    @staticmethod
    def with_merchant_id(merchant_id: str) -> services.PaymentRequest:
        return services.PaymentRequest(
            merchant_id=merchant_id,
            currency=money.Currency.EUR,
            total_amount=decimal.Decimal("100.00"),
            tip=decimal.Decimal("0"),
            taxes=[],
            card=services.CardRequest(
                cardholder_name="Fulanito de tal",
                expiration_month=1,
                expiration_year=2002,
                pan=pydantic.SecretStr("1234560000001234"),
                cvv=pydantic.SecretStr("123"),
            )
        )


class PaymentResponseFaker:
    @staticmethod
    def with_approved_transaction(payment_id: str, approval_number: str) -> services.PaymentResponse:
        return services.PaymentResponse(
            payment_id=payment_id,
            approval_number=approval_number,
            status="APPROVED"
        )

    @staticmethod
    def with_rejected_transaction(payment_id: str) -> services.PaymentResponse:
        return services.PaymentResponse(
            payment_id=payment_id,
            approval_number="",
            status="REJECTED"
        )


class StubApprovedTransactionCardNotPresentProvider(adapters.CardNotPresentProvider):
    def __init__(self,
                 approval_number: str = "",
                 network: str = "CBK") -> None:
        self.approval_number = approval_number
        self.network = network

    def sale(self, transaction: adapters.Transaction) -> adapters.TransactionResponse:
        return adapters.TransactionResponse(
            transaction_id="fake-transaction-id",
            network=self.network,
            response_code="00",
            response_message="Approved or completed successfully",
            status=adapters.TransactionStatus.APPROVED,
            approval_number=self.approval_number,
        )


class StubRejectedTransactionCardNotPresentProvider(adapters.CardNotPresentProvider):
    def __init__(self,
                 network: str = "CBK") -> None:
        self.network = network

    def sale(self, transaction: adapters.Transaction) -> adapters.TransactionResponse:
        return adapters.TransactionResponse(
            transaction_id="fake-transaction-id",
            network=self.network,
            response_code="05",
            response_message="Do not honor",
            status=adapters.TransactionStatus.REJECTED,
            approval_number="",
        )


class CardNotPresentRepository(adapters.CardNotPresentRepository):

    def __init__(self, ids: List[str]) -> None:
        self.ids = ids
        self.payments: Dict[str, model.CardNotPresentPayment] = {}

    def generate_id(self) -> str:
        return self.ids.pop()

    def find_by_id(self, payment_id: str) -> Optional[model.CardNotPresentPayment]:
        return self.payments.get(payment_id)

    def create_payment(self, payment: model.CardNotPresentPayment) -> None:
        self.payments[payment.payment_id] = payment

    def update_payment(self, payment: model.CardNotPresentPayment) -> None:
        self.payments[payment.payment_id] = payment


class StubPendingCardNotPresentPayment:
    @staticmethod
    def with_payment_id_and_merchant_id(payment_id: str, merchant_id: str) -> model.CardNotPresentPayment:
        return model.CardNotPresentPayment.create(
            merchant_id=merchant_id,
            payment_id=payment_id,
            currency=money.Currency.EUR,
            total_amount=decimal.Decimal("100.00"),
            tip=decimal.Decimal("0"),
            taxes=[],
            card_masked_pan="123456******1234"
        )
