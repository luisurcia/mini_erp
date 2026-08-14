from datetime import datetime, timezone

from app.exceptions import NotFoundError
from app.models.inventory import StockMovement
from app.models.sales import Sale, SaleItem
from app.repositories.product_repository import ProductRepository
from app.repositories.sales_repository import SalesRepository
from app.services.inventory_service import InventoryService


class SalesService:
    """Records real sales, keeping inventory consistent with what's sold."""

    def __init__(
        self,
        sales_repo: SalesRepository | None = None,
        product_repo: ProductRepository | None = None,
        inventory_service: InventoryService | None = None,
    ):
        self.sales_repo = sales_repo or SalesRepository()
        self.product_repo = product_repo or ProductRepository()
        self.inventory_service = inventory_service or InventoryService()

    def record_sale(
        self,
        customer_id: int,
        items: list[dict],
        status: str = Sale.STATUS_COMPLETED,
        sale_date: datetime | None = None,
        notes: str | None = None,
    ) -> Sale:
        if not items:
            raise ValueError("A sale needs at least one line item")

        sale = Sale(
            customer_id=customer_id,
            status=status,
            sale_date=sale_date or datetime.now(timezone.utc),
            notes=notes,
        )

        for line in items:
            product = self.product_repo.get(line["product_id"])
            if product is None:
                raise NotFoundError(f"Product #{line['product_id']} not found")
            quantity = int(line["quantity"])

            sale.items.append(
                SaleItem(product=product, quantity=quantity, unit_price=product.unit_price)
            )

            if status == Sale.STATUS_COMPLETED:
                self.inventory_service.consume(
                    product.id,
                    quantity,
                    reason=StockMovement.REASON_SALE,
                    note=f"Sale line for {product.display_name}",
                    commit=False,
                )

        sale.recalculate_total()
        self.sales_repo.add(sale)
        self.sales_repo.commit()
        return sale

    def total_revenue(self, sales: list[Sale]):
        return sum((sale.total_amount for sale in sales), start=0)
