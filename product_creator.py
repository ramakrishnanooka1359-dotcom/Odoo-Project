from odoo_rpc import OdooRPC
from config import ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD
import time

# =================================================
# Odoo connection
# =================================================

odoo = OdooRPC(
    ODOO_URL,
    ODOO_DB,
    ODOO_USERNAME,
    ODOO_PASSWORD
)

# =================================================
# Helpers
# =================================================

def get_id(model, field, value):
    ids = odoo.call(model, "search", [[(field, "=", value)]])
    if not ids:
        raise Exception(f"{model} not found: {value}")
    return ids[0]


def get_stock_location_id():
    loc = odoo.call(
        "stock.location",
        "search_read",
        [[("complete_name", "=", "Markw/Stock")]],
        {"fields": ["id"]}
    )
    if not loc:
        raise Exception("Stock location not found")
    return loc[0]["id"]


def get_product_template_by_name(name):
    ids = odoo.call(
        "product.template",
        "search",
        [[("name", "=", name)]],
        {"limit": 1}
    )
    return ids[0] if ids else None


def get_uom_id(logical_name):
    mapping = {
        "Liter": "L",
        "Kilogram": "kg",
    }
    uom_name = mapping.get(logical_name)
    if not uom_name:
        raise Exception(f"Unsupported UoM: {logical_name}")
    return get_id("uom.uom", "name", uom_name)


def normalize_key(name):
    return name.upper().replace(" ", "")


def set_stock_exact(product_id, location_id, quantity):
    """
    Ensure EXACT stock quantity for a product at a location.
    Safe to run multiple times (no duplication).
    """
    quant_ids = odoo.call(
        "stock.quant",
        "search",
        [[
            ("product_id", "=", product_id),
            ("location_id", "=", location_id),
        ]]
    )

    if quant_ids:
        odoo.call(
            "stock.quant",
            "write",
            [quant_ids, {"quantity": quantity}]
        )
    else:
        odoo.call(
            "stock.quant",
            "create",
            [{
                "product_id": product_id,
                "location_id": location_id,
                "quantity": quantity,
            }]
        )

# =================================================
# Product creation
# =================================================

def create_or_update_product_template(product_name, uom_name):
    pack_attr_id = get_id("product.attribute", "name", "Pack Size")
    uom_id = get_uom_id(uom_name)

    template_id = get_product_template_by_name(product_name)

    if product_name.lower() == "milk":
        pack_values = ["250 ml", "500 ml", "1 L"]
    else:
        pack_values = ["250 g", "500 g", "1 kg"]

    value_ids = [
        get_id("product.attribute.value", "name", v)
        for v in pack_values
    ]

    BASE_PRICES = {
        "milk": 20,
        "curd": 20,
        "ghee": 100,
        "paneer": 240,
    }

    if template_id:
        print(f"🔁 Updating product: {product_name}")
        odoo.call(
            "product.template",
            "write",
            [[template_id], {
                "uom_id": uom_id,
                "uom_po_id": uom_id,
                "list_price": BASE_PRICES[product_name.lower()],
            }]
        )
    else:
        print(f"🆕 Creating product: {product_name}")
        template_id = odoo.call(
            "product.template",
            "create",
            [{
                "name": product_name,
                "type": "product",
                "uom_id": uom_id,
                "uom_po_id": uom_id,
                "list_price": BASE_PRICES[product_name.lower()],
                "attribute_line_ids": [(
                    0, 0, {
                        "attribute_id": pack_attr_id,
                        "value_ids": [(6, 0, value_ids)]
                    }
                )]
            }]
        )

    time.sleep(1)
    set_variant_prices_stock_and_sku(template_id, product_name)

    return template_id

# =================================================
# Variant pricing + stock + SKU
# =================================================

def set_variant_prices_stock_and_sku(template_id, product_name):
    location_id = get_stock_location_id()
    pname = product_name.lower()
    pname_code = product_name.upper()

    PRICE_MAP = {
        "milk": {
            "250ML": 0,
            "500ML": 20,
            "1L": 60,
        },
        "curd": {
            "250G": 0,
            "500G": 20,
            "1KG": 60,
        },
        "ghee": {
            "250G": 0,
            "500G": 100,
            "1KG": 300,
        },
        "paneer": {
            "250G": -120,
            "500G": 0,
            "1KG": 240,
        },
    }

    variants = odoo.call(
        "product.product",
        "search_read",
        [[("product_tmpl_id", "=", template_id)]],
        {"fields": ["id", "product_template_attribute_value_ids"]}
    )

    for variant in variants:
        ptav_ids = variant["product_template_attribute_value_ids"]

        ptavs = odoo.call(
            "product.template.attribute.value",
            "read",
            [ptav_ids],
            {"fields": ["id", "name"]}
        )

        size_name = ptavs[0]["name"]
        size_key = normalize_key(size_name)

        extra = PRICE_MAP[pname].get(size_key, 0)
        odoo.call(
            "product.template.attribute.value",
            "write",
            [[ptavs[0]["id"]], {"price_extra": extra}]
        )

        sku = f"{pname_code}-{size_key}"
        odoo.call(
            "product.product",
            "write",
            [[variant["id"]], {"default_code": sku}]
        )

        # ✅ SAFE STOCK SET (NO DUPLICATION)
        set_stock_exact(variant["id"], location_id, 100)

        print(f"✅ {product_name} | {size_name} | SKU={sku}")

# =================================================
# Script execution (THIS IS REQUIRED)
# =================================================

if __name__ == "__main__":
    PRODUCTS = [
        ("Milk", "Liter"),
        ("Curd", "Kilogram"),
        ("Ghee", "Kilogram"),
        ("Paneer", "Kilogram"),   
    ]

    for name, uom in PRODUCTS:
        create_or_update_product_template(name, uom)
