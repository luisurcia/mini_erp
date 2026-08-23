from app.exceptions import DuplicateUsernameError, LastAdminError
from app.models.user import User
from app.repositories.user_repository import UserRepository


class UserService:
    """Owns user-management rules: unique usernames, and guarding against
    ever removing the last remaining admin account."""

    def __init__(self, user_repo: UserRepository | None = None):
        self.user_repo = user_repo or UserRepository()

    def create_user(self, username: str, password: str, role: str) -> User:
        self._ensure_username_available(username)

        user = User(username=username, role=role)
        user.set_password(password)
        self.user_repo.add(user)
        self.user_repo.commit()
        return user

    def update_user(
        self, user: User, username: str, role: str, password: str | None = None
    ) -> User:
        self._ensure_username_available(username, ignore_user_id=user.id)

        if user.role == User.ROLE_ADMIN and role != User.ROLE_ADMIN:
            self._ensure_not_last_admin()

        user.username = username
        user.role = role
        if password:
            user.set_password(password)
        self.user_repo.commit()
        return user

    def delete_user(self, user: User) -> None:
        if user.role == User.ROLE_ADMIN:
            self._ensure_not_last_admin()
        self.user_repo.delete(user)
        self.user_repo.commit()

    def _ensure_username_available(self, username: str, ignore_user_id: int | None = None) -> None:
        existing = self.user_repo.get_by_username(username)
        if existing is not None and existing.id != ignore_user_id:
            raise DuplicateUsernameError(f"Username '{username}' is already taken.")

    def _ensure_not_last_admin(self) -> None:
        if self.user_repo.count_by_role(User.ROLE_ADMIN) <= 1:
            raise LastAdminError("At least one admin account must remain.")
