from app.extensions import db
from app.models.base import BaseModel


class InventoryItem(BaseModel):
    """Stock of one product in one warehouse. Unique per (product,
    warehouse) pair — a product has one row per warehouse it has ever
    had stock in, not one row total. See #25.
    """

    __tablename__ = "inventory_items"
    __table_args__ = (
        db.UniqueConstraint(
            "product_id", "warehouse_id", name="uq_inventory_item_product_warehouse"
        ),
    )

    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    warehouse_id = db.Column(db.Integer, db.ForeignKey("warehouses.id"), nullable=False)
    quantity_on_hand = db.Column(db.Integer, nullable=False, default=0)
    reorder_level = db.Column(db.Integer, nullable=False, default=10)

    product = db.relationship("Product", back_populates="inventory_items")
    warehouse = db.relationship("Warehouse")

    @property
    def is_low_stock(self) -> bool:
        return self.quantity_on_hand <= self.reorder_level

    def __repr__(self) -> str:
        return (
            f"<InventoryItem product_id={self.product_id} "
            f"warehouse_id={self.warehouse_id} qty={self.quantity_on_hand}>"
        )


class StockMovement(BaseModel):
    """Audit trail entry for every change to stock."""

    __tablename__ = "stock_movements"

    REASON_RESTOCK = "restock"
    REASON_SALE = "sale"
    REASON_ADJUSTMENT = "adjustment"
    REASON_TRANSFER = "transfer"

    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    # Nullable: movements recorded before warehouses existed have no
    # warehouse on file and are left as-is rather than backfilled.
    warehouse_id = db.Column(db.Integer, db.ForeignKey("warehouses.id"), nullable=True)
    change_qty = db.Column(db.Integer, nullable=False)  # positive or negative
    reason = db.Column(db.String(20), nullable=False)
    note = db.Column(db.String(255), nullable=True)

    product = db.relationship("Product")
    warehouse = db.relationship("Warehouse")

    def __repr__(self) -> str:
        return (
            f"<StockMovement product_id={self.product_id} "
            f"change={self.change_qty} ({self.reason})>"
        )
