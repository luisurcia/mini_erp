from sqlalchemy import inspect, text

from app.extensions import db
from app.models.user import User
from app.models.warehouse import Warehouse


def ensure_product_short_name_column() -> None:
    """Backfill `products.short_name` for databases created before it existed.

    db.create_all() only creates missing tables, not missing columns on
    tables that already exist, so pre-existing databases need this to pick
    up the short_name column.
    """
    inspector = inspect(db.engine)
    columns = {column["name"] for column in inspector.get_columns("products")}
    if "short_name" not in columns:
        db.session.execute(text("ALTER TABLE products ADD COLUMN short_name VARCHAR(3)"))
        db.session.commit()


def ensure_products_optional_columns_nullable() -> None:
    """Make `products.flavor_id` and `products.unit_price` nullable for
    databases created before those fields became hideable (#37, #38).

    SQLite can't ALTER a column's NOT NULL constraint, so rebuild the
    table: rename aside, recreate from the current model via create_all(),
    copy every row across (ids and all column values preserved), drop the
    old table. FK enforcement is off (PRAGMA foreign_keys = 0) and row ids
    are unchanged, so the inventory_items / sale_items / stock_movements
    references to products.id stay valid.
    """
    inspector = inspect(db.engine)
    by_name = {c["name"]: c for c in inspector.get_columns("products")}
    already_nullable = by_name["flavor_id"]["nullable"] and by_name["unit_price"]["nullable"]
    if already_nullable:
        return

    cols = (
        "id, flavor_id, name, short_name, sku, size_ml, unit_price, is_active, "
        "created_at, updated_at"
    )
    db.session.execute(text("ALTER TABLE products RENAME TO products_old"))
    db.session.commit()
    db.create_all()
    db.session.execute(text(f"INSERT INTO products ({cols}) SELECT {cols} FROM products_old"))
    db.session.execute(text("DROP TABLE products_old"))
    db.session.commit()


def ensure_sale_invoice_number_column() -> None:
    """Backfill `sales.invoice_number` for databases created before it existed.

    db.create_all() only creates missing tables, not missing columns on
    tables that already exist, so pre-existing databases need this to pick
    up the invoice_number column.
    """
    inspector = inspect(db.engine)
    columns = {column["name"] for column in inspector.get_columns("sales")}
    if "invoice_number" not in columns:
        db.session.execute(text("ALTER TABLE sales ADD COLUMN invoice_number VARCHAR(40)"))
        db.session.commit()


def ensure_sale_tax_columns() -> None:
    """Backfill `sales.tax_*` columns for databases created before IVA support.

    db.create_all() only creates missing tables, not missing columns on
    tables that already exist, so pre-existing databases need this to pick
    up the tax_applied, tax_rate_applied and tax_amount columns.
    """
    inspector = inspect(db.engine)
    columns = {column["name"] for column in inspector.get_columns("sales")}
    if "tax_applied" not in columns:
        db.session.execute(
            text("ALTER TABLE sales ADD COLUMN tax_applied BOOLEAN NOT NULL DEFAULT 0")
        )
    if "tax_rate_applied" not in columns:
        db.session.execute(text("ALTER TABLE sales ADD COLUMN tax_rate_applied NUMERIC(5, 2)"))
    if "tax_amount" not in columns:
        db.session.execute(
            text("ALTER TABLE sales ADD COLUMN tax_amount NUMERIC(10, 2) NOT NULL DEFAULT 0")
        )
    db.session.commit()


def ensure_company_language_column() -> None:
    """Backfill `company_settings.language` for databases created before it existed.

    db.create_all() only creates missing tables, not missing columns on
    tables that already exist, so pre-existing databases need this to pick
    up the language column.
    """
    inspector = inspect(db.engine)
    columns = {column["name"] for column in inspector.get_columns("company_settings")}
    if "language" not in columns:
        db.session.execute(
            text(
                "ALTER TABLE company_settings ADD COLUMN language "
                "VARCHAR(5) NOT NULL DEFAULT 'es'"
            )
        )
        db.session.commit()


def ensure_company_product_field_toggles() -> None:
    """Backfill the product-form visibility toggles for databases created
    before per-field simplification existed.

    Defaults to 1 (shown) for every toggle, so upgrading an existing
    database doesn't silently hide fields that were always there.
    """
    inspector = inspect(db.engine)
    columns = {column["name"] for column in inspector.get_columns("company_settings")}
    for name in (
        "product_short_name_enabled",
        "product_size_enabled",
        "product_sku_enabled",
        "product_flavor_enabled",
        "product_price_enabled",
    ):
        if name not in columns:
            db.session.execute(
                text(f"ALTER TABLE company_settings ADD COLUMN {name} BOOLEAN NOT NULL DEFAULT 1")
            )
    db.session.commit()


def ensure_company_currency_columns() -> None:
    """Backfill the currency-display columns for databases created before
    money formatting was configurable (see #39).

    Defaults match the model (CLP / "$" / 0 decimals) so an existing
    `client/scoby` database picks up peso formatting on the next deploy
    without a manual settings change.
    """
    inspector = inspect(db.engine)
    columns = {column["name"] for column in inspector.get_columns("company_settings")}
    if "currency_code" not in columns:
        db.session.execute(
            text(
                "ALTER TABLE company_settings ADD COLUMN currency_code "
                "VARCHAR(3) NOT NULL DEFAULT 'CLP'"
            )
        )
    if "currency_symbol" not in columns:
        db.session.execute(
            text(
                "ALTER TABLE company_settings ADD COLUMN currency_symbol "
                "VARCHAR(8) NOT NULL DEFAULT '$'"
            )
        )
    if "currency_decimals" not in columns:
        db.session.execute(
            text(
                "ALTER TABLE company_settings ADD COLUMN currency_decimals "
                "INTEGER NOT NULL DEFAULT 0"
            )
        )
    db.session.commit()


def ensure_customer_columns() -> None:
    """Backfill `customers.rut`/`shipping_address`/`segment_id` for
    databases created before Scoby's customer segmentation existed.

    SQLite's ALTER TABLE can't add a UNIQUE constraint, so `rut`'s
    uniqueness is only enforced on fresh installs (db.create_all()), not
    on databases upgraded through this path.
    """
    inspector = inspect(db.engine)
    columns = {column["name"] for column in inspector.get_columns("customers")}
    if "rut" not in columns:
        db.session.execute(text("ALTER TABLE customers ADD COLUMN rut VARCHAR(20)"))
    if "shipping_address" not in columns:
        db.session.execute(text("ALTER TABLE customers ADD COLUMN shipping_address TEXT"))
    if "segment_id" not in columns:
        db.session.execute(text("ALTER TABLE customers ADD COLUMN segment_id INTEGER"))
    db.session.commit()


def ensure_customer_nickname_and_structured_address() -> None:
    """#41: add customers.nickname. #42: replace the free-text
    shipping_address column with structured street/number/city/commune/
    region columns.

    The old free-text values are not parsed into the new fields — only
    demo data ever used the column, and Scoby re-enters real addresses in
    the structured form. SQLite 3.35+ (this deploy target is 3.45) supports
    DROP COLUMN directly, so no table rebuild is needed.
    """
    inspector = inspect(db.engine)
    columns = {column["name"] for column in inspector.get_columns("customers")}
    if "nickname" not in columns:
        db.session.execute(text("ALTER TABLE customers ADD COLUMN nickname VARCHAR(80)"))
    for column in (
        "shipping_street",
        "shipping_number",
        "shipping_city",
        "shipping_commune",
        "shipping_region",
    ):
        if column not in columns:
            db.session.execute(
                text(f"ALTER TABLE customers ADD COLUMN {column} VARCHAR(120)")
            )
    if "shipping_address" in columns:
        db.session.execute(text("ALTER TABLE customers DROP COLUMN shipping_address"))
    db.session.commit()


def ensure_customer_segment_active_column() -> None:
    """Backfill `customer_segments.is_active` for databases created before
    segments could be deactivated instead of deleted.

    Defaults to 1 (active) so upgrading doesn't silently hide segments
    already in use by existing customers.
    """
    inspector = inspect(db.engine)
    columns = {column["name"] for column in inspector.get_columns("customer_segments")}
    if "is_active" not in columns:
        db.session.execute(
            text("ALTER TABLE customer_segments ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 1")
        )
        db.session.commit()


def ensure_inventory_item_warehouse_column() -> None:
    """Migrate `inventory_items` from one row per product to one row per
    (product, warehouse) pair, for databases created before multi-warehouse
    stock existed (#25).

    `Warehouse.ensure_defaults()` must have already run — every existing
    row is assigned to the default warehouse (`Bodega Principal`), since
    pre-multi-warehouse stock wasn't tracked by location.

    SQLite can't ALTER a column onto a table with a *new* composite UNIQUE
    constraint, so this rebuilds the table: rename the old one aside,
    let `db.create_all()` create the new (already-registered) schema, copy
    the data across with the default warehouse filled in, then drop the
    old table.
    """
    inspector = inspect(db.engine)
    columns = {column["name"] for column in inspector.get_columns("inventory_items")}
    if "warehouse_id" in columns:
        return

    default_warehouse = Warehouse.query.filter_by(is_default=True).first()
    if default_warehouse is None:
        raise RuntimeError(
            "Warehouse.ensure_defaults() must run before ensure_inventory_item_warehouse_column()"
        )

    db.session.execute(text("ALTER TABLE inventory_items RENAME TO inventory_items_old"))
    db.session.commit()
    db.create_all()
    db.session.execute(
        text(
            "INSERT INTO inventory_items "
            "(id, product_id, warehouse_id, quantity_on_hand, reorder_level, "
            "created_at, updated_at) "
            "SELECT id, product_id, :warehouse_id, quantity_on_hand, reorder_level, "
            "created_at, updated_at FROM inventory_items_old"
        ),
        {"warehouse_id": default_warehouse.id},
    )
    db.session.execute(text("DROP TABLE inventory_items_old"))
    db.session.commit()


def ensure_stock_movement_warehouse_column() -> None:
    """Backfill `stock_movements.warehouse_id` for databases created before
    multi-warehouse stock existed.

    Left NULL for existing rows — movements recorded before warehouses
    existed genuinely don't have one, no default to backfill them with.
    """
    inspector = inspect(db.engine)
    columns = {column["name"] for column in inspector.get_columns("stock_movements")}
    if "warehouse_id" not in columns:
        db.session.execute(
            text("ALTER TABLE stock_movements ADD COLUMN warehouse_id INTEGER")
        )
        db.session.commit()


def ensure_sale_item_warehouse_column() -> None:
    """Backfill `sale_items.warehouse_id` for databases created before
    Sales picked a warehouse per line (#23/#24).

    Left NULL for existing rows — sales recorded before then genuinely
    don't have one, no default to backfill them with.
    """
    inspector = inspect(db.engine)
    columns = {column["name"] for column in inspector.get_columns("sale_items")}
    if "warehouse_id" not in columns:
        db.session.execute(
            text("ALTER TABLE sale_items ADD COLUMN warehouse_id INTEGER")
        )
        db.session.commit()


def ensure_user_name_columns() -> None:
    """Backfill `users.first_name` / `users.last_name` for databases
    created before display names existed (#44). Nullable — existing users
    fall back to showing their username until an admin fills these in.
    """
    inspector = inspect(db.engine)
    columns = {column["name"] for column in inspector.get_columns("users")}
    for column in ("first_name", "last_name"):
        if column not in columns:
            db.session.execute(
                text(f"ALTER TABLE users ADD COLUMN {column} VARCHAR(80)")
            )
    db.session.commit()


def ensure_user_role_column() -> None:
    """Backfill `users.role` for databases created before roles existed.

    db.create_all() only creates missing tables, not missing columns on
    tables that already exist, so pre-existing databases need this to pick
    up the role column added alongside user management.
    """
    inspector = inspect(db.engine)
    columns = {column["name"] for column in inspector.get_columns("users")}
    if "role" not in columns:
        db.session.execute(
            text(
                "ALTER TABLE users ADD COLUMN role VARCHAR(20) "
                f"NOT NULL DEFAULT '{User.ROLE_ADMIN}'"
            )
        )
        db.session.commit()
