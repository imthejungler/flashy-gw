import decimal
import enum

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
    vat: decimal.Decimal
    card: CardRequest


class PaymentStatus(enum.Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class PaymentResponse(pydantic.BaseModel):
    payment_id: str
    status: PaymentStatus
    response_code: str
    response_message: str
    approval_code: str = ""


def process_payment(request: PaymentRequest,
                    repository: adapters.CardNotPresentPaymentRepository,
                    processor: adapters.CardNotPresentProvider) -> PaymentResponse:
    payment_id = repository.generate_id()

    payment = repository.create_payment(payment=_map_request_to_model(
        payment_id=payment_id, request=request))

    response = processor.sale(
        transaction=_map_request_to_adapter_transaction(
            payment_id=payment_id, request=request))

    if response.status == adapters.TransactionStatus.APPROVED:
        payment.approve(response_code=response.response_code,
                        response_message=response.response_message,
                        approval_code=response.approval_code)
        repository.update_payment(payment=payment)
        return PaymentResponse(
            payment_id=payment_id,
            response_code=response.response_code,
            response_message=response.response_message,
            approval_code=response.approval_code,
            status=PaymentStatus.APPROVED
        )

    payment.reject(response_code=response.response_code,
                   response_message=response.response_message)
    repository.update_payment(payment=payment)
    return PaymentResponse(
        payment_id=payment_id,
        response_code=response.response_code,
        response_message=response.response_message,
        approval_code=response.approval_code,
        status=PaymentStatus.REJECTED
    )


def _map_request_to_model(payment_id: str, request: PaymentRequest) -> model.CardNotPresentPayment:
    return model.CardNotPresentPayment.create(
        merchant_id=request.merchant_id,
        payment_id=payment_id,
        currency=request.currency,
        total_amount=request.total_amount,
        tip=request.tip,
        vat=request.vat,
        card_masked_pan=card.PAN.mask(request.card.pan.get_secret_value()),
    )


def _map_request_to_adapter_transaction(payment_id: str, request: PaymentRequest) -> adapters.Transaction:
    return adapters.Transaction(
        client_reference_id=payment_id,
        currency=request.currency,
        merchant_id=request.merchant_id,
        total_amount=request.total_amount,
        tip=request.tip,
        vat=request.vat,
        card=adapters.Card(
            cardholder_name=request.card.cardholder_name,
            expiration_month=request.card.expiration_month,
            expiration_year=request.card.expiration_year,
            pan=request.card.pan.get_secret_value(),
            cvv=request.card.cvv.get_secret_value(),
        ),
    )
