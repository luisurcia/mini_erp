from app.extensions import db
from app.models.product import Product
from app.repositories.product_repository import ProductRepository
from app.services.inventory_service import InventoryService


def test_total_stock_sums_across_warehouses(app, warehouse, fermentation_warehouse):
    p = Product(name="Kombucha", sku="K-1", size_ml=355, is_active=True)
    db.session.add(p)
    db.session.flush()
    InventoryService().create_inventory_item(p.id, warehouse.id, initial_qty=30)
    InventoryService().create_inventory_item(p.id, fermentation_warehouse.id, initial_qty=12)
    db.session.commit()

    assert p.total_stock == 42


def test_total_stock_is_zero_without_inventory_items(app):
    p = Product(name="Nuevo", sku="N-1", size_ml=355, is_active=True)
    db.session.add(p)
    db.session.commit()
    assert p.total_stock == 0


def test_get_active_excludes_inactive_products(app):
    db.session.add_all([
        Product(name="Activo", sku="A-1", size_ml=355, is_active=True),
        Product(name="Descontinuado", sku="D-1", size_ml=355, is_active=False),
    ])
    db.session.commit()

    names = [p.name for p in ProductRepository().get_active()]
    assert names == ["Activo"]
