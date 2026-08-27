"""Shared display helpers that depend on Company settings, not on any one
blueprint or template — used both as a plain function (Python call sites)
and registered as a Jinja global (templates)."""

from decimal import ROUND_HALF_UP, Decimal

from flask_babel import format_decimal

from app.models.company import Company
from app.models.product import Product


def format_money(value, settings: Company | None = None) -> str:
    """Render a monetary amount using the company's currency settings:
    symbol prefix, locale-aware thousands grouping, and exactly
    currency_decimals decimal places (0 for CLP — see #39). `None` is
    treated as zero so callers don't have to guard optional prices."""
    settings = settings or Company.get_settings()
    decimals = settings.currency_decimals
    amount = Decimal(str(value if value is not None else 0)).quantize(
        settings.money_quantum, rounding=ROUND_HALF_UP
    )
    pattern = "#,##0" + ("." + "0" * decimals if decimals else "")
    return f"{settings.currency_symbol}{format_decimal(amount, format=pattern)}"


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
