from app.models.product import Flavor, Product
from app.repositories.base_repository import Repository


class FlavorRepository(Repository[Flavor]):
    def __init__(self):
        super().__init__(Flavor)


class ProductRepository(Repository[Product]):
    def __init__(self):
        super().__init__(Product)

    def get_active(self) -> list[Product]:
        # outerjoin, not join: a product may have no flavor when the
        # company has hidden that field (#37).
        return (
            Product.query.filter_by(is_active=True)
            .outerjoin(Flavor)
            .order_by(Flavor.name, Product.name)
            .all()
        )

    def get_by_sku(self, sku: str) -> Product | None:
        return Product.query.filter_by(sku=sku).first()
