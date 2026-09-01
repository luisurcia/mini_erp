from flask import flash, redirect, render_template, url_for
from flask_babel import gettext as _
from flask_login import login_required

from app.blueprints.inventory import bp
from app.blueprints.inventory.forms import RestockForm, TransferForm, WarehouseForm
from app.display import product_label
from app.exceptions import MiniErpError
from app.models.user import User
from app.models.warehouse import Warehouse
from app.permissions import admin_required, module_required
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.warehouse_repository import WarehouseRepository
from app.services.inventory_service import InventoryService
from app.services.supply_service import SupplyService


@bp.route("/")
@login_required
@module_required(User.MODULE_INVENTORY)
def index():
    products = ProductRepository().get_all()
    warehouses = WarehouseRepository().get_stock_locations()
    stock = {
        (item.product_id, item.warehouse_id): item for item in InventoryRepository().get_all()
    }
    warehouse_totals = [
        sum(
            stock[(product.id, warehouse.id)].quantity_on_hand
            for product in products
            if (product.id, warehouse.id) in stock
        )
        for warehouse in warehouses
    ]
    return render_template(
        "inventory/index.html",
        products=products,
        warehouses=warehouses,
        stock=stock,
        warehouse_totals=warehouse_totals,
        grand_total=sum(warehouse_totals),
    )


@bp.route("/<int:product_id>/<int:warehouse_id>/restock", methods=["GET", "POST"])
@login_required
@module_required(User.MODULE_INVENTORY)
def restock(product_id, warehouse_id):
    product = ProductRepository().get(product_id)
    warehouse = WarehouseRepository().get(warehouse_id)
    if product is None or warehouse is None:
        flash(_("Product or warehouse not found."), "danger")
        return redirect(url_for("inventory.index"))

    existing_item = InventoryRepository().get_by_product_and_warehouse(product_id, warehouse_id)
    form = RestockForm()
    # Stock only enters through the fermentation warehouse (#86); elsewhere
    # this screen just edits the reorder level, so drop the quantity field.
    can_restock = warehouse.is_fermentation
    if not can_restock:
        del form.quantity
    if not form.is_submitted():
        form.reorder_level.data = existing_item.reorder_level if existing_item else 10

    if form.validate_on_submit():
        try:
            quantity = (form.quantity.data or 0) if can_restock else 0
            if quantity > 0:
                InventoryService().restock(
                    product_id,
                    warehouse_id,
                    quantity,
                    note=form.note.data,
                    reorder_level=form.reorder_level.data,
                )
                flash(
                    _(
                        "Restocked %(qty)s units of %(name)s in %(warehouse)s.",
                        qty=quantity,
                        name=product_label(product),
                        warehouse=warehouse.name,
                    ),
                    "success",
                )
                _warn_on_negative_supplies()
            else:
                InventoryService().set_reorder_level(
                    product_id, warehouse_id, form.reorder_level.data
                )
                flash(_("Reorder level updated."), "success")
            return redirect(url_for("inventory.index"))
        except MiniErpError as exc:
            flash(str(exc), "danger")

    on_hand = existing_item.quantity_on_hand if existing_item else 0
    return render_template(
        "inventory/restock_form.html",
        form=form,
        product=product,
        warehouse=warehouse,
        on_hand=on_hand,
        can_restock=can_restock,
    )


@bp.route("/transfer", methods=["GET", "POST"])
@login_required
@module_required(User.MODULE_INVENTORY)
def transfer():
    form = TransferForm()
    locations = WarehouseRepository().get_stock_locations()
    form.product_id.choices = [
        (p.id, product_label(p)) for p in ProductRepository().get_active()
    ]
    # Only the flow routes: send from Fermentación/Principal, receive into
    # Principal/distribución (#86). The service validates too.
    form.from_warehouse_id.choices = [
        (w.id, w.name) for w in locations if w.stage in (
            Warehouse.STAGE_FERMENTATION, Warehouse.STAGE_MAIN
        )
    ]
    form.to_warehouse_id.choices = [
        (w.id, w.name) for w in locations if w.stage in (
            Warehouse.STAGE_MAIN, Warehouse.STAGE_DISTRIBUTION
        )
    ]

    # On-hand quantity per (product, warehouse), keyed "<pid>-<wid>" so the
    # form can show the live stock of the picked warehouses (#50).
    stock_levels = {
        f"{item.product_id}-{item.warehouse_id}": item.quantity_on_hand
        for item in InventoryRepository().get_all()
    }
    warehouse_stages = {str(w.id): w.stage for w in locations}

    if form.validate_on_submit():
        try:
            InventoryService().transfer(
                form.product_id.data,
                form.from_warehouse_id.data,
                form.to_warehouse_id.data,
                form.quantity.data,
                note=form.note.data,
            )
            product = ProductRepository().get(form.product_id.data)
            from_warehouse = WarehouseRepository().get(form.from_warehouse_id.data)
            to_warehouse = WarehouseRepository().get(form.to_warehouse_id.data)
            flash(
                _(
                    "Transferred %(qty)s units of %(name)s from %(from_wh)s to %(to_wh)s.",
                    qty=form.quantity.data,
                    name=product_label(product),
                    from_wh=from_warehouse.name,
                    to_wh=to_warehouse.name,
                ),
                "success",
            )
            return redirect(url_for("inventory.index"))
        except MiniErpError as exc:
            flash(str(exc), "danger")

    return render_template(
        "inventory/transfer_form.html",
        form=form,
        stock_levels=stock_levels,
        warehouse_stages=warehouse_stages,
    )


@bp.route("/<int:product_id>/history")
@login_required
@module_required(User.MODULE_INVENTORY)
def history(product_id):
    product = ProductRepository().get(product_id)
    if product is None:
        flash(_("Product not found."), "danger")
        return redirect(url_for("inventory.index"))

    movements = InventoryService().movement_history(product_id)
    return render_template("inventory/history.html", product=product, movements=movements)


def _warn_on_negative_supplies() -> None:
    """After an assembly restock, flash a warning (not an error — the
    stock still went in) if a product's bill of materials pushed a supply
    below zero (#89)."""
    shortfalls = SupplyService().negative_stock()
    if shortfalls:
        detail = ", ".join(f"{name}: {qty}" for name, qty in shortfalls)
        flash(
            _(
                "Stock was received, but supply stock is now negative: "
                "%(detail)s. Restock the supplies warehouse.",
                detail=detail,
            ),
            "warning",
        )


@bp.route("/warehouses")
@login_required
@admin_required
def warehouses():
    all_warehouses = WarehouseRepository().get_all()
    return render_template("inventory/warehouses_list.html", warehouses=all_warehouses)


@bp.route("/warehouses/new", methods=["GET", "POST"])
@login_required
@admin_required
def new_warehouse():
    form = WarehouseForm()

    if form.validate_on_submit():
        warehouse = Warehouse(name=form.name.data, is_active=form.is_active.data)
        WarehouseRepository().add(warehouse)
        WarehouseRepository().commit()
        flash(_("Warehouse '%(name)s' created.", name=warehouse.name), "success")
        return redirect(url_for("inventory.warehouses"))

    return render_template("inventory/warehouse_form.html", form=form, mode="new")


@bp.route("/warehouses/<int:warehouse_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_warehouse(warehouse_id):
    warehouse = WarehouseRepository().get(warehouse_id)
    if warehouse is None:
        flash(_("Warehouse not found."), "danger")
        return redirect(url_for("inventory.warehouses"))

    form = WarehouseForm(obj=warehouse)

    if form.validate_on_submit():
        if warehouse.is_supplies and not form.is_active.data:
            flash(_("The supplies warehouse can't be deactivated."), "danger")
        else:
            warehouse.name = form.name.data
            warehouse.is_active = form.is_active.data
            WarehouseRepository().commit()
            flash(_("Warehouse '%(name)s' updated.", name=warehouse.name), "success")
            return redirect(url_for("inventory.warehouses"))

    return render_template(
        "inventory/warehouse_form.html", form=form, mode="edit", warehouse=warehouse
    )
