from decimal import Decimal

from app.extensions import db
from app.models.company import Company


def test_get_settings_creates_default_row_with_spanish_language(app):
    settings = Company.get_settings()

    assert settings.id is not None
    assert settings.name == "Scoby Kombucha"
    assert settings.brand_name == "Kombucha ERP"
    assert settings.language == Company.LANGUAGE_ES
    assert settings.tax_rate == Decimal("19.00")
    assert settings.tax_enabled_default is True
    assert settings.product_short_name_enabled is True
    assert settings.product_size_enabled is True
    assert settings.product_sku_enabled is True
    assert settings.product_flavor_enabled is True
    assert settings.product_price_enabled is True
    assert settings.currency_code == "CLP"
    assert settings.currency_symbol == "$"
    assert settings.currency_decimals == 0
    assert settings.money_quantum == Decimal("1")


def test_get_settings_returns_existing_row(app):
    first = Company.get_settings()
    second = Company.get_settings()

    assert first.id == second.id


def test_supported_languages_include_french(app):
    assert Company.LANGUAGE_FR in Company.LANGUAGES
    assert Company.LANGUAGE_LABELS[Company.LANGUAGE_FR] == "Français"


def test_select_locale_falls_back_to_company_default_outside_request(app):
    from app import _select_locale

    Company.get_settings().language = Company.LANGUAGE_FR
    db.session.commit()
    # No request context / no logged-in user -> company default.
    assert _select_locale() == Company.LANGUAGE_FR
