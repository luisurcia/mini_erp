from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal

from app.display import product_label
from app.exceptions import NotFoundError
from app.models.company import Company
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
        invoice_number: str | None = None,
        include_tax: bool = False,
    ) -> Sale:
        if not items:
            raise ValueError("A sale needs at least one line item")

        sale = Sale(
            customer_id=customer_id,
            status=status,
            sale_date=sale_date or datetime.now(timezone.utc),
            notes=notes,
            invoice_number=invoice_number,
            tax_applied=include_tax,
            tax_rate_applied=Company.get_settings().tax_rate if include_tax else None,
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

    def average_sale_total(self, sales: list[Sale]):
        if not sales:
            return Decimal("0")
        return self.total_revenue(sales) / len(sales)

    def invoice_count(self, sales: list[Sale]) -> int:
        return sum(1 for sale in sales if sale.invoice_number)

    def sales_by_product(self, sales: list[Sale]) -> list[dict]:
        """Revenue and share of total per product, across the given sales."""
        settings = Company.get_settings()
        totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
        for sale in sales:
            for item in sale.items:
                totals[product_label(item.product, settings)] += item.subtotal

        grand_total = sum(totals.values(), start=Decimal("0"))
        return [
            {
                "product": name,
                "amount": float(amount),
                "percentage": float(amount / grand_total * 100) if grand_total else 0,
            }
            for name, amount in sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
        ]

    def monthly_sales_counts(self, sales: list[Sale]) -> list[int]:
        """Count of sales per calendar month (Jan..Dec) for the given sales."""
        counts = [0] * 12
        for sale in sales:
            counts[sale.sale_date.month - 1] += 1
        return counts

    def monthly_bottles_sold(self, sales: list[Sale]) -> list[int]:
        """Sum of item quantities per calendar month (Jan..Dec) for the given sales."""
        totals = [0] * 12
        for sale in sales:
            for item in sale.items:
                totals[sale.sale_date.month - 1] += item.quantity
        return totals
