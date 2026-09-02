from flask import Blueprint

bp = Blueprint("purchases", __name__, template_folder="../../templates/purchases")

from app.blueprints.purchases import routes  # noqa: E402,F401
