from flask import Flask, render_template

from app.cli import register_cli
from app.extensions import bootstrap, db, login_manager
from config import Config


def create_app(config_class: type = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    bootstrap.init_app(app)

    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("errors/403.html"), 403

    _register_blueprints(app)
    register_cli(app)

    return app


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
