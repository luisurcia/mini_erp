import click
from flask import Flask

from app.extensions import db
from app.models.company import Company  # noqa: F401 (registers table for create_all)
from app.models.customer_segment import CustomerSegment
from app.models.product_supply import ProductSupply  # noqa: F401 (create_all)
from app.models.purchase import Purchase  # noqa: F401 (create_all)
from app.models.purchase_category import PurchaseCategory
from app.models.user import User
from app.models.warehouse import Warehouse
from app.schema import (
    consolidate_supply_stock_into_supplies_warehouse,
    ensure_company_brand_name_column,
    ensure_company_currency_columns,
    ensure_company_language_column,
    ensure_company_name_column,
    ensure_company_product_field_toggles,
    ensure_customer_columns,
    ensure_customer_nickname_and_structured_address,
    ensure_customer_segment_active_column,
    ensure_inventory_item_warehouse_column,
    ensure_product_color_column,
    ensure_product_short_name_column,
    ensure_products_optional_columns_nullable,
    ensure_purchase_category_catalog,
    ensure_sale_invoice_number_column,
    ensure_sale_item_warehouse_column,
    ensure_sale_payment_columns,
    ensure_sale_tax_columns,
    ensure_stock_movement_warehouse_column,
    ensure_supply_movement_sale_column,
    ensure_user_language_column,
    ensure_user_name_columns,
    ensure_user_role_column,
    ensure_warehouse_kind_column,
    ensure_warehouse_stage_column,
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
    ensure_product_color_column()
    ensure_sale_invoice_number_column()
    ensure_sale_tax_columns()
    ensure_sale_payment_columns()
    ensure_company_language_column()
    ensure_company_name_column()
    ensure_company_brand_name_column()
    ensure_company_product_field_toggles()
    ensure_company_currency_columns()
    ensure_customer_columns()
    ensure_customer_nickname_and_structured_address()
    ensure_customer_segment_active_column()
    ensure_supply_movement_sale_column()
    CustomerSegment.ensure_defaults()
    PurchaseCategory.ensure_defaults()
    ensure_purchase_category_catalog()
    # `kind`/`stage` columns must exist before ensure_defaults() (it
    # creates the supplies + fermentation warehouses, which query by them).
    ensure_warehouse_kind_column()
    ensure_warehouse_stage_column()
    Warehouse.ensure_defaults()
    ensure_inventory_item_warehouse_column()
    ensure_stock_movement_warehouse_column()
    ensure_sale_item_warehouse_column()
    # After the supplies warehouse exists, pull all supply stock into it.
    consolidate_supply_stock_into_supplies_warehouse()


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

    @app.cli.command("reset-data")
    @click.option("--yes", is_flag=True, help="Skip the confirmation prompt.")
    def reset_data_command(yes):
        """Delete all operational data, keeping only users and company settings.

        Use before loading a client's real data into a database that still
        has demo data. Take a backup first. See #116.
        """
        from app.maintenance import reset_data

        if not yes:
            click.confirm(
                "This deletes ALL customers, sales, products, inventory, "
                "supplies, purchases and warehouses. Users and company "
                "settings are kept. Continue?",
                abort=True,
            )
        deleted = reset_data()
        total = sum(deleted.values())
        click.echo(f"Deleted {total} rows across {len(deleted)} tables.")
        click.echo("Kept: users, company settings.")
        click.echo(
            "Recreated defaults: warehouses, customer segments, purchase categories."
        )

    @app.cli.command("import-ventas")
    @click.argument("archivo")
    @click.option("--dry-run", is_flag=True, help="Recorre y reporta sin escribir nada.")
    def import_ventas_command(archivo, dry_run):
        """Carga el historial de ventas de Scoby desde la planilla (#118).

        Correr SIEMPRE primero con --dry-run, sobre una base recién
        reseteada con `flask reset-data`. Escribe un log en instance/.
        """
        from datetime import datetime
        from pathlib import Path

        from app.migration import build_report, import_ventas

        result = import_ventas(archivo, dry_run=dry_run)
        report = build_report(result)

        instance = Path(app.instance_path)
        instance.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        suffix = "dry-run" if dry_run else "carga"
        log_path = instance / f"migracion-ventas-{stamp}-{suffix}.md"
        log_path.write_text(report, encoding="utf-8")

        click.echo(report)
        click.echo(f"\nLog guardado en: {log_path}")
        if dry_run:
            click.echo("Fue una simulación — no se escribió nada en la base.")

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
