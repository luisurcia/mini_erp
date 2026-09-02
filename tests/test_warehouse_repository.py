from app.extensions import db
from app.models.warehouse import Warehouse
from app.repositories.warehouse_repository import WarehouseRepository
from app.schema import ensure_warehouse_stage_column


def test_get_stock_locations_orders_fermentation_then_main_then_distribution(
    app, warehouse, fermentation_warehouse, distribution_warehouse, supplies_warehouse
):
    stages = [w.stage for w in WarehouseRepository().get_stock_locations()]

    assert stages == [
        Warehouse.STAGE_FERMENTATION,
        Warehouse.STAGE_MAIN,
        Warehouse.STAGE_DISTRIBUTION,
    ]


def test_get_sellable_excludes_fermentation_and_supplies(
    app, warehouse, fermentation_warehouse, distribution_warehouse, supplies_warehouse
):
    names = [w.name for w in WarehouseRepository().get_sellable()]

    assert warehouse.name in names
    assert distribution_warehouse.name in names
    assert fermentation_warehouse.name not in names
    assert supplies_warehouse.name not in names


def test_get_fermentation_and_get_main(app, warehouse, fermentation_warehouse):
    repo = WarehouseRepository()
    assert repo.get_fermentation().id == fermentation_warehouse.id
    assert repo.get_main().id == warehouse.id


def test_get_supplies_warehouse_returns_the_one_supplies_warehouse(
    app, warehouse, supplies_warehouse
):
    assert WarehouseRepository().get_supplies_warehouse().id == supplies_warehouse.id


def test_get_default_is_the_main_warehouse(app, warehouse, supplies_warehouse):
    assert WarehouseRepository().get_default().stage == Warehouse.STAGE_MAIN


def test_ensure_supplies_warehouse_is_idempotent(app):
    first = Warehouse.ensure_supplies_warehouse()
    second = Warehouse.ensure_supplies_warehouse()
    assert first.id == second.id
    assert Warehouse.query.filter_by(kind=Warehouse.KIND_SUPPLIES).count() == 1
    db.session.rollback()


def test_ensure_fermentation_warehouse_is_idempotent(app):
    first = Warehouse.ensure_fermentation_warehouse()
    second = Warehouse.ensure_fermentation_warehouse()
    assert first.id == second.id
    assert Warehouse.query.filter_by(stage=Warehouse.STAGE_FERMENTATION).count() == 1
    db.session.rollback()


def test_stage_migration_classifies_and_renames_existing_warehouses(app):
    # A database created before stages existed: no stages yet, and the team
    # already made a warehouse called "En Fermentación" by hand.
    db.session.add_all(
        [
            Warehouse(name="Bodega Principal", is_default=True),
            Warehouse(name="Bodega Norte"),
            Warehouse(name="En Fermentación"),
        ]
    )
    db.session.commit()

    ensure_warehouse_stage_column()

    principal = Warehouse.query.filter_by(name="Bodega Principal").one()
    norte = Warehouse.query.filter_by(name="Bodega Norte").one()
    ferm = Warehouse.query.filter_by(stage=Warehouse.STAGE_FERMENTATION).one()

    assert principal.stage == Warehouse.STAGE_MAIN
    assert norte.stage == Warehouse.STAGE_DISTRIBUTION
    assert ferm.name == "Bodega de Fermentación"
