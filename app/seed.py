from datetime import UTC, datetime, timedelta

from flask import Flask

from app.extensions import db
from app.models.customer import Customer
from app.models.customer_segment import CustomerSegment
from app.models.product import Flavor, Product
from app.models.product_supply import ProductSupply
from app.models.supply import Supply
from app.models.user import User
from app.models.warehouse import Warehouse
from app.services.inventory_service import InventoryService
from app.services.sales_service import SalesService
from app.services.supply_service import SupplyService

FLAVORS = [
    ("Original", "Classic lightly-sweet kombucha, the everyday favorite."),
    ("Ginger Lemon", "Zesty ginger and lemon, a bright and spicy kick."),
    ("Hibiscus Rose", "Floral hibiscus with a hint of rose, tart and fragrant."),
    ("Mixed Berry", "Strawberry, raspberry and blueberry blend."),
    ("Mango Turmeric", "Tropical mango with anti-inflammatory turmeric."),
]

PRICE_BY_FLAVOR = {
    "Original": 4.50,
    "Ginger Lemon": 4.95,
    "Hibiscus Rose": 5.25,
    "Mixed Berry": 5.25,
    "Mango Turmeric": 5.50,
}


def seed_demo_data(app: Flask) -> None:
    _seed_admin(app)
    if Flavor.query.count() > 0:
        return  # already seeded

    products = _seed_flavors_and_products()
    supplies = _seed_supplies()
    _seed_recipes(products, supplies)
    customers = _seed_customers()
    _seed_sales(customers, products)


def _seed_admin(app: Flask) -> None:
    if User.query.filter_by(username=app.config["ADMIN_USERNAME"]).first():
        return
    admin = User(username=app.config["ADMIN_USERNAME"])
    admin.set_password(app.config["ADMIN_PASSWORD"])
    db.session.add(admin)
    db.session.commit()


def _seed_flavors_and_products() -> dict[str, Product]:
    inventory_service = InventoryService()
    # Demo stock: some fermenting, most already moved to Principal and
    # ready to sell. Julien / Mario start empty (they fill by transfer).
    main_warehouse_id = Warehouse.query.filter_by(is_default=True).first().id
    fermentation_warehouse_id = Warehouse.ensure_fermentation_warehouse().id
    products: dict[str, Product] = {}

    for name, description in FLAVORS:
        flavor = Flavor(name=name, description=description)
        db.session.add(flavor)
        db.session.flush()

        product = Product(
            flavor_id=flavor.id,
            name="Kombucha",
            sku=f"KOMB-{name[:3].upper()}-355",
            size_ml=355,
            unit_price=PRICE_BY_FLAVOR[name],
            is_active=True,
        )
        db.session.add(product)
        db.session.flush()
        products[name] = product

        inventory_service.create_inventory_item(
            product.id, main_warehouse_id, initial_qty=100, reorder_level=20
        )
        inventory_service.create_inventory_item(
            product.id, fermentation_warehouse_id, initial_qty=40, reorder_level=0
        )

    db.session.commit()
    return products


SUPPLIES = [
    ("Botellas 355ml", "unidad", 0.35, 1000),
    ("Etiquetas", "unidad", 0.08, 1500),
    ("Tapas", "unidad", 0.05, 1200),
]


def _seed_supplies() -> dict[str, Supply]:
    supply_service = SupplyService()
    supplies_warehouse_id = Warehouse.ensure_supplies_warehouse().id
    supplies: dict[str, Supply] = {}

    for name, unit, unit_price, initial_qty in SUPPLIES:
        supply = Supply(name=name, unit=unit, unit_price=unit_price, is_active=True)
        db.session.add(supply)
        db.session.flush()
        supplies[name] = supply

        supply_service.create_supply_item(
            supply.id, supplies_warehouse_id, initial_qty=initial_qty, reorder_level=200
        )
    return supplies


def _seed_recipes(products: dict[str, Product], supplies: dict[str, Supply]) -> None:
    """Every demo kombucha consumes 1 bottle + 1 label + 1 cap per unit (#48)."""
    for product in products.values():
        for supply_name in ("Botellas 355ml", "Etiquetas", "Tapas"):
            db.session.add(
                ProductSupply(
                    product_id=product.id,
                    supply_id=supplies[supply_name].id,
                    quantity_per_unit=1,
                )
            )
    db.session.commit()

    db.session.commit()


def _seed_customers() -> dict[str, Customer]:
    segments_by_name = {segment.name: segment for segment in CustomerSegment.query.all()}

    def segment_id(name: str) -> int | None:
        segment = segments_by_name.get(name)
        return segment.id if segment else None

    customers = {
        "green_leaf": Customer(
            name="Green Leaf Cafe",
            nickname="El Verde",
            rut="76.123.456-7",
            email="orders@greenleafcafe.example",
            phone="+1-555-0101",
            shipping_street="Av. Providencia",
            shipping_number="1234",
            shipping_commune="Providencia",
            shipping_city="Santiago",
            shipping_region="Metropolitana",
            segment_id=segment_id("Comercio"),
            notes="Local cafe, orders wholesale monthly.",
        ),
        "maria": Customer(
            name="Maria Torres",
            rut="12.345.678-9",
            email="maria.torres@example.com",
            shipping_street="Los Aromos",
            shipping_number="456",
            shipping_commune="Ñuñoa",
            shipping_city="Santiago",
            shipping_region="Metropolitana",
            segment_id=segment_id("Persona natural"),
            instagram_handle="maria.wellness",
            notes="Found us through Instagram, buys for personal use and small events.",
        ),
        "fresh_market": Customer(
            name="Fresh Market Co-op",
            rut="77.987.654-3",
            email="buyers@freshmarket.example",
            phone="+1-555-0199",
            shipping_street="Camino La Dehesa",
            shipping_number="890",
            shipping_commune="Lo Barnechea",
            shipping_city="Santiago",
            shipping_region="Metropolitana",
            segment_id=segment_id("Distribuidor"),
            notes="Interested in a recurring wholesale order.",
        ),
    }
    db.session.add_all(customers.values())
    db.session.commit()
    return customers


def _seed_sales(customers: dict[str, Customer], products: dict[str, Product]) -> None:
    sales_service = SalesService()
    now = datetime.now(UTC)

    paid_sale = sales_service.record_sale(
        customer_id=customers["green_leaf"].id,
        items=[
            {"product_id": products["Original"].id, "quantity": 20},
            {"product_id": products["Mango Turmeric"].id, "quantity": 10},
        ],
        sale_date=now - timedelta(days=6),
        notes="Monthly wholesale restock.",
    )
    sales_service.register_payment(
        paid_sale.id, "TRF-20260101-0042", paid_at=now - timedelta(days=4)
    )

    sales_service.record_sale(
        customer_id=customers["maria"].id,
        items=[{"product_id": products["Ginger Lemon"].id, "quantity": 6}],
        sale_date=now - timedelta(days=2),
        notes="Personal order via Instagram DM.",
    )

    sales_service.record_sale(
        customer_id=customers["fresh_market"].id,
        items=[{"product_id": products["Mixed Berry"].id, "quantity": 36}],
        sale_date=now - timedelta(days=45),
        notes="First trial order before committing to a recurring contract.",
    )
