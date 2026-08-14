from app.models.customer import Customer
from app.repositories.base_repository import Repository


class CustomerRepository(Repository[Customer]):
    def __init__(self):
        super().__init__(Customer)
