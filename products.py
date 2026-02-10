from odoo_rpc import OdooRPC
from config import ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_API_KEY, MARKWAVE_COMPANY_ID, VARIANT_PRICES
from product_creator import create_or_update_product_template


# -------------------------
# READ PRODUCTS (Frontend)
# -------------------------
def fetch_products():
    """
    Fetch product VARIANTS from Odoo using JSON-RPC
    """
    odoo = OdooRPC(
        ODOO_URL,
        ODOO_DB,
        ODOO_USERNAME,
        ODOO_API_KEY
    )

    return odoo.call(
        model="product.product",
        method="search_read",
        args=[[]],
        kwargs={
            "fields": [
                "id",
                "name",
                "default_code",
                "list_price",
                "qty_available"
            ],
            "limit": 100
        }
    )


def fetch_products_with_lots():
    """
    Fetch products + variants + prices + LOT numbers + expiry + stock
    """
    odoo = OdooRPC(
        ODOO_URL,
        ODOO_DB,
        ODOO_USERNAME,
        ODOO_API_KEY
    )

    products = odoo.call(
        "product.product",
        "search_read",
        [[]],
        {
            "fields": [
                "id",
                "name",
                "default_code",
                "lst_price",
                "qty_available"
            ]
        }
    )

    result = []

    for p in products:
        quants = odoo.call(
            "stock.quant",
            "search_read",
            [[("product_id", "=", p["id"]), ("quantity", ">", 0)]],
            {"fields": ["quantity", "lot_id"]}
        )

        lots = []
        for q in quants:
            if q["lot_id"]:
                lot = odoo.call(
                    "stock.lot",
                    "read",
                    [[q["lot_id"][0]]],
                    {"fields": ["name", "expiration_date"]}
                )[0]

                lots.append({
                    "lot_number": lot["name"],
                    "expiry_date": lot["expiration_date"],
                    "quantity": q["quantity"]
                })

        result.append({
            "product": p["name"],
            "sku": p["default_code"],
            "price": p["lst_price"],
            "total_stock": p["qty_available"],
            "lots": lots
        })

    return result


# -------------------------
# SYNC PRODUCTS (Admin)
# -------------------------
def create_all_products():
    """
    Create / update products in Odoo (SAFE to re-run)
    """
    create_or_update_product_template("Milk", "Liter")
    create_or_update_product_template("Curd", "Kilogram")
    create_or_update_product_template("Ghee", "Kilogram")
    create_or_update_product_template("Paneer", "Kilogram")


def update_variant_prices():
    """
    Update prices for all product variants based on VARIANT_PRICES config
    Filters by MARKWAVE_COMPANY_ID to only update Markwave products
    """
    odoo = OdooRPC(
        ODOO_URL,
        ODOO_DB,
        ODOO_USERNAME,
        ODOO_API_KEY
    )

    for default_code, price in VARIANT_PRICES.items():
        products = odoo.call(
            "product.product",
            "search",
            [[
                ("default_code", "=", default_code),
                ("company_id", "=", MARKWAVE_COMPANY_ID),
            ]]
        )

        if not products:
            print(f"⚠️ Variant not found: {default_code}")
            continue

        product_id = products[0]

        odoo.call(
            "product.product",
            "write",
            [[product_id], {"lst_price": price}]
        )

        print(f"✅ Updated price: {default_code} → ₹{price}")

