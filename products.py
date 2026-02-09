from odoo_rpc import OdooRPC
from config import ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_API_KEY


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

    products = odoo.call(
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

    return products

