from datetime import date
from decimal import Decimal

from app.extensions import db
from app.maintenance import reset_data
from app.models.company import Company
from app.models.customer import Customer
from app.models.customer_segment import CustomerSegment
from app.models.product import Flavor, Product
from app.models.purchase import Purchase
from app.models.purchase_category import PurchaseCategory
from app.models.sales import Sale, SaleItem
from app.models.user import User
from app.models.warehouse import Warehouse
from app.services.purchase_service import PurchaseService
from app.services.sales_service import SalesService


def _seed_some_data(customer, product):
    user = User(username="operator")
    user.set_password("secret123")
    db.session.add(user)
    Company.get_settings().name = "Scoby Kombucha"
    SalesService().record_sale(
        customer_id=customer.id,
        items=[{"product_id": product.id, "quantity": 2}],
    )
    PurchaseService().record_purchase(
        purchase_date=date(2026, 9, 1),
        item="Alcohol gel",
        supplier="Proveedor X",
        amount=Decimal("10000"),
    )
    db.session.commit()


def test_reset_data_wipes_operational_records(app, customer, product):
    _seed_some_data(customer, product)
    assert Sale.query.count() == 1
    assert Purchase.query.count() == 1

    reset_data()

    assert Customer.query.count() == 0
    assert Sale.query.count() == 0
    assert SaleItem.query.count() == 0
    assert Product.query.count() == 0
    assert Flavor.query.count() == 0
    assert Purchase.query.count() == 0


def test_reset_data_keeps_users_and_company_settings(app, customer, product):
    _seed_some_data(customer, product)

    reset_data()

    assert User.query.count() == 1
    assert User.query.first().username == "operator"
    assert Company.query.count() == 1
    assert Company.get_settings().name == "Scoby Kombucha"


def test_reset_data_recreates_the_baseline_catalogs(app, customer, product):
    _seed_some_data(customer, product)

    reset_data()

    assert Warehouse.query.count() > 0
    assert {s.name for s in CustomerSegment.query} == set(CustomerSegment.DEFAULTS)
    assert {c.name for c in PurchaseCategory.query} == set(PurchaseCategory.DEFAULTS)


def test_reset_data_is_idempotent(app):
    reset_data()
    wh_after_first = Warehouse.query.count()

    reset_data()

    # Second run only clears + rebuilds the baseline catalogs; the end
    # state matches the first run.
    assert Warehouse.query.count() == wh_after_first
    assert CustomerSegment.query.count() == len(CustomerSegment.DEFAULTS)
    assert PurchaseCategory.query.count() == len(PurchaseCategory.DEFAULTS)
