from flask import flash, redirect, render_template, url_for
from flask_babel import gettext as _
from flask_login import login_required

from app.blueprints.inventory import bp
from app.blueprints.inventory.forms import RestockForm, WarehouseForm
from app.exceptions import MiniErpError
from app.models.warehouse import Warehouse
from app.permissions import admin_required, editor_required
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.warehouse_repository import WarehouseRepository
from app.services.inventory_service import InventoryService


@bp.route("/")
@login_required
def index():
    products = ProductRepository().get_all()
    warehouses = WarehouseRepository().get_active()
    stock = {
        (item.product_id, item.warehouse_id): item for item in InventoryRepository().get_all()
    }
    return render_template(
        "inventory/index.html", products=products, warehouses=warehouses, stock=stock
    )


@bp.route("/<int:product_id>/<int:warehouse_id>/restock", methods=["GET", "POST"])
@login_required
@editor_required
def restock(product_id, warehouse_id):
    product = ProductRepository().get(product_id)
    warehouse = WarehouseRepository().get(warehouse_id)
    if product is None or warehouse is None:
        flash(_("Product or warehouse not found."), "danger")
        return redirect(url_for("inventory.index"))

    existing_item = InventoryRepository().get_by_product_and_warehouse(product_id, warehouse_id)
    form = RestockForm()
    if not form.is_submitted():
        form.reorder_level.data = existing_item.reorder_level if existing_item else 10

    if form.validate_on_submit():
        try:
            quantity = form.quantity.data or 0
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
                        name=product.display_name,
                        warehouse=warehouse.name,
                    ),
                    "success",
                )
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
    )


@bp.route("/<int:product_id>/history")
@login_required
def history(product_id):
    product = ProductRepository().get(product_id)
    if product is None:
        flash(_("Product not found."), "danger")
        return redirect(url_for("inventory.index"))

    movements = InventoryService().movement_history(product_id)
    return render_template("inventory/history.html", product=product, movements=movements)


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
        warehouse.name = form.name.data
        warehouse.is_active = form.is_active.data
        WarehouseRepository().commit()
        flash(_("Warehouse '%(name)s' updated.", name=warehouse.name), "success")
        return redirect(url_for("inventory.warehouses"))

    return render_template(
        "inventory/warehouse_form.html", form=form, mode="edit", warehouse=warehouse
    )
