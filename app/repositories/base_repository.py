from typing import Generic, TypeVar

from app.extensions import db

ModelType = TypeVar("ModelType")


class Repository(Generic[ModelType]):
    """Generic CRUD data-access wrapper around a SQLAlchemy model."""

    model: type[ModelType]

    def __init__(self, model: type[ModelType]):
        self.model = model

    def get(self, entity_id: int) -> ModelType | None:
        return db.session.get(self.model, entity_id)

    def get_all(self):
        return self.model.query.order_by(self.model.id).all()

    def add(self, entity: ModelType) -> ModelType:
        db.session.add(entity)
        return entity

    def delete(self, entity: ModelType) -> None:
        db.session.delete(entity)

    def commit(self) -> None:
        db.session.commit()
