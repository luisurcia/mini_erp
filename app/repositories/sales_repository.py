from datetime import datetime

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
