from flask import Blueprint

bp = Blueprint("users", __name__, template_folder="../../templates/users")

from app.blueprints.users import routes  # noqa: E402,F401
