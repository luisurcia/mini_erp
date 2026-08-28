import click
from flask import Flask

from app.extensions import db
from app.models.company import Company  # noqa: F401 (registers table for create_all)
from app.models.customer_segment import CustomerSegment
from app.models.user import User
from app.models.warehouse import Warehouse
from app.schema import (
    ensure_company_currency_columns,
    ensure_company_language_column,
    ensure_company_product_field_toggles,
    ensure_customer_columns,
    ensure_customer_nickname_and_structured_address,
    ensure_customer_segment_active_column,
    ensure_inventory_item_warehouse_column,
    ensure_product_short_name_column,
    ensure_products_optional_columns_nullable,
    ensure_sale_invoice_number_column,
    ensure_sale_item_warehouse_column,
    ensure_sale_tax_columns,
    ensure_stock_movement_warehouse_column,
    ensure_user_language_column,
    ensure_user_name_columns,
    ensure_user_role_column,
)


def _upgrade_schema() -> None:
    """Bring an existing database's schema up to date. Safe to call
    against a brand-new database too — every step is a no-op there.

    Order matters: `db.create_all()` must run first (adds any wholly new
    tables), `Warehouse.ensure_defaults()` must run before
    `ensure_inventory_item_warehouse_column()` (it needs a default
    warehouse to assign existing stock to).
    """
    db.create_all()
    ensure_user_role_column()
    ensure_user_name_columns()
    ensure_user_language_column()
    ensure_product_short_name_column()
    # After short_name (this rebuilds the products table and copies it).
    ensure_products_optional_columns_nullable()
    ensure_sale_invoice_number_column()
    ensure_sale_tax_columns()
    ensure_company_language_column()
    ensure_company_product_field_toggles()
    ensure_company_currency_columns()
    ensure_customer_columns()
    ensure_customer_nickname_and_structured_address()
    ensure_customer_segment_active_column()
    CustomerSegment.ensure_defaults()
    Warehouse.ensure_defaults()
    ensure_inventory_item_warehouse_column()
    ensure_stock_movement_warehouse_column()
    ensure_sale_item_warehouse_column()


def register_cli(app: Flask) -> None:
    @app.cli.command("init-db")
    def init_db():
        """Create all database tables."""
        _upgrade_schema()
        click.echo("Database tables created.")

    @app.cli.command("seed-demo")
    def seed_demo():
        """Populate the database with kombucha demo data."""
        from app.seed import seed_demo_data

        _upgrade_schema()
        seed_demo_data(app)
        click.echo("Demo data seeded.")

    @app.cli.command("create-admin")
    @click.option("--username", prompt=True)
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
    def create_admin(username, password):
        """Create (or update the password of) the admin user."""
        db.create_all()
        user = User.query.filter_by(username=username).first()
        if user is None:
            user = User(username=username)
            db.session.add(user)
        user.set_password(password)
        db.session.commit()
        click.echo(f"Admin user '{username}' is ready.")
