from fastapi import FastAPI
from products import fetch_products_with_lots, create_all_products, fetch_animal_kart_products_with_locations
from orders import create_sale_order
from config import MARKWAVE_COMPANY_ID, ANIMAL_KART_COMPANY_ID

app = FastAPI(title="Multi Company Odoo API")



@app.get("/")
def health():
    return {"status": "running"}


# ==========================
# MARKWAVE API
# ==========================
@app.get("/markwave/products")
def get_markwave_products():
    return fetch_products_with_lots(MARKWAVE_COMPANY_ID)


@app.post("/markwave/orders")
def create_markwave_order(order_data: dict):
    return create_sale_order(
        company_id=MARKWAVE_COMPANY_ID,
        customer_id=order_data["customer_id"],
        order_lines=order_data["items"]
    )


# ==========================
# ANIMAL KART API
# ==========================
@app.get("/animal-kart/products")
def get_animal_kart_products():
    return fetch_animal_kart_products_with_locations()


@app.post("/animal-kart/orders")
def create_animal_kart_order(order_data: dict):
    return create_sale_order(
        company_id=ANIMAL_KART_COMPANY_ID,
        customer_id=order_data["customer_id"],
        order_lines=order_data["items"]
    )
