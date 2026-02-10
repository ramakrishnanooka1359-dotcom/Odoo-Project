from odoo_rpc import OdooRPC
from config import ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_API_KEY, MARKWAVE_LOCATION_ID, VARIANT_PRICES
import time
from datetime import date, timedelta

# =================================================
# Odoo connection
# =================================================

odoo = OdooRPC(
    ODOO_URL,
    ODOO_DB,
    ODOO_USERNAME,
    ODOO_API_KEY
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
    """Return the configured Markwave stock location ID"""
    return MARKWAVE_LOCATION_ID


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
    return get_id("uom.uom", "name", mapping[logical_name])


def normalize_key(name):
    return name.upper().replace(" ", "")

# =================================================
# LOT HELPERS (FIXED)
# =================================================

def enable_lot_tracking(template_id):
    odoo.call(
        "product.template",
        "write",
        [[template_id], {"tracking": "lot"}]
    )


# 🔧 CHANGE 1: return (lot_id, is_new_lot)
def create_lot(product_id, lot_name, expiry_date):
    lot_ids = odoo.call(
        "stock.lot",
        "search",
        [[("name", "=", lot_name), ("product_id", "=", product_id)]]
    )

    if lot_ids:
        return lot_ids[0], False   # ❌ existing lot

    lot_id = odoo.call(
        "stock.lot",
        "create",
        [{
            "name": lot_name,
            "product_id": product_id,
            "expiration_date": expiry_date,
        }]
    )

    return lot_id, True           # ✅ new lot


def set_stock_with_lot(product_id, location_id, lot_id, quantity):
    """
    Idempotent stock setter:
    - If quant exists → SET quantity
    - If not → CREATE once
    - Safe to re-run unlimited times
    """

    quant_ids = odoo.call(
        "stock.quant",
        "search",
        [[
            ("product_id", "=", product_id),
            ("location_id", "=", location_id),
            ("lot_id", "=", lot_id),
        ]],
        {"limit": 1}
    )

    if quant_ids:
        odoo.call(
            "stock.quant",
            "write",
            [[quant_ids[0]], {"quantity": quantity}]
        )
    else:
        odoo.call(
            "stock.quant",
            "create",
            [{
                "product_id": product_id,
                "location_id": location_id,
                "lot_id": lot_id,
                "quantity": quantity,
                "company_id": 2,  # 🔒 Markwave only
            }]
        )

# =================================================
# Product creation
# =================================================

def create_or_update_product_template(product_name, uom_name):
    pack_attr_id = get_id("product.attribute", "name", "Pack Size")
    uom_id = get_uom_id(uom_name)

    template_id = get_product_template_by_name(product_name)

    pack_values = ["250 ml", "500 ml", "1 L"] if product_name.lower() == "milk" \
        else ["250 g", "500 g", "1 kg"]

    value_ids = [get_id("product.attribute.value", "name", v) for v in pack_values]

    BASE_PRICES = {
        "milk": 0,
        "curd": 0,
        "ghee": 0,
        "paneer": 0,
    }

    if not template_id:
        template_id = odoo.call(
            "product.template",
            "create",
            [{
                "name": product_name,
                "type": "product",
                "uom_id": uom_id,
                "uom_po_id": uom_id,
                "list_price": 0.0,
                "attribute_line_ids": [(
                    0, 0,
                    {"attribute_id": pack_attr_id, "value_ids": [(6, 0, value_ids)]}
                )]
            }]
        )

    enable_lot_tracking(template_id)

    # ✅ FIX 2 — FORCE base price = 0 (even for existing products)
    odoo.call(
        "product.template",
        "write",
        [[template_id], {"list_price": 0.0}]
    )

    time.sleep(1)
    set_variant_prices_stock_and_lots(template_id, product_name)

# =================================================
# Variant pricing + LOT + EXPIRY + STOCK
# =================================================

def set_variant_prices_stock_and_lots(template_id, product_name):
    location_id = get_stock_location_id()
    pname = product_name.lower()
    pname_code = product_name.upper()


    mfg_date = date(2026, 2, 7)

    EXPIRY_DAYS = {
        "milk": 7,
        "curd": 7,
        "paneer": 10,
        "ghee": 365,
    }

    expiry_date = (mfg_date + timedelta(days=EXPIRY_DAYS[pname])).isoformat()

    variants = odoo.call(
        "product.product",
        "search_read",
        [[("product_tmpl_id", "=", template_id)]],
        {"fields": ["id", "product_template_attribute_value_ids"]}
    )

    for variant in variants:
        ptav = odoo.call(
            "product.template.attribute.value",
            "read",
            [variant["product_template_attribute_value_ids"]],
            {"fields": ["id", "name"]}
        )[0]

        size_key = normalize_key(ptav["name"])

        sku = f"{pname_code}-{size_key}"
        
        # Get price from VARIANT_PRICES config
        variant_price = VARIANT_PRICES.get(sku, 0)
        
        # Update variant with SKU and price
        odoo.call(
            "product.product",
            "write",
            [[variant["id"]], {
                "default_code": sku,
                "lst_price": variant_price
            }]
        )

        lot_name = f"{sku}-{mfg_date.strftime('%Y%m%d')}"
        lot_id, _ = create_lot(variant["id"], lot_name, expiry_date)

        set_stock_with_lot(
            variant["id"], location_id, lot_id, 1000
        )

        print(
            f"✅ {sku} | PRICE=₹{variant_price} | LOT={lot_name} | EXP={expiry_date}"
        )

# =================================================
# Script execution
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
