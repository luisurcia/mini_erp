from app.models.product_supply import ProductSupply
from app.repositories.base_repository import Repository


class ProductSupplyRepository(Repository[ProductSupply]):
    def __init__(self):
        super().__init__(ProductSupply)

    def for_product(self, product_id: int) -> list[ProductSupply]:
        return ProductSupply.query.filter_by(product_id=product_id).all()

    def for_products(self, product_ids: list[int]) -> list[ProductSupply]:
        if not product_ids:
            return []
        return ProductSupply.query.filter(
            ProductSupply.product_id.in_(product_ids)
        ).all()

    def get_by_product_and_supply(
        self, product_id: int, supply_id: int
    ) -> ProductSupply | None:
        return ProductSupply.query.filter_by(
            product_id=product_id, supply_id=supply_id
        ).first()
