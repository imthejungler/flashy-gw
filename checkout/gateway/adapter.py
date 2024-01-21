import abc
import decimal
import enum
from typing import List

import pydantic

from checkout.standard_types import money


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


class CardProcessingAdapter(abc.ABC):
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


class FakeCardProcessingAdapter(CardProcessingAdapter):

    def __init__(self,
                 approval_number: str = "",
                 network: str = "CBK") -> None:
        self.approval_number = approval_number
        self.network = network

    def sale(self, transaction: Transaction) -> TransactionResponse:
        return TransactionResponse(
            transaction_id="fake-transaction-id",
            network=self.network,
            response_code="00",
            response_message="Approved or completed successfully",
            status=TransactionStatus.APPROVED,
            approval_number=self.approval_number,
        )


class DefaultCardProcessingAdapter(CardProcessingAdapter):
    def sale(self, transaction: Transaction) -> TransactionResponse:
        pass
