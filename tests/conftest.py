import pytest

from app import create_app
from app.extensions import db
from app.models.customer import Customer
from app.models.product import Flavor, Product
from app.models.warehouse import Warehouse
from app.services.inventory_service import InventoryService
from config import TestConfig


@pytest.fixture()
def app():
    application = create_app(TestConfig)
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def customer(app):
    c = Customer(name="Test Customer", email="test@example.com")
    db.session.add(c)
    db.session.commit()
    return c


@pytest.fixture()
def warehouse(app):
    w = Warehouse(name="Main Warehouse", is_active=True, is_default=True)
    db.session.add(w)
    db.session.commit()
    return w


@pytest.fixture()
def product(app, warehouse):
    flavor = Flavor(name="Original", description="Classic")
    db.session.add(flavor)
    db.session.flush()

    p = Product(
        flavor_id=flavor.id,
        name="Kombucha",
        sku="KOMB-ORI-355",
        size_ml=355,
        unit_price=4.50,
        is_active=True,
    )
    db.session.add(p)
    db.session.flush()

    InventoryService().create_inventory_item(p.id, warehouse.id, initial_qty=50, reorder_level=10)
    db.session.commit()
    return p
