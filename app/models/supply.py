from app.extensions import db
from app.models.base import BaseModel


class Supply(BaseModel):
    """A production input (bottle, label, cap, ...) — distinct from
    Product, which is the finished good sold to customers. See #29."""

    __tablename__ = "supplies"

    name = db.Column(db.String(120), unique=True, nullable=False)
    unit = db.Column(db.String(40), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    supply_items = db.relationship(
        "SupplyItem", back_populates="supply", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Supply {self.name}>"


class SupplyItem(BaseModel):
    """Stock of one supply in one warehouse. Mirrors InventoryItem's
    (product, warehouse) pattern — one row per warehouse a supply has ever
    had stock in."""

    __tablename__ = "supply_items"
    __table_args__ = (
        db.UniqueConstraint(
            "supply_id", "warehouse_id", name="uq_supply_item_supply_warehouse"
        ),
    )

    supply_id = db.Column(db.Integer, db.ForeignKey("supplies.id"), nullable=False)
    warehouse_id = db.Column(db.Integer, db.ForeignKey("warehouses.id"), nullable=False)
    quantity_on_hand = db.Column(db.Integer, nullable=False, default=0)
    reorder_level = db.Column(db.Integer, nullable=False, default=10)

    supply = db.relationship("Supply", back_populates="supply_items")
    warehouse = db.relationship("Warehouse")

    @property
    def is_low_stock(self) -> bool:
        return self.quantity_on_hand <= self.reorder_level

    def __repr__(self) -> str:
        return (
            f"<SupplyItem supply_id={self.supply_id} "
            f"warehouse_id={self.warehouse_id} qty={self.quantity_on_hand}>"
        )


class SupplyMovement(BaseModel):
    """Audit trail entry for every change to supply stock: restock,
    manual adjustment, or automatic consumption when assembled bottles
    enter the fermentation warehouse and draw on a product's bill of
    materials (`assembly`, see #89 — this used to happen at sale time,
    `sale`, see #48). No 'transfer' reason — supplies live in a single
    warehouse."""

    __tablename__ = "supply_movements"

    REASON_RESTOCK = "restock"
    REASON_ADJUSTMENT = "adjustment"
    REASON_ASSEMBLY = "assembly"
    # Kept for historical rows only — supplies are no longer consumed at
    # sale time (#89).
    REASON_SALE = "sale"

    supply_id = db.Column(db.Integer, db.ForeignKey("supplies.id"), nullable=False)
    warehouse_id = db.Column(db.Integer, db.ForeignKey("warehouses.id"), nullable=True)
    # Legacy: pre-#89 consumption was linked to the sale that caused it.
    sale_id = db.Column(db.Integer, db.ForeignKey("sales.id"), nullable=True)
    change_qty = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(20), nullable=False)
    note = db.Column(db.String(255), nullable=True)

    supply = db.relationship("Supply")
    warehouse = db.relationship("Warehouse")
    sale = db.relationship("Sale")

    def __repr__(self) -> str:
        return (
            f"<SupplyMovement supply_id={self.supply_id} "
            f"change={self.change_qty} ({self.reason})>"
        )
