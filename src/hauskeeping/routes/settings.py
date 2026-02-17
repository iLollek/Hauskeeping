from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..extensions import bcrypt, db
from ..models.push_subscription import PushSubscription

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


@settings_bp.route("/")
@login_required
def index():
    """Einstellungsseite anzeigen."""
    return render_template("settings/index.html")


@settings_bp.route("/email", methods=["POST"])
@login_required
def update_email():
    """E-Mail-Adresse aendern."""
    email = request.form.get("email", "").strip()

    if not email:
        current_user.email = None
    else:
        current_user.email = email

    db.session.commit()
    flash("E-Mail-Adresse wurde aktualisiert.", "success")
    return redirect(url_for("settings.index"))


@settings_bp.route("/password", methods=["POST"])
@login_required
def update_password():
    """Passwort aendern."""
    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    new_password_confirm = request.form.get("new_password_confirm", "")

    if not bcrypt.check_password_hash(current_user.password_hash, current_password):
        flash("Aktuelles Passwort ist falsch.", "danger")
        return redirect(url_for("settings.index"))

    if len(new_password) < 6:
        flash("Neues Passwort muss mindestens 6 Zeichen lang sein.", "danger")
        return redirect(url_for("settings.index"))

    if new_password != new_password_confirm:
        flash("Passwoerter stimmen nicht ueberein.", "danger")
        return redirect(url_for("settings.index"))

    current_user.password_hash = bcrypt.generate_password_hash(new_password).decode(
        "utf-8"
    )
    db.session.commit()
    flash("Passwort wurde geaendert.", "success")
    return redirect(url_for("settings.index"))


@settings_bp.route("/notifications", methods=["POST"])
@login_required
def update_notifications():
    """Benachrichtigungseinstellungen speichern."""
    current_user.email_notifications_enabled = (
        "email_notifications_enabled" in request.form
    )
    current_user.email_notification_day = request.form.get(
        "email_notification_day", 0, type=int
    )
    current_user.push_notifications_enabled = (
        "push_notifications_enabled" in request.form
    )

    db.session.commit()
    flash("Benachrichtigungseinstellungen wurden gespeichert.", "success")
    return redirect(url_for("settings.index"))


@settings_bp.route("/push/vapid-public-key")
@login_required
def vapid_public_key():
    """VAPID Public Key fuer die Browser-seitige Push-Registrierung."""
    key = current_app.config.get("VAPID_PUBLIC_KEY", "")
    return jsonify({"public_key": key})


@settings_bp.route("/push/subscribe", methods=["POST"])
@login_required
def push_subscribe():
    """Browser-Push-Subscription registrieren."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Keine Daten erhalten."}), 400

    endpoint = data.get("endpoint")
    p256dh = data.get("keys", {}).get("p256dh")
    auth = data.get("keys", {}).get("auth")
    platform = data.get("platform", "unknown")

    if not endpoint or not p256dh or not auth:
        return jsonify({"error": "Unvollstaendige Subscription-Daten."}), 400

    # Bestehende Subscription mit gleichem Endpoint aktualisieren oder neu anlegen
    existing = PushSubscription.query.filter_by(
        user_id=current_user.id, endpoint=endpoint
    ).first()

    if existing:
        existing.p256dh = p256dh
        existing.auth = auth
        existing.platform = platform
    else:
        sub = PushSubscription(
            user_id=current_user.id,
            endpoint=endpoint,
            p256dh=p256dh,
            auth=auth,
            platform=platform,
        )
        db.session.add(sub)

    # Push automatisch aktivieren wenn erste Subscription registriert wird
    current_user.push_notifications_enabled = True
    db.session.commit()

    return jsonify({"success": True})


@settings_bp.route("/push/unsubscribe", methods=["POST"])
@login_required
def push_unsubscribe():
    """Browser-Push-Subscription entfernen."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Keine Daten erhalten."}), 400

    endpoint = data.get("endpoint")
    if endpoint:
        sub = PushSubscription.query.filter_by(
            user_id=current_user.id, endpoint=endpoint
        ).first()
        if sub:
            db.session.delete(sub)

    # Wenn keine Subscriptions mehr vorhanden, Push deaktivieren
    remaining = PushSubscription.query.filter_by(user_id=current_user.id).count()
    if remaining == 0:
        current_user.push_notifications_enabled = False

    db.session.commit()
    return jsonify({"success": True})
