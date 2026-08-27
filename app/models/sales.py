from decimal import ROUND_HALF_UP, Decimal

from app.extensions import db
from app.models.base import BaseModel


class Sale(BaseModel):
    __tablename__ = "sales"

    STATUS_PENDING = "pending"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"

    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    status = db.Column(db.String(20), nullable=False, default=STATUS_COMPLETED)
    sale_date = db.Column(db.DateTime, nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    invoice_number = db.Column(db.String(40), nullable=True)
    notes = db.Column(db.String(255), nullable=True)
    tax_applied = db.Column(db.Boolean, nullable=False, default=False)
    tax_rate_applied = db.Column(db.Numeric(5, 2), nullable=True)
    tax_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    customer = db.relationship("Customer")
    items = db.relationship(
        "SaleItem", back_populates="sale", cascade="all, delete-orphan"
    )

    @property
    def subtotal_amount(self):
        return sum((item.subtotal for item in self.items), start=Decimal("0"))

    def recalculate_total(self) -> None:
        from app.models.company import Company

        quantum = Company.get_settings().money_quantum
        subtotal = self.subtotal_amount
        if self.tax_applied and self.tax_rate_applied is not None:
            self.tax_amount = (subtotal * self.tax_rate_applied / Decimal("100")).quantize(
                quantum, rounding=ROUND_HALF_UP
            )
        else:
            self.tax_amount = Decimal("0")
        self.total_amount = subtotal + self.tax_amount

    def __repr__(self) -> str:
        return f"<Sale #{self.id} customer_id={self.customer_id} total={self.total_amount}>"


class SaleItem(BaseModel):
    __tablename__ = "sale_items"

    sale_id = db.Column(db.Integer, db.ForeignKey("sales.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    # Nullable: which warehouse a line was drawn from wasn't tracked before
    # Sales became warehouse-aware (#24) — historical lines have none.
    warehouse_id = db.Column(db.Integer, db.ForeignKey("warehouses.id"), nullable=True)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)

    sale = db.relationship("Sale", back_populates="items")
    product = db.relationship("Product")
    warehouse = db.relationship("Warehouse")

    @property
    def subtotal(self):
        return self.unit_price * self.quantity

    def __repr__(self) -> str:
        return f"<SaleItem sale_id={self.sale_id} product_id={self.product_id} qty={self.quantity}>"
