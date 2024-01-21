import decimal
import enum
import time
from typing import List

from checkout.standard_types import base_types, money, card


class Payment(base_types.Aggregate):
    merchant_id: str
    payment_id: str
    currency: money.Currency
    total_amount: decimal.Decimal
    tip: decimal.Decimal
    taxes: List[money.Tax]


class PaymentStatus(enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    VOIDED = "VOIDED"


class NotPresentCard(base_types.ValueObjet):
    masked_pan: str


class CardNotPresentPayment(Payment):
    status: PaymentStatus
    card: NotPresentCard

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
            )
        )
