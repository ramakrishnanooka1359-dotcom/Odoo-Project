import xmlrpc.client
import os
from config import ODOO_URL, ODOO_DB, ODOO_USERNAME

ODOO_API_KEY = os.getenv("ODOO_API_KEY")

# --------------------------------
# CONNECT TO ODOO
# --------------------------------

common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_API_KEY, {})

models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")

# --------------------------------
# GET COMPANY ID (Hardcoded)
# --------------------------------

company_id = 7
print("Using Company ID:", company_id)

# --------------------------------
# DEFINE PRODUCT VARIANT IDS
# (Replace with your actual IDs)
# --------------------------------

PRODUCTS = {
    "MURRAH": 89,        # replace with actual product.product id
    "JAFARABADI": 90,
    "BANNI": 91,
    "NILI_RAVI": 92,
}

# --------------------------------
# DEFINE STOCK LOCATION IDS
# (Internal Stock locations only)
# --------------------------------

LOCATIONS = {
    "KURNOOL": 52,       # KNL/Stock location id
    "VIJAYAWADA": 58,    # VJA/Stock id
    "GUNTUR": 64,        # GNT/Stock id
    "KAKINADA": 70,      # KKD/Stock id
}

# --------------------------------
# FUNCTION TO ADD SERIAL STOCK
# --------------------------------

def add_serial_stock(product_id, location_id, quantity, prefix):
    for i in range(1, quantity + 1):

        serial_name = f"{prefix}-{i}"

        # 1️⃣ Create Lot / Serial
        lot_id = models.execute_kw(
            ODOO_DB, uid, ODOO_API_KEY,
            'stock.lot', 'create',
            [{
                'name': serial_name,
                'product_id': product_id,
                'company_id': company_id,
            }]
        )

        # 2️⃣ Create Stock Quant
        models.execute_kw(
            ODOO_DB, uid, ODOO_API_KEY,
            'stock.quant', 'create',
            [{
                'product_id': product_id,
                'location_id': location_id,
                'quantity': 1,
                'lot_id': lot_id,
                'company_id': company_id,
            }]
        )

        print(f"Created Serial {serial_name}")

# --------------------------------
# ADD STOCK AS PER YOUR REQUIREMENT
# --------------------------------

# Kurnool Warehouse
add_serial_stock(PRODUCTS["MURRAH"], LOCATIONS["KURNOOL"], 1000, "KUR-MUR")
add_serial_stock(PRODUCTS["JAFARABADI"], LOCATIONS["KURNOOL"], 500, "KUR-JAF")

# Vijayawada Warehouse
add_serial_stock(PRODUCTS["MURRAH"], LOCATIONS["VIJAYAWADA"], 500, "VJA-MUR")
add_serial_stock(PRODUCTS["NILI_RAVI"], LOCATIONS["VIJAYAWADA"], 500, "VJA-NIL")

# Guntur Warehouse
add_serial_stock(PRODUCTS["BANNI"], LOCATIONS["GUNTUR"], 500, "GNT-BAN")

# Kakinada Warehouse
add_serial_stock(PRODUCTS["MURRAH"], LOCATIONS["KAKINADA"], 100, "KKD-MUR")
add_serial_stock(PRODUCTS["JAFARABADI"], LOCATIONS["KAKINADA"], 500, "KKD-JAF")

print("✅ Stock & Serials Added Successfully")
