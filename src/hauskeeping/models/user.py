from datetime import datetime, timezone

from flask_login import UserMixin

from ..extensions import db


class User(UserMixin, db.Model):
    """
    Zentrale Tabelle fuer alle registrierten User.

    Unterstuetzt zwei Rollen: ``member`` (Standard) und ``hausmeister`` (Admin).
    """

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="member")

    # Notification-Einstellungen
    email_notifications_enabled = db.Column(db.Boolean, default=False)
    email_notification_day = db.Column(db.Integer, default=0)  # 0=Mo, 6=So
    push_notifications_enabled = db.Column(db.Boolean, default=False)
    overdue_reminders_enabled = db.Column(db.Boolean, default=True)

    # Beziehungen
    invited_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    inviter = db.relationship(
        "User", remote_side=[id], backref="invited_users", foreign_keys=[invited_by]
    )
    tasks_created = db.relationship(
        "Task", backref="creator", foreign_keys="Task.created_by"
    )
    tasks_assigned = db.relationship(
        "Task", backref="assignee", foreign_keys="Task.assigned_to"
    )
    tasks_completed = db.relationship(
        "Task", backref="completer", foreign_keys="Task.completed_by"
    )
    shopping_items = db.relationship("ShoppingListItem", backref="added_by_user")
    push_subscriptions = db.relationship(
        "PushSubscription", backref="user", cascade="all, delete-orphan"
    )

    @property
    def is_hausmeister(self):
        """
        Prueft, ob der User die Rolle Hausmeister hat.

        :return: True wenn Hausmeister
        :rtype: bool
        """
        return self.role == "hausmeister"

    def __repr__(self):
        return f"<User {self.username}>"


class InviteCode(db.Model):
    """
    Einladungscodes, die von Hausmeistern generiert werden.

    Jeder Code ist einmalig verwendbar und hat ein Ablaufdatum.
    """

    __tablename__ = "invite_codes"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(36), unique=True, nullable=False)
    created_by = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    expires_at = db.Column(db.DateTime, nullable=False)
    used_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    used_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    creator = db.relationship("User", foreign_keys=[created_by], backref="created_invites")
    redeemer = db.relationship("User", foreign_keys=[used_by])

    @property
    def is_valid(self):
        """
        Prueft, ob der Invite-Code noch gueltig ist.

        :return: True wenn aktiv und nicht abgelaufen
        :rtype: bool
        """
        now = datetime.now(timezone.utc)
        expires = self.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return self.is_active and expires > now

    def __repr__(self):
        return f"<InviteCode {self.code[:8]}...>"
