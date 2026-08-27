from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.display import product_label
from app.exceptions import InsufficientStockError, MiniErpError
from app.extensions import db
from app.models.company import Company
from app.models.customer import Customer
from app.repositories.sales_repository import SalesRepository
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


def test_record_sale_without_line_or_catalog_price_raises(app, customer, product):
    """When the product has no catalog price (#38) the sale line must
    carry one; otherwise the sale is rejected, not saved with a null."""
    product.unit_price = None
    db.session.commit()

    service = SalesService()
    with pytest.raises(MiniErpError):
        service.record_sale(
            customer_id=customer.id,
            items=[{"product_id": product.id, "quantity": 2}],
        )

    assert len(SalesRepository().get_all()) == 0


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
    company.currency_decimals = 2  # cents currency: tax rounds to 2 places
    db.session.commit()

    sale = SalesService().record_sale(
        customer_id=customer.id,
        items=[{"product_id": product.id, "quantity": 3}],
        include_tax=True,
    )

    assert sale.tax_applied is True
    assert sale.tax_rate_applied == Decimal("19.00")
    assert sale.subtotal_amount == Decimal("13.50")
    # 13.50 * 19% = 2.565 -> 2.57 (round half up)
    assert sale.tax_amount == Decimal("2.57")
    assert sale.total_amount == Decimal("16.07")


def test_record_sale_tax_rounds_to_currency_decimals(app, customer, product):
    """With a 0-decimal currency (CLP, the default), tax is rounded to a
    whole unit of currency rather than to cents. See #39."""
    company = Company.get_settings()
    company.tax_rate = Decimal("19.00")
    assert company.currency_decimals == 0
    db.session.commit()

    sale = SalesService().record_sale(
        customer_id=customer.id,
        items=[{"product_id": product.id, "quantity": 3}],
        include_tax=True,
    )

    # 13.50 * 19% = 2.565 -> 3 (rounded to 0 decimals)
    assert sale.tax_amount == Decimal("3")
    assert sale.total_amount == Decimal("16.50")


def test_sales_by_product_returns_amount_and_percentage(app, customer, product):
    service = SalesService()
    sale = service.record_sale(
        customer_id=customer.id, items=[{"product_id": product.id, "quantity": 2}]
    )

    result = service.sales_by_product([sale])

    assert result == [
        {"product": product_label(product), "amount": 9.0, "percentage": 100.0}
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


def test_average_bottles_per_sale(app, customer, product):
    service = SalesService()
    sale1 = service.record_sale(
        customer_id=customer.id, items=[{"product_id": product.id, "quantity": 1}]
    )
    sale2 = service.record_sale(
        customer_id=customer.id, items=[{"product_id": product.id, "quantity": 3}]
    )

    assert service.average_bottles_per_sale([sale1, sale2]) == Decimal("2")


def test_average_bottles_per_sale_with_no_sales_returns_zero(app):
    assert SalesService().average_bottles_per_sale([]) == Decimal("0")


def test_top_customers_by_consumption_ranks_by_total_amount(app, customer, product):
    other = Customer(name="Other Customer", email="other@example.com")
    db.session.add(other)
    db.session.commit()

    service = SalesService()
    small_sale = service.record_sale(
        customer_id=customer.id, items=[{"product_id": product.id, "quantity": 1}]
    )
    big_sale_1 = service.record_sale(
        customer_id=other.id, items=[{"product_id": product.id, "quantity": 3}]
    )
    big_sale_2 = service.record_sale(
        customer_id=other.id, items=[{"product_id": product.id, "quantity": 2}]
    )

    ranked = service.top_customers_by_consumption([small_sale, big_sale_1, big_sale_2])

    assert [entry["customer"].id for entry in ranked] == [other.id, customer.id]
    assert ranked[0]["total_amount"] == big_sale_1.total_amount + big_sale_2.total_amount
    assert ranked[0]["total_units"] == 5
    assert ranked[0]["sale_count"] == 2


def test_top_customers_by_consumption_respects_limit(app, customer, product):
    customers = [customer]
    for i in range(2):
        c = Customer(name=f"Customer {i}", email=f"c{i}@example.com")
        db.session.add(c)
        customers.append(c)
    db.session.commit()

    service = SalesService()
    sales = [
        service.record_sale(customer_id=c.id, items=[{"product_id": product.id, "quantity": 1}])
        for c in customers
    ]

    assert len(service.top_customers_by_consumption(sales, limit=1)) == 1
