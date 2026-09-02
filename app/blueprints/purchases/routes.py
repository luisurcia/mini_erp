from datetime import date

from flask import flash, redirect, render_template, request, url_for
from flask_babel import gettext as _
from flask_login import login_required

from app.blueprints.purchases import bp
from app.blueprints.purchases.forms import PurchaseForm, VoidPurchaseForm
from app.exceptions import NotFoundError
from app.models.user import User
from app.permissions import module_required
from app.repositories.purchase_repository import PurchaseRepository
from app.services.purchase_service import PurchaseService

ALL_MONTHS = "all"


def _month_names() -> list[str]:
    return [
        _("Jan"), _("Feb"), _("Mar"), _("Apr"), _("May"), _("Jun"),
        _("Jul"), _("Aug"), _("Sep"), _("Oct"), _("Nov"), _("Dec"),
    ]


@bp.route("/")
@login_required
@module_required(User.MODULE_PURCHASES)
def index():
    repo = PurchaseRepository()
    today = date.today()

    available_years = repo.distinct_years() or [today.year]
    selected_year = request.args.get("year", type=int)
    if selected_year not in available_years:
        selected_year = available_years[0]

    # Default to the whole year; narrow to a month for the month-end total.
    raw_month = request.args.get("month", default="")
    selected_month = int(raw_month) if raw_month.isdigit() and 1 <= int(raw_month) <= 12 else None

    purchases = repo.in_period(selected_year, selected_month)
    service = PurchaseService(repo)

    return render_template(
        "purchases/index.html",
        purchases=purchases,
        period_total=service.period_total(purchases),
        active_count=sum(1 for p in purchases if not p.voided),
        available_years=available_years,
        selected_year=selected_year,
        selected_month=selected_month,
        month_names=_month_names(),
    )


@bp.route("/new", methods=["GET", "POST"])
@login_required
@module_required(User.MODULE_PURCHASES)
def new_purchase():
    form = PurchaseForm()
    if not form.is_submitted():
        form.purchase_date.data = date.today()

    if form.validate_on_submit():
        purchase = PurchaseService().record_purchase(
            purchase_date=form.purchase_date.data,
            item=form.item.data,
            supplier=form.supplier.data,
            amount=form.amount.data,
            category=form.category.data,
            invoice_number=form.invoice_number.data,
            includes_tax=form.includes_tax.data,
            notes=form.notes.data,
        )
        flash(_("Purchase %(code)s recorded.", code=purchase.code), "success")
        return redirect(url_for("purchases.index"))

    return render_template("purchases/purchase_form.html", form=form, mode="new")


@bp.route("/<int:purchase_id>/edit", methods=["GET", "POST"])
@login_required
@module_required(User.MODULE_PURCHASES)
def edit_purchase(purchase_id):
    purchase = PurchaseRepository().get(purchase_id)
    if purchase is None:
        flash(_("Purchase not found."), "danger")
        return redirect(url_for("purchases.index"))

    form = PurchaseForm(obj=purchase)

    if form.validate_on_submit():
        PurchaseService().update_purchase(
            purchase_id,
            purchase_date=form.purchase_date.data,
            item=form.item.data,
            supplier=form.supplier.data,
            amount=form.amount.data,
            category=form.category.data,
            invoice_number=form.invoice_number.data,
            includes_tax=form.includes_tax.data,
            notes=form.notes.data,
        )
        flash(_("Purchase %(code)s updated.", code=purchase.code), "success")
        return redirect(url_for("purchases.index"))

    return render_template(
        "purchases/purchase_form.html",
        form=form,
        mode="edit",
        purchase=purchase,
        void_form=VoidPurchaseForm(),
    )


@bp.route("/<int:purchase_id>/void", methods=["POST"])
@login_required
@module_required(User.MODULE_PURCHASES)
def void_purchase(purchase_id):
    if VoidPurchaseForm().validate_on_submit():
        try:
            purchase = PurchaseService().set_voided(purchase_id, True)
            flash(_("Purchase %(code)s voided.", code=purchase.code), "success")
        except NotFoundError:
            flash(_("Purchase not found."), "danger")
    return redirect(url_for("purchases.edit_purchase", purchase_id=purchase_id))


@bp.route("/<int:purchase_id>/restore", methods=["POST"])
@login_required
@module_required(User.MODULE_PURCHASES)
def restore_purchase(purchase_id):
    if VoidPurchaseForm().validate_on_submit():
        try:
            purchase = PurchaseService().set_voided(purchase_id, False)
            flash(_("Purchase %(code)s restored.", code=purchase.code), "success")
        except NotFoundError:
            flash(_("Purchase not found."), "danger")
    return redirect(url_for("purchases.edit_purchase", purchase_id=purchase_id))
