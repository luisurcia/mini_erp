from datetime import date, datetime

from app.extensions import db
from app.models.customer import Customer
from app.models.product import Product
from app.reports import (
    build_dispatch_ticket_pdf,
    build_unpaid_sales_pdf,
    dispatch_line_items,
)
from app.services.inventory_service import InventoryService
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


def test_dispatch_ticket_is_a_pdf_with_the_line_items(app, warehouse, customer, product):
    other = Product(
        flavor_id=product.flavor_id, name="Ginger", sku="GIN-1", size_ml=355,
        unit_price=5, is_active=True,
    )
    db.session.add(other)
    db.session.flush()
    InventoryService().create_inventory_item(
        other.id, warehouse.id, initial_qty=50, reorder_level=0
    )
    db.session.commit()

    customer.phone = "+56 9 1234 5678"
    customer.shipping_street = "Av. Siempre Viva"
    customer.shipping_number = "742"
    customer.shipping_commune = "Providencia"
    db.session.commit()

    sale = SalesService().record_sale(
        customer_id=customer.id,
        items=[
            {"product_id": product.id, "quantity": 3},
            {"product_id": other.id, "quantity": 2},
        ],
    )
    pdf = build_dispatch_ticket_pdf(sale, generated_on=date(2026, 9, 9))

    assert pdf[:5] == b"%PDF-"
    assert len(pdf) > 800
    assert sum(i.quantity for i in sale.items) == 5


def test_dispatch_ticket_handles_a_customer_with_no_contact_details(app, customer, product):
    customer.rut = customer.email = customer.phone = None
    db.session.commit()
    sale = SalesService().record_sale(
        customer_id=customer.id,
        items=[{"product_id": product.id, "quantity": 1}],
    )
    assert customer.shipping_address_line is None

    pdf = build_dispatch_ticket_pdf(sale)
    assert pdf[:5] == b"%PDF-"


def test_dispatch_ticket_sums_one_product_drawn_from_several_warehouses(
    app, warehouse, distribution_warehouse, customer, product
):
    InventoryService().create_inventory_item(
        product.id, distribution_warehouse.id, initial_qty=50, reorder_level=0
    )
    db.session.commit()

    sale = SalesService().record_sale(
        customer_id=customer.id,
        items=[
            {"product_id": product.id, "quantity": 3, "warehouse_id": warehouse.id},
            {
                "product_id": product.id,
                "quantity": 2,
                "warehouse_id": distribution_warehouse.id,
            },
        ],
    )
    # Two SaleItem rows (one per warehouse), but one product on the ticket.
    assert len(sale.items) == 2
    assert dispatch_line_items(sale) == [(5, "Original - Kombucha (355ml)")]

    pdf = build_dispatch_ticket_pdf(sale)
    assert pdf[:5] == b"%PDF-"


def test_dispatch_line_items_are_ordered_by_product_label(app, warehouse, customer, product):
    zephyr = Product(
        flavor_id=product.flavor_id, name="Zephyr", sku="ZPH-1", size_ml=355,
        unit_price=5, is_active=True,
    )
    db.session.add(zephyr)
    db.session.flush()
    InventoryService().create_inventory_item(
        zephyr.id, warehouse.id, initial_qty=50, reorder_level=0
    )
    db.session.commit()

    sale = SalesService().record_sale(
        customer_id=customer.id,
        items=[
            {"product_id": zephyr.id, "quantity": 1},
            {"product_id": product.id, "quantity": 4},
        ],
    )
    labels = [label for _q, label in dispatch_line_items(sale)]
    assert labels == sorted(labels, key=str.lower)
