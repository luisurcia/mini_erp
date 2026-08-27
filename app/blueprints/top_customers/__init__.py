from flask import Blueprint

bp = Blueprint("top_customers", __name__, template_folder="../../templates/top_customers")

from app.blueprints.top_customers import routes  # noqa: E402,F401
