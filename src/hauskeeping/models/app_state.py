from ..extensions import db


class AppState(db.Model):
    """
    Einfacher Key-Value-Speicher fuer internen App-Zustand.

    Wird z.B. genutzt, um den Zeitpunkt des letzten Recurrence-Spawns
    zu verfolgen, damit Ausfallzeiten (Downtimes) korrekt behandelt werden.
    """

    __tablename__ = "app_state"

    key = db.Column(db.String(50), primary_key=True)
    value = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f"<AppState {self.key}={self.value}>"
