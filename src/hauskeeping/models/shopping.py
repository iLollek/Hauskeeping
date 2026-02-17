from datetime import datetime, timezone

from ..extensions import db


class ShoppingListItem(db.Model):
    """
    Eintraege der gemeinsamen Einkaufsliste.

    Artikel koennen kategorisiert und abgehakt werden.
    """

    __tablename__ = "shopping_list_items"

    CATEGORIES = [
        ("lebensmittel", "Lebensmittel"),
        ("haushalt", "Haushalt"),
        ("drogerie", "Drogerie"),
        ("sonstiges", "Sonstiges"),
    ]

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=True, default="sonstiges")
    is_checked = db.Column(db.Boolean, default=False)
    added_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f"<ShoppingListItem {self.name}>"
