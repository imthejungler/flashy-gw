import abc
import decimal
import enum
from typing import List, Optional

import pydantic

from checkout.card_processing import services, adapters
from checkout.gateway import model
from checkout.standard_types import money


# CARD PROCESSING ADAPTER #########################################
class Card(pydantic.BaseModel):
    cardholder_name: str
    expiration_month: int
    expiration_year: int
    pan: pydantic.SecretStr
    cvv: pydantic.SecretStr


class Transaction(pydantic.BaseModel):
    client_id: str = "FLASHY_GW"
    client_reference_id: str
    currency: money.Currency
    total_amount: decimal.Decimal
    tip: decimal.Decimal
    taxes: List[money.Tax]
    card: Card


class TransactionStatus(enum.Enum):
    PENDING = enum.auto()
    APPROVED = enum.auto()
    REJECTED = enum.auto()


class TransactionResponse(pydantic.BaseModel):
    network: str
    response_code: str
    response_message: str
    approval_number: str
    status: TransactionStatus


class CardNotPresentProvider(abc.ABC):
    @abc.abstractmethod
    def sale(self, transaction: Transaction) -> TransactionResponse:
        """
        Authorizes and captures a transaction in one step:
        - Validates the card data,
        - Checks the card's restrictions,
        - Evaluates the transaction against an anti-fraud system,

        if any of these conditions fails, returns a rejected transaction.

        Otherwise, returns the response of the Acquiring processor.
        :return:
        TransactionResponse
        """


class DefaultCardNotPresentProvider(CardNotPresentProvider):
    def sale(self, transaction: Transaction) -> TransactionResponse:
        return services.process_sale(
            request=DefaultCardNotPresentProvider._transaction_to_request(transaction=transaction),
            router=adapters.DefaultTransactionRouter(),
            account_range_provider=adapters.DefaultAccountRangeProvider(),
            repo=adapters.DefaultCardNotPresentTransactionRepository()
        )

    @staticmethod
    def _transaction_to_request(transaction: Transaction) -> services.TransactionRequest:
        return services.TransactionRequest(
            client_id=transaction.client_id,
            client_reference_id=transaction.client_reference_id,
            merchant_id=transaction.merchant_id,
            merchant_economic_activity=transaction.merchant_economic_activity,
            currency=transaction.currency,
            total_amount=transaction.total_amount,
            tip=transaction.tip,
            taxes=transaction.taxes,
            card=services.Card(
                cardholder_name=transaction.card.cardholder_name,
                expiration_month=transaction.card.expiration_month,
                expiration_year=transaction.card.expiration_year,
                pan=transaction.card.pan,
                cvv=transaction.card.cvv,
            ),
        )


# PAYMENT REPOSITORY #########################################
class CardNotPresentPaymentRepository(abc.ABC):

    @abc.abstractmethod
    def generate_id(self) -> str:
        ...

    @abc.abstractmethod
    def find_by_id(self, payment_id: str) -> Optional[model.CardNotPresentPayment]:
        ...

    @abc.abstractmethod
    def create_payment(self, payment: model.CardNotPresentPayment) -> model.CardNotPresentPayment:
        ...

    @abc.abstractmethod
    def update_payment(self, payment: model.CardNotPresentPayment) -> model.CardNotPresentPayment:
        ...


class DefaultCardNotPresentPaymentRepository(CardNotPresentPaymentRepository):
    def generate_id(self) -> str:
        pass

    def find_by_id(self, payment_id: str) -> Optional[model.CardNotPresentPayment]:
        pass

    def create_payment(self, payment: model.CardNotPresentPayment) -> model.CardNotPresentPayment:
        pass

    def update_payment(self, payment: model.CardNotPresentPayment) -> model.CardNotPresentPayment:
        pass
