from app.extensions import db
from app.models.base import BaseModel


class Warehouse(BaseModel):
    """One of Scoby's physical warehouses. A simple admin-editable catalog
    (rename/add/deactivate), same pattern as CustomerSegment — see #25.
    """

    __tablename__ = "warehouses"

    DEFAULTS = ["Bodega Julien", "Bodega Mario", "Bodega Principal"]
    DEFAULT_NAME = "Bodega Principal"

    name = db.Column(db.String(80), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_default = db.Column(db.Boolean, nullable=False, default=False)

    @classmethod
    def ensure_defaults(cls) -> None:
        if cls.query.count() > 0:
            return
        db.session.add_all(
            cls(name=name, is_default=(name == cls.DEFAULT_NAME)) for name in cls.DEFAULTS
        )
        db.session.commit()

    def __repr__(self) -> str:
        return f"<Warehouse {self.name}>"
