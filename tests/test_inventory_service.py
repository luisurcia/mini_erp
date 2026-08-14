import pytest

from app.exceptions import InsufficientStockError, NotFoundError
from app.services.inventory_service import InventoryService


def test_restock_increases_quantity(app, product):
    service = InventoryService()
    item = service.restock(product.id, 10, note="delivery")
    assert item.quantity_on_hand == 60


def test_consume_decreases_quantity(app, product):
    service = InventoryService()
    item = service.consume(product.id, 5)
    assert item.quantity_on_hand == 45


def test_consume_more_than_available_raises(app, product):
    service = InventoryService()
    with pytest.raises(InsufficientStockError):
        service.consume(product.id, 999)


def test_consume_unknown_product_raises_not_found(app):
    service = InventoryService()
    with pytest.raises(NotFoundError):
        service.consume(product_id=99999, quantity=1)


def test_low_stock_report_flags_items_at_or_below_reorder_level(app, product):
    service = InventoryService()
    service.consume(product.id, 45)  # 50 - 45 = 5, reorder level is 10
    low_stock = service.low_stock_report()
    assert any(item.product_id == product.id for item in low_stock)
