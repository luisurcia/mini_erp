"""Shared display helpers that depend on Company settings, not on any one
blueprint or template — used both as a plain function (Python call sites)
and registered as a Jinja global (templates)."""

from app.models.company import Company
from app.models.product import Product


def product_label(product: Product, settings: Company | None = None) -> str:
    """Product name for pickers/lists: flavor + name, size only if the
    company still asks for it on the product form."""
    settings = settings or Company.get_settings()
    label = f"{product.flavor.name} - {product.name}"
    if settings.product_size_enabled:
        label += f" ({product.size_ml}ml)"
    return label


def product_short_label(product: Product, settings: Company | None = None) -> str:
    """Compact product label for tight spaces (e.g. a grid column header):
    the product's short name, falling back to the full label when short
    names are off or this product doesn't have one."""
    settings = settings or Company.get_settings()
    if settings.product_short_name_enabled and product.short_name:
        return product.short_name
    return product_label(product, settings)
