from app.exceptions import InsufficientStockError, NotFoundError
from app.models.inventory import InventoryItem, StockMovement
from app.repositories.inventory_repository import (
    InventoryRepository,
    StockMovementRepository,
)
from app.repositories.product_repository import ProductRepository


class InventoryService:
    """Owns every mutation of stock levels, so quantities never go negative
    and every change is recorded as a StockMovement."""

    def __init__(
        self,
        inventory_repo: InventoryRepository | None = None,
        movement_repo: StockMovementRepository | None = None,
        product_repo: ProductRepository | None = None,
    ):
        self.inventory_repo = inventory_repo or InventoryRepository()
        self.movement_repo = movement_repo or StockMovementRepository()
        self.product_repo = product_repo or ProductRepository()

    def create_inventory_item(
        self, product_id: int, initial_qty: int = 0, reorder_level: int = 10
    ) -> InventoryItem:
        item = InventoryItem(
            product_id=product_id,
            quantity_on_hand=initial_qty,
            reorder_level=reorder_level,
        )
        self.inventory_repo.add(item)
        self.inventory_repo.commit()
        return item

    def restock(self, product_id: int, quantity: int, note: str | None = None) -> InventoryItem:
        if quantity <= 0:
            raise ValueError("Restock quantity must be positive")

        item = self._get_item_or_raise(product_id)
        item.quantity_on_hand += quantity
        self._record_movement(product_id, quantity, StockMovement.REASON_RESTOCK, note)
        self.inventory_repo.commit()
        return item

    def consume(
        self,
        product_id: int,
        quantity: int,
        reason: str = StockMovement.REASON_SALE,
        note: str | None = None,
        commit: bool = True,
    ) -> InventoryItem:
        if quantity <= 0:
            raise ValueError("Consume quantity must be positive")

        item = self._get_item_or_raise(product_id)
        if item.quantity_on_hand < quantity:
            product = self.product_repo.get(product_id)
            product_name = product.name if product else f"product #{product_id}"
            raise InsufficientStockError(product_name, quantity, item.quantity_on_hand)

        item.quantity_on_hand -= quantity
        self._record_movement(product_id, -quantity, reason, note)
        if commit:
            self.inventory_repo.commit()
        return item

    def adjust(self, product_id: int, new_quantity: int, note: str | None = None) -> InventoryItem:
        item = self._get_item_or_raise(product_id)
        delta = new_quantity - item.quantity_on_hand
        item.quantity_on_hand = new_quantity
        self._record_movement(product_id, delta, StockMovement.REASON_ADJUSTMENT, note)
        self.inventory_repo.commit()
        return item

    def low_stock_report(self) -> list[InventoryItem]:
        return self.inventory_repo.low_stock()

    def movement_history(self, product_id: int) -> list[StockMovement]:
        return self.movement_repo.for_product(product_id)

    def _get_item_or_raise(self, product_id: int) -> InventoryItem:
        item = self.inventory_repo.get_by_product(product_id)
        if item is None:
            raise NotFoundError(f"No inventory record for product #{product_id}")
        return item

    def _record_movement(
        self, product_id: int, change_qty: int, reason: str, note: str | None
    ) -> None:
        movement = StockMovement(
            product_id=product_id, change_qty=change_qty, reason=reason, note=note
        )
        self.movement_repo.add(movement)
