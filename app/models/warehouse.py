from app.extensions import db
from app.models.base import BaseModel


class Warehouse(BaseModel):
    """One of Scoby's physical warehouses. A simple admin-editable catalog
    (rename/add/deactivate), same pattern as CustomerSegment — see #25.

    `kind` splits distribution warehouses (finished product) from the
    single supplies warehouse (bottles/labels/caps) — see #48.

    `stage` places a finished-product warehouse in Scoby's flow (#86):

      producción → Fermentación → Principal → distribución (Julien, Mario)

    - `fermentation`: the one warehouse assembled bottles enter (the only
      place stock can be restocked). Unique.
    - `main`: Bodega Principal. Receives from Fermentación, sends to
      distribution. Unique.
    - `distribution`: Julien, Mario, ... — receive only by transfer from
      Principal. Can be many.

    `kind`/`stage` are set once and not editable from the UI.
    """

    __tablename__ = "warehouses"

    KIND_DISTRIBUTION = "distribution"
    KIND_SUPPLIES = "supplies"

    STAGE_FERMENTATION = "fermentation"
    STAGE_MAIN = "main"
    STAGE_DISTRIBUTION = "distribution"

    # (name, stage) for a fresh database. Principal is is_default.
    DEFAULTS = [
        ("Bodega de Fermentación", STAGE_FERMENTATION),
        ("Bodega Principal", STAGE_MAIN),
        ("Bodega Julien", STAGE_DISTRIBUTION),
        ("Bodega Mario", STAGE_DISTRIBUTION),
    ]
    DEFAULT_NAME = "Bodega Principal"
    SUPPLIES_NAME = "Bodega de Insumos"
    FERMENTATION_NAME = "Bodega de Fermentación"

    # Transfers are only allowed along the flow: Fermentación → Principal,
    # Principal → distribución. Everything else is rejected (#86).
    ALLOWED_TRANSFERS = {
        (STAGE_FERMENTATION, STAGE_MAIN),
        (STAGE_MAIN, STAGE_DISTRIBUTION),
    }

    name = db.Column(db.String(80), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_default = db.Column(db.Boolean, nullable=False, default=False)
    kind = db.Column(db.String(20), nullable=False, default=KIND_DISTRIBUTION)
    stage = db.Column(db.String(20), nullable=False, default=STAGE_DISTRIBUTION)

    @property
    def is_supplies(self) -> bool:
        return self.kind == self.KIND_SUPPLIES

    @property
    def is_fermentation(self) -> bool:
        return self.stage == self.STAGE_FERMENTATION

    @property
    def is_main(self) -> bool:
        return self.stage == self.STAGE_MAIN

    @classmethod
    def ensure_defaults(cls) -> None:
        if cls.query.count() == 0:
            db.session.add_all(
                cls(name=name, stage=stage, is_default=(stage == cls.STAGE_MAIN))
                for name, stage in cls.DEFAULTS
            )
            db.session.commit()
        cls.ensure_supplies_warehouse()
        cls.ensure_fermentation_warehouse()

    @classmethod
    def ensure_supplies_warehouse(cls) -> "Warehouse":
        """Guarantee exactly one supplies warehouse exists (#48)."""
        supplies = cls.query.filter_by(kind=cls.KIND_SUPPLIES).first()
        if supplies is None:
            supplies = cls(name=cls.SUPPLIES_NAME, kind=cls.KIND_SUPPLIES)
            db.session.add(supplies)
            db.session.commit()
        return supplies

    @classmethod
    def ensure_fermentation_warehouse(cls) -> "Warehouse":
        """Guarantee exactly one fermentation-stage warehouse exists (#86)."""
        ferm = cls.query.filter_by(stage=cls.STAGE_FERMENTATION).first()
        if ferm is None:
            ferm = cls(
                name=cls.FERMENTATION_NAME,
                kind=cls.KIND_DISTRIBUTION,
                stage=cls.STAGE_FERMENTATION,
            )
            db.session.add(ferm)
            db.session.commit()
        return ferm

    def __repr__(self) -> str:
        return f"<Warehouse {self.name} ({self.stage})>"
