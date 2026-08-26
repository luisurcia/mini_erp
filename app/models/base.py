from datetime import UTC, datetime

from app.extensions import db


def utcnow() -> datetime:
    return datetime.now(UTC)


class BaseModel(db.Model):
    """Shared columns/behavior for all domain models."""

    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
