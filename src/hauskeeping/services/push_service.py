import json
import logging

from pywebpush import WebPushException, webpush

from ..extensions import db
from ..models.push_subscription import PushSubscription
from ..models.user import User

logger = logging.getLogger(__name__)


def send_push_notification(subscription, payload, vapid_private_key, vapid_claims):
    """
    Sendet eine einzelne Web-Push-Nachricht an eine Subscription.

    Bei HTTP 410 (Gone) wird die Subscription automatisch aus der DB geloescht.

    :param subscription: PushSubscription-Objekt aus der Datenbank
    :param payload: Dict mit Notification-Daten (title, body, icon, url)
    :param vapid_private_key: VAPID Private Key aus der Config
    :param vapid_claims: Dict mit ``sub`` (mailto:-Adresse)
    :return: True bei Erfolg, False bei Fehler
    """
    subscription_info = {
        "endpoint": subscription.endpoint,
        "keys": {
            "p256dh": subscription.p256dh,
            "auth": subscription.auth,
        },
    }

    try:
        webpush(
            subscription_info=subscription_info,
            data=json.dumps(payload),
            vapid_private_key=vapid_private_key,
            vapid_claims=vapid_claims,
        )
        return True
    except WebPushException as e:
        if hasattr(e, "response") and e.response is not None:
            status = e.response.status_code
            if status == 410:
                logger.info(
                    "Subscription %d abgelaufen (410 Gone), wird geloescht.",
                    subscription.id,
                )
                db.session.delete(subscription)
                db.session.commit()
                return False
        logger.exception(
            "Fehler beim Senden der Push-Nachricht an Subscription %d",
            subscription.id,
        )
        return False


def send_push_to_user(user, title, body, url=None):
    """
    Sendet eine Push-Nachricht an alle registrierten Geraete eines Users.

    Benoetigt einen aktiven Flask-App-Kontext fuer den Zugriff auf die Config.

    :param user: User-Objekt oder User-ID
    :param title: Titel der Benachrichtigung
    :param body: Text der Benachrichtigung
    :param url: Optionale URL, die beim Klick geoeffnet wird
    """
    from flask import current_app

    if isinstance(user, int):
        user = db.session.get(User, user)

    if not user or not user.push_notifications_enabled:
        return

    subscriptions = PushSubscription.query.filter_by(user_id=user.id).all()
    if not subscriptions:
        return

    vapid_private_key = current_app.config.get("VAPID_PRIVATE_KEY")
    vapid_claim_email = current_app.config.get("VAPID_CLAIM_EMAIL")

    if not vapid_private_key or not vapid_claim_email:
        logger.warning("VAPID-Keys nicht konfiguriert. Push-Nachricht wird nicht gesendet.")
        return

    vapid_claims = {"sub": f"mailto:{vapid_claim_email}"}

    payload = {
        "title": title,
        "body": body,
    }
    if url:
        payload["url"] = url

    for sub in subscriptions:
        send_push_notification(sub, payload, vapid_private_key, vapid_claims)
