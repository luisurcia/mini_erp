from app.extensions import db
from app.models.base import BaseModel


class Customer(BaseModel):
    __tablename__ = "customers"

    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(40), nullable=True)
    instagram_handle = db.Column(db.String(80), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Customer {self.name}>"
