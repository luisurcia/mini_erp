from flask import flash, redirect, render_template, request, url_for
from flask_babel import gettext as _
from flask_login import login_required

from app.blueprints.inventory.forms import RestockForm
from app.blueprints.supplies import bp
from app.blueprints.supplies.forms import ProductRecipeForm, SupplyForm
from app.display import product_label
from app.exceptions import MiniErpError
from app.models.product_supply import ProductSupply
from app.models.supply import Supply
from app.models.user import User
from app.permissions import admin_required, module_required
from app.repositories.product_repository import ProductRepository
from app.repositories.product_supply_repository import ProductSupplyRepository
from app.repositories.supply_repository import SupplyItemRepository, SupplyRepository
from app.repositories.warehouse_repository import WarehouseRepository
from app.services.supply_service import SupplyService


@bp.route("/")
@login_required
@module_required(User.MODULE_SUPPLIES)
def index():
    supplies = SupplyRepository().get_all()
    return render_template("supplies/index.html", supplies=supplies)


@bp.route("/new", methods=["GET", "POST"])
@login_required
@module_required(User.MODULE_SUPPLIES)
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
@module_required(User.MODULE_SUPPLIES)
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
@module_required(User.MODULE_SUPPLIES)
def stock():
    supplies = SupplyRepository().get_all()
    supplies_warehouse = WarehouseRepository().get_supplies_warehouse()
    warehouses = [supplies_warehouse] if supplies_warehouse else []
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
@module_required(User.MODULE_SUPPLIES)
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
@module_required(User.MODULE_SUPPLIES)
def history(supply_id):
    supply = SupplyRepository().get(supply_id)
    if supply is None:
        flash(_("Supply not found."), "danger")
        return redirect(url_for("supplies.stock"))

    movements = SupplyService().movement_history(supply_id)
    return render_template("supplies/history.html", supply=supply, movements=movements)


@bp.route("/recipes")
@login_required
@admin_required
def recipes():
    products = ProductRepository().get_all()
    rows = ProductSupplyRepository().for_products([p.id for p in products])
    recipe_by_product: dict[int, list[ProductSupply]] = {}
    for row in rows:
        recipe_by_product.setdefault(row.product_id, []).append(row)
    return render_template(
        "supplies/recipes.html",
        products=products,
        recipe_by_product=recipe_by_product,
    )


@bp.route("/recipes/<int:product_id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_recipe(product_id):
    product = ProductRepository().get(product_id)
    if product is None:
        flash(_("Product not found."), "danger")
        return redirect(url_for("supplies.recipes"))

    repo = ProductSupplyRepository()
    supply_repo = SupplyRepository()
    existing = {row.supply_id: row for row in repo.for_product(product_id)}

    # Every active supply, plus any inactive one already in this recipe —
    # a deactivated supply stays in the recipes it's part of (#48).
    supplies = list(supply_repo.get_active())
    active_ids = {s.id for s in supplies}
    supplies += [
        supply_repo.get(supply_id)
        for supply_id in existing
        if supply_id not in active_ids
    ]
    supplies.sort(key=lambda s: s.name)

    form = ProductRecipeForm()
    if form.validate_on_submit():
        for supply in supplies:
            raw = request.form.get(f"quantity__{supply.id}", "").strip()
            try:
                qty = int(raw) if raw else 0
            except ValueError:
                qty = 0
            row = existing.get(supply.id)
            if qty > 0 and row is None:
                repo.add(
                    ProductSupply(
                        product_id=product_id,
                        supply_id=supply.id,
                        quantity_per_unit=qty,
                    )
                )
            elif qty > 0:
                row.quantity_per_unit = qty
            elif row is not None:
                repo.delete(row)
        repo.commit()
        flash(
            _("Supplies recipe updated for %(name)s.", name=product_label(product)),
            "success",
        )
        return redirect(url_for("supplies.recipes"))

    return render_template(
        "supplies/recipe_form.html",
        form=form,
        product=product,
        supplies=supplies,
        existing=existing,
        active_ids=active_ids,
    )
