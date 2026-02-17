import re
from datetime import datetime, timezone

from ..extensions import db


class ShoppingCategory(db.Model):
    """
    Benutzerdefinierte Kategorien fuer die Einkaufsliste.

    Jede Kategorie hat einen Namen, einen URL-sicheren Slug und eine Farbe.
    """

    __tablename__ = "shopping_categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    color = db.Column(db.String(7), nullable=False, default="#6c757d")
    position = db.Column(db.Integer, nullable=False, default=0)

    @staticmethod
    def make_slug(name):
        """Erzeugt einen URL-sicheren Slug aus einem Kategorienamen."""
        slug = name.lower().strip()
        slug = re.sub(r"[äÄ]", "ae", slug)
        slug = re.sub(r"[öÖ]", "oe", slug)
        slug = re.sub(r"[üÜ]", "ue", slug)
        slug = re.sub(r"ß", "ss", slug)
        slug = re.sub(r"[^a-z0-9]+", "-", slug)
        slug = slug.strip("-")
        return slug or "kategorie"

    def __repr__(self):
        return f"<ShoppingCategory {self.name}>"


class ShoppingListItem(db.Model):
    """
    Eintraege der gemeinsamen Einkaufsliste.

    Artikel koennen kategorisiert und abgehakt werden.
    """

    __tablename__ = "shopping_list_items"

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
