from product_creator import get_variant_id, add_stock

milk_500_id = get_variant_id("Milk", "500")

add_stock(
    product_id=milk_500_id,
    quantity=100,
    lot_name="MILK-060226-A",
    expiry_date="2026-02-08"
)
