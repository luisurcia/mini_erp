from decimal import Decimal

from app.extensions import db
from app.models.base import BaseModel


class Company(BaseModel):
    """Single-row company configuration (tax settings, etc.)."""

    __tablename__ = "company_settings"

    tax_rate = db.Column(db.Numeric(5, 2), nullable=False, default=Decimal("19.00"))
    tax_enabled_default = db.Column(db.Boolean, nullable=False, default=True)

    @classmethod
    def get_settings(cls) -> "Company":
        settings = cls.query.first()
        if settings is None:
            settings = cls()
            db.session.add(settings)
            db.session.commit()
        return settings

    def __repr__(self) -> str:
        return f"<Company tax_rate={self.tax_rate}>"
