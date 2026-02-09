from fastapi import FastAPI
from products import fetch_products_with_lots, create_all_products

app = FastAPI(title="Odoo Inventory API")

@app.get("/")
def health():
    return {"status": "running"}

@app.get("/products")
def get_products():
    """
    Frontend API: returns Odoo prices & stock
    """
    return fetch_products_with_lots()

@app.post("/sync-products")
def sync_products():
    """
    Admin API: creates/syncs products
    """
    create_all_products()
    return {"message": "Product sync completed"}
