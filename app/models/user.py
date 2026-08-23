from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models.base import BaseModel


class User(BaseModel, UserMixin):
    __tablename__ = "users"

    ROLE_ADMIN = "admin"
    ROLE_EDITOR = "editor"
    ROLE_VIEWER = "viewer"
    ROLES = [ROLE_ADMIN, ROLE_EDITOR, ROLE_VIEWER]

    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=ROLE_ADMIN)

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    @property
    def is_admin(self) -> bool:
        return self.role == self.ROLE_ADMIN

    @property
    def can_edit(self) -> bool:
        """Admins and editors can create/update records; viewers cannot."""
        return self.role in (self.ROLE_ADMIN, self.ROLE_EDITOR)

    def __repr__(self) -> str:
        return f"<User {self.username}>"
