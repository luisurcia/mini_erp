from datetime import datetime

from sqlalchemy import extract

from app.extensions import db
from app.models.sales import Sale
from app.repositories.base_repository import Repository


class SalesRepository(Repository[Sale]):
    def __init__(self):
        super().__init__(Sale)

    def get_all(self) -> list[Sale]:
        return Sale.query.order_by(Sale.sale_date.desc()).all()

    def by_payment_status(self, payment_status: str) -> list[Sale]:
        return (
            Sale.query.filter(Sale.payment_status == payment_status)
            .order_by(Sale.sale_date.desc())
            .all()
        )

    def completed_between(self, start: datetime, end: datetime) -> list[Sale]:
        return Sale.query.filter(
            Sale.status == Sale.STATUS_COMPLETED,
            Sale.sale_date >= start,
            Sale.sale_date <= end,
        ).all()

    def completed_in_year(self, year: int) -> list[Sale]:
        return Sale.query.filter(
            Sale.status == Sale.STATUS_COMPLETED,
            extract("year", Sale.sale_date) == year,
        ).all()

    def completed_in_years(self, years: list[int]) -> list[Sale]:
        """Completed sales across any of the given calendar years — the
        Dashboard's multi-year filter (#83). Empty list = every year."""
        if not years:
            return self.completed_all()
        return Sale.query.filter(
            Sale.status == Sale.STATUS_COMPLETED,
            extract("year", Sale.sale_date).in_(years),
        ).all()

    def completed_all(self) -> list[Sale]:
        return Sale.query.filter(Sale.status == Sale.STATUS_COMPLETED).all()

    def distinct_years(self) -> list[int]:
        rows = db.session.query(extract("year", Sale.sale_date)).distinct().all()
        return sorted({int(row[0]) for row in rows if row[0] is not None}, reverse=True)

    def last_purchase_by_customer(self) -> dict[int, datetime]:
        """customer id -> date of their most recent completed sale, across
        all history (not scoped to any year/month filter). See #40."""
        rows = (
            db.session.query(Sale.customer_id, db.func.max(Sale.sale_date))
            .filter(Sale.status == Sale.STATUS_COMPLETED)
            .group_by(Sale.customer_id)
            .all()
        )
        return {customer_id: last_date for customer_id, last_date in rows}
