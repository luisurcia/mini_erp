class MiniErpError(Exception):
    """Base class for domain errors raised by the service layer."""


class NotFoundError(MiniErpError):
    """Raised when a requested entity does not exist."""


class InsufficientStockError(MiniErpError):
    """Raised when a sale would consume more stock than is on hand."""

    def __init__(self, product_name: str, requested: int, available: int):
        self.product_name = product_name
        self.requested = requested
        self.available = available
        super().__init__(
            f"Not enough stock for '{product_name}': requested {requested}, "
            f"only {available} available."
        )


class InvalidStageTransitionError(MiniErpError):
    """Raised when an opportunity is moved to an invalid pipeline stage."""
