import abc
import decimal
import enum
from typing import List, Optional

import pydantic

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
    def sale(self, payment: Transaction) -> TransactionResponse:
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

    # @abc.abstractmethod
    # def authorize(self, transaction: Transaction) -> TransactionResponse:
    #     """
    #     Authorize a transaction:
    #     - Validates the card data,
    #     - Checks the card's restrictions,
    #     - Evaluates the transaction against an anti-fraud system,
    #
    #     if any of this conditions fails, returns a rejected transaction.
    #
    #     Otherwise, returns the response of the Acquiring processor.
    #     :return:
    #     TransactionResponse
    #     """
    #
    # @abc.abstractmethod
    # def capture(self, authorized_transaction: AutorizedTransaction) -> TransactionResponse:
    #     """
    #     Captures a previously authorized transaction:
    #     - Validates the card data,
    #     - Checks the card's restrictions,
    #     - Evaluates the transaction against an anti-fraud system,
    #
    #     if any of this conditions fails, returns a rejected transaction.
    #
    #     Otherwise, returns the response of the Acquiring processor.
    #     :return:
    #     TransactionResponse
    #     """


class DefaultCardNotPresentProvider(CardNotPresentProvider):
    def sale(self, payment: Transaction) -> TransactionResponse:
        pass


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
