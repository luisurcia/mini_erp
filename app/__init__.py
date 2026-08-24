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

    @app.context_processor
    def inject_locale():
        return {"current_locale": str(get_locale())}

    app.jinja_env.globals["sale_status_label"] = _sale_status_label
    app.jinja_env.globals["opportunity_stage_label"] = _opportunity_stage_label
    app.jinja_env.globals["opportunity_source_label"] = _opportunity_source_label
    app.jinja_env.globals["user_role_label"] = _user_role_label

    _register_blueprints(app)
    register_cli(app)

    return app


def _select_locale() -> str:
    from app.models.company import Company

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


def _opportunity_stage_label(stage: str) -> str:
    from flask_babel import gettext as _

    from app.models.opportunity import Opportunity

    labels = {
        Opportunity.STAGE_NEW: _("New"),
        Opportunity.STAGE_CONTACTED: _("Contacted"),
        Opportunity.STAGE_QUOTED: _("Quoted"),
        Opportunity.STAGE_WON: _("Won"),
        Opportunity.STAGE_LOST: _("Lost"),
    }
    return labels.get(stage, stage)


def _opportunity_source_label(source: str) -> str:
    from flask_babel import gettext as _

    from app.models.opportunity import Opportunity

    labels = {
        Opportunity.SOURCE_INSTAGRAM: _("Instagram DM"),
        Opportunity.SOURCE_WEBSITE: _("Website"),
        Opportunity.SOURCE_REFERRAL: _("Referral"),
        Opportunity.SOURCE_OTHER: _("Other"),
    }
    return labels.get(source, source)


def _user_role_label(role: str) -> str:
    from app.blueprints.users.forms import ROLE_LABELS

    return str(ROLE_LABELS.get(role, role))


def _register_blueprints(app: Flask) -> None:
    from app.blueprints.auth import bp as auth_bp
    from app.blueprints.company import bp as company_bp
    from app.blueprints.dashboard import bp as dashboard_bp
    from app.blueprints.inventory import bp as inventory_bp
    from app.blueprints.opportunities import bp as opportunities_bp
    from app.blueprints.sales import bp as sales_bp
    from app.blueprints.users import bp as users_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(inventory_bp, url_prefix="/inventory")
    app.register_blueprint(sales_bp, url_prefix="/sales")
    app.register_blueprint(opportunities_bp, url_prefix="/opportunities")
    app.register_blueprint(users_bp, url_prefix="/users")
    app.register_blueprint(company_bp, url_prefix="/company")
