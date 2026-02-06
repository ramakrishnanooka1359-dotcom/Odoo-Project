from odoo_rpc import OdooRPC
from config import *

odoo = OdooRPC(
    ODOO_URL,
    ODOO_DB,
    ODOO_USERNAME,
    ODOO_PASSWORD
)

print("✅ Connected to Odoo, UID:", odoo.uid)
