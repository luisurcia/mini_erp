from app.models.customer import Customer
from app.repositories.base_repository import Repository
from app.search import search_ilike


class CustomerRepository(Repository[Customer]):
    def __init__(self):
        super().__init__(Customer)

    def search(self, term: str | None = None) -> list[Customer]:
        """Customers whose name, RUT or nickname contains `term`, ordered
        by name. No term → every customer (#123)."""
        query = search_ilike(
            Customer.query, term, Customer.name, Customer.rut, Customer.nickname
        )
        return query.order_by(Customer.name).all()
