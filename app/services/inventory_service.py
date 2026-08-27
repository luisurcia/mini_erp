from app.exceptions import InsufficientStockError, NotFoundError
from app.models.inventory import InventoryItem, StockMovement
from app.repositories.inventory_repository import (
    InventoryRepository,
    StockMovementRepository,
)
from app.repositories.product_repository import ProductRepository


class InventoryService:
    """Owns every mutation of stock levels, so quantities never go negative
    and every change is recorded as a StockMovement. Stock is tracked per
    (product, warehouse) — see #25."""

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
        self, product_id: int, warehouse_id: int, initial_qty: int = 0, reorder_level: int = 10
    ) -> InventoryItem:
        item = InventoryItem(
            product_id=product_id,
            warehouse_id=warehouse_id,
            quantity_on_hand=initial_qty,
            reorder_level=reorder_level,
        )
        self.inventory_repo.add(item)
        self.inventory_repo.commit()
        return item

    def restock(
        self,
        product_id: int,
        warehouse_id: int,
        quantity: int,
        note: str | None = None,
        reorder_level: int | None = None,
    ) -> InventoryItem:
        if quantity <= 0:
            raise ValueError("Restock quantity must be positive")

        item = self._get_or_create_item(product_id, warehouse_id)
        if reorder_level is not None:
            item.reorder_level = reorder_level
        item.quantity_on_hand += quantity
        self._record_movement(
            product_id, warehouse_id, quantity, StockMovement.REASON_RESTOCK, note
        )
        self.inventory_repo.commit()
        return item

    def consume(
        self,
        product_id: int,
        warehouse_id: int,
        quantity: int,
        reason: str = StockMovement.REASON_SALE,
        note: str | None = None,
        commit: bool = True,
    ) -> InventoryItem:
        if quantity <= 0:
            raise ValueError("Consume quantity must be positive")

        item = self._get_item_or_raise(product_id, warehouse_id)
        if item.quantity_on_hand < quantity:
            product = self.product_repo.get(product_id)
            product_name = product.name if product else f"product #{product_id}"
            raise InsufficientStockError(
                product_name, quantity, item.quantity_on_hand, item.warehouse.name
            )

        item.quantity_on_hand -= quantity
        self._record_movement(product_id, warehouse_id, -quantity, reason, note)
        if commit:
            self.inventory_repo.commit()
        return item

    def set_reorder_level(
        self, product_id: int, warehouse_id: int, reorder_level: int
    ) -> InventoryItem:
        """Update just the reorder threshold, without adding stock — used
        when the seller only wants to tweak the alert level."""
        item = self._get_or_create_item(product_id, warehouse_id)
        item.reorder_level = reorder_level
        self.inventory_repo.commit()
        return item

    def adjust(
        self, product_id: int, warehouse_id: int, new_quantity: int, note: str | None = None
    ) -> InventoryItem:
        item = self._get_or_create_item(product_id, warehouse_id)
        delta = new_quantity - item.quantity_on_hand
        item.quantity_on_hand = new_quantity
        self._record_movement(
            product_id, warehouse_id, delta, StockMovement.REASON_ADJUSTMENT, note
        )
        self.inventory_repo.commit()
        return item

    def low_stock_report(self) -> list[InventoryItem]:
        return self.inventory_repo.low_stock()

    def movement_history(self, product_id: int) -> list[StockMovement]:
        return self.movement_repo.for_product(product_id)

    def _get_item_or_raise(self, product_id: int, warehouse_id: int) -> InventoryItem:
        item = self.inventory_repo.get_by_product_and_warehouse(product_id, warehouse_id)
        if item is None:
            raise NotFoundError(
                f"No inventory record for product #{product_id} in warehouse #{warehouse_id}"
            )
        return item

    def _get_or_create_item(self, product_id: int, warehouse_id: int) -> InventoryItem:
        """Restock/adjust create the (product, warehouse) row on first use
        instead of requiring it to be seeded upfront — a product starts
        with no stock anywhere until someone puts some in a warehouse."""
        item = self.inventory_repo.get_by_product_and_warehouse(product_id, warehouse_id)
        if item is None:
            item = InventoryItem(
                product_id=product_id, warehouse_id=warehouse_id,
                quantity_on_hand=0, reorder_level=10,
            )
            self.inventory_repo.add(item)
        return item

    def _record_movement(
        self, product_id: int, warehouse_id: int, change_qty: int, reason: str, note: str | None
    ) -> None:
        movement = StockMovement(
            product_id=product_id,
            warehouse_id=warehouse_id,
            change_qty=change_qty,
            reason=reason,
            note=note,
        )
        self.movement_repo.add(movement)
