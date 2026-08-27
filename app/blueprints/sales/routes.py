from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from flask import flash, redirect, render_template, request, url_for
from flask_babel import gettext as _
from flask_login import login_required

from app.blueprints.sales import bp
from app.blueprints.sales.forms import SaleMetaForm
from app.display import product_label
from app.exceptions import MiniErpError
from app.models.company import Company
from app.models.user import User
from app.permissions import module_required
from app.repositories.customer_repository import CustomerRepository
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.sales_repository import SalesRepository
from app.repositories.warehouse_repository import WarehouseRepository
from app.services.sales_service import SalesService


@bp.route("/")
@login_required
@module_required(User.MODULE_SALES)
def index():
    sales = SalesRepository().get_all()
    return render_template("sales/index.html", sales=sales)


@bp.route("/new", methods=["GET", "POST"])
@login_required
@module_required(User.MODULE_SALES)
def new_sale():
    form = SaleMetaForm()
    form.customer_id.choices = _customer_choices()
    if not form.is_submitted():
        form.include_tax.data = Company.get_settings().tax_enabled_default
        form.sale_date.data = date.today()

    products = ProductRepository().get_active()
    warehouses = WarehouseRepository().get_active()
    stock = {
        (item.product_id, item.warehouse_id): item for item in InventoryRepository().get_all()
    }

    if form.validate_on_submit():
        items, errors = _parse_line_items(products, warehouses)
        for error in errors:
            flash(error, "danger")
        if not errors and not items:
            flash(_("Add at least one product line to the sale."), "danger")
        elif not errors:
            try:
                sale = SalesService().record_sale(
                    customer_id=form.customer_id.data,
                    items=items,
                    sale_date=datetime.combine(form.sale_date.data, datetime.now().time()),
                    invoice_number=form.invoice_number.data or None,
                    include_tax=form.include_tax.data,
                )
                flash(_("Sale #%(id)s recorded.", id=sale.id), "success")
                return redirect(url_for("sales.detail", sale_id=sale.id))
            except MiniErpError as exc:
                flash(str(exc), "danger")

    return render_template(
        "sales/sale_form.html",
        form=form,
        products=products,
        warehouses=warehouses,
        stock=stock,
        tax_rate=Company.get_settings().tax_rate,
    )


@bp.route("/<int:sale_id>")
@login_required
@module_required(User.MODULE_SALES)
def detail(sale_id):
    sale = SalesRepository().get(sale_id)
    if sale is None:
        flash(_("Sale not found."), "danger")
        return redirect(url_for("sales.index"))
    return render_template("sales/detail.html", sale=sale)


def _customer_choices():
    return [(c.id, c.name) for c in CustomerRepository().get_all()]


def _parse_line_items(products, warehouses) -> tuple[list[dict], list[str]]:
    """Read the product x warehouse grid: a quantity per (product,
    warehouse) cell, plus one unit price per product row (the price a
    product sells for varies by customer/quantity, not by which warehouse
    fulfills it — see #23).
    """
    items: list[dict] = []
    errors: list[str] = []

    for product in products:
        product_lines = []
        for warehouse in warehouses:
            raw_qty = request.form.get(f"quantity__{product.id}__{warehouse.id}")
            if not raw_qty:
                continue
            try:
                quantity = int(raw_qty)
            except ValueError:
                continue
            if quantity > 0:
                product_lines.append((warehouse.id, quantity))

        if not product_lines:
            continue

        raw_price = request.form.get(f"unit_price__{product.id}")
        unit_price = None
        if raw_price:
            try:
                unit_price = Decimal(raw_price)
            except InvalidOperation:
                unit_price = None

        if unit_price is None or unit_price <= 0:
            errors.append(
                _("Enter a unit price for %(name)s.", name=product_label(product))
            )
            continue

        for warehouse_id, quantity in product_lines:
            items.append(
                {
                    "product_id": product.id,
                    "warehouse_id": warehouse_id,
                    "quantity": quantity,
                    "unit_price": unit_price,
                }
            )

    return items, errors
