from app.extensions import db
from app.models.base import BaseModel


class Flavor(BaseModel):
    __tablename__ = "flavors"

    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)

    products = db.relationship("Product", back_populates="flavor")

    def __repr__(self) -> str:
        return f"<Flavor {self.name}>"


class Product(BaseModel):
    __tablename__ = "products"

    # flavor_id / unit_price are nullable: a company can hide either field
    # from the product form (Company.product_flavor_enabled / _price_enabled).
    # See #37, #38.
    flavor_id = db.Column(db.Integer, db.ForeignKey("flavors.id"), nullable=True)
    name = db.Column(db.String(120), nullable=False)
    short_name = db.Column(db.String(3), nullable=True)
    sku = db.Column(db.String(40), unique=True, nullable=False)
    size_ml = db.Column(db.Integer, nullable=False, default=355)
    unit_price = db.Column(db.Numeric(10, 2), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    flavor = db.relationship("Flavor", back_populates="products")
    inventory_items = db.relationship(
        "InventoryItem", back_populates="product", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Product {self.name} ({self.sku})>"
