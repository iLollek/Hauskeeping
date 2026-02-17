from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..extensions import bcrypt, db

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
