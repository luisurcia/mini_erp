from app.models.warehouse import Warehouse
from app.repositories.base_repository import Repository


class WarehouseRepository(Repository[Warehouse]):
    def __init__(self):
        super().__init__(Warehouse)

    def get_active(self) -> list[Warehouse]:
        return Warehouse.query.filter_by(is_active=True).order_by(Warehouse.id).all()

    def get_distribution(self) -> list[Warehouse]:
        """Active distribution warehouses only — the ones that hold finished
        product (Inventory, Sales, Transfers). Excludes the supplies
        warehouse. See #48."""
        return (
            Warehouse.query.filter_by(
                is_active=True, kind=Warehouse.KIND_DISTRIBUTION
            )
            .order_by(Warehouse.id)
            .all()
        )

    def get_supplies_warehouse(self) -> Warehouse | None:
        return Warehouse.query.filter_by(kind=Warehouse.KIND_SUPPLIES).first()

    def get_default(self) -> Warehouse | None:
        default = Warehouse.query.filter_by(
            is_default=True, kind=Warehouse.KIND_DISTRIBUTION
        ).first()
        if default is not None:
            return default
        distribution = self.get_distribution()
        return distribution[0] if distribution else None
