from flask import Blueprint

bp = Blueprint(
    "opportunities", __name__, template_folder="../../templates/opportunities"
)

from app.blueprints.opportunities import routes  # noqa: E402,F401
