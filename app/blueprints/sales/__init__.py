from flask import Blueprint

bp = Blueprint("sales", __name__, template_folder="../../templates/sales")

from app.blueprints.sales import routes  # noqa: E402,F401
