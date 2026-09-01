from datetime import date, datetime

from app.models.customer import Customer
from app.reports import build_unpaid_sales_pdf
from app.services.sales_service import SalesService


def test_unpaid_sales_pdf_is_a_pdf_document(app, customer, product):
    sale = SalesService().record_sale(
        customer_id=customer.id,
        items=[{"product_id": product.id, "quantity": 2}],
    )
    pdf = build_unpaid_sales_pdf([sale], generated_on=date(2026, 9, 1))

    assert pdf[:5] == b"%PDF-"
    assert len(pdf) > 800


def test_unpaid_sales_pdf_handles_an_empty_list(app):
    pdf = build_unpaid_sales_pdf([], generated_on=date(2026, 9, 1))

    assert pdf[:5] == b"%PDF-"


def test_unpaid_sales_pdf_groups_several_sales_per_customer(app, customer, product):
    from app.extensions import db

    other = Customer(name="Other Co", segment_id=None)
    db.session.add(other)
    db.session.commit()

    service = SalesService()
    # `customer` gets two unpaid sales, `other` gets one — the grouped
    # layout + per-customer subtotal path must render without error.
    for day in (10, 3):
        service.record_sale(
            customer_id=customer.id,
            items=[{"product_id": product.id, "quantity": 1}],
            sale_date=datetime(2026, 8, day),
        )
    service.record_sale(
        customer_id=other.id,
        items=[{"product_id": product.id, "quantity": 1}],
        sale_date=datetime(2026, 8, 20),
    )
    sales = service.sales_repo.by_payment_status("unpaid")

    pdf = build_unpaid_sales_pdf(sales, generated_on=date(2026, 9, 1))

    assert pdf[:5] == b"%PDF-"
    assert len(pdf) > 1000
