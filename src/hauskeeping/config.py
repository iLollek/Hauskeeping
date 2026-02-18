import os


class Config:
    """
    Zentrale Konfigurationsklasse fuer Hauskeeping.

    Liest alle Einstellungen aus Umgebungsvariablen.
    Fallback-Werte sind fuer lokale Entwicklung vorgesehen.
    """

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")

    # Datenbank
    _db_url = os.getenv("DATABASE_URL", "sqlite:///hauskeeping.db")
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Reverse Proxy
    USE_PROXY = os.getenv("USE_PROXY", "false").lower() == "true"
    PROXY_PREFIX = os.getenv("PROXY_PREFIX", "")

    # Mail
    MAIL_SERVER = os.getenv("MAIL_SERVER")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "false").lower() == "true"
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER")

    # VAPID (Web Push)
    VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY")
    VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY")
    VAPID_CLAIM_EMAIL = os.getenv("VAPID_CLAIM_EMAIL")
