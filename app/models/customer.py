from app.extensions import db
from app.models.base import BaseModel


class Customer(BaseModel):
    __tablename__ = "customers"

    name = db.Column(db.String(120), nullable=False)
    nickname = db.Column(db.String(80), nullable=True)
    rut = db.Column(db.String(20), unique=True, nullable=True)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(40), nullable=True)
    # Structured shipping address (#42) — replaced the old free-text
    # `shipping_address` column.
    shipping_street = db.Column(db.String(120), nullable=True)
    shipping_number = db.Column(db.String(20), nullable=True)
    shipping_city = db.Column(db.String(80), nullable=True)
    shipping_commune = db.Column(db.String(80), nullable=True)
    shipping_region = db.Column(db.String(80), nullable=True)
    segment_id = db.Column(db.Integer, db.ForeignKey("customer_segments.id"), nullable=True)
    instagram_handle = db.Column(db.String(80), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    segment = db.relationship("CustomerSegment")

    @property
    def shipping_address_line(self) -> str | None:
        """The structured address parts joined into one line for display,
        or None when nothing is filled in."""
        street = " ".join(p for p in (self.shipping_street, self.shipping_number) if p)
        parts = [street, self.shipping_commune, self.shipping_city, self.shipping_region]
        line = ", ".join(p for p in parts if p)
        return line or None

    def __repr__(self) -> str:
        return f"<Customer {self.name}>"
