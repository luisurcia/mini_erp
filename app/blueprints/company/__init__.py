from flask import Blueprint

bp = Blueprint("company", __name__, template_folder="../../templates/company")

from app.blueprints.company import routes  # noqa: E402,F401
