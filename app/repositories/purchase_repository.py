from sqlalchemy import extract, func

from app.extensions import db
from app.models.purchase import Purchase
from app.repositories.base_repository import Repository


class PurchaseRepository(Repository[Purchase]):
    def __init__(self):
        super().__init__(Purchase)

    def get_all(self) -> list[Purchase]:
        return Purchase.query.order_by(Purchase.sequence.desc()).all()

    def next_sequence(self) -> int:
        """The correlative for the next purchase — MAX(sequence) + 1."""
        return (db.session.query(func.max(Purchase.sequence)).scalar() or 0) + 1

    def in_period(self, year: int, month: int | None = None) -> list[Purchase]:
        """Purchases in a calendar year, optionally narrowed to one month.
        Ordered oldest first, then by correlative."""
        query = Purchase.query.filter(extract("year", Purchase.purchase_date) == year)
        if month is not None:
            query = query.filter(extract("month", Purchase.purchase_date) == month)
        return query.order_by(Purchase.purchase_date, Purchase.sequence).all()

    def distinct_years(self) -> list[int]:
        rows = db.session.query(extract("year", Purchase.purchase_date)).distinct().all()
        return sorted({int(row[0]) for row in rows if row[0] is not None}, reverse=True)
