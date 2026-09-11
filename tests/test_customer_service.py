import pytest

from app.exceptions import MiniErpError, NotFoundError
from app.extensions import db
from app.models.customer import Customer
from app.models.sales import Sale
from app.services.customer_service import CustomerService
from app.services.sales_service import SalesService


@pytest.fixture()
def other_customer(app):
    c = Customer(name="Celso Gonzales")
    db.session.add(c)
    db.session.commit()
    return c


def test_merge_reassigns_sales_and_deletes_discarded_customer(
    app, customer, other_customer, product
):
    sales_service = SalesService()
    sale = sales_service.record_sale(
        customer_id=other_customer.id, items=[{"product_id": product.id, "quantity": 1}]
    )

    result = CustomerService().merge(discard_id=other_customer.id, canonical_id=customer.id)

    assert result["reassigned_sales"] == 1
    assert result["discarded_name"] == "Celso Gonzales"
    assert db.session.get(Sale, sale.id).customer_id == customer.id
    assert db.session.get(Customer, other_customer.id) is None


def test_merge_keeps_the_discarded_name_as_a_note_on_the_canonical(app, customer, other_customer):
    CustomerService().merge(discard_id=other_customer.id, canonical_id=customer.id)

    assert "Celso Gonzales" in db.session.get(Customer, customer.id).notes


def test_merge_appends_to_existing_notes_instead_of_overwriting(app, customer, other_customer):
    customer.notes = "Cliente frecuente."
    db.session.commit()

    CustomerService().merge(discard_id=other_customer.id, canonical_id=customer.id)

    notes = db.session.get(Customer, customer.id).notes
    assert "Cliente frecuente." in notes
    assert "Celso Gonzales" in notes


def test_merge_into_self_raises(app, customer):
    with pytest.raises(MiniErpError):
        CustomerService().merge(discard_id=customer.id, canonical_id=customer.id)


def test_merge_with_unknown_customer_raises_not_found(app, customer):
    with pytest.raises(NotFoundError):
        CustomerService().merge(discard_id=999, canonical_id=customer.id)
    with pytest.raises(NotFoundError):
        CustomerService().merge(discard_id=customer.id, canonical_id=999)
