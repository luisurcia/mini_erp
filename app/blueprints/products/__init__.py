from flask import Blueprint

bp = Blueprint("products", __name__, template_folder="../../templates/products")

from app.blueprints.products import routes  # noqa: E402,F401
