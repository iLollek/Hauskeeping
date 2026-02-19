from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, render_template, request, send_from_directory, url_for
from flask_login import current_user, login_required

from ..models.task import Task

main_bp = Blueprint("main", __name__)


@main_bp.route("/sw.js")
def service_worker():
    """Service Worker vom Root-Pfad ausliefern (Scope muss / sein)."""
    return send_from_directory(
        main_bp.root_path + "/../static", "sw.js", mimetype="application/javascript"
    )


@main_bp.route("/manifest.json")
def manifest():
    """Dynamisches Web App Manifest mit korrekten Pfaden."""
    return jsonify({
        "name": "Hauskeeping",
        "short_name": "Hauskeeping",
        "description": "Haushalt gemeinsam organisieren",
        "start_url": url_for("main.dashboard"),
        "scope": url_for("main.dashboard"),
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": "#212529",
        "icons": [
            {
                "src": url_for("static", filename="icons/icon-192.png"),
                "sizes": "192x192",
                "type": "image/png",
            },
            {
                "src": url_for("static", filename="icons/icon-512.png"),
                "sizes": "512x512",
                "type": "image/png",
            },
        ],
    })


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
        .order_by(Task.due_date)
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

    calendar_week = monday.isocalendar()[1]

    return render_template(
        "main/dashboard.html",
        days=days,
        week_offset=week_offset,
        monday=monday,
        sunday=sunday,
        calendar_week=calendar_week,
        current_user=current_user,
    )
