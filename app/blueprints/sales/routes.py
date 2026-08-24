from flask import flash, redirect, render_template, request, url_for
from flask_babel import gettext as _
from flask_login import login_required

from app.blueprints.sales import bp
from app.blueprints.sales.forms import SaleMetaForm
from app.exceptions import MiniErpError
from app.models.company import Company
from app.models.sales import Sale
from app.permissions import editor_required
from app.repositories.customer_repository import CustomerRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.sales_repository import SalesRepository
from app.services.sales_service import SalesService


@bp.route("/")
@login_required
def index():
    sales = SalesRepository().get_all()
    return render_template("sales/index.html", sales=sales)


@bp.route("/new", methods=["GET", "POST"])
@login_required
@editor_required
def new_sale():
    form = SaleMetaForm()
    form.customer_id.choices = _customer_choices()
    form.status.choices = [
        (Sale.STATUS_COMPLETED, _("Completed")),
        (Sale.STATUS_PENDING, _("Pending")),
    ]
    if not form.is_submitted():
        form.include_tax.data = Company.get_settings().tax_enabled_default
    products = ProductRepository().get_active()

    if form.validate_on_submit():
        items = _parse_line_items()
        if not items:
            flash(_("Add at least one product line to the sale."), "danger")
        else:
            try:
                sale = SalesService().record_sale(
                    customer_id=form.customer_id.data,
                    items=items,
                    status=form.status.data,
                    notes=form.notes.data,
                    invoice_number=form.invoice_number.data or None,
                    include_tax=form.include_tax.data,
                )
                flash(_("Sale #%(id)s recorded.", id=sale.id), "success")
                return redirect(url_for("sales.detail", sale_id=sale.id))
            except MiniErpError as exc:
                flash(str(exc), "danger")

    return render_template("sales/sale_form.html", form=form, products=products)


@bp.route("/<int:sale_id>")
@login_required
def detail(sale_id):
    sale = SalesRepository().get(sale_id)
    if sale is None:
        flash(_("Sale not found."), "danger")
        return redirect(url_for("sales.index"))
    return render_template("sales/detail.html", sale=sale)


def _customer_choices():
    return [(c.id, c.name) for c in CustomerRepository().get_all()]


def _parse_line_items() -> list[dict]:
    product_ids = request.form.getlist("product_id[]")
    quantities = request.form.getlist("quantity[]")
    items = []
    for product_id, quantity in zip(product_ids, quantities):
        if not product_id or not quantity:
            continue
        qty = int(quantity)
        if qty <= 0:
            continue
        items.append({"product_id": int(product_id), "quantity": qty})
    return items
