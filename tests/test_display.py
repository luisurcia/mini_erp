from decimal import Decimal

from app.display import format_money
from app.extensions import db
from app.models.company import Company


def test_format_money_default_currency_has_no_decimals(app):
    # Default company currency is CLP / "$" / 0 decimals, es locale -> "." grouping.
    assert format_money(45000) == "$45.000"
    assert format_money(Decimal("1234567")) == "$1.234.567"


def test_format_money_rounds_to_configured_decimals(app):
    assert format_money(Decimal("1234.56")) == "$1.235"
    assert format_money(Decimal("1234.49")) == "$1.234"


def test_format_money_treats_none_as_zero(app):
    assert format_money(None) == "$0"


def test_format_money_respects_decimals_and_symbol(app):
    company = Company.get_settings()
    company.currency_symbol = "US$"
    company.currency_decimals = 2
    db.session.commit()

    assert format_money(Decimal("1234.5")) == "US$1.234,50"
    assert format_money(1000) == "US$1.000,00"
