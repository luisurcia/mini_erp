from datetime import date

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
