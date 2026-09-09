from datetime import date
from decimal import Decimal

from app.exceptions import NotFoundError
from app.models.purchase import Purchase
from app.models.purchase_category import PurchaseCategory
from app.repositories.purchase_repository import PurchaseRepository


class PurchaseService:
    """The plant-overhead expense ledger (#93). Its only real rule is the
    running correlative; everything else is plain CRUD over `Purchase`.
    """

    def __init__(self, repo: PurchaseRepository | None = None):
        self.repo = repo or PurchaseRepository()

    def record_purchase(
        self,
        *,
        purchase_date: date,
        item: str,
        supplier: str,
        amount: Decimal,
        category_id: int | None = None,
        invoice_number: str | None = None,
        includes_tax: bool = False,
        notes: str | None = None,
    ) -> Purchase:
        purchase = Purchase(
            sequence=self.repo.next_sequence(),
            purchase_date=purchase_date,
            item=item,
            supplier=supplier,
            category_id=self._resolve_category_id(category_id),
            invoice_number=invoice_number or None,
            amount=amount,
            includes_tax=includes_tax,
            notes=notes or None,
        )
        self.repo.add(purchase)
        self.repo.commit()
        return purchase

    def update_purchase(
        self,
        purchase_id: int,
        *,
        purchase_date: date,
        item: str,
        supplier: str,
        amount: Decimal,
        category_id: int | None = None,
        invoice_number: str | None = None,
        includes_tax: bool = False,
        notes: str | None = None,
    ) -> Purchase:
        purchase = self._get(purchase_id)
        purchase.purchase_date = purchase_date
        purchase.item = item
        purchase.supplier = supplier
        purchase.amount = amount
        purchase.category_id = self._resolve_category_id(category_id)
        purchase.invoice_number = invoice_number or None
        purchase.includes_tax = includes_tax
        purchase.notes = notes or None
        self.repo.commit()
        return purchase

    def set_voided(self, purchase_id: int, voided: bool) -> Purchase:
        purchase = self._get(purchase_id)
        purchase.voided = voided
        self.repo.commit()
        return purchase

    def period_total(self, purchases: list[Purchase]) -> Decimal:
        """Sum of the given purchases, excluding voided ones."""
        return sum(
            (p.amount for p in purchases if not p.voided), start=Decimal("0")
        )

    def _resolve_category_id(self, category_id: int | None) -> int:
        """Every purchase gets a real category — the chosen one, or the
        "No definido" fallback when none was picked (#110)."""
        if category_id is not None:
            return category_id
        return PurchaseCategory.get_fallback().id

    def _get(self, purchase_id: int) -> Purchase:
        purchase = self.repo.get(purchase_id)
        if purchase is None:
            raise NotFoundError(f"Purchase #{purchase_id} not found")
        return purchase
