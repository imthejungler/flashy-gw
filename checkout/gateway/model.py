import decimal
import enum

from checkout.standard_types import base_types, money, helpers


class Receipt(base_types.ValueObjet):
    response_code: str
    response_message: str
    approval_code: str = ""


class PendingReceipt(Receipt):
    response_code: str = "F99"
    response_message: str = "Pending Payment"
    approval_code: str = ""


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
    vat: decimal.Decimal
    receipt: Receipt
    status: PaymentStatus
    card: NotPresentCard
    payment_date: int

    @classmethod
    def create(
            cls,
            *,
            merchant_id: str,
            payment_id: str,
            currency: money.Currency,
            total_amount: decimal.Decimal,
            tip: decimal.Decimal,
            vat: decimal.Decimal,
            card_masked_pan: str,
    ) -> "CardNotPresentPayment":
        return cls(
            merchant_id=merchant_id,
            payment_id=payment_id,
            currency=currency,
            total_amount=total_amount,
            tip=tip,
            vat=vat,
            status=PaymentStatus.PENDING,
            card=NotPresentCard(
                masked_pan=card_masked_pan
            ),
            payment_date=helpers.time_ns(),
            receipt=PendingReceipt()
        )

    def approve(self, response_code: str, response_message: str, approval_code: str) -> None:
        self.status = PaymentStatus.APPROVED
        self.receipt = Receipt(
            response_code=response_code,
            response_message=response_message,
            approval_code=approval_code
        )

    def reject(self, response_code: str, response_message: str) -> None:
        self.status = PaymentStatus.REJECTED
        self.receipt = Receipt(
            response_code=response_code,
            response_message=response_message,
        )
