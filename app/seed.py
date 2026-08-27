from datetime import UTC, datetime, timedelta

from flask import Flask

from app.extensions import db
from app.models.customer import Customer
from app.models.customer_segment import CustomerSegment
from app.models.opportunity import Opportunity
from app.models.product import Flavor, Product
from app.models.user import User
from app.services.inventory_service import InventoryService
from app.services.opportunity_service import OpportunityService
from app.services.sales_service import SalesService

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
    customers = _seed_customers()
    _seed_opportunities(customers, products)
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

        inventory_service.create_inventory_item(product.id, initial_qty=100, reorder_level=20)

    db.session.commit()
    return products


def _seed_customers() -> dict[str, Customer]:
    segments_by_name = {segment.name: segment for segment in CustomerSegment.query.all()}

    def segment_id(name: str) -> int | None:
        segment = segments_by_name.get(name)
        return segment.id if segment else None

    customers = {
        "green_leaf": Customer(
            name="Green Leaf Cafe",
            rut="76.123.456-7",
            email="orders@greenleafcafe.example",
            phone="+1-555-0101",
            shipping_address="Av. Providencia 1234, Providencia, Santiago",
            segment_id=segment_id("Comercio"),
            notes="Local cafe, orders wholesale monthly.",
        ),
        "maria": Customer(
            name="Maria Torres",
            rut="12.345.678-9",
            email="maria.torres@example.com",
            shipping_address="Los Aromos 456, Depto 12B, Ñuñoa, Santiago",
            segment_id=segment_id("Persona natural"),
            instagram_handle="maria.wellness",
            notes="Found us through Instagram, buys for personal use and small events.",
        ),
        "fresh_market": Customer(
            name="Fresh Market Co-op",
            rut="77.987.654-3",
            email="buyers@freshmarket.example",
            phone="+1-555-0199",
            shipping_address="Camino La Dehesa 890, Bodega 3, Lo Barnechea, Santiago",
            segment_id=segment_id("Distribuidor"),
            notes="Interested in a recurring wholesale order.",
        ),
    }
    db.session.add_all(customers.values())
    db.session.commit()
    return customers


def _seed_opportunities(customers: dict[str, Customer], products: dict[str, Product]) -> None:
    opportunity_service = OpportunityService()
    opportunity_service.create(
        customer_id=customers["maria"].id,
        product_id=products["Ginger Lemon"].id,
        quantity_requested=12,
        source=Opportunity.SOURCE_INSTAGRAM,
        notes="DM'd asking about pricing for a birthday event.",
    )
    opp2 = opportunity_service.create(
        customer_id=customers["green_leaf"].id,
        product_id=products["Hibiscus Rose"].id,
        quantity_requested=24,
        source=Opportunity.SOURCE_WEBSITE,
        notes="Wants a quote for a monthly wholesale order.",
    )
    opportunity_service.update_stage(opp2.id, Opportunity.STAGE_QUOTED)

    opp3 = opportunity_service.create(
        customer_id=customers["fresh_market"].id,
        product_id=products["Mixed Berry"].id,
        quantity_requested=48,
        source=Opportunity.SOURCE_REFERRAL,
        notes="Referred by Green Leaf Cafe, evaluating suppliers.",
    )
    opportunity_service.update_stage(opp3.id, Opportunity.STAGE_CONTACTED)


def _seed_sales(customers: dict[str, Customer], products: dict[str, Product]) -> None:
    sales_service = SalesService()
    now = datetime.now(UTC)

    sales_service.record_sale(
        customer_id=customers["green_leaf"].id,
        items=[
            {"product_id": products["Original"].id, "quantity": 20},
            {"product_id": products["Mango Turmeric"].id, "quantity": 10},
        ],
        sale_date=now - timedelta(days=6),
        notes="Monthly wholesale restock.",
    )

    sales_service.record_sale(
        customer_id=customers["maria"].id,
        items=[{"product_id": products["Ginger Lemon"].id, "quantity": 6}],
        sale_date=now - timedelta(days=2),
        notes="Personal order via Instagram DM.",
    )
