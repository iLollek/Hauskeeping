import re
from datetime import datetime, timezone

from ..extensions import db


class TaskCategory(db.Model):
    """
    Benutzerdefinierte Kategorien fuer Aufgaben.

    Jede Kategorie hat einen Namen, einen URL-sicheren Slug und eine Farbe.
    """

    __tablename__ = "task_categories"

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
        return f"<TaskCategory {self.name}>"


class Task(db.Model):
    """
    Haushaltsaufgaben – das Kernmodell von Hauskeeping.

    Unterstuetzt Zuweisung an User, Kategorien und optionale
    Wiederholungsregeln.
    """

    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.Date, nullable=False)
    is_done = db.Column(db.Boolean, default=False)
    category_id = db.Column(
        db.Integer, db.ForeignKey("task_categories.id"), nullable=True
    )
    assigned_to = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    recurrence_rule = db.Column(db.String(50), nullable=True)
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    category = db.relationship("TaskCategory", backref="tasks")

    @property
    def is_overdue(self):
        """
        Prueft, ob die Aufgabe ueberfaellig ist.

        :return: True wenn nicht erledigt und Faelligkeitsdatum ueberschritten
        :rtype: bool
        """
        if self.is_done:
            return False
        return self.due_date < datetime.now(timezone.utc).date()

    def __repr__(self):
        return f"<Task {self.title}>"
