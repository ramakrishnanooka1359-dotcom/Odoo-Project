from odoo_rpc import OdooRPC
from config import *

odoo = OdooRPC(
    ODOO_URL,
    ODOO_DB,
    ODOO_USERNAME,
    ODOO_PASSWORD
)

# -------------------------
# Generic helpers
# -------------------------

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
        raise Exception("Markw/Stock location not found")
    return loc[0]["id"]

def get_uom_id(logical_name):
    """
    Map logical names to actual Odoo UoM names
    """
    mapping = {
        "Liter": "L",
        "Kilogram": "kg",
    }

    odoo_name = mapping.get(logical_name)
    if not odoo_name:
        raise Exception(f"Unsupported UoM logical name: {logical_name}")

    ids = odoo.call(
        "uom.uom",
        "search",
        [[("name", "=", odoo_name)]]
    )
    if not ids:
        raise Exception(f"uom.uom not found in Odoo: {odoo_name}")

    return ids[0]

# -------------------------
# Product creation
# -------------------------

def create_product_template(product_name, uom_name):
    pack_attr_id = get_id("product.attribute", "name", "Pack Size")
    uom_id = get_id("uom.uom", "name", uom_name)

    template_id = odoo.call(
        "product.template",
        "create",
        [{
            "name": product_name,
            "type": "product",
            "tracking": "lot",
            "uom_id": uom_id,
            "uom_po_id": uom_id,
            "attribute_line_ids": [(0, 0, {
                "attribute_id": pack_attr_id,
                "value_ids": [(6, 0, [
                    get_id("product.attribute.value", "name", "250 ml"),
                    get_id("product.attribute.value", "name", "500 ml"),
                    get_id("product.attribute.value", "name", "1 L")
                ])]
            })]
        }]
    )

    set_variant_prices(template_id)
    return template_id

# -------------------------
# Variant pricing
# -------------------------

def set_variant_prices(template_id):
    variants = odoo.call(
        "product.product",
        "search_read",
        [[("product_tmpl_id", "=", template_id)]],
        {"fields": ["id", "name"]}
    )

    for v in variants:
        if "250" in v["name"]:
            price = 20
        elif "500" in v["name"]:
            price = 40
        else:
            price = 80

        odoo.call(
            "product.product",
            "write",
            [[v["id"]], {"lst_price": price}]
        )

