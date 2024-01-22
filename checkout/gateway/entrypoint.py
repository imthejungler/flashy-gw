from fastapi import FastAPI

from checkout.gateway import services, adapters

app = FastAPI()


@app.post("/v1/payments")
async def make_payment(request: services.PaymentRequest) -> services.PaymentResponse:
    """
    Makes a payment with the usage of the payment provider services.
    """
    return services.process_payment(
        request=request,
        repository=adapters.PostgresCardNotPresentPaymentRepository(),
        processor=adapters.FlashyCardNotPresentProvider()
    )

# @app.get("/v1/payments/{payment_id}")
# async def get_payment(payment_id: str) -> services.PaymentResponse:
#     return {"message": f"Hello {payment_id}"}`


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
