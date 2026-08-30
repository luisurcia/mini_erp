from app.extensions import db
from app.models.base import BaseModel


class ProductSupply(BaseModel):
    """One line of a product's bill of materials: how many units of a
    supply are consumed per unit of that product sold. A product with no
    rows consumes nothing. See #48."""

    __tablename__ = "product_supplies"
    __table_args__ = (
        db.UniqueConstraint("product_id", "supply_id", name="uq_product_supply"),
    )

    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    supply_id = db.Column(db.Integer, db.ForeignKey("supplies.id"), nullable=False)
    quantity_per_unit = db.Column(db.Integer, nullable=False, default=1)

    product = db.relationship("Product", back_populates="supply_recipe")
    supply = db.relationship("Supply")

    def __repr__(self) -> str:
        return (
            f"<ProductSupply product_id={self.product_id} "
            f"supply_id={self.supply_id} x{self.quantity_per_unit}>"
        )
