from app.models.warehouse import Warehouse
from app.repositories.base_repository import Repository


class WarehouseRepository(Repository[Warehouse]):
    def __init__(self):
        super().__init__(Warehouse)

    def get_active(self) -> list[Warehouse]:
        return Warehouse.query.filter_by(is_active=True).order_by(Warehouse.id).all()

    def get_default(self) -> Warehouse | None:
        default = Warehouse.query.filter_by(is_default=True).first()
        if default is not None:
            return default
        active = self.get_active()
        return active[0] if active else None
