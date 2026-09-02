from collections import defaultdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.display import product_label, product_short_label
from app.exceptions import MiniErpError, NotFoundError
from app.models.company import Company
from app.models.inventory import StockMovement
from app.models.product import Product
from app.models.sales import Sale, SaleItem
from app.repositories.product_repository import ProductRepository
from app.repositories.sales_repository import SalesRepository
from app.repositories.warehouse_repository import WarehouseRepository
from app.services.inventory_service import InventoryService


class SalesService:
    """Records real sales, keeping inventory consistent with what's sold."""

    def __init__(
        self,
        sales_repo: SalesRepository | None = None,
        product_repo: ProductRepository | None = None,
        inventory_service: InventoryService | None = None,
        warehouse_repo: WarehouseRepository | None = None,
    ):
        self.sales_repo = sales_repo or SalesRepository()
        self.product_repo = product_repo or ProductRepository()
        self.inventory_service = inventory_service or InventoryService()
        self.warehouse_repo = warehouse_repo or WarehouseRepository()

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
            sale_date=sale_date or datetime.now(UTC),
            notes=notes,
            invoice_number=invoice_number,
            tax_applied=include_tax,
            tax_rate_applied=Company.get_settings().tax_rate if include_tax else None,
        )

        # Callers that don't know about warehouses yet (seed data) fall
        # back to the default warehouse rather than requiring every caller
        # to pick one.
        default_warehouse_id = None

        for line in items:
            product = self.product_repo.get(line["product_id"])
            if product is None:
                raise NotFoundError(f"Product #{line['product_id']} not found")
            quantity = int(line["quantity"])
            unit_price = line.get("unit_price")
            if unit_price is None:
                unit_price = product.unit_price
            if unit_price is None:
                raise MiniErpError(
                    f"No unit price for '{product_label(product)}'. Enter a price on "
                    f"the sale line (this product has no catalog price)."
                )
            warehouse_id = line.get("warehouse_id")
            if warehouse_id is None:
                if default_warehouse_id is None:
                    default_warehouse_id = self.warehouse_repo.get_default().id
                warehouse_id = default_warehouse_id

            sale.items.append(
                SaleItem(
                    product=product,
                    quantity=quantity,
                    unit_price=unit_price,
                    warehouse_id=warehouse_id,
                )
            )

            if status == Sale.STATUS_COMPLETED:
                self.inventory_service.consume(
                    product.id,
                    warehouse_id,
                    quantity,
                    reason=StockMovement.REASON_SALE,
                    note=f"Sale line for {product_label(product)}",
                    commit=False,
                )

        sale.recalculate_total()
        self.sales_repo.add(sale)
        self.sales_repo.commit()
        return sale

    def register_payment(
        self, sale_id: int, reference: str, paid_at: datetime | None = None
    ) -> Sale:
        """Mark a sale as paid, recording the transfer/reference number (#51)."""
        sale = self.sales_repo.get(sale_id)
        if sale is None:
            raise NotFoundError(f"Sale #{sale_id} not found")
        reference = (reference or "").strip()
        if not reference:
            raise MiniErpError("A payment reference is required.")
        if sale.payment_status == Sale.PAYMENT_PAID:
            raise MiniErpError(f"Sale #{sale_id} is already marked as paid.")
        sale.payment_status = Sale.PAYMENT_PAID
        sale.payment_reference = reference
        sale.paid_at = paid_at or datetime.now(UTC)
        self.sales_repo.commit()
        return sale

    def revert_payment(self, sale_id: int) -> Sale:
        """Undo a payment, back to unpaid (admin-only in the UI, see #51)."""
        sale = self.sales_repo.get(sale_id)
        if sale is None:
            raise NotFoundError(f"Sale #{sale_id} not found")
        sale.payment_status = Sale.PAYMENT_UNPAID
        sale.payment_reference = None
        sale.paid_at = None
        self.sales_repo.commit()
        return sale

    def active_products_by_demand(
        self, window_days: int = 90, now: datetime | None = None
    ) -> list[Product]:
        """Active products ordered for the New Sale grid (#94): the ones
        sold in the last `window_days`, most units first, then the rest in
        the catalog's default (alphabetical) order.

        Ranking is by units sold (sum of SaleItem.quantity), not revenue —
        the grid is a data-entry aid, so "what we ship most" is a better
        predictor of the next line than "what bills most". The rolling
        window keeps the order tracking current demand instead of freezing
        on all-time history.
        """
        reference = now or datetime.now(UTC)
        # Stored sale_date values are naive (SQLite drops tzinfo); compare
        # against a naive UTC cutoff so the filter behaves.
        cutoff = (reference - timedelta(days=window_days)).replace(tzinfo=None)

        units: dict[int, int] = defaultdict(int)
        for sale in self.sales_repo.completed_since(cutoff):
            for item in sale.items:
                units[item.product_id] += item.quantity

        # Stable sort: get_active() is already alphabetical, so products
        # with no recent sales keep that order and ties break the same way.
        return sorted(
            self.product_repo.get_active(),
            key=lambda product: units.get(product.id, 0),
            reverse=True,
        )

    def total_revenue(self, sales: list[Sale]):
        return sum((sale.total_amount for sale in sales), start=0)

    def average_sale_total(self, sales: list[Sale]):
        if not sales:
            return Decimal("0")
        return self.total_revenue(sales) / len(sales)

    def invoice_count(self, sales: list[Sale]) -> int:
        return sum(1 for sale in sales if sale.invoice_number)

    def taxed_sales_count(self, sales: list[Sale]) -> int:
        """Number of sales that carry IVA — for Scoby a taxed sale is a
        factura (vs. a boleta), so this is the dashboard's "N° de facturas"
        (#91)."""
        return sum(1 for sale in sales if sale.tax_applied)

    def total_bottles(self, sales: list[Sale]) -> int:
        """Units sold across every line of the given sales (#91)."""
        return sum(item.quantity for sale in sales for item in sale.items)

    def average_unit_price(self, sales: list[Sale]):
        """Simple average of the unit price on every sale line across the
        given sales — "what price do we typically sell a unit at". The line
        price is net (IVA is added on top of the subtotal, not the line).
        Each line counts once, regardless of quantity. See #84."""
        prices = [item.unit_price for sale in sales for item in sale.items]
        if not prices:
            return Decimal("0")
        return sum(prices, start=Decimal("0")) / len(prices)

    def average_bottles_per_sale(self, sales: list[Sale]):
        """Average number of units (across all line items) per sale —
        one of Scoby's dashboard KPIs, see #30."""
        if not sales:
            return Decimal("0")
        return Decimal(self.total_bottles(sales)) / len(sales)

    def sales_by_product(self, sales: list[Sale]) -> list[dict]:
        """Revenue and share of total per product, across the given sales.

        Each entry carries both the full ``product`` label (for the pie
        legend) and a compact ``product_short`` one (for the per-product
        bar chart, where a long label doesn't fit under the axis) — see #91.
        """
        settings = Company.get_settings()
        totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
        short_labels: dict[str, str] = {}
        for sale in sales:
            for item in sale.items:
                name = product_label(item.product, settings)
                totals[name] += item.subtotal
                short_labels[name] = product_short_label(item.product, settings)

        grand_total = sum(totals.values(), start=Decimal("0"))
        return [
            {
                "product": name,
                "product_short": short_labels[name],
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

    def top_customers_by_consumption(
        self,
        sales: list[Sale],
        limit: int = 10,
        last_purchase_by_customer: dict[int, datetime] | None = None,
    ) -> list[dict]:
        """Ranks customers by total amount spent across the given sales.

        `last_purchase_by_customer` (customer id -> datetime), when given,
        fills each entry's ``last_purchase`` — pass the *unfiltered*
        history from SalesRepository.last_purchase_by_customer() so the
        column shows the customer's real last order, not just the last one
        inside the current year/month filter (#40).
        """
        totals: dict[int, dict] = {}
        for sale in sales:
            entry = totals.setdefault(
                sale.customer_id,
                {
                    "customer": sale.customer,
                    "total_amount": Decimal("0"),
                    "total_units": 0,
                    "sale_count": 0,
                    "last_purchase": None,
                },
            )
            entry["total_amount"] += sale.total_amount
            entry["total_units"] += sum(item.quantity for item in sale.items)
            entry["sale_count"] += 1

        for customer_id, entry in totals.items():
            if last_purchase_by_customer is not None:
                entry["last_purchase"] = last_purchase_by_customer.get(customer_id)

        ranked = sorted(totals.values(), key=lambda entry: entry["total_amount"], reverse=True)
        return ranked[:limit]

    def monthly_bottles_sold(self, sales: list[Sale]) -> list[int]:
        """Sum of item quantities per calendar month (Jan..Dec) for the given sales."""
        totals = [0] * 12
        for sale in sales:
            for item in sale.items:
                totals[sale.sale_date.month - 1] += item.quantity
        return totals
