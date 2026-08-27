from flask import Blueprint

bp = Blueprint("supplies", __name__, template_folder="../../templates/supplies")

from app.blueprints.supplies import routes  # noqa: E402,F401
