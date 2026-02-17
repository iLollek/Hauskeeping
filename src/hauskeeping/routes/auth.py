from datetime import datetime, timezone

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from ..extensions import bcrypt, db
from ..models.user import InviteCode, User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Login-Seite und -Verarbeitung.

    GET: Zeigt das Login-Formular an.
    POST: Validiert Benutzername und Passwort, startet die Session.
    """
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            next_page = request.args.get("next")
            return redirect(next_page or url_for("main.dashboard"))

        flash("Benutzername oder Passwort falsch.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """
    Registrierungs-Seite mit Invite-Code-Validierung.

    GET: Zeigt das Registrierungsformular an.
    POST: Validiert den Invite-Code und erstellt einen neuen User.
    """
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        invite_code = request.form.get("invite_code", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")

        # Validierung
        errors = []
        if not invite_code:
            errors.append("Invite-Code ist erforderlich.")
        if not username or len(username) < 3:
            errors.append("Benutzername muss mindestens 3 Zeichen lang sein.")
        if not password or len(password) < 6:
            errors.append("Passwort muss mindestens 6 Zeichen lang sein.")
        if password != password_confirm:
            errors.append("Passwoerter stimmen nicht ueberein.")

        if User.query.filter_by(username=username).first():
            errors.append("Dieser Benutzername ist bereits vergeben.")

        # Invite-Code pruefen
        invite = InviteCode.query.filter_by(code=invite_code).first()
        if not invite or not invite.is_valid:
            errors.append("Ungueltiger oder abgelaufener Invite-Code.")

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("auth/register.html")

        # User erstellen
        pw_hash = bcrypt.generate_password_hash(password).decode("utf-8")
        user = User(
            username=username,
            password_hash=pw_hash,
            role="member",
            invited_by=invite.created_by,
        )
        db.session.add(user)
        db.session.flush()

        # Invite-Code einloesen
        invite.used_by = user.id
        invite.used_at = datetime.now(timezone.utc)
        invite.is_active = False
        db.session.commit()

        flash("Registrierung erfolgreich! Du kannst dich jetzt anmelden.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/logout")
@login_required
def logout():
    """Meldet den aktuellen User ab und leitet zum Login weiter."""
    logout_user()
    flash("Du wurdest abgemeldet.", "info")
    return redirect(url_for("auth.login"))
