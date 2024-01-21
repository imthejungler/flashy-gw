import decimal
import enum
from collections.abc import Iterator
from typing import List, Optional

import pydantic

from checkout.card_processing import adapters
from checkout.standard_types import money, card


class Card(pydantic.BaseModel):
    cardholder_name: str
    expiration_month: int
    expiration_year: int
    pan: pydantic.SecretStr
    cvv: pydantic.SecretStr


class Transaction(pydantic.BaseModel):
    client_id: str
    client_reference_id: str
    merchant_id: str
    merchant_economic_activity: str
    currency: money.Currency
    total_amount: decimal.Decimal
    tip: decimal.Decimal
    taxes: List[money.Tax]
    card: Card


class TransactionStatus(enum.Enum):
    PENDING = enum.auto()
    APPROVED = enum.auto()
    REJECTED = enum.auto()


class TransactionResult(pydantic.BaseModel):
    # card_franchise: str
    # card_country: str
    network: card.AcquiringNetwork
    response_code: str
    response_message: str
    approval_code: str
    status: TransactionStatus
    attempts: int = 0


def process_sale(transaction: Transaction,
                 router: adapters.TransactionRouter) -> TransactionResult:
    processors = router.get_acquiring_processing_providers(
        package=adapters.TransactionPackage(franchise=card.Franchise.VISA))

    return _process_transaction(processors=processors, transaction=transaction)


def _process_transaction(
        processors: Iterator[adapters.AcquiringProcessorProvider],
        transaction: Transaction,
        previous_result: Optional[adapters.FinancialMessageResult] = None,
        attempt: int = 0) -> TransactionResult:
    capture_message = _transaction_to_capture_message(transaction)
    processor = next(processors,
                     adapters.NoAcquiringProcessorProviderAvailable(last_financial_message_result=previous_result))
    result = processor.capture(message=capture_message)
    if isinstance(result, adapters.ApprovedCapture):
        """
        I used this approach only here and not in the response of the service
        because normally its going to return to a REST API which would make
        this approach too gimmicky.
        """
        return TransactionResult(
            network=result.network.value,
            response_code=result.response_code,
            response_message=result.response_message,
            approval_code=result.approval_code,
            status=TransactionStatus.APPROVED,
            attempts=attempt
        )

    if isinstance(result, adapters.RejectedCapture) and result.is_retryable:
        attempt = attempt + 1
        return _process_transaction(processors=processors, transaction=transaction, previous_result=result,
                                    attempt=attempt)

    return TransactionResult(
        network=result.network.value,
        response_code=result.response_code,
        response_message=result.response_message,
        status=TransactionStatus.REJECTED,
        approval_code="",
        attempts=attempt
    )


def _transaction_to_capture_message(transaction: Transaction) -> adapters.CaptureMessage:
    return adapters.CaptureMessage(
        merchant_id=transaction.merchant_id,
        currency=transaction.currency,
        total_amount=transaction.total_amount,
        tip=transaction.tip,
        taxes=transaction.taxes,
        cardholder_name=transaction.card.cardholder_name,
        expiration_month=transaction.card.expiration_month,
        expiration_year=transaction.card.expiration_year,
        pan=transaction.card.pan.get_secret_value(),
        cvv=transaction.card.cvv.get_secret_value(),
    )
