import os
from dotenv import load_dotenv

load_dotenv()   # loads .env file

ODOO_URL = "http://54.157.185.157:8069"
ODOO_DB = "Odoo-Inventory"
ODOO_USERNAME = "nookaramakrishna6789@gmail.com"

ODOO_API_KEY = os.getenv("ODOO_API_KEY")

# Markwave configuration
MARKWAVE_COMPANY_ID = 2
MARKWAVE_LOCATION_ID = 22

# Product variant pricing
VARIANT_PRICES = {
    "CURD-1KG": 100,
    "CURD-250G": 20,
    "CURD-500G": 40,
    "MILK-1L": 80,
    "MILK-250ML": 20,
    "MILK-500ML": 40,
    "GHEE-1KG": 400,
    "GHEE-250G": 100,
    "GHEE-500G": 200,
    "PANEER-1KG": 480,
    "PANEER-250G": 120,
    "PANEER-500G": 240,
}
