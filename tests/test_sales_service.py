from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.exceptions import InsufficientStockError
from app.extensions import db
from app.models.company import Company
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


def test_record_sale_without_tax_leaves_total_equal_to_subtotal(app, customer, product):
    sale = SalesService().record_sale(
        customer_id=customer.id, items=[{"product_id": product.id, "quantity": 3}]
    )

    assert sale.tax_applied is False
    assert sale.tax_amount == Decimal("0")
    assert sale.total_amount == sale.subtotal_amount == Decimal("13.50")


def test_record_sale_with_tax_applies_configured_rate(app, customer, product):
    company = Company.get_settings()
    company.tax_rate = Decimal("19.00")
    db.session.commit()

    sale = SalesService().record_sale(
        customer_id=customer.id,
        items=[{"product_id": product.id, "quantity": 3}],
        include_tax=True,
    )

    assert sale.tax_applied is True
    assert sale.tax_rate_applied == Decimal("19.00")
    assert sale.subtotal_amount == Decimal("13.50")
    assert sale.tax_amount == Decimal("2.56")
    assert sale.total_amount == Decimal("16.06")


def test_sales_by_product_returns_amount_and_percentage(app, customer, product):
    service = SalesService()
    sale = service.record_sale(
        customer_id=customer.id, items=[{"product_id": product.id, "quantity": 2}]
    )

    result = service.sales_by_product([sale])

    assert result == [
        {"product": product.display_name, "amount": 9.0, "percentage": 100.0}
    ]


def test_monthly_sales_counts_and_bottles_bucket_by_sale_month(app, customer, product):
    service = SalesService()
    sale_jan = service.record_sale(
        customer_id=customer.id,
        items=[{"product_id": product.id, "quantity": 1}],
        sale_date=datetime(2026, 1, 15, tzinfo=UTC),
    )
    sale_mar = service.record_sale(
        customer_id=customer.id,
        items=[{"product_id": product.id, "quantity": 4}],
        sale_date=datetime(2026, 3, 5, tzinfo=UTC),
    )

    counts = service.monthly_sales_counts([sale_jan, sale_mar])
    bottles = service.monthly_bottles_sold([sale_jan, sale_mar])

    assert counts == [1, 0, 1] + [0] * 9
    assert bottles == [1, 0, 4] + [0] * 9


def test_invoice_count_counts_only_sales_with_invoice_number(app, customer, product):
    service = SalesService()
    with_invoice = service.record_sale(
        customer_id=customer.id,
        items=[{"product_id": product.id, "quantity": 1}],
        invoice_number="F-001",
    )
    without_invoice = service.record_sale(
        customer_id=customer.id, items=[{"product_id": product.id, "quantity": 1}]
    )

    assert service.invoice_count([with_invoice, without_invoice]) == 1


def test_average_sale_total(app, customer, product):
    service = SalesService()
    sale1 = service.record_sale(
        customer_id=customer.id, items=[{"product_id": product.id, "quantity": 1}]
    )
    sale2 = service.record_sale(
        customer_id=customer.id, items=[{"product_id": product.id, "quantity": 3}]
    )

    assert service.average_sale_total([sale1, sale2]) == Decimal("9.00")


def test_average_sale_total_with_no_sales_returns_zero(app):
    assert SalesService().average_sale_total([]) == Decimal("0")
