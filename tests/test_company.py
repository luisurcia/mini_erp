from decimal import Decimal

from app.models.company import Company


def test_get_settings_creates_default_row_with_spanish_language(app):
    settings = Company.get_settings()

    assert settings.id is not None
    assert settings.language == Company.LANGUAGE_ES
    assert settings.tax_rate == Decimal("19.00")
    assert settings.tax_enabled_default is True
    assert settings.product_short_name_enabled is True
    assert settings.product_size_enabled is True
    assert settings.product_sku_enabled is True


def test_get_settings_returns_existing_row(app):
    first = Company.get_settings()
    second = Company.get_settings()

    assert first.id == second.id
