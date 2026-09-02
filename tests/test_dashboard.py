from datetime import UTC, datetime

from app.blueprints.dashboard.routes import _pct_change, _period_stats
from app.services.sales_service import SalesService


def test_pct_change_basic():
    assert _pct_change(100, 125) == 25.0
    assert _pct_change(200, 150) == -25.0
    assert _pct_change(50, 50) == 0.0


def test_pct_change_from_zero_is_undefined():
    assert _pct_change(0, 10) is None
    assert _pct_change(0, 0) is None


def test_period_stats_are_computed_per_set_of_sales(app, customer, product):
    service = SalesService()
    # 2025: one taxed sale of 2 units.
    service.record_sale(
        customer_id=customer.id,
        items=[{"product_id": product.id, "quantity": 2}],
        sale_date=datetime(2025, 9, 10, tzinfo=UTC),
        include_tax=True,
    )
    # 2026: two sales, 3 + 1 units, untaxed.
    for qty in (3, 1):
        service.record_sale(
            customer_id=customer.id,
            items=[{"product_id": product.id, "quantity": qty}],
            sale_date=datetime(2026, 9, 10, tzinfo=UTC),
        )

    all_sales = SalesService().sales_repo.completed_all()
    y2025 = [s for s in all_sales if s.sale_date.year == 2025]
    y2026 = [s for s in all_sales if s.sale_date.year == 2026]

    s25 = _period_stats(service, y2025)
    s26 = _period_stats(service, y2026)

    assert s25["ticket_count"] == 1
    assert s25["total_bottles"] == 2
    assert s25["invoice_count"] == 1  # the taxed sale counts as a factura

    assert s26["ticket_count"] == 2
    assert s26["total_bottles"] == 4
    assert s26["invoice_count"] == 0
    assert s26["average_bottles_per_sale"] == 2  # 4 bottles / 2 sales
