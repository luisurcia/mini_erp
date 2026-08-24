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

    customer = db.relationship("Customer")
    items = db.relationship(
        "SaleItem", back_populates="sale", cascade="all, delete-orphan"
    )
    opportunity = db.relationship("Opportunity", back_populates="sale", uselist=False)

    def recalculate_total(self) -> None:
        self.total_amount = sum((item.subtotal for item in self.items), start=0)

    def __repr__(self) -> str:
        return f"<Sale #{self.id} customer_id={self.customer_id} total={self.total_amount}>"


class SaleItem(BaseModel):
    __tablename__ = "sale_items"

    sale_id = db.Column(db.Integer, db.ForeignKey("sales.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)

    sale = db.relationship("Sale", back_populates="items")
    product = db.relationship("Product")

    @property
    def subtotal(self):
        return self.unit_price * self.quantity

    def __repr__(self) -> str:
        return f"<SaleItem sale_id={self.sale_id} product_id={self.product_id} qty={self.quantity}>"
