from odoo_rpc import OdooRPC
from config import ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_API_KEY

# Connect
odoo = OdooRPC(
    ODOO_URL,
    ODOO_DB,
    ODOO_USERNAME,
    ODOO_API_KEY
)

# 🔹 Only STORABLE products
product_ids = odoo.call(
    "product.product",
    "search",
    [[["type", "=", "product"]]]
)

print(f"Total storable products found: {len(product_ids)}")

products = odoo.call(
    "product.product",
    "read",
    [product_ids],
    {"fields": ["name", "barcode", "type"]}
)

for product in products:
    if not product["barcode"]:
        new_barcode = str(890000000000 + product["id"])

        odoo.call(
            "product.product",
            "write",
            [[product["id"]], {"barcode": new_barcode}]
        )

        print(f"Added barcode {new_barcode} to {product['name']}")

print("✅ Only storable products processed successfully.")
