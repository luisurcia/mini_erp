from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models.base import BaseModel


class User(BaseModel, UserMixin):
    __tablename__ = "users"

    ROLE_ADMIN = "admin"
    ROLE_BODEGUERO = "bodeguero"
    ROLE_VENTAS = "venta"
    ROLES = [ROLE_ADMIN, ROLE_BODEGUERO, ROLE_VENTAS]

    # Per-module access — a role sees (and can reach) only these modules'
    # screens. Users/Company stay admin-only and aren't modeled here; see
    # admin_required in app/permissions.py. See #31.
    #
    # The Products catalog is master data (low change frequency, high blast
    # radius) so it's admin-only: MODULE_PRODUCTS is not granted to any
    # non-admin role. The supplies-recipe screens are admin-only the same
    # way, gated with admin_required inside the supplies blueprint. See #78.
    # The Purchases ledger (plant-overhead expenses) is admin-only too for
    # now — financial data; extend to bodeguero later if needed (#93).
    MODULE_PRODUCTS = "products"
    MODULE_INVENTORY = "inventory"
    MODULE_SUPPLIES = "supplies"
    MODULE_SALES = "sales"
    MODULE_TOP_CUSTOMERS = "top_customers"
    MODULE_CUSTOMERS = "customers"
    MODULE_PURCHASES = "purchases"

    _ALL_MODULES = {
        MODULE_PRODUCTS,
        MODULE_INVENTORY,
        MODULE_SUPPLIES,
        MODULE_SALES,
        MODULE_TOP_CUSTOMERS,
        MODULE_CUSTOMERS,
        MODULE_PURCHASES,
    }

    ROLE_MODULES = {
        ROLE_ADMIN: _ALL_MODULES,
        ROLE_BODEGUERO: {MODULE_INVENTORY, MODULE_SUPPLIES},
        ROLE_VENTAS: {MODULE_SALES, MODULE_TOP_CUSTOMERS, MODULE_CUSTOMERS},
    }

    username = db.Column(db.String(80), unique=True, nullable=False)
    # Display name — `username` stays the login identifier, screens show
    # this instead. Nullable: pre-#44 users and the seeded admin have none
    # and fall back to the username. See #44.
    first_name = db.Column(db.String(80), nullable=True)
    last_name = db.Column(db.String(80), nullable=True)
    # Preferred UI language. Null = follow the company default. Each user
    # sets their own from /auth/language. See #43.
    language = db.Column(db.String(5), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=ROLE_ADMIN)

    @property
    def display_name(self) -> str:
        full = f"{self.first_name or ''} {self.last_name or ''}".strip()
        return full or self.username

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    @property
    def is_admin(self) -> bool:
        return self.role == self.ROLE_ADMIN

    def can_access(self, module: str) -> bool:
        return module in self.ROLE_MODULES.get(self.role, set())

    def __repr__(self) -> str:
        return f"<User {self.username}>"
