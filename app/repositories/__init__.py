from app.repositories.customer_repository import CustomerRepository
from app.repositories.inventory_repository import (
    InventoryRepository,
    StockMovementRepository,
)
from app.repositories.opportunity_repository import OpportunityRepository
from app.repositories.product_repository import FlavorRepository, ProductRepository
from app.repositories.sales_repository import SalesRepository

__all__ = [
    "CustomerRepository",
    "InventoryRepository",
    "StockMovementRepository",
    "OpportunityRepository",
    "FlavorRepository",
    "ProductRepository",
    "SalesRepository",
]
