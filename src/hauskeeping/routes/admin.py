import uuid
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..models.shopping import ShoppingListItem
from ..models.task import Task
from ..models.user import InviteCode, User

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def hausmeister_required(f):
    """
    Dekorator, der sicherstellt, dass der User die Rolle Hausmeister hat.

    Leitet auf das Dashboard um, wenn der User kein Hausmeister ist.
    """

    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_hausmeister:
            flash("Zugriff verweigert. Nur Hausmeister.", "danger")
            return redirect(url_for("main.dashboard"))
        return f(*args, **kwargs)

    return decorated_function


@admin_bp.route("/invite-codes")
@hausmeister_required
def invite_codes():
    """
    Zeigt alle Invite-Codes an.

    Gruppiert nach aktiv, eingeloest und abgelaufen.
    """
    codes = InviteCode.query.order_by(InviteCode.created_at.desc()).all()
    return render_template("admin/invite_codes.html", codes=codes)


@admin_bp.route("/invite-codes/create", methods=["POST"])
@hausmeister_required
def create_invite_code():
    """Generiert einen neuen Invite-Code mit 7 Tagen Gueltigkeit."""
    expires_days = request.form.get("expires_days", 7, type=int)
    if expires_days < 1:
        expires_days = 7

    code = InviteCode(
        code=str(uuid.uuid4()),
        created_by=current_user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=expires_days),
    )
    db.session.add(code)
    db.session.commit()

    flash(f"Invite-Code erstellt: {code.code}", "success")
    return redirect(url_for("admin.invite_codes"))


@admin_bp.route("/users")
@hausmeister_required
def user_list():
    """Zeigt alle registrierten User an."""
    users = User.query.order_by(User.created_at).all()
    return render_template("admin/users.html", users=users)


@admin_bp.route("/users/<int:user_id>/promote", methods=["POST"])
@hausmeister_required
def promote_user(user_id):
    """
    Ernennt einen User zum Hausmeister.

    :param user_id: ID des Users
    :type user_id: int
    """
    user = db.get_or_404(User, user_id)
    if user.id == current_user.id:
        flash("Du kannst dich nicht selbst befoerdern.", "warning")
        return redirect(url_for("admin.user_list"))

    user.role = "hausmeister"
    db.session.commit()

    flash(f"'{user.username}' ist jetzt Hausmeister.", "success")
    return redirect(url_for("admin.user_list"))


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@hausmeister_required
def delete_user(user_id):
    """
    Entfernt einen User aus dem System.

    :param user_id: ID des zu entfernenden Users
    :type user_id: int
    """
    user = db.get_or_404(User, user_id)
    if user.id == current_user.id:
        flash("Du kannst dich nicht selbst entfernen.", "warning")
        return redirect(url_for("admin.user_list"))

    # Nullable FKs auf NULL setzen
    Task.query.filter_by(assigned_to=user.id).update({"assigned_to": None})
    Task.query.filter_by(completed_by=user.id).update({"completed_by": None})
    InviteCode.query.filter_by(used_by=user.id).update({"used_by": None})
    User.query.filter_by(invited_by=user.id).update({"invited_by": None})

    # NOT NULL FKs: Eintraege dem loeschenden Admin zuweisen
    Task.query.filter_by(created_by=user.id).update({"created_by": current_user.id})
    ShoppingListItem.query.filter_by(added_by=user.id).update({"added_by": current_user.id})
    InviteCode.query.filter_by(created_by=user.id).update({"created_by": current_user.id})

    db.session.delete(user)
    db.session.commit()

    flash(f"Benutzer '{user.username}' wurde entfernt.", "success")
    return redirect(url_for("admin.user_list"))


@admin_bp.route("/push/test", methods=["POST"])
@hausmeister_required
def test_push():
    """
    Sendet eine Test-Push-Benachrichtigung an einen User.

    Erwartet JSON: {"user_id": int, "title": str, "body": str}
    """
    from ..models.push_subscription import PushSubscription
    from ..services.push_service import send_push_to_user

    data = request.get_json()
    if not data:
        return jsonify({"error": "Keine Daten erhalten."}), 400

    user_id = data.get("user_id")
    title = (data.get("title") or "").strip()
    body = (data.get("body") or "").strip()

    if not user_id or not title or not body:
        return jsonify({"error": "user_id, title und body sind erforderlich."}), 400

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "Benutzer nicht gefunden."}), 404

    sub_count = PushSubscription.query.filter_by(user_id=user.id).count()
    if sub_count == 0:
        return jsonify({"error": f"{user.username} hat keine aktiven Push-Subscriptions."}), 400

    if not user.push_notifications_enabled:
        return jsonify({"error": f"{user.username} hat Push-Benachrichtigungen deaktiviert."}), 400

    try:
        send_push_to_user(user, title, body)
    except Exception as exc:
        return jsonify({"error": f"Sendefehler: {exc}"}), 500

    return jsonify({"success": True, "message": f"Push an {user.username} gesendet ({sub_count} Gerät(e))."})
