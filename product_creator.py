from odoo_rpc import OdooRPC
from config import *
import time

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
    uom_id = get_uom_id(uom_name)

    # Decide variant values based on product
    if product_name.lower() == "milk":
        pack_values = ["250 ml", "500 ml", "1 L"]
    else:  # curd & ghee
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
            "tracking": "lot",
            "uom_id": uom_id,
            "uom_po_id": uom_id,
            "attribute_line_ids": [(0, 0, {
                "attribute_id": pack_attr_id,
                "value_ids": [(6, 0, value_ids)]
            })]
        }]
    )

    set_variant_prices_and_stock(template_id, product_name)
    return template_id

# -------------------------
# Variant pricing
# -------------------------
def set_variant_prices_and_stock(template_id, product_name):
    attempts = 5
    variants = []

    for _ in range(attempts):
        variants = odoo.call(
            "product.product",
            "search_read",
            [[("product_tmpl_id", "=", template_id)]],
            {
                "fields": [
                    "id",
                    "name",
                    "product_template_attribute_value_ids"
                ]
            }
        )
        if variants:
            break
        time.sleep(1)

    if not variants:
        raise Exception(f"No variants created for template {template_id}")

    location_id = get_stock_location_id()

    for v in variants:
        attr_ids = v.get("product_template_attribute_value_ids") or []

        vals = odoo.call(
            "product.template.attribute.value",
            "read",
            [attr_ids],
            {"fields": ["name"]}
        )

        names = [x["name"].lower() for x in vals]

        has_250 = any("250" in n for n in names)
        has_500 = any("500" in n for n in names)
        has_1kg_l = any("1" in n for n in names)

        pname = product_name.lower()

        # -------- PRICING --------
        if pname == "milk":
            if has_250:
                price = 20
            elif has_500:
                price = 40
            else:
                price = 80

        elif pname == "curd":
            if has_250:
                price = 20
            elif has_500:
                price = 40
            else:
                price = 80

        elif pname == "ghee":
            if has_250:
                price = 100
            elif has_500:
                price = 200
            else:
                price = 400
        else:
            price = 0

        # Set price
        odoo.call(
            "product.product",
            "write",
            [[v["id"]], {"lst_price": price}]
        )

        # -------- STOCK = 100 --------
        odoo.call(
            "stock.quant",
            "create",
            [{
                "product_id": v["id"],
                "location_id": location_id,
                "quantity": 100
            }]
        )

        print(f"✅ {product_name} | {names} | ₹{price} | Stock=100")

