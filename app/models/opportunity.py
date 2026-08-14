from app.extensions import db
from app.models.base import BaseModel


class Opportunity(BaseModel):
    """An incoming request/lead that may (or may not) turn into a real Sale."""

    __tablename__ = "opportunities"

    STAGE_NEW = "new"
    STAGE_CONTACTED = "contacted"
    STAGE_QUOTED = "quoted"
    STAGE_WON = "won"
    STAGE_LOST = "lost"

    STAGES = [STAGE_NEW, STAGE_CONTACTED, STAGE_QUOTED, STAGE_WON, STAGE_LOST]
    OPEN_STAGES = [STAGE_NEW, STAGE_CONTACTED, STAGE_QUOTED]

    SOURCE_INSTAGRAM = "instagram_dm"
    SOURCE_WEBSITE = "website"
    SOURCE_REFERRAL = "referral"
    SOURCE_OTHER = "other"

    SOURCES = [SOURCE_INSTAGRAM, SOURCE_WEBSITE, SOURCE_REFERRAL, SOURCE_OTHER]

    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True)
    quantity_requested = db.Column(db.Integer, nullable=False, default=1)
    stage = db.Column(db.String(20), nullable=False, default=STAGE_NEW)
    source = db.Column(db.String(20), nullable=False, default=SOURCE_OTHER)
    notes = db.Column(db.String(255), nullable=True)
    sale_id = db.Column(db.Integer, db.ForeignKey("sales.id"), nullable=True)

    customer = db.relationship("Customer")
    product = db.relationship("Product")
    sale = db.relationship("Sale", back_populates="opportunity")

    @property
    def is_open(self) -> bool:
        return self.stage in self.OPEN_STAGES

    def __repr__(self) -> str:
        return f"<Opportunity #{self.id} customer_id={self.customer_id} stage={self.stage}>"
