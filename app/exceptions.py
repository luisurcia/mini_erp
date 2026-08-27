class MiniErpError(Exception):
    """Base class for domain errors raised by the service layer."""


class NotFoundError(MiniErpError):
    """Raised when a requested entity does not exist."""


class InsufficientStockError(MiniErpError):
    """Raised when a sale would consume more stock than is on hand."""

    def __init__(
        self, product_name: str, requested: int, available: int, warehouse_name: str | None = None
    ):
        self.product_name = product_name
        self.requested = requested
        self.available = available
        self.warehouse_name = warehouse_name
        location = f" in '{warehouse_name}'" if warehouse_name else ""
        super().__init__(
            f"Not enough stock for '{product_name}'{location}: requested {requested}, "
            f"only {available} available."
        )


class DuplicateUsernameError(MiniErpError):
    """Raised when a username is already taken by another user."""


class LastAdminError(MiniErpError):
    """Raised when an action would leave the system with no admin user."""
