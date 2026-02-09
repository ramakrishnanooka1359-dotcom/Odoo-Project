from fastapi import FastAPI
from products import create_all_products

app = FastAPI(title="Odoo Inventory API")

@app.get("/")
def health():
    return {"status": "running"}

@app.post("/sync-products")
def sync_products():
    create_all_products()
    return {"message": "Product sync completed"}
