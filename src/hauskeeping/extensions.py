from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
bcrypt = Bcrypt()
mail = Mail()

login_manager.login_view = "auth.login"
login_manager.login_message = "Bitte melde dich an, um fortzufahren."
login_manager.login_message_category = "warning"
