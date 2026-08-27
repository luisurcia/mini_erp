from app.models.inventory import InventoryItem, StockMovement
from app.repositories.base_repository import Repository


class InventoryRepository(Repository[InventoryItem]):
    def __init__(self):
        super().__init__(InventoryItem)

    def get_by_product(self, product_id: int) -> InventoryItem | None:
        return InventoryItem.query.filter_by(product_id=product_id).first()

    def get_by_product_and_warehouse(
        self, product_id: int, warehouse_id: int
    ) -> InventoryItem | None:
        return InventoryItem.query.filter_by(
            product_id=product_id, warehouse_id=warehouse_id
        ).first()

    def low_stock(self) -> list[InventoryItem]:
        return [item for item in self.get_all() if item.is_low_stock]


class StockMovementRepository(Repository[StockMovement]):
    def __init__(self):
        super().__init__(StockMovement)

    def for_product(self, product_id: int) -> list[StockMovement]:
        return (
            StockMovement.query.filter_by(product_id=product_id)
            .order_by(StockMovement.created_at.desc())
            .all()
        )
