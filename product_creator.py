from odoo_rpc import OdooRPC
from config import *
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
    return name.lower().replace(" ", "")

# =================================================
# Product creation
# =================================================

def create_product_template(product_name, uom_name):
    pack_attr_id = get_id("product.attribute", "name", "Pack Size")
    uom_id = get_uom_id(uom_name)

    if product_name.lower() == "milk":
        pack_values = ["250 ml", "500 ml", "1 L"]
    else:
        pack_values = ["250 g", "500 g", "1 kg"]

    value_ids = [
        get_id("product.attribute.value", "name", v)
        for v in pack_values
    ]

    template_id = odoo.call(
        "product.template",
        "create",
        [{
            "name": product_name,
            "type": "product",
            "uom_id": uom_id,
            "uom_po_id": uom_id,
            "attribute_line_ids": [(
                0, 0, {
                    "attribute_id": pack_attr_id,
                    "value_ids": [(6, 0, value_ids)]
                }
            )]
        }]
    )

    BASE_PRICES = {
        "milk": 20,
        "curd": 20,
        "ghee": 100,
    }

    odoo.call(
        "product.template",
        "write",
        [[template_id], {"list_price": BASE_PRICES[product_name.lower()]}]
    )

    time.sleep(1)
    set_variant_prices_and_stock(template_id, product_name)

    return template_id

# =================================================
# Variant pricing + stock
# =================================================

def set_variant_prices_and_stock(template_id, product_name):
    location_id = get_stock_location_id()
    pname = product_name.lower()

    PRICE_MAP = {
        "milk": {
            "250ml": 0,
            "500ml": 20,
            "1l": 60,
        },
        "curd": {
            "250g": 0,
            "500g": 20,
            "1kg": 60,
        },
        "ghee": {
            "250g": 0,
            "500g": 100,
            "1kg": 300,
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

        for ptav in ptavs:
            key = normalize_key(ptav["name"])
            extra = PRICE_MAP[pname].get(key, 0)

            odoo.call(
                "product.template.attribute.value",
                "write",
                [[ptav["id"]], {"price_extra": extra}]
            )

        odoo.call(
            "stock.quant",
            "create",
            [{
                "product_id": variant["id"],
                "location_id": location_id,
                "quantity": 100,
            }]
        )
            )

