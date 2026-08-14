from app.extensions import db
from app.models.base import BaseModel


class InventoryItem(BaseModel):
    __tablename__ = "inventory_items"

    product_id = db.Column(
        db.Integer, db.ForeignKey("products.id"), unique=True, nullable=False
    )
    quantity_on_hand = db.Column(db.Integer, nullable=False, default=0)
    reorder_level = db.Column(db.Integer, nullable=False, default=10)

    product = db.relationship("Product", back_populates="inventory_item")

    @property
    def is_low_stock(self) -> bool:
        return self.quantity_on_hand <= self.reorder_level

    def __repr__(self) -> str:
        return f"<InventoryItem product_id={self.product_id} qty={self.quantity_on_hand}>"


class StockMovement(BaseModel):
    """Audit trail entry for every change to stock."""

    __tablename__ = "stock_movements"

    REASON_RESTOCK = "restock"
    REASON_SALE = "sale"
    REASON_ADJUSTMENT = "adjustment"

    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    change_qty = db.Column(db.Integer, nullable=False)  # positive or negative
    reason = db.Column(db.String(20), nullable=False)
    note = db.Column(db.String(255), nullable=True)

    product = db.relationship("Product")

    def __repr__(self) -> str:
        return f"<StockMovement product_id={self.product_id} change={self.change_qty} ({self.reason})>"
