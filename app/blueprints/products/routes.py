from uuid import uuid4

from flask import flash, redirect, render_template, url_for
from flask_babel import gettext as _
from flask_login import login_required

from app.blueprints.products import bp
from app.blueprints.products.forms import ProductForm
from app.models.company import Company
from app.models.product import Product
from app.permissions import editor_required
from app.repositories.product_repository import FlavorRepository, ProductRepository

# Matches Product.size_ml's own column default — used when a company hides
# the size field and a value still has to be stored.
DEFAULT_SIZE_ML = 355


@bp.route("/")
@login_required
def index():
    products = ProductRepository().get_all()
    settings = Company.get_settings()
    return render_template("products/index.html", products=products, settings=settings)


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
        short_name = form.short_name.data or None if settings.product_short_name_enabled else None
        product = Product(
            flavor_id=form.flavor_id.data,
            name=form.name.data,
            short_name=short_name,
            sku=sku,
            size_ml=size_ml,
            unit_price=form.unit_price.data,
            is_active=form.is_active.data,
        )
        ProductRepository().add(product)
        ProductRepository().commit()
        flash(_("Product '%(name)s' created.", name=product.display_name), "success")
        return redirect(url_for("products.index"))

    return render_template("products/product_form.html", form=form, mode="new")


@bp.route("/<int:product_id>/edit", methods=["GET", "POST"])
@login_required
@editor_required
def edit_product(product_id):
    product = ProductRepository().get(product_id)
    if product is None:
        flash(_("Product not found."), "danger")
        return redirect(url_for("products.index"))

    settings = Company.get_settings()
    form = ProductForm(obj=product)
    form.flavor_id.choices = _flavor_choices()
    _apply_product_field_visibility(form, settings)

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
        ProductRepository().commit()
        flash(_("Product '%(name)s' updated.", name=product.display_name), "success")
        return redirect(url_for("products.index"))

    return render_template(
        "products/product_form.html", form=form, mode="edit", product=product
    )


def _flavor_choices():
    return [(flavor.id, flavor.name) for flavor in FlavorRepository().get_all()]
