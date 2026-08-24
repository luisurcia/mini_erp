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

    def distinct_years(self) -> list[int]:
        rows = db.session.query(extract("year", Sale.sale_date)).distinct().all()
        return sorted({int(row[0]) for row in rows if row[0] is not None}, reverse=True)
