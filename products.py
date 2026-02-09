from odoo_rpc import OdooRPC
from config import ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_API_KEY
<<<<<<< HEAD


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

=======
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
>>>>>>> c33a002 (added a new line)
