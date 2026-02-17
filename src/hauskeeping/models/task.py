from datetime import datetime, timezone

from ..extensions import db


class Task(db.Model):
    """
    Haushaltsaufgaben – das Kernmodell von Hauskeeping.

    Unterstuetzt Prioritaeten, Zuweisung an User und optionale
    Wiederholungsregeln.
    """

    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.Date, nullable=False)
    is_done = db.Column(db.Boolean, default=False)
    priority = db.Column(db.String(20), nullable=False, default="medium")
    assigned_to = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    recurrence_rule = db.Column(db.String(50), nullable=True)
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

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

    @property
    def priority_color(self):
        """
        Gibt die Bootstrap-Farbklasse fuer die Prioritaet zurueck.

        :return: Bootstrap-Farbklasse
        :rtype: str
        """
        colors = {
            "high": "danger",
            "medium": "warning",
            "low": "success",
        }
        return colors.get(self.priority, "secondary")

    def __repr__(self):
        return f"<Task {self.title}>"
