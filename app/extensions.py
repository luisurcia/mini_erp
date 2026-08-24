from flask_babel import Babel
from flask_bootstrap import Bootstrap5
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
login_manager = LoginManager()
bootstrap = Bootstrap5()
babel = Babel()

login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"
