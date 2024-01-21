import decimal
import enum
import uuid
from typing import List, Optional

import pydantic

from checkout.gateway import adapter
from checkout.standard_types import money
from checkout.standard_types.helpers import IDGenerator


class CardRequest(pydantic.BaseModel):
    cardholder_name: str
    expiration_month: int
    expiration_year: int
    pan: pydantic.SecretStr
    cvv: pydantic.SecretStr


class PaymentRequest(pydantic.BaseModel):
    merchant_id: str
    currency: money.Currency
    total_amount: decimal.Decimal
    tip: decimal.Decimal
    taxes: List[money.Tax]
    card: CardRequest


class PaymentStatus(enum.Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class PaymentResponse(pydantic.BaseModel):
    approval_number: Optional[str]
    status: PaymentStatus


def process_payment(request: PaymentRequest,
                    card_processing_adapter: adapter.CardProcessingAdapter) -> PaymentResponse:
    payment_id = IDGenerator.uuid(prefix="CP" + request.merchant_id)
    transaction_response = card_processing_adapter.sale(
        transaction=adapter.Transaction(
            client_reference_id=payment_id,
            currency=request.currency,
            total_amount=request.total_amount,
            tip=request.tip,
            taxes=request.taxes,
            card=adapter.Card(
                cardholder_name=request.card.cardholder_name,
                expiration_month=request.card.expiration_month,
                expiration_year=request.card.expiration_year,
                pan=request.card.pan.get_secret_value(),
                cvv=request.card.cvv.get_secret_value(),
            ),
        ))

    if transaction_response.status == adapter.TransactionStatus.APPROVED:
        return PaymentResponse(
            approval_number=transaction_response.approval_number,
            status=PaymentStatus.APPROVED
        )

    return PaymentResponse(
            approval_number=transaction_response.approval_number,
            status=PaymentStatus.REJECTED
        )
