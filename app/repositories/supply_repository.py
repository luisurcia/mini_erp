from app.models.supply import Supply, SupplyItem, SupplyMovement
from app.repositories.base_repository import Repository


class SupplyRepository(Repository[Supply]):
    def __init__(self):
        super().__init__(Supply)

    def get_active(self) -> list[Supply]:
        return Supply.query.filter_by(is_active=True).order_by(Supply.name).all()


class SupplyItemRepository(Repository[SupplyItem]):
    def __init__(self):
        super().__init__(SupplyItem)

    def get_by_supply_and_warehouse(
        self, supply_id: int, warehouse_id: int
    ) -> SupplyItem | None:
        return SupplyItem.query.filter_by(
            supply_id=supply_id, warehouse_id=warehouse_id
        ).first()

    def low_stock(self) -> list[SupplyItem]:
        return [item for item in self.get_all() if item.is_low_stock]


class SupplyMovementRepository(Repository[SupplyMovement]):
    def __init__(self):
        super().__init__(SupplyMovement)

    def for_supply(self, supply_id: int) -> list[SupplyMovement]:
        return (
            SupplyMovement.query.filter_by(supply_id=supply_id)
            .order_by(SupplyMovement.created_at.desc())
            .all()
        )
