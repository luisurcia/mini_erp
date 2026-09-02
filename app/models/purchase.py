from app.extensions import db
from app.models.base import BaseModel


class Purchase(BaseModel):
    """A plant-overhead expense — cleaning supplies, a machine part, office
    items: anything bought to run the plant that isn't a production input
    (those are Supplies, #29). A flat ledger with a running correlative:
    no stock, no warehouse, no consumption. See #93.
    """

    __tablename__ = "purchases"

    # Global running number, never resets. Shown as C-0001, C-0002, ...
    # Assigned as MAX(sequence) + 1 at creation — fine at this volume, and
    # there is no sequence table anywhere else in the app. `unique` still
    # guarantees no duplicates if two creates ever race.
    sequence = db.Column(db.Integer, unique=True, nullable=False)
    purchase_date = db.Column(db.Date, nullable=False)
    item = db.Column(db.String(200), nullable=False)
    supplier = db.Column(db.String(160), nullable=False)
    # Free text for now — a category catalog is a future enhancement (#93).
    category = db.Column(db.String(80), nullable=True)
    invoice_number = db.Column(db.String(60), nullable=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    # Purely informational: whether `amount` was entered tax-inclusive. No
    # tax is computed or split — the client records whatever the document
    # says, gross or net (#93).
    includes_tax = db.Column(db.Boolean, nullable=False, default=False)
    notes = db.Column(db.String(255), nullable=True)
    # A ledger shouldn't have gaps, so entries are voided, not deleted:
    # the row and its number stay (struck through, out of the total).
    voided = db.Column(db.Boolean, nullable=False, default=False)

    @property
    def code(self) -> str:
        return f"C-{self.sequence:04d}"

    def __repr__(self) -> str:
        return f"<Purchase {self.code} {self.supplier} {self.amount}>"
