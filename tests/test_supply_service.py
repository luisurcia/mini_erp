import pytest

from app.extensions import db
from app.models.supply import Supply
from app.models.warehouse import Warehouse
from app.services.supply_service import SupplyService


def _make_supply(name="Botellas", unit="unidad", unit_price=0.35):
    supply = Supply(name=name, unit=unit, unit_price=unit_price, is_active=True)
    db.session.add(supply)
    db.session.commit()
    return supply


def test_restock_increases_quantity(app, warehouse):
    supply = _make_supply()
    service = SupplyService()
    item = service.restock(supply.id, warehouse.id, 100, note="delivery")
    assert item.quantity_on_hand == 100


def test_restock_twice_accumulates(app, warehouse):
    supply = _make_supply()
    service = SupplyService()
    service.restock(supply.id, warehouse.id, 100)
    item = service.restock(supply.id, warehouse.id, 50)
    assert item.quantity_on_hand == 150


def test_adjust_sets_exact_quantity_and_records_delta(app, warehouse):
    supply = _make_supply()
    service = SupplyService()
    service.restock(supply.id, warehouse.id, 100)
    item = service.adjust(supply.id, warehouse.id, 80, note="recount")

    assert item.quantity_on_hand == 80
    movements = service.movement_history(supply.id)
    adjustment = next(m for m in movements if m.reason == "adjustment")
    assert adjustment.change_qty == -20


def test_low_stock_report_flags_items_at_or_below_reorder_level(app, warehouse):
    supply = _make_supply()
    service = SupplyService()
    service.restock(supply.id, warehouse.id, 5, reorder_level=10)

    low_stock = service.low_stock_report()
    assert any(item.supply_id == supply.id for item in low_stock)


def test_restock_in_a_different_warehouse_creates_its_own_row(app, warehouse):
    other = Warehouse(name="Other Warehouse", is_active=True)
    db.session.add(other)
    db.session.commit()

    supply = _make_supply()
    service = SupplyService()
    service.restock(supply.id, warehouse.id, 100)
    item = service.restock(supply.id, other.id, 30)

    assert item.quantity_on_hand == 30
    main_item = service.supply_item_repo.get_by_supply_and_warehouse(supply.id, warehouse.id)
    assert main_item.quantity_on_hand == 100


def test_restock_with_non_positive_quantity_raises(app, warehouse):
    supply = _make_supply()
    service = SupplyService()
    with pytest.raises(ValueError):
        service.restock(supply.id, warehouse.id, 0)
