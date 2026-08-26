from uuid import uuid4

from flask import flash, redirect, render_template, url_for
from flask_babel import gettext as _
from flask_login import login_required

from app.blueprints.inventory import bp
from app.blueprints.inventory.forms import ProductForm, RestockForm
from app.exceptions import MiniErpError
from app.models.company import Company
from app.models.product import Product
from app.permissions import editor_required
from app.repositories.product_repository import FlavorRepository, ProductRepository
from app.services.inventory_service import InventoryService

# Matches Product.size_ml's own column default — used when a company hides
# the size field and a value still has to be stored.
DEFAULT_SIZE_ML = 355


@bp.route("/")
@login_required
def index():
    products = ProductRepository().get_all()
    return render_template("inventory/index.html", products=products)


def _apply_product_field_visibility(form: ProductForm, settings: Company) -> None:
    """Drop fields a company has hidden from its product form.

    Removing a field from the bound form (rather than hiding it in the
    template) means it's skipped by both rendering and validation for free
    — `render_form` only draws what's left in `form`.
    """
    if not settings.product_short_name_enabled:
        del form.short_name
    if not settings.product_size_enabled:
        del form.size_ml
    if not settings.product_sku_enabled:
        del form.sku


def _generate_sku(product_name: str, size_ml: int) -> str:
    """Stand in for a SKU when a company doesn't want to type one.

    Not meant to be meaningful — just unique enough (~16M combinations) not
    to collide in a single-company, low-volume catalog.
    """
    slug = "".join(ch for ch in product_name.upper() if ch.isalnum())[:6] or "PROD"
    return f"{slug}-{size_ml}-{uuid4().hex[:5].upper()}"


@bp.route("/new", methods=["GET", "POST"])
@login_required
@editor_required
def new_product():
    settings = Company.get_settings()
    form = ProductForm()
    form.flavor_id.choices = _flavor_choices()
    _apply_product_field_visibility(form, settings)

    if form.validate_on_submit():
        size_ml = form.size_ml.data if settings.product_size_enabled else DEFAULT_SIZE_ML
        sku = (
            form.sku.data
            if settings.product_sku_enabled
            else _generate_sku(form.name.data, size_ml)
        )
        product = Product(
            flavor_id=form.flavor_id.data,
            name=form.name.data,
            short_name=(form.short_name.data or None) if settings.product_short_name_enabled else None,
            sku=sku,
            size_ml=size_ml,
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
        flash(_("Product '%(name)s' created.", name=product.display_name), "success")
        return redirect(url_for("inventory.index"))

    return render_template("inventory/product_form.html", form=form, mode="new")


@bp.route("/<int:product_id>/edit", methods=["GET", "POST"])
@login_required
@editor_required
def edit_product(product_id):
    product = ProductRepository().get(product_id)
    if product is None:
        flash(_("Product not found."), "danger")
        return redirect(url_for("inventory.index"))

    settings = Company.get_settings()
    form = ProductForm(obj=product)
    form.flavor_id.choices = _flavor_choices()
    _apply_product_field_visibility(form, settings)
    if not form.is_submitted():
        form.reorder_level.data = product.inventory_item.reorder_level
        form.initial_qty.data = product.inventory_item.quantity_on_hand

    if form.validate_on_submit():
        product.flavor_id = form.flavor_id.data
        product.name = form.name.data
        if settings.product_short_name_enabled:
            product.short_name = form.short_name.data or None
        if settings.product_sku_enabled:
            product.sku = form.sku.data
        if settings.product_size_enabled:
            product.size_ml = form.size_ml.data
        product.unit_price = form.unit_price.data
        product.is_active = form.is_active.data
        product.inventory_item.reorder_level = form.reorder_level.data
        ProductRepository().commit()
        flash(_("Product '%(name)s' updated.", name=product.display_name), "success")
        return redirect(url_for("inventory.index"))

    return render_template(
        "inventory/product_form.html", form=form, mode="edit", product=product
    )


@bp.route("/<int:product_id>/restock", methods=["GET", "POST"])
@login_required
@editor_required
def restock(product_id):
    product = ProductRepository().get(product_id)
    if product is None:
        flash(_("Product not found."), "danger")
        return redirect(url_for("inventory.index"))

    form = RestockForm()
    if form.validate_on_submit():
        try:
            InventoryService().restock(product_id, form.quantity.data, note=form.note.data)
            flash(
                _(
                    "Restocked %(qty)s units of %(name)s.",
                    qty=form.quantity.data,
                    name=product.display_name,
                ),
                "success",
            )
            return redirect(url_for("inventory.index"))
        except MiniErpError as exc:
            flash(str(exc), "danger")

    return render_template("inventory/restock_form.html", form=form, product=product)


@bp.route("/<int:product_id>/history")
@login_required
def history(product_id):
    product = ProductRepository().get(product_id)
    if product is None:
        flash(_("Product not found."), "danger")
        return redirect(url_for("inventory.index"))

    movements = InventoryService().movement_history(product_id)
    return render_template("inventory/history.html", product=product, movements=movements)


def _flavor_choices():
    return [(flavor.id, flavor.name) for flavor in FlavorRepository().get_all()]
