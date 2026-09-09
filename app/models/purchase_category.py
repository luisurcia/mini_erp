from app.extensions import db
from app.models.base import BaseModel


class PurchaseCategory(BaseModel):
    """Small, admin-editable catalog used to classify purchases (#110).

    Same shape and philosophy as CustomerSegment (#21): a handful of
    lookup values that rarely change, managed from Company settings, and
    deactivated rather than deleted since purchases reference them by FK.

    One row is special: FALLBACK_NAME ("No definido") is assigned to any
    purchase recorded without a category, so a purchase is never
    unclassified and the client can spot the ones still to sort out.
    """

    __tablename__ = "purchase_categories"

    FALLBACK_NAME = "No definido"
    DEFAULTS = [
        FALLBACK_NAME,
        "Insumos",
        "Repuestos",
        "Artículos de Limpieza",
        "Otros",
    ]

    name = db.Column(db.String(80), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    @property
    def is_fallback(self) -> bool:
        return self.name == self.FALLBACK_NAME

    @classmethod
    def ensure_defaults(cls) -> None:
        if cls.query.count() > 0:
            return
        db.session.add_all(cls(name=name) for name in cls.DEFAULTS)
        db.session.commit()

    @classmethod
    def get_fallback(cls) -> "PurchaseCategory":
        """The "No definido" category, recreated if someone deleted it, so
        the service can always fall back to a real row."""
        category = cls.query.filter_by(name=cls.FALLBACK_NAME).first()
        if category is None:
            category = cls(name=cls.FALLBACK_NAME)
            db.session.add(category)
            db.session.flush()
        return category

    def __repr__(self) -> str:
        return f"<PurchaseCategory {self.name}>"
