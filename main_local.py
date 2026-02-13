from fastapi import FastAPI
from products import fetch_products_with_lots
from config import MARKWAVE_COMPANY_ID, ANIMAL_KART_COMPANY_ID

app = FastAPI(title="Multi Company Odoo API - LOCAL")


@app.get("/")
def health():
    return {"status": "running locally"}


# ==========================
# MARKWAVE API
# ==========================
@app.get("/markwave/products")
def get_markwave_products():
    return fetch_products_with_lots(MARKWAVE_COMPANY_ID)


# ==========================
# ANIMAL KART API
# ==========================
@app.get("/animal-kart/products")
def get_animal_kart_products():
    return fetch_products_with_lots(ANIMAL_KART_COMPANY_ID)
