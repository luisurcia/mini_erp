import pytest

from app.exceptions import DuplicateUsernameError, LastAdminError
from app.models.user import User
from app.services.user_service import UserService


def test_create_user_sets_role_and_hashes_password(app):
    service = UserService()
    user = service.create_user("editor1", "password123", User.ROLE_EDITOR)
    assert user.role == User.ROLE_EDITOR
    assert user.check_password("password123")


def test_create_user_duplicate_username_raises(app):
    service = UserService()
    service.create_user("dupe", "password123", User.ROLE_VIEWER)
    with pytest.raises(DuplicateUsernameError):
        service.create_user("dupe", "otherpass", User.ROLE_EDITOR)


def test_update_user_changes_username_and_role(app):
    service = UserService()
    user = service.create_user("original", "password123", User.ROLE_VIEWER)
    service.update_user(user, username="renamed", role=User.ROLE_EDITOR)
    assert user.username == "renamed"
    assert user.role == User.ROLE_EDITOR


def test_update_user_password_only_changes_when_provided(app):
    service = UserService()
    user = service.create_user("pwtest", "password123", User.ROLE_VIEWER)
    service.update_user(user, username="pwtest", role=User.ROLE_VIEWER, password=None)
    assert user.check_password("password123")

    service.update_user(user, username="pwtest", role=User.ROLE_VIEWER, password="newpass456")
    assert user.check_password("newpass456")


def test_delete_user_removes_it(app):
    service = UserService()
    admin = service.create_user("admin1", "password123", User.ROLE_ADMIN)
    victim = service.create_user("victim", "password123", User.ROLE_VIEWER)
    service.delete_user(victim)
    assert User.query.filter_by(username="victim").first() is None
    assert User.query.filter_by(username="admin1").first() is not None


def test_cannot_demote_last_admin(app):
    service = UserService()
    admin = service.create_user("sole_admin", "password123", User.ROLE_ADMIN)
    with pytest.raises(LastAdminError):
        service.update_user(admin, username="sole_admin", role=User.ROLE_EDITOR)


def test_cannot_delete_last_admin(app):
    service = UserService()
    admin = service.create_user("sole_admin", "password123", User.ROLE_ADMIN)
    with pytest.raises(LastAdminError):
        service.delete_user(admin)


def test_can_demote_admin_when_another_admin_remains(app):
    service = UserService()
    admin1 = service.create_user("admin1", "password123", User.ROLE_ADMIN)
    service.create_user("admin2", "password123", User.ROLE_ADMIN)
    service.update_user(admin1, username="admin1", role=User.ROLE_EDITOR)
    assert admin1.role == User.ROLE_EDITOR
