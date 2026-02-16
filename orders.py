from odoo_rpc import OdooRPC
from config import (
    ODOO_URL,
    ODOO_DB,
    ODOO_USERNAME,
    ODOO_API_KEY,
    MARKWAVE_COMPANY_ID,
    ANIMAL_KART_COMPANY_ID
)


def create_sale_order(company_id: int, customer_id: int, order_lines: list):
    """
    order_lines example:
    [
        {"product_id": 45, "quantity": 2, "price": 350000}
    ]
    """

    odoo = OdooRPC(
        ODOO_URL,
        ODOO_DB,
        ODOO_USERNAME,
        ODOO_API_KEY
    )

    context = {
        "allowed_company_ids": [company_id]
    }

    # -----------------------------------
    # 1️⃣ Create Sale Order
    # -----------------------------------
    order_id = odoo.call(
        "sale.order",
        "create",
        [{
            "partner_id": customer_id,
            "company_id": company_id,
            "order_line": [
                (0, 0, {
                    "product_id": line["product_id"],
                    "product_uom_qty": line["quantity"],
                    "price_unit": line["price"]
                }) for line in order_lines
            ]
        }],
        {"context": context}
    )

    # -----------------------------------
    # 2️⃣ Confirm Sale Order
    # -----------------------------------
    odoo.call(
        "sale.order",
        "action_confirm",
        [[order_id]],
        {"context": context}
    )

    return {"status": "Order Created", "order_id": order_id}
