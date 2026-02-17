import logging
from datetime import datetime, timedelta, timezone

from flask import current_app, render_template
from flask_mail import Message

from ..extensions import db, mail
from ..models.task import Task
from ..models.user import User

logger = logging.getLogger(__name__)


def send_weekly_summary():
    """
    Versendet die woechentliche Aufgaben-Zusammenfassung per E-Mail.

    Wird fuer jeden User aufgerufen, der ``email_notifications_enabled = True``
    hat und dessen ``email_notification_day`` dem aktuellen Wochentag entspricht.
    Benoetigt einen aktiven Flask-App-Kontext.
    """
    today = datetime.now(timezone.utc).date()
    weekday = today.weekday()  # 0=Mo, 6=So

    users = User.query.filter_by(
        email_notifications_enabled=True,
        email_notification_day=weekday,
    ).all()

    for user in users:
        if not user.email:
            logger.warning(
                "User %s hat E-Mail-Benachrichtigungen aktiv, aber keine E-Mail-Adresse.",
                user.username,
            )
            continue

        try:
            _send_summary_to_user(user, today)
        except Exception:
            logger.exception(
                "Fehler beim Senden der Zusammenfassung an %s", user.username
            )


def _send_summary_to_user(user, today):
    """Erstellt und versendet die Zusammenfassungs-Mail fuer einen User."""
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    next_monday = monday + timedelta(weeks=1)
    next_sunday = next_monday + timedelta(days=6)

    # Aufgaben der aktuellen Woche (zugewiesen an den User)
    current_week_tasks = (
        Task.query.filter(
            Task.assigned_to == user.id,
            Task.due_date >= monday,
            Task.due_date <= sunday,
            Task.is_done == False,  # noqa: E712
        )
        .order_by(Task.due_date)
        .all()
    )

    # Ueberfaellige Aufgaben
    overdue_tasks = (
        Task.query.filter(
            Task.assigned_to == user.id,
            Task.due_date < monday,
            Task.is_done == False,  # noqa: E712
        )
        .order_by(Task.due_date)
        .all()
    )

    # Vorschau naechste Woche
    next_week_tasks = (
        Task.query.filter(
            Task.assigned_to == user.id,
            Task.due_date >= next_monday,
            Task.due_date <= next_sunday,
            Task.is_done == False,  # noqa: E712
        )
        .order_by(Task.due_date)
        .all()
    )

    # Erledigte Aufgaben der Vorwoche (Statistik)
    prev_monday = monday - timedelta(weeks=1)
    prev_sunday = monday - timedelta(days=1)
    completed_last_week = Task.query.filter(
        Task.assigned_to == user.id,
        Task.due_date >= prev_monday,
        Task.due_date <= prev_sunday,
        Task.is_done == True,  # noqa: E712
    ).count()

    total_open = len(current_week_tasks) + len(overdue_tasks)
    subject = f"Deine Hauskeeping-Woche – {total_open} Aufgaben stehen an"

    html_body = render_template(
        "email/weekly_summary.html",
        user=user,
        current_week_tasks=current_week_tasks,
        overdue_tasks=overdue_tasks,
        next_week_tasks=next_week_tasks,
        completed_last_week=completed_last_week,
        monday=monday,
        sunday=sunday,
    )

    msg = Message(
        subject=subject,
        recipients=[user.email],
        html=html_body,
    )
    mail.send(msg)
    logger.info("Woechentliche Zusammenfassung an %s gesendet.", user.email)
