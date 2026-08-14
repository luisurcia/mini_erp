from flask import flash, redirect, render_template, url_for
from flask_login import login_required

from app.blueprints.inventory import bp
from app.blueprints.inventory.forms import ProductForm, RestockForm
from app.exceptions import MiniErpError
from app.models.product import Product
from app.repositories.product_repository import FlavorRepository, ProductRepository
from app.services.inventory_service import InventoryService


@bp.route("/")
@login_required
def index():
    products = ProductRepository().get_all()
    return render_template("inventory/index.html", products=products)


@bp.route("/new", methods=["GET", "POST"])
@login_required
def new_product():
    form = ProductForm()
    form.flavor_id.choices = _flavor_choices()

    if form.validate_on_submit():
        product = Product(
            flavor_id=form.flavor_id.data,
            name=form.name.data,
            sku=form.sku.data,
            size_ml=form.size_ml.data,
            unit_price=form.unit_price.data,
            is_active=form.is_active.data,
        )
        ProductRepository().add(product)
        ProductRepository().commit()

        InventoryService().create_inventory_item(
            product_id=product.id,
            initial_qty=form.initial_qty.data or 0,
            reorder_level=form.reorder_level.data,
        )
        flash(f"Product '{product.display_name}' created.", "success")
        return redirect(url_for("inventory.index"))

    return render_template("inventory/product_form.html", form=form, mode="new")


@bp.route("/<int:product_id>/edit", methods=["GET", "POST"])
@login_required
def edit_product(product_id):
    product = ProductRepository().get(product_id)
    if product is None:
        flash("Product not found.", "danger")
        return redirect(url_for("inventory.index"))

    form = ProductForm(obj=product)
    form.flavor_id.choices = _flavor_choices()
    if not form.is_submitted():
        form.reorder_level.data = product.inventory_item.reorder_level
        form.initial_qty.data = product.inventory_item.quantity_on_hand

    if form.validate_on_submit():
        product.flavor_id = form.flavor_id.data
        product.name = form.name.data
        product.sku = form.sku.data
        product.size_ml = form.size_ml.data
        product.unit_price = form.unit_price.data
        product.is_active = form.is_active.data
        product.inventory_item.reorder_level = form.reorder_level.data
        ProductRepository().commit()
        flash(f"Product '{product.display_name}' updated.", "success")
        return redirect(url_for("inventory.index"))

    return render_template(
        "inventory/product_form.html", form=form, mode="edit", product=product
    )


@bp.route("/<int:product_id>/restock", methods=["GET", "POST"])
@login_required
def restock(product_id):
    product = ProductRepository().get(product_id)
    if product is None:
        flash("Product not found.", "danger")
        return redirect(url_for("inventory.index"))

    form = RestockForm()
    if form.validate_on_submit():
        try:
            InventoryService().restock(product_id, form.quantity.data, note=form.note.data)
            flash(f"Restocked {form.quantity.data} units of {product.display_name}.", "success")
            return redirect(url_for("inventory.index"))
        except MiniErpError as exc:
            flash(str(exc), "danger")

    return render_template("inventory/restock_form.html", form=form, product=product)


@bp.route("/<int:product_id>/history")
@login_required
def history(product_id):
    product = ProductRepository().get(product_id)
    if product is None:
        flash("Product not found.", "danger")
        return redirect(url_for("inventory.index"))

    movements = InventoryService().movement_history(product_id)
    return render_template("inventory/history.html", product=product, movements=movements)


def _flavor_choices():
    return [(flavor.id, flavor.name) for flavor in FlavorRepository().get_all()]
