from decimal import Decimal

from app.extensions import db
from app.models.base import BaseModel


class Company(BaseModel):
    """Single-row company configuration (tax settings, language, etc.)."""

    __tablename__ = "company_settings"

    LANGUAGE_ES = "es"
    LANGUAGE_EN = "en"
    LANGUAGE_FR = "fr"
    LANGUAGES = [LANGUAGE_ES, LANGUAGE_EN, LANGUAGE_FR]
    # Shown as-is in language pickers — a language's own name, never
    # translated (a French speaker looks for "Français" whatever the
    # current UI language is).
    LANGUAGE_LABELS = {LANGUAGE_ES: "Español", LANGUAGE_EN: "English", LANGUAGE_FR: "Français"}

    # Shown on generated documents (e.g. the unpaid-sales PDF, #81).
    name = db.Column(db.String(120), nullable=False, default="Scoby Kombucha")
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

    # Per-field visibility on the "new/edit product" form. A hidden field
    # is dropped from the form entirely and its column left null/derived.
    # Price can be hidden too (#38): since #23 every real Sale line carries
    # its own price, so a catalog price is optional — Scoby enters it per
    # sale. Flavor likewise (#37): Scoby folds the flavor into the name.
    product_short_name_enabled = db.Column(db.Boolean, nullable=False, default=True)
    product_size_enabled = db.Column(db.Boolean, nullable=False, default=True)
    product_sku_enabled = db.Column(db.Boolean, nullable=False, default=True)
    product_flavor_enabled = db.Column(db.Boolean, nullable=False, default=True)
    product_price_enabled = db.Column(db.Boolean, nullable=False, default=True)

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
