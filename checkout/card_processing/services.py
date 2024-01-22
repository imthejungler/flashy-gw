import decimal
import enum
from collections.abc import Iterator
from typing import Optional

import pydantic

from checkout.card_processing import adapters, model
from checkout.standard_types import money, card


class Card(pydantic.BaseModel):
    cardholder_name: str
    expiration_month: int
    expiration_year: int
    pan: pydantic.SecretStr
    cvv: pydantic.SecretStr


class TransactionRequest(pydantic.BaseModel):
    client_id: str
    client_reference_id: str
    merchant_id: str
    merchant_economic_activity: str
    currency: money.Currency
    total_amount: decimal.Decimal
    tip: decimal.Decimal
    vat: decimal.Decimal
    card: Card


class TransactionStatus(enum.Enum):
    PENDING = enum.auto()
    APPROVED = enum.auto()
    REJECTED = enum.auto()


class TransactionResponse(pydantic.BaseModel):
    card_franchise: str
    card_country: str
    network: card.AcquiringNetwork
    response_code: str
    response_message: str
    approval_code: str
    status: TransactionStatus
    attempts: int = 0


def process_sale(request: TransactionRequest,
                 router: adapters.TransactionRouter,
                 account_range_provider: adapters.AccountRangeProvider,
                 repo: adapters.CardNotPresentTransactionRepository) -> TransactionResponse:
    pan_info = account_range_provider.get_pan_info(pan=request.card.pan)
    processors = router.get_acquiring_processing_providers(
        package=adapters.TransactionPackage(franchise=card.Franchise.VISA))

    return _process_transaction(processors=processors, repo=repo,
                                request=request, pan_info=pan_info)


def _process_transaction(
        processors: Iterator[adapters.AcquiringProcessorProvider],
        repo: adapters.CardNotPresentTransactionRepository,
        request: TransactionRequest, pan_info: adapters.PANInfo,
        previous_result: Optional[adapters.FinancialMessageResult] = None, attempt: int = 0) -> TransactionResponse:
    processor = next(processors, adapters.NoProcessorAvailable(last_financial_message_result=previous_result))

    transaction = repo.register_transaction(
        transaction=_request_and_pan_into_to_transaction(pan_info=pan_info,
                                                         request=request,
                                                         transaction_id=repo.generate_id()))

    result = processor.capture(message=_transaction_request_to_capture_message(request=request))

    if isinstance(result, adapters.ApprovedCapture):
        return _approve_transaction(attempt=attempt, repo=repo, result=result, transaction=transaction)

    if isinstance(result, adapters.RejectedCapture) and result.is_retryable:
        return _retry_transaction(attempt=attempt, pan_info=pan_info, processors=processors, repo=repo, request=request,
                                  result=result, transaction=transaction)

    return _reject_transaction(attempt=attempt, repo=repo, result=result, transaction=transaction)


def _retry_transaction(attempt: int, repo: adapters.CardNotPresentTransactionRepository,
                       pan_info: adapters.PANInfo,
                       processors: Iterator[adapters.AcquiringProcessorProvider],
                       request: TransactionRequest,
                       result: adapters.FinancialMessageResult,
                       transaction: model.CardNotPresentTransaction) -> TransactionResponse:
    transaction.reject(
        network=result.network,
        response_code=result.response_code,
        response_message=result.response_message,
        attempt=attempt,
        was_retryable=result.is_retryable,
    )
    repo.update_transaction(transaction=transaction)
    return _process_transaction(processors=processors, repo=repo,
                                request=request, pan_info=pan_info,
                                previous_result=result, attempt=attempt + 1)


def _reject_transaction(attempt: int, repo: adapters.CardNotPresentTransactionRepository,
                        result: adapters.FinancialMessageResult,
                        transaction: model.CardNotPresentTransaction) -> TransactionResponse:
    transaction.reject(
        network=result.network,
        response_code=result.response_code,
        response_message=result.response_message,
        attempt=attempt,
        was_retryable=result.is_retryable)
    repo.update_transaction(transaction=transaction)
    return TransactionResponse(
        card_franchise=transaction.card_data.franchise,
        card_country=transaction.card_data.country,
        network=result.network.value,
        response_code=result.response_code,
        response_message=result.response_message,
        status=TransactionStatus.REJECTED,
        approval_code="",
        attempts=attempt
    )


def _approve_transaction(attempt: int, repo: adapters.CardNotPresentTransactionRepository,
                         result: adapters.FinancialMessageResult,
                         transaction: model.CardNotPresentTransaction) -> TransactionResponse:
    transaction.approve(
        network=result.network,
        response_code=result.response_code,
        response_message=result.response_message,
        attempt=attempt,
        approval_code=result.approval_code
    )
    repo.update_transaction(transaction=transaction)
    return TransactionResponse(
        card_franchise=transaction.card_data.franchise,
        card_country=transaction.card_data.country,
        network=result.network.value,
        response_code=result.response_code,
        response_message=result.response_message,
        approval_code=result.approval_code,
        status=TransactionStatus.APPROVED,
        attempts=attempt
    )


def _request_and_pan_into_to_transaction(request: TransactionRequest, pan_info: adapters.PANInfo,
                                         transaction_id: str) -> model.CardNotPresentTransaction:
    return model.CardNotPresentTransaction.capture(
        transaction_id=transaction_id,
        client_id=request.client_id,
        client_reference_id=request.client_reference_id,
        merchant_id=request.merchant_id,
        merchant_economic_activity=request.merchant_economic_activity,
        currency=request.currency,
        total_amount=request.total_amount,
        tip=request.tip,
        vat=request.vat,
        cardholder_name=request.card.cardholder_name,
        franchise=pan_info.franchise,
        card_category=pan_info.category,
        card_country=pan_info.country,
        card_masked_pan=card.PAN.mask(request.card.pan.get_secret_value()),
        card_expiration_month=request.card.expiration_month,
        card_expiration_year=request.card.expiration_year,
    )


def _transaction_request_to_capture_message(request: TransactionRequest) -> adapters.CaptureMessage:
    return adapters.CaptureMessage(
        merchant_id=request.merchant_id,
        currency=request.currency,
        total_amount=request.total_amount,
        tip=request.tip,
        taxes=request.taxes,
        cardholder_name=request.card.cardholder_name,
        expiration_month=request.card.expiration_month,
        expiration_year=request.card.expiration_year,
        pan=request.card.pan.get_secret_value(),
        cvv=request.card.cvv.get_secret_value(),
    )
