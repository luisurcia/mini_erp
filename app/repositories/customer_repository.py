from sqlalchemy import func

from app.models.customer import Customer
from app.repositories.base_repository import Repository
from app.search import search_ilike


class CustomerRepository(Repository[Customer]):
    def __init__(self):
        super().__init__(Customer)

    def all_by_name(self) -> list[Customer]:
        """Every customer, ordered case-insensitively by name — the option
        list for the Sales customer <select> (#132). ``get_all()`` orders
        by id (creation order), which isn't what a person scans."""
        return Customer.query.order_by(func.lower(Customer.name)).all()

    def search(self, term: str | None = None) -> list[Customer]:
        """Customers whose name, RUT or nickname contains `term`, ordered
        by name. No term → every customer (#123)."""
        query = search_ilike(
            Customer.query, term, Customer.name, Customer.rut, Customer.nickname
        )
        return query.order_by(Customer.name).all()
