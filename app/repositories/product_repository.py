from app.models.product import Flavor, Product
from app.repositories.base_repository import Repository


class FlavorRepository(Repository[Flavor]):
    def __init__(self):
        super().__init__(Flavor)


class ProductRepository(Repository[Product]):
    def __init__(self):
        super().__init__(Product)

    def get_active(self) -> list[Product]:
        return (
            Product.query.filter_by(is_active=True)
            .join(Flavor)
            .order_by(Flavor.name, Product.name)
            .all()
        )

    def get_by_sku(self, sku: str) -> Product | None:
        return Product.query.filter_by(sku=sku).first()
