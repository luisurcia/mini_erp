import pytest
from decimal import Decimal

from app.exceptions import InsufficientStockError
from app.services.inventory_service import InventoryService
from app.services.sales_service import SalesService


def test_record_sale_creates_sale_and_consumes_stock(app, customer, product):
    service = SalesService()
    sale = service.record_sale(
        customer_id=customer.id,
        items=[{"product_id": product.id, "quantity": 3}],
    )

    assert sale.id is not None
    assert sale.total_amount == Decimal("13.50")
    assert len(sale.items) == 1

    remaining = InventoryService().low_stock_report()
    item = InventoryService().inventory_repo.get_by_product(product.id)
    assert item.quantity_on_hand == 47


def test_record_sale_with_insufficient_stock_raises_and_does_not_partially_commit(
    app, customer, product
):
    service = SalesService()
    with pytest.raises(InsufficientStockError):
        service.record_sale(
            customer_id=customer.id,
            items=[{"product_id": product.id, "quantity": 9999}],
        )

    item = InventoryService().inventory_repo.get_by_product(product.id)
    assert item.quantity_on_hand == 50


def test_record_sale_requires_at_least_one_item(app, customer):
    service = SalesService()
    with pytest.raises(ValueError):
        service.record_sale(customer_id=customer.id, items=[])
