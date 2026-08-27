import pytest

from app.exceptions import InsufficientStockError, NotFoundError
from app.extensions import db
from app.models.warehouse import Warehouse
from app.services.inventory_service import InventoryService


def test_restock_increases_quantity(app, product, warehouse):
    service = InventoryService()
    item = service.restock(product.id, warehouse.id, 10, note="delivery")
    assert item.quantity_on_hand == 60


def test_consume_decreases_quantity(app, product, warehouse):
    service = InventoryService()
    item = service.consume(product.id, warehouse.id, 5)
    assert item.quantity_on_hand == 45


def test_consume_more_than_available_raises(app, product, warehouse):
    service = InventoryService()
    with pytest.raises(InsufficientStockError):
        service.consume(product.id, warehouse.id, 999)


def test_consume_unknown_product_raises_not_found(app, warehouse):
    service = InventoryService()
    with pytest.raises(NotFoundError):
        service.consume(product_id=99999, warehouse_id=warehouse.id, quantity=1)


def test_consume_unknown_warehouse_raises_not_found(app, product):
    service = InventoryService()
    with pytest.raises(NotFoundError):
        service.consume(product_id=product.id, warehouse_id=99999, quantity=1)


def test_low_stock_report_flags_items_at_or_below_reorder_level(app, product, warehouse):
    service = InventoryService()
    service.consume(product.id, warehouse.id, 45)  # 50 - 45 = 5, reorder level is 10
    low_stock = service.low_stock_report()
    assert any(item.product_id == product.id for item in low_stock)


def test_restock_in_a_different_warehouse_creates_its_own_row(app, product, warehouse):
    other = Warehouse(name="Other Warehouse", is_active=True)
    db.session.add(other)
    db.session.commit()

    service = InventoryService()
    item = service.restock(product.id, other.id, 7)

    assert item.quantity_on_hand == 7
    # the original warehouse's stock is untouched
    main_item = InventoryService().inventory_repo.get_by_product_and_warehouse(
        product.id, warehouse.id
    )
    assert main_item.quantity_on_hand == 50


def test_transfer_moves_stock_between_warehouses(app, product, warehouse):
    other = Warehouse(name="Other Warehouse", is_active=True)
    db.session.add(other)
    db.session.commit()

    service = InventoryService()
    source, destination = service.transfer(product.id, warehouse.id, other.id, 20, note="rebalance")

    assert source.quantity_on_hand == 30
    assert destination.quantity_on_hand == 20

    movements = service.movement_history(product.id)
    transfer_movements = [m for m in movements if m.reason == "transfer"]
    assert len(transfer_movements) == 2
    assert {m.change_qty for m in transfer_movements} == {-20, 20}


def test_transfer_with_insufficient_stock_raises_and_does_not_partially_apply(
    app, product, warehouse
):
    other = Warehouse(name="Other Warehouse", is_active=True)
    db.session.add(other)
    db.session.commit()

    service = InventoryService()
    with pytest.raises(InsufficientStockError):
        service.transfer(product.id, warehouse.id, other.id, 999)

    source = service.inventory_repo.get_by_product_and_warehouse(product.id, warehouse.id)
    assert source.quantity_on_hand == 50


def test_transfer_to_same_warehouse_raises(app):
    service = InventoryService()
    with pytest.raises(ValueError):
        service.transfer(1, 1, 1, 5)
