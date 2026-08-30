from app.extensions import db
from app.models.base import BaseModel


class Warehouse(BaseModel):
    """One of Scoby's physical warehouses. A simple admin-editable catalog
    (rename/add/deactivate), same pattern as CustomerSegment — see #25.

    `kind` splits distribution warehouses (finished product, can be many)
    from the single supplies warehouse (bottles/labels/caps, exactly one).
    It's set once and not editable from the UI — see #48.
    """

    __tablename__ = "warehouses"

    KIND_DISTRIBUTION = "distribution"
    KIND_SUPPLIES = "supplies"

    DEFAULTS = ["Bodega Julien", "Bodega Mario", "Bodega Principal"]
    DEFAULT_NAME = "Bodega Principal"
    SUPPLIES_NAME = "Bodega de Insumos"

    name = db.Column(db.String(80), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_default = db.Column(db.Boolean, nullable=False, default=False)
    kind = db.Column(db.String(20), nullable=False, default=KIND_DISTRIBUTION)

    @property
    def is_supplies(self) -> bool:
        return self.kind == self.KIND_SUPPLIES

    @classmethod
    def ensure_defaults(cls) -> None:
        if cls.query.count() == 0:
            db.session.add_all(
                cls(name=name, is_default=(name == cls.DEFAULT_NAME))
                for name in cls.DEFAULTS
            )
            db.session.commit()
        cls.ensure_supplies_warehouse()

    @classmethod
    def ensure_supplies_warehouse(cls) -> "Warehouse":
        """Guarantee exactly one supplies warehouse exists (#48)."""
        supplies = cls.query.filter_by(kind=cls.KIND_SUPPLIES).first()
        if supplies is None:
            supplies = cls(name=cls.SUPPLIES_NAME, kind=cls.KIND_SUPPLIES)
            db.session.add(supplies)
            db.session.commit()
        return supplies

    def __repr__(self) -> str:
        return f"<Warehouse {self.name}>"
