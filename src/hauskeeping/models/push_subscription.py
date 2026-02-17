from datetime import datetime, timezone

from ..extensions import db


class PushSubscription(db.Model):
    """
    Browser-seitige Push-Subscriptions fuer Web Push Notifications.

    Speichert die vom Browser generierten Keys und Endpoints
    fuer jeden registrierten User/Geraet.
    """

    __tablename__ = "push_subscriptions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    endpoint = db.Column(db.Text, nullable=False)
    p256dh = db.Column(db.Text, nullable=False)
    auth = db.Column(db.Text, nullable=False)
    platform = db.Column(db.String(20), nullable=True)
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f"<PushSubscription user={self.user_id}>"
