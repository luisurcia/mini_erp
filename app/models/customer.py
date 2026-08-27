from app.extensions import db
from app.models.base import BaseModel


class Customer(BaseModel):
    __tablename__ = "customers"

    name = db.Column(db.String(120), nullable=False)
    rut = db.Column(db.String(20), unique=True, nullable=True)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(40), nullable=True)
    shipping_address = db.Column(db.Text, nullable=True)
    segment_id = db.Column(db.Integer, db.ForeignKey("customer_segments.id"), nullable=True)
    instagram_handle = db.Column(db.String(80), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    segment = db.relationship("CustomerSegment")

    def __repr__(self) -> str:
        return f"<Customer {self.name}>"
