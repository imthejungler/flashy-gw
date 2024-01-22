from typing import List

import fastapi
from fastapi import FastAPI

from checkout.gateway import services, adapters

app = FastAPI()


#
#
# @app.get("/merchants")
# async def get_merchants() -> services.MerchantResponse:
#     """
#     Get all the merchants. No pagination is required. There's only one.
#     """
#     return services.get_merchants(
#         repository=adapters.PostgresMerchantsRepository()
#     )


@app.post("/v1/payments",
          summary="Makes a payment with the usage of the payment provider services.")
async def make_payment(request: services.PaymentRequest) -> services.PaymentResponse:
    """
    Cards:
    - 4444444444444444 rejects
    - 5555555555555555 rejects,
    - any other causes an approval ex.: 3333111122223333
    """
    return services.process_payment(
        request=request,
        repository=adapters.PostgresCardNotPresentPaymentRepository(),
        processor=adapters.FlashyCardNotPresentProvider()
    )


@app.get("/v1/merchants/{merchant_id}/payments")
async def get_payment(merchant_id: str) -> List[services.GetPaymentResponse]:
    """
    Get a payment from a merchant.
    """
    return services.get_payments(
        merchant_id=merchant_id,
        repository=adapters.PostgresCardNotPresentPaymentRepository()
    )


@app.get("/v1/merchants/{merchant_id}/payments/{payment_id}")
async def get_payment(merchant_id: str, payment_id: str) -> services.GetPaymentResponse:
    """
    Get a payment from a merchant.
    """
    response = services.get_payment(
        merchant_id=merchant_id,
        payment_id=payment_id,
        repository=adapters.PostgresCardNotPresentPaymentRepository()
    )
    if not response:
        raise fastapi.HTTPException(status_code=404, detail="Item not found")

    return response

# @app.get("/api/python")
# def hello_world():
#     print(hi)
#     connection = psycopg2.connect(
#         host=os.environ.get("POSTGRES_HOST"),
#         dbname=os.environ.get("POSTGRES_DATABASE"),
#         user=os.environ.get("POSTGRES_USER"),
#         password=os.environ.get("POSTGRES_PASSWORD"),
#     )
#
#     cursor = connection.cursor()
#     cursor.execute("""SELECT * FROM payments""")
#     values = cursor.fetchall()
#     cursor.close()
#     return values
