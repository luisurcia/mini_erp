from datetime import datetime

from app.extensions import db
from app.models.customer import Customer
from app.models.sales import Sale
from app.repositories.sales_repository import SalesRepository
from app.services.sales_service import SalesService


def _sale(customer, product, year, month=6):
    return SalesService().record_sale(
        customer_id=customer.id,
        items=[{"product_id": product.id, "quantity": 1}],
        sale_date=datetime(year, month, 15),
    )


def _customer(name):
    c = Customer(name=name)
    db.session.add(c)
    db.session.commit()
    return c


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


def test_list_sales_combines_customer_and_payment_filters(app, customer, product):
    other = _customer("Other Co")
    paid = _sale(customer, product, 2026)
    _sale(customer, product, 2026, month=7)
    _sale(other, product, 2026)
    SalesService().register_payment(paid.id, "TRF-1")

    repo = SalesRepository()
    assert len(repo.list_sales()) == 3
    assert len(repo.list_sales(customer_id=customer.id)) == 2
    assert len(repo.list_sales(customer_id=other.id)) == 1
    assert len(repo.list_sales(payment_status=Sale.PAYMENT_UNPAID)) == 2
    assert (
        len(repo.list_sales(payment_status=Sale.PAYMENT_UNPAID, customer_id=customer.id))
        == 1
    )
    assert repo.list_sales(payment_status=Sale.PAYMENT_PAID, customer_id=other.id) == []


def test_customers_with_sales_lists_only_those_with_sales_by_name(app, customer, product):
    _customer("Zzz No Sales")  # no sales — excluded
    beta = _customer("Beta Store")
    _sale(customer, product, 2026)  # the `customer` fixture is "Test Customer"
    _sale(beta, product, 2026)
    _sale(beta, product, 2026, month=8)  # beta appears once, not twice

    names = [c.name for c in SalesRepository().customers_with_sales()]
    assert names == ["Beta Store", "Test Customer"]
