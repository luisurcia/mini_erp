from app.extensions import db
from app.models.warehouse import Warehouse
from app.repositories.warehouse_repository import WarehouseRepository


def test_get_distribution_excludes_the_supplies_warehouse(app, warehouse, supplies_warehouse):
    names = [w.name for w in WarehouseRepository().get_distribution()]
    assert warehouse.name in names
    assert supplies_warehouse.name not in names


def test_get_supplies_warehouse_returns_the_one_supplies_warehouse(
    app, warehouse, supplies_warehouse
):
    assert WarehouseRepository().get_supplies_warehouse().id == supplies_warehouse.id


def test_get_default_is_a_distribution_warehouse(app, warehouse, supplies_warehouse):
    assert WarehouseRepository().get_default().kind == Warehouse.KIND_DISTRIBUTION


def test_ensure_supplies_warehouse_is_idempotent(app):
    first = Warehouse.ensure_supplies_warehouse()
    second = Warehouse.ensure_supplies_warehouse()
    assert first.id == second.id
    assert Warehouse.query.filter_by(kind=Warehouse.KIND_SUPPLIES).count() == 1
    db.session.rollback()
