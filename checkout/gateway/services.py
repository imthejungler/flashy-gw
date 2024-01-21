import decimal
import enum
from typing import List, Optional

import pydantic

from checkout.gateway import adapters, model
from checkout.standard_types import money, card


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
    payment_id: str
    status: PaymentStatus
    approval_number: Optional[str] = None


def process_payment(request: PaymentRequest,
                    repository: adapters.CardNotPresentRepository,
                    processor: adapters.CardNotPresentProvider) -> PaymentResponse:
    payment_id = repository.generate_id()

    payment = repository.create_payment(payment=_map_request_to_model(
        payment_id=payment_id, request=request))

    transaction_response = processor.sale(
        payment=_map_request_to_adapter_transaction(
            payment_id=payment_id, request=request))

    if transaction_response.status == adapters.TransactionStatus.APPROVED:
        payment.approve(approval_number=transaction_response.approval_number)
        repository.update_payment(payment=payment)
        return PaymentResponse(
            payment_id=payment_id,
            approval_number=transaction_response.approval_number,
            status=PaymentStatus.APPROVED
        )

    payment.reject(rejection_code=transaction_response.response_code,
                   rejection_message=transaction_response.response_message)
    repository.update_payment(payment=payment)
    return PaymentResponse(
        payment_id=payment_id,
        approval_number=transaction_response.approval_number,
        status=PaymentStatus.REJECTED
    )


def _map_request_to_model(payment_id: str, request: PaymentRequest) -> model.CardNotPresentPayment:
    return model.CardNotPresentPayment.create(
        merchant_id=request.merchant_id,
        payment_id=payment_id,
        currency=request.currency,
        total_amount=request.total_amount,
        tip=request.tip,
        taxes=request.taxes,
        card_masked_pan=card.PAN.mask(request.card.pan.get_secret_value()),
    )


def _map_request_to_adapter_transaction(payment_id: str, request: PaymentRequest) -> adapters.Transaction:
    return adapters.Transaction(
        client_reference_id=payment_id,
        currency=request.currency,
        total_amount=request.total_amount,
        tip=request.tip,
        taxes=request.taxes,
        card=adapters.Card(
            cardholder_name=request.card.cardholder_name,
            expiration_month=request.card.expiration_month,
            expiration_year=request.card.expiration_year,
            pan=request.card.pan.get_secret_value(),
            cvv=request.card.cvv.get_secret_value(),
        ),
    )
