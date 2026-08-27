from app.extensions import db
from app.models.base import BaseModel


class CustomerSegment(BaseModel):
    """Small, admin-editable catalog used to classify customers.

    Kept as a simple lookup table (not a full CRUD module with its own
    permissions/screen) since it's a handful of values that rarely change
    — managed from Company settings instead. See mini_erp#21.
    """

    __tablename__ = "customer_segments"

    DEFAULTS = ["Persona natural", "Comercio", "Distribuidor", "Otros"]

    name = db.Column(db.String(60), unique=True, nullable=False)

    @classmethod
    def ensure_defaults(cls) -> None:
        if cls.query.count() > 0:
            return
        db.session.add_all(cls(name=name) for name in cls.DEFAULTS)
        db.session.commit()

    def __repr__(self) -> str:
        return f"<CustomerSegment {self.name}>"
