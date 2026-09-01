from sqlalchemy import case

from app.models.warehouse import Warehouse
from app.repositories.base_repository import Repository

# Fermentación first, then Principal, then the distribution warehouses.
_STAGE_ORDER = case(
    (Warehouse.stage == Warehouse.STAGE_FERMENTATION, 0),
    (Warehouse.stage == Warehouse.STAGE_MAIN, 1),
    else_=2,
)


class WarehouseRepository(Repository[Warehouse]):
    def __init__(self):
        super().__init__(Warehouse)

    def get_active(self) -> list[Warehouse]:
        return Warehouse.query.filter_by(is_active=True).order_by(Warehouse.id).all()

    def get_stock_locations(self) -> list[Warehouse]:
        """Every active finished-product warehouse, in flow order —
        Fermentación, Principal, then distribución. Used by the Inventory
        matrix and the transfer form. Excludes the supplies warehouse (#86)."""
        return (
            Warehouse.query.filter_by(
                is_active=True, kind=Warehouse.KIND_DISTRIBUTION
            )
            .order_by(_STAGE_ORDER, Warehouse.id)
            .all()
        )

    def get_sellable(self) -> list[Warehouse]:
        """Warehouses a sale can draw stock from — Principal + distribución,
        not Fermentación (you don't sell fermenting product). See #86."""
        return (
            Warehouse.query.filter(
                Warehouse.is_active.is_(True),
                Warehouse.kind == Warehouse.KIND_DISTRIBUTION,
                Warehouse.stage.in_(
                    [Warehouse.STAGE_MAIN, Warehouse.STAGE_DISTRIBUTION]
                ),
            )
            .order_by(_STAGE_ORDER, Warehouse.id)
            .all()
        )

    def get_fermentation(self) -> Warehouse | None:
        return Warehouse.query.filter_by(stage=Warehouse.STAGE_FERMENTATION).first()

    def get_main(self) -> Warehouse | None:
        return Warehouse.query.filter_by(stage=Warehouse.STAGE_MAIN).first()

    def get_supplies_warehouse(self) -> Warehouse | None:
        return Warehouse.query.filter_by(kind=Warehouse.KIND_SUPPLIES).first()

    def get_default(self) -> Warehouse | None:
        """The warehouse used when a caller doesn't specify one (seed data,
        legacy) — Bodega Principal / the `main` warehouse."""
        return self.get_main() or (self.get_sellable()[:1] or [None])[0]
