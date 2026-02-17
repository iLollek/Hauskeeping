from datetime import datetime, timedelta, timezone

from flask import Blueprint, render_template, request
from flask_login import current_user, login_required

from ..models.task import Task

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
@login_required
def dashboard():
    """
    Kalender-Dashboard als Hauptseite.

    Zeigt die Wochenansicht mit allen Aufgaben der aktuellen Woche.
    Per Query-Parameter ``week_offset`` kann zwischen Wochen navigiert werden.
    """
    week_offset = request.args.get("week_offset", 0, type=int)

    today = datetime.now(timezone.utc).date()
    # Montag der aktuellen Woche berechnen
    monday = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
    sunday = monday + timedelta(days=6)

    tasks = (
        Task.query.filter(Task.due_date >= monday, Task.due_date <= sunday)
        .order_by(Task.due_date, Task.priority.desc())
        .all()
    )

    # Aufgaben nach Wochentag gruppieren
    days = []
    day_names = [
        "Montag",
        "Dienstag",
        "Mittwoch",
        "Donnerstag",
        "Freitag",
        "Samstag",
        "Sonntag",
    ]
    for i in range(7):
        day_date = monday + timedelta(days=i)
        day_tasks = [t for t in tasks if t.due_date == day_date]
        days.append(
            {
                "name": day_names[i],
                "date": day_date,
                "tasks": day_tasks,
                "is_today": day_date == today,
            }
        )

    return render_template(
        "main/dashboard.html",
        days=days,
        week_offset=week_offset,
        monday=monday,
        sunday=sunday,
        current_user=current_user,
    )
