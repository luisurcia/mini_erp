from datetime import datetime

from app.repositories.sales_repository import SalesRepository
from app.services.sales_service import SalesService


def _sale(customer, product, year, month=6):
    return SalesService().record_sale(
        customer_id=customer.id,
        items=[{"product_id": product.id, "quantity": 1}],
        sale_date=datetime(year, month, 15),
    )


def test_completed_in_years_filters_to_the_given_years(app, customer, product):
    _sale(customer, product, 2024)
    _sale(customer, product, 2025)
    _sale(customer, product, 2026)

    repo = SalesRepository()
    years = lambda sales: sorted({s.sale_date.year for s in sales})  # noqa: E731

    assert years(repo.completed_in_years([2024, 2026])) == [2024, 2026]
    assert years(repo.completed_in_years([2025])) == [2025]


def test_completed_in_years_with_an_empty_list_returns_every_year(app, customer, product):
    _sale(customer, product, 2024)
    _sale(customer, product, 2026)

    assert len(SalesRepository().completed_in_years([])) == 2


def test_completed_in_years_ignores_years_with_no_sales(app, customer, product):
    _sale(customer, product, 2025)

    assert SalesRepository().completed_in_years([2023, 2099]) == []
