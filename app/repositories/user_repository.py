from app.models.user import User
from app.repositories.base_repository import Repository


class UserRepository(Repository[User]):
    def __init__(self):
        super().__init__(User)

    def get_by_username(self, username: str) -> User | None:
        return User.query.filter_by(username=username).first()

    def count_by_role(self, role: str) -> int:
        return User.query.filter_by(role=role).count()
