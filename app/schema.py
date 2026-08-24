from sqlalchemy import inspect, text

from app.extensions import db
from app.models.user import User


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
