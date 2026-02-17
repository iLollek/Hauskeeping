from flask import Flask

from .admin import admin_bp
from .auth import auth_bp
from .main import main_bp
from .shopping import shopping_bp
from .tasks import tasks_bp


def register_blueprints(app: Flask):
    """
    Registriert alle Blueprints in der Flask-App.

    :param app: Die Flask-App-Instanz
    :type app: Flask
    """
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(shopping_bp)
    app.register_blueprint(admin_bp)
