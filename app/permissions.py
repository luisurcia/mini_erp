from functools import wraps

from flask import abort
from flask_login import current_user

from app.models.user import User


def roles_required(*roles: str):
    """Restrict a view to users whose role is one of `roles`."""

    def decorator(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                abort(403)
            return view(*args, **kwargs)

        return wrapped_view

    return decorator


def admin_required(view):
    return roles_required(User.ROLE_ADMIN)(view)


def module_required(module: str):
    """Restrict a view to users whose role has access to `module` — used
    on every route (read and write) of a module's blueprint, so a role
    without access can't reach it directly by URL either, not just from
    a hidden nav link. See #31."""

    def decorator(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):
            if not current_user.is_authenticated or not current_user.can_access(module):
                abort(403)
            return view(*args, **kwargs)

        return wrapped_view

    return decorator
