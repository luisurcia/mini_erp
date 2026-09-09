from datetime import date
from decimal import Decimal

import pytest

from app.exceptions import NotFoundError
from app.extensions import db
from app.models.purchase_category import PurchaseCategory
from app.repositories.purchase_repository import PurchaseRepository
from app.services.purchase_service import PurchaseService


def _record(service, *, day=1, month=6, year=2026, amount="1000", **kw):
    return service.record_purchase(
        purchase_date=date(year, month, day),
        item=kw.get("item", "Alcohol gel"),
        supplier=kw.get("supplier", "Proveedor X"),
        amount=Decimal(amount),
        category_id=kw.get("category_id"),
        invoice_number=kw.get("invoice_number"),
        includes_tax=kw.get("includes_tax", False),
    )


def test_record_purchase_assigns_a_global_running_correlative(app):
    service = PurchaseService()
    first = _record(service)
    second = _record(service)

    assert (first.sequence, second.sequence) == (1, 2)
    assert (first.code, second.code) == ("C-0001", "C-0002")


def test_correlative_keeps_climbing_after_a_void(app):
    service = PurchaseService()
    _record(service)
    voided = _record(service)
    service.set_voided(voided.id, True)
    third = _record(service)

    # The gap stays — a voided entry keeps its number, the next is C-0003.
    assert third.code == "C-0003"


def test_period_total_excludes_voided_purchases(app):
    service = PurchaseService()
    a = _record(service, amount="1000")
    _record(service, amount="2500")
    service.set_voided(a.id, True)

    all_three = PurchaseRepository().get_all()
    assert service.period_total(all_three) == Decimal("2500")


def test_set_voided_toggles_both_ways(app):
    service = PurchaseService()
    purchase = _record(service)

    service.set_voided(purchase.id, True)
    assert PurchaseRepository().get(purchase.id).voided is True

    service.set_voided(purchase.id, False)
    assert PurchaseRepository().get(purchase.id).voided is False


def test_set_voided_on_missing_purchase_raises(app):
    with pytest.raises(NotFoundError):
        PurchaseService().set_voided(999, True)


def test_update_purchase_changes_the_fields_but_not_the_code(app):
    service = PurchaseService()
    category = PurchaseCategory(name="Repuestos")
    db.session.add(category)
    db.session.commit()
    purchase = _record(service, amount="1000")

    service.update_purchase(
        purchase.id,
        purchase_date=date(2026, 7, 9),
        item="Repuesto bomba",
        supplier="Servicio Técnico",
        amount=Decimal("64500"),
        category_id=category.id,
        invoice_number="A-778",
        includes_tax=True,
    )

    updated = PurchaseRepository().get(purchase.id)
    assert updated.code == "C-0001"
    assert updated.amount == Decimal("64500")
    assert updated.category_name == "Repuestos"
    assert updated.includes_tax is True


def test_purchase_without_a_category_gets_the_no_definido_fallback(app):
    service = PurchaseService()
    purchase = _record(service)

    assert purchase.category is not None
    assert purchase.category.name == PurchaseCategory.FALLBACK_NAME


def test_get_fallback_reuses_the_existing_no_definido_row(app):
    first = PurchaseCategory.get_fallback()
    db.session.commit()
    second = PurchaseCategory.get_fallback()

    assert first.id == second.id
    assert (
        PurchaseCategory.query.filter_by(name=PurchaseCategory.FALLBACK_NAME).count()
        == 1
    )


def test_in_period_filters_by_year_and_optional_month(app):
    service = PurchaseService()
    _record(service, year=2025, month=3)
    _record(service, year=2026, month=1)
    _record(service, year=2026, month=1)
    _record(service, year=2026, month=8)

    repo = PurchaseRepository()
    assert len(repo.in_period(2026)) == 3
    assert len(repo.in_period(2026, 1)) == 2
    assert len(repo.in_period(2025)) == 1
    assert repo.distinct_years() == [2026, 2025]
