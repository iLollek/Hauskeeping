import os

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import Config
from .extensions import bcrypt, db, login_manager, mail, migrate


def create_app():
    """
    Application Factory fuer Hauskeeping.

    Erstellt und konfiguriert die Flask-App, initialisiert Extensions,
    registriert Blueprints und CLI-Commands.

    :return: Die konfigurierte Flask-App
    :rtype: Flask
    """
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )
    app.config.from_object(Config)

    # Extensions initialisieren
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)

    # Proxy-Konfiguration
    if app.config["USE_PROXY"]:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
        app.config["APPLICATION_ROOT"] = app.config["PROXY_PREFIX"]

    # Models importieren (fuer Flask-Migrate)
    from . import models  # noqa: F401

    # User-Loader fuer Flask-Login
    from .models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Blueprints registrieren
    from .routes import register_blueprints

    register_blueprints(app)

    # CLI-Commands registrieren
    from .cli import register_commands

    register_commands(app)

    # Scheduler initialisieren (nur im Hauptprozess, nicht im Reloader)
    import os

    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
        from .scheduler import init_scheduler

        init_scheduler(app)

    return app
