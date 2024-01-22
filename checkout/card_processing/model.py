import decimal
import enum

import pydantic

from checkout.standard_types import money, card, helpers


class TransactionTypes(enum.Enum):
    AUTHORIZATION = "AUTHORIZATION"
    CAPTURE = "CAPTURE"
    REVERSAL = "REVERSAL"
    VOID = "VOID"


class PCIComplianceCard(pydantic.BaseModel):
    cardholder_name: str
    franchise: str
    category: str
    country: str
    masked_pan: str
    expiration_month: int
    expiration_year: int


class TransactionStatus(enum.Enum):
    PROCESSING = "PROCESSING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class NetworkResponse(pydantic.BaseModel):
    network: card.AcquiringNetwork
    response_code: str
    response_message: str
    approval_code: str
    attempt: int = 0


class ApprovedNetworkResponse(NetworkResponse):
    approval_code: str


class RejectNetworkResponse(NetworkResponse):
    was_retryable: bool
    approval_code: str = ""


class NoNetworkResponse(NetworkResponse):
    network: card.AcquiringNetwork = card.AcquiringNetwork.NONE
    response_code: str = "F99"
    response_message: str = "Processing Transaction"
    approval_code: str = ""
    attempt: int = 0


class CardNotPresentTransaction(pydantic.BaseModel):
    transaction_id: str
    client_id: str
    client_reference_id: str
    merchant_id: str
    transaction_type: TransactionTypes
    currency: money.Currency
    total_amount: decimal.Decimal
    tip: decimal.Decimal
    vat: decimal.Decimal
    card_data: PCIComplianceCard
    status: TransactionStatus
    network_response: NetworkResponse
    transaction_date: int

    @classmethod
    def capture(
            cls,
            *,
            transaction_id: str,
            client_id: str,
            client_reference_id: str,
            merchant_id: str,
            currency: money.Currency,
            total_amount: decimal.Decimal,
            tip: decimal.Decimal,
            vat: decimal.Decimal,
            cardholder_name: str,
            franchise: str,
            card_country: str,
            card_category: str,
            card_masked_pan: str,
            card_expiration_month: int,
            card_expiration_year: int,
    ) -> "CardNotPresentTransaction":
        return cls(
            transaction_id=transaction_id,
            client_id=client_id,
            client_reference_id=client_reference_id,
            merchant_id=merchant_id,
            currency=currency,
            total_amount=total_amount,
            tip=tip,
            vat=vat,
            card_data=PCIComplianceCard(
                cardholder_name=cardholder_name,
                country=card_country,
                franchise=franchise,
                category=card_category,
                masked_pan=card_masked_pan,
                expiration_month=card_expiration_month,
                expiration_year=card_expiration_year,
            ),
            transaction_type=TransactionTypes.CAPTURE,
            status=TransactionStatus.PROCESSING,
            network_response=NoNetworkResponse(),
            transaction_date=helpers.time_ns(),
        )

    def approve(self,
                network: card.AcquiringNetwork,
                response_code: str,
                response_message: str,
                attempt: int,
                approval_code: str) -> None:
        self.status = TransactionStatus.APPROVED
        self.network_response = ApprovedNetworkResponse(
            network=network,
            response_code=response_code,
            response_message=response_message,
            attempt=attempt,
            approval_code=approval_code
        )

    def reject(self,
               network: card.AcquiringNetwork,
               response_code: str,
               response_message: str,
               attempt: int,
               was_retryable: bool) -> None:
        self.status = TransactionStatus.REJECTED
        self.network_response = RejectNetworkResponse(
            network=network,
            response_code=response_code,
            response_message=response_message,
            attempt=attempt,
            was_retryable=was_retryable
        )
