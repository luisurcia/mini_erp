from flask import flash, redirect, render_template, url_for
from flask_babel import gettext as _
from flask_login import login_required

from app.blueprints.inventory.forms import RestockForm
from app.blueprints.supplies import bp
from app.blueprints.supplies.forms import SupplyForm
from app.exceptions import MiniErpError
from app.models.supply import Supply
from app.permissions import editor_required
from app.repositories.supply_repository import SupplyItemRepository, SupplyRepository
from app.repositories.warehouse_repository import WarehouseRepository
from app.services.supply_service import SupplyService


@bp.route("/")
@login_required
def index():
    supplies = SupplyRepository().get_all()
    return render_template("supplies/index.html", supplies=supplies)


@bp.route("/new", methods=["GET", "POST"])
@login_required
@editor_required
def new_supply():
    form = SupplyForm()

    if form.validate_on_submit():
        supply = Supply(
            name=form.name.data,
            unit=form.unit.data,
            unit_price=form.unit_price.data,
            is_active=form.is_active.data,
        )
        SupplyRepository().add(supply)
        SupplyRepository().commit()
        flash(_("Supply '%(name)s' created.", name=supply.name), "success")
        return redirect(url_for("supplies.index"))

    return render_template("supplies/supply_form.html", form=form, mode="new")


@bp.route("/<int:supply_id>/edit", methods=["GET", "POST"])
@login_required
@editor_required
def edit_supply(supply_id):
    supply = SupplyRepository().get(supply_id)
    if supply is None:
        flash(_("Supply not found."), "danger")
        return redirect(url_for("supplies.index"))

    form = SupplyForm(obj=supply)

    if form.validate_on_submit():
        supply.name = form.name.data
        supply.unit = form.unit.data
        supply.unit_price = form.unit_price.data
        supply.is_active = form.is_active.data
        SupplyRepository().commit()
        flash(_("Supply '%(name)s' updated.", name=supply.name), "success")
        return redirect(url_for("supplies.index"))

    return render_template("supplies/supply_form.html", form=form, mode="edit", supply=supply)


@bp.route("/stock")
@login_required
def stock():
    supplies = SupplyRepository().get_all()
    warehouses = WarehouseRepository().get_active()
    stock_by_cell = {
        (item.supply_id, item.warehouse_id): item for item in SupplyItemRepository().get_all()
    }
    warehouse_totals = [
        sum(
            stock_by_cell[(supply.id, warehouse.id)].quantity_on_hand
            for supply in supplies
            if (supply.id, warehouse.id) in stock_by_cell
        )
        for warehouse in warehouses
    ]
    return render_template(
        "supplies/stock.html",
        supplies=supplies,
        warehouses=warehouses,
        stock=stock_by_cell,
        warehouse_totals=warehouse_totals,
        grand_total=sum(warehouse_totals),
    )


@bp.route("/<int:supply_id>/<int:warehouse_id>/restock", methods=["GET", "POST"])
@login_required
@editor_required
def restock(supply_id, warehouse_id):
    supply = SupplyRepository().get(supply_id)
    warehouse = WarehouseRepository().get(warehouse_id)
    if supply is None or warehouse is None:
        flash(_("Supply or warehouse not found."), "danger")
        return redirect(url_for("supplies.stock"))

    existing_item = SupplyItemRepository().get_by_supply_and_warehouse(supply_id, warehouse_id)
    form = RestockForm()
    if not form.is_submitted():
        form.reorder_level.data = existing_item.reorder_level if existing_item else 10

    if form.validate_on_submit():
        try:
            quantity = form.quantity.data or 0
            if quantity > 0:
                SupplyService().restock(
                    supply_id,
                    warehouse_id,
                    quantity,
                    note=form.note.data,
                    reorder_level=form.reorder_level.data,
                )
                flash(
                    _(
                        "Restocked %(qty)s %(unit)s of %(name)s in %(warehouse)s.",
                        qty=quantity,
                        unit=supply.unit,
                        name=supply.name,
                        warehouse=warehouse.name,
                    ),
                    "success",
                )
            else:
                SupplyService().set_reorder_level(supply_id, warehouse_id, form.reorder_level.data)
                flash(_("Reorder level updated."), "success")
            return redirect(url_for("supplies.stock"))
        except MiniErpError as exc:
            flash(str(exc), "danger")

    on_hand = existing_item.quantity_on_hand if existing_item else 0
    return render_template(
        "supplies/restock_form.html",
        form=form,
        supply=supply,
        warehouse=warehouse,
        on_hand=on_hand,
    )


@bp.route("/<int:supply_id>/history")
@login_required
def history(supply_id):
    supply = SupplyRepository().get(supply_id)
    if supply is None:
        flash(_("Supply not found."), "danger")
        return redirect(url_for("supplies.stock"))

    movements = SupplyService().movement_history(supply_id)
    return render_template("supplies/history.html", supply=supply, movements=movements)
