from flask import Flask, render_template
from flask_babel import get_locale

from app.cli import register_cli
from app.extensions import babel, bootstrap, db, login_manager
from config import Config


def create_app(config_class: type = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    bootstrap.init_app(app)
    babel.init_app(app, locale_selector=_select_locale)

    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("errors/403.html"), 403

    @app.get("/health")
    def health_check():
        """Unauthenticated liveness check — CI curls this after a deploy
        restart to confirm the app actually came back up before going green."""
        try:
            db.session.execute(db.text("SELECT 1"))
            db_status = "ok"
        except Exception:
            app.logger.critical("health_check_db_failure", exc_info=True)
            db_status = "error"
        status_code = 200 if db_status == "ok" else 503
        return {"status": db_status, "database": db_status}, status_code

    @app.context_processor
    def inject_locale():
        from app.models.company import Company

        settings = Company.get_settings()
        return {
            "current_locale": str(get_locale()),
            # Product name in the navbar / page title / login (#97).
            "brand_name": settings.brand_name,
            # Exposed for client-side money formatting (Intl.NumberFormat)
            # in the few templates that compute totals in JS. Server-side
            # rendering uses format_money() instead.
            "currency_symbol": settings.currency_symbol,
            "currency_decimals": settings.currency_decimals,
        }

    from app.display import format_money, product_label, product_short_label

    app.jinja_env.globals["sale_status_label"] = _sale_status_label
    app.jinja_env.globals["payment_status_label"] = _payment_status_label
    app.jinja_env.globals["user_role_label"] = _user_role_label
    app.jinja_env.globals["product_label"] = product_label
    app.jinja_env.globals["product_short_label"] = product_short_label
    app.jinja_env.globals["format_money"] = format_money
    app.jinja_env.globals["stock_movement_reason_label"] = _stock_movement_reason_label

    _register_blueprints(app)
    register_cli(app)

    return app


def _select_locale() -> str:
    from flask import has_request_context
    from flask_login import current_user

    from app.models.company import Company

    # A logged-in user's own choice wins; otherwise the company default.
    # The request-context guard keeps this safe for non-request callers
    # (CLI, tests) where current_user isn't available. See #43.
    if (
        has_request_context()
        and current_user.is_authenticated
        and current_user.language
    ):
        return current_user.language
    return Company.get_settings().language


def _sale_status_label(status: str) -> str:
    from flask_babel import gettext as _

    from app.models.sales import Sale

    labels = {
        Sale.STATUS_COMPLETED: _("Completed"),
        Sale.STATUS_PENDING: _("Pending"),
        Sale.STATUS_CANCELLED: _("Cancelled"),
    }
    return labels.get(status, status)


def _payment_status_label(status: str) -> str:
    from flask_babel import gettext as _

    from app.models.sales import Sale

    labels = {
        Sale.PAYMENT_PAID: _("Paid"),
        Sale.PAYMENT_UNPAID: _("Unpaid"),
    }
    return labels.get(status, status)


def _user_role_label(role: str) -> str:
    from app.blueprints.users.forms import ROLE_LABELS

    return str(ROLE_LABELS.get(role, role))


def _stock_movement_reason_label(reason: str) -> str:
    from flask_babel import gettext as _

    from app.models.inventory import StockMovement

    labels = {
        StockMovement.REASON_RESTOCK: _("Restock"),
        StockMovement.REASON_SALE: _("Sale"),
        StockMovement.REASON_ADJUSTMENT: _("Adjustment"),
        StockMovement.REASON_TRANSFER: _("Transfer"),
    }
    return labels.get(reason, reason)


def _register_blueprints(app: Flask) -> None:
    from app.blueprints.auth import bp as auth_bp
    from app.blueprints.company import bp as company_bp
    from app.blueprints.customers import bp as customers_bp
    from app.blueprints.dashboard import bp as dashboard_bp
    from app.blueprints.inventory import bp as inventory_bp
    from app.blueprints.products import bp as products_bp
    from app.blueprints.purchases import bp as purchases_bp
    from app.blueprints.sales import bp as sales_bp
    from app.blueprints.supplies import bp as supplies_bp
    from app.blueprints.top_customers import bp as top_customers_bp
    from app.blueprints.users import bp as users_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(products_bp, url_prefix="/products")
    app.register_blueprint(inventory_bp, url_prefix="/inventory")
    app.register_blueprint(supplies_bp, url_prefix="/supplies")
    app.register_blueprint(purchases_bp, url_prefix="/purchases")
    app.register_blueprint(sales_bp, url_prefix="/sales")
    app.register_blueprint(top_customers_bp, url_prefix="/top-customers")
    app.register_blueprint(customers_bp, url_prefix="/customers")
    app.register_blueprint(users_bp, url_prefix="/users")
    app.register_blueprint(company_bp, url_prefix="/company")
