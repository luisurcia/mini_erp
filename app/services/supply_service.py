from app.models.supply import SupplyItem, SupplyMovement
from app.repositories.supply_repository import SupplyItemRepository, SupplyMovementRepository


class SupplyService:
    """Owns every mutation of supply stock levels, mirroring
    InventoryService for production inputs (bottles, labels, caps, ...)
    instead of finished products. See #29."""

    def __init__(
        self,
        supply_item_repo: SupplyItemRepository | None = None,
        movement_repo: SupplyMovementRepository | None = None,
    ):
        self.supply_item_repo = supply_item_repo or SupplyItemRepository()
        self.movement_repo = movement_repo or SupplyMovementRepository()

    def create_supply_item(
        self, supply_id: int, warehouse_id: int, initial_qty: int = 0, reorder_level: int = 10
    ) -> SupplyItem:
        item = SupplyItem(
            supply_id=supply_id,
            warehouse_id=warehouse_id,
            quantity_on_hand=initial_qty,
            reorder_level=reorder_level,
        )
        self.supply_item_repo.add(item)
        self.supply_item_repo.commit()
        return item

    def restock(
        self,
        supply_id: int,
        warehouse_id: int,
        quantity: int,
        note: str | None = None,
        reorder_level: int | None = None,
    ) -> SupplyItem:
        if quantity <= 0:
            raise ValueError("Restock quantity must be positive")

        item = self._get_or_create_item(supply_id, warehouse_id)
        if reorder_level is not None:
            item.reorder_level = reorder_level
        item.quantity_on_hand += quantity
        self._record_movement(
            supply_id, warehouse_id, quantity, SupplyMovement.REASON_RESTOCK, note
        )
        self.supply_item_repo.commit()
        return item

    def set_reorder_level(
        self, supply_id: int, warehouse_id: int, reorder_level: int
    ) -> SupplyItem:
        item = self._get_or_create_item(supply_id, warehouse_id)
        item.reorder_level = reorder_level
        self.supply_item_repo.commit()
        return item

    def adjust(
        self, supply_id: int, warehouse_id: int, new_quantity: int, note: str | None = None
    ) -> SupplyItem:
        item = self._get_or_create_item(supply_id, warehouse_id)
        delta = new_quantity - item.quantity_on_hand
        item.quantity_on_hand = new_quantity
        self._record_movement(
            supply_id, warehouse_id, delta, SupplyMovement.REASON_ADJUSTMENT, note
        )
        self.supply_item_repo.commit()
        return item

    def low_stock_report(self) -> list[SupplyItem]:
        return self.supply_item_repo.low_stock()

    def movement_history(self, supply_id: int) -> list[SupplyMovement]:
        return self.movement_repo.for_supply(supply_id)

    def _get_or_create_item(self, supply_id: int, warehouse_id: int) -> SupplyItem:
        item = self.supply_item_repo.get_by_supply_and_warehouse(supply_id, warehouse_id)
        if item is None:
            item = SupplyItem(
                supply_id=supply_id, warehouse_id=warehouse_id,
                quantity_on_hand=0, reorder_level=10,
            )
            self.supply_item_repo.add(item)
        return item

    def _record_movement(
        self, supply_id: int, warehouse_id: int, change_qty: int, reason: str, note: str | None
    ) -> None:
        movement = SupplyMovement(
            supply_id=supply_id,
            warehouse_id=warehouse_id,
            change_qty=change_qty,
            reason=reason,
            note=note,
        )
        self.movement_repo.add(movement)
