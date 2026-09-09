"""One-off maintenance operations run from the CLI. Kept out of any
blueprint so they can be unit-tested on their own."""

from sqlalchemy import text

from app.extensions import db
from app.models.customer_segment import CustomerSegment
from app.models.purchase_category import PurchaseCategory
from app.models.warehouse import Warehouse

# Tables emptied by `flask reset-data`, children before parents. SQLite FK
# enforcement is off in this app, so the order isn't strictly required,
# but keep it sane in case that ever changes. `users` and
# `company_settings` are deliberately absent — accounts and configuration
# survive the reset (see #116).
WIPE_ORDER = [
    "stock_movements",
    "supply_movements",
    "inventory_items",
    "supply_items",
    "product_supplies",
    "sale_items",
    "sales",
    "purchases",
    "products",
    "flavors",
    "supplies",
    "customers",
    "customer_segments",
    "purchase_categories",
    "warehouses",
]


def reset_data() -> dict[str, int]:
    """Delete every operational record — customers, sales, products,
    flavors, inventory, supplies, purchases, warehouses and their lookup
    catalogs — keeping only user accounts and the single company settings
    row. Then recreate the baseline catalogs and warehouses so the
    database is ready for a fresh real-data load (#116).

    Returns {table_name: rows_deleted}.
    """
    deleted: dict[str, int] = {}
    for table in WIPE_ORDER:
        result = db.session.execute(text(f"DELETE FROM {table}"))
        deleted[table] = result.rowcount
    db.session.commit()
    # The DELETEs were raw SQL, so the session's identity map still holds
    # the now-gone rows — drop them before re-seeding reuses their ids.
    db.session.expunge_all()

    CustomerSegment.ensure_defaults()
    PurchaseCategory.ensure_defaults()
    Warehouse.ensure_defaults()

    return deleted
