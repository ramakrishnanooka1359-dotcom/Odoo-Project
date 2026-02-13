from odoo_rpc import OdooRPC
from config import ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_API_KEY, MARKWAVE_COMPANY_ID, ANIMAL_KART_COMPANY_ID, VARIANT_PRICES
from product_creator import create_or_update_product_template


# -------------------------
# READ PRODUCTS (Frontend)
# -------------------------
def fetch_products(company_id: int):
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
        args=[[
            ("company_id", "=", company_id),
            ("type", "=", "product"),
            ("sale_ok", "=", True)
        ]],
        kwargs={
            "fields": [
                "id",
                "display_name",
                "default_code",
                "barcode",
                "lst_price",
                "standard_price",
                "qty_available",
                "product_template_attribute_value_ids"
            ],
            "context": {
                "allowed_company_ids": [company_id]
            },
            "limit": 100
        }
    )


def fetch_products_with_lots(company_id: int):
    """
    Fetch storable products for a specific company
    """
    odoo = OdooRPC(
        ODOO_URL,
        ODOO_DB,
        ODOO_USERNAME,
        ODOO_API_KEY
    )

    # ✅ Fetch only storable products for specific company
    products = odoo.call(
        "product.product",
        "search_read",
        [[
            ("type", "=", "product"),        # Only Storable
            ("sale_ok", "=", True),
            ("company_id", "=", company_id)
        ]],
        {
            "fields": [
                "id",
                "display_name",
                "default_code",
                "barcode",
                "lst_price",
                "standard_price",
                "qty_available",
                "product_template_attribute_value_ids"
            ],
            "context": {
                "allowed_company_ids": [company_id]
            }
        }
    )

    result = []

    for p in products:
        # ✅ Filter stock quants by company
        quants = odoo.call(
            "stock.quant",
            "search_read",
            [[
                ("product_id", "=", p["id"]),
                ("quantity", ">", 0),
                ("company_id", "=", company_id)
            ]],
            {
                "fields": ["quantity", "lot_id"],
                "context": {
                    "allowed_company_ids": [company_id]
                }
            }
        )

        lots = []
        for q in quants:
            if q["lot_id"]:
                lot = odoo.call(
                    "stock.lot",
                    "read",
                    [[q["lot_id"][0]]],
                    {
                        "fields": ["name", "expiration_date"],
                        "context": {
                            "allowed_company_ids": [company_id]
                        }
                    }
                )[0]

                lots.append({
                    "lot_number": lot["name"],
                    "expiry_date": lot["expiration_date"],
                    "quantity": q["quantity"]
                })

        result.append({
            "product": p["display_name"],
            "sku": p["default_code"],
            "barcode": p.get("barcode"),
            "price": p["lst_price"],
            "cost_price": p.get("standard_price"),
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


def fetch_animal_kart_products_with_locations():
    """
    Fetch Animal Kart products with location-wise stock
    """

    odoo = OdooRPC(
        ODOO_URL,
        ODOO_DB,
        ODOO_USERNAME,
        ODOO_API_KEY
    )

    # Step 1: Get Animal Kart products (storable only)
    products = odoo.call(
        "product.product",
        "search_read",
        [[
            ("company_id", "=", ANIMAL_KART_COMPANY_ID),
            ("type", "=", "product")
        ]],
        {
            "fields": [
                "id",
                "display_name",
                "default_code",
                "barcode",
                "lst_price",
                "standard_price",
                "qty_available"
            ],
            "context": {
                "allowed_company_ids": [ANIMAL_KART_COMPANY_ID]
            }
        }
    )

    result = []

    # Step 2: For each product get stock by location
    for p in products:

        quants = odoo.call(
            "stock.quant",
            "search_read",
            [[
                ("product_id", "=", p["id"]),
                ("company_id", "=", ANIMAL_KART_COMPANY_ID),
                ("quantity", ">", 0)
            ]],
            {
                "fields": ["quantity", "location_id"],
                "context": {
                    "allowed_company_ids": [ANIMAL_KART_COMPANY_ID]
                }
            }
        )

        locations = []

        for q in quants:
            if q["location_id"]:
                locations.append({
                    "location_name": q["location_id"][1],
                    "quantity": q["quantity"]
                })

        result.append({
            "product": p["display_name"],
            "sku": p["default_code"],
            "barcode": p.get("barcode"),
            "price": p["lst_price"],
            "cost_price": p.get("standard_price"),
            "total_stock": p["qty_available"],
            "locations": locations
        })

    return result

