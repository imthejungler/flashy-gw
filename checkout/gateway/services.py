import decimal
import enum
from typing import Optional, List

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

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "merchant_id": "1",
                    "currency": "EUR",
                    "total_amount": "100.0",
                    "tip": "0.0",
                    "vat": "0.0",
                    "card": {
                        "cardholder_name": "Juls Cesar",
                        "expiration_month": 2024,
                        "expiration_year": 12,
                        "pan": "4444444444444444",
                        "cvv": "000"
                    }
                },
                {
                    "merchant_id": "1",
                    "currency": "EUR",
                    "total_amount": "100.0",
                    "tip": "0.0",
                    "vat": "0.0",
                    "card": {
                        "cardholder_name": "Juls Cesar",
                        "expiration_month": 2024,
                        "expiration_year": 12,
                        "pan": "5555555555555555",
                        "cvv": "000"
                    }
                },
                {
                    "merchant_id": "1",
                    "currency": "EUR",
                    "total_amount": "100.0",
                    "tip": "0.0",
                    "vat": "0.0",
                    "card": {
                        "cardholder_name": "Juls Cesar",
                        "expiration_month": 2024,
                        "expiration_year": 12,
                        "pan": "3333333333333333",
                        "cvv": "000"
                    }
                }
            ]
        }
    }


class PaymentStatus(enum.Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class PaymentResponse(pydantic.BaseModel):
    payment_id: str
    status: PaymentStatus
    response_code: str
    response_message: str
    approval_code: str = ""


class GetPaymentResponse(pydantic.BaseModel):
    payment_id: str
    currency: money.Currency
    total_amount: decimal.Decimal
    tip: decimal.Decimal
    vat: decimal.Decimal
    last_four_digits: str
    status: PaymentStatus


class PaymentNotFoundError(Exception):
    message: str = "Payment not found"


def get_payments(
        merchant_id: str,
        repository: adapters.CardNotPresentPaymentRepository) -> List[GetPaymentResponse]:
    payments = repository.get_payments(merchant_id=merchant_id)

    return [GetPaymentResponse(
        payment_id=payment.payment_id,
        currency=payment.currency,
        total_amount=payment.total_amount,
        tip=payment.tip,
        vat=payment.vat,
        last_four_digits=payment.card.masked_pan[-4:],
        status=PaymentStatus[payment.status.value],
    ) for payment in payments]


def get_payment(
        merchant_id: str, payment_id: str,
        repository: adapters.CardNotPresentPaymentRepository) -> Optional[GetPaymentResponse]:
    payment: model.CardNotPresentPayment = repository.find_payment(merchant_id=merchant_id, payment_id=payment_id)
    if not payment:
        return None
    return GetPaymentResponse(
        payment_id=payment.payment_id,
        currency=payment.currency,
        total_amount=payment.total_amount,
        tip=payment.tip,
        vat=payment.vat,
        last_four_digits=payment.card.masked_pan[-4:],
        status=PaymentStatus[payment.status.value],
    )


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

# def get_merchants(repository: adapters.MerchantsRepository):
#     return None
#
# class Merchant:
#
#
# class MerchantResponse:
#     merchants: List[Merchant]
