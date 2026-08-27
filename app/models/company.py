from decimal import Decimal

from app.extensions import db
from app.models.base import BaseModel


class Company(BaseModel):
    """Single-row company configuration (tax settings, language, etc.)."""

    __tablename__ = "company_settings"

    LANGUAGE_ES = "es"
    LANGUAGE_EN = "en"
    LANGUAGES = [LANGUAGE_ES, LANGUAGE_EN]

    tax_rate = db.Column(db.Numeric(5, 2), nullable=False, default=Decimal("19.00"))
    tax_enabled_default = db.Column(db.Boolean, nullable=False, default=True)
    language = db.Column(db.String(5), nullable=False, default=LANGUAGE_ES)

    # Money display. `client/scoby` bills in Chilean pesos, which have no
    # cents — so the default here is CLP with 0 decimals, and every amount
    # shown in the app is formatted through app.display.format_money using
    # these settings. Tax rounding follows currency_decimals too (see
    # Sale.recalculate_total). See #39.
    currency_code = db.Column(db.String(3), nullable=False, default="CLP")
    currency_symbol = db.Column(db.String(8), nullable=False, default="$")
    currency_decimals = db.Column(db.Integer, nullable=False, default=0)

    # Per-field visibility on the "new/edit product" form. Unit price is
    # never toggleable: Sales reads it directly off the product, so a
    # product without one can't be sold.
    product_short_name_enabled = db.Column(db.Boolean, nullable=False, default=True)
    product_size_enabled = db.Column(db.Boolean, nullable=False, default=True)
    product_sku_enabled = db.Column(db.Boolean, nullable=False, default=True)

    @property
    def money_quantum(self) -> Decimal:
        """The smallest representable amount for the configured currency —
        e.g. Decimal('1') for CLP (0 decimals), Decimal('0.01') for USD.
        Used to round computed amounts (tax) to whole units of currency."""
        return Decimal(1).scaleb(-self.currency_decimals)

    @classmethod
    def get_settings(cls) -> "Company":
        settings = cls.query.first()
        if settings is None:
            settings = cls()
            db.session.add(settings)
            db.session.commit()
        return settings

    def __repr__(self) -> str:
        return f"<Company tax_rate={self.tax_rate}>"
