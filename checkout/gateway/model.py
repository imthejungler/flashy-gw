import decimal
import enum
from typing import List

from checkout.standard_types import base_types, money, helpers


class Receipt(base_types.ValueObjet):
    post_time: int


class ApprovalReceipt(Receipt):
    approval_number: str


class RejectionReceipt(Receipt):
    rejection_code: str
    rejection_message: str


class PendingReceipt(Receipt):
    post_time: int = 0


class PaymentStatus(enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    VOIDED = "VOIDED"


class NotPresentCard(base_types.ValueObjet):
    masked_pan: str


class CardNotPresentPayment(base_types.Aggregate):
    merchant_id: str
    payment_id: str
    currency: money.Currency
    total_amount: decimal.Decimal
    tip: decimal.Decimal
    taxes: List[money.Tax]
    receipt: Receipt
    status: PaymentStatus
    card: NotPresentCard

    def approve(self, approval_number: str) -> None:
        self.status = PaymentStatus.APPROVED
        self.receipt = ApprovalReceipt(
            post_time=helpers.time_ns(),
            approval_number=approval_number
        )

    def reject(self, rejection_code: str, rejection_message: str) -> None:
        self.status = PaymentStatus.REJECTED
        self.receipt = RejectionReceipt(
            post_time=helpers.time_ns(),
            rejection_code=rejection_code,
            rejection_message=rejection_message
        )

    @classmethod
    def create(
            cls,
            *,
            merchant_id: str,
            payment_id: str,
            currency: money.Currency,
            total_amount: decimal.Decimal,
            tip: decimal.Decimal,
            taxes: List[money.Tax],
            card_masked_pan: str,
    ) -> "CardNotPresentPayment":
        return cls(
            merchant_id=merchant_id,
            payment_id=payment_id,
            currency=currency,
            total_amount=total_amount,
            tip=tip,
            taxes=taxes,
            status=PaymentStatus.PENDING,
            card=NotPresentCard(
                masked_pan=card_masked_pan
            ),
            receipt=PendingReceipt()
        )
