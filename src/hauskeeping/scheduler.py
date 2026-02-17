import atexit
import logging
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(daemon=True)
atexit.register(lambda: scheduler.shutdown(wait=False) if scheduler.running else None)


def init_scheduler(app):
    """
    Initialisiert den APScheduler mit allen geplanten Jobs.

    Muss innerhalb von ``create_app()`` aufgerufen werden.
    """
    if scheduler.running:
        return

    # Job 1: Woechentliche E-Mail-Zusammenfassung
    # Laeuft taeglich um 07:00 UTC – die Funktion selbst filtert nach Wochentag.
    scheduler.add_job(
        func=_run_weekly_email_summary,
        trigger="cron",
        hour=7,
        minute=0,
        id="weekly_email_summary",
        replace_existing=True,
        kwargs={"app": app},
    )

    # Job 2: Push fuer heute faellige Aufgaben – taeglich um 08:00 UTC
    scheduler.add_job(
        func=_run_due_today_push,
        trigger="cron",
        hour=8,
        minute=0,
        id="due_today_push",
        replace_existing=True,
        kwargs={"app": app},
    )

    # Job 3: Push-Erinnerung fuer ueberfaellige Aufgaben – taeglich um 09:00 UTC
    scheduler.add_job(
        func=_run_overdue_push,
        trigger="cron",
        hour=9,
        minute=0,
        id="overdue_push",
        replace_existing=True,
        kwargs={"app": app},
    )

    scheduler.start()
    logger.info("APScheduler gestartet mit %d Jobs.", len(scheduler.get_jobs()))


def _run_weekly_email_summary(app):
    """Wrapper der den Flask-App-Kontext fuer den Mail-Service bereitstellt."""
    with app.app_context():
        from .services.mail_service import send_weekly_summary

        try:
            send_weekly_summary()
        except Exception:
            logger.exception("Fehler beim Senden der woechentlichen Zusammenfassung.")


def _run_due_today_push(app):
    """Sendet Push-Benachrichtigungen fuer heute faellige Aufgaben."""
    with app.app_context():
        from .models.task import Task
        from .services.push_service import send_push_to_user

        today = datetime.now(timezone.utc).date()

        tasks = (
            Task.query.filter(
                Task.due_date == today,
                Task.is_done == False,  # noqa: E712
                Task.assigned_to.isnot(None),
            )
            .all()
        )

        user_tasks = {}
        for task in tasks:
            user_tasks.setdefault(task.assigned_to, []).append(task)

        for user_id, task_list in user_tasks.items():
            count = len(task_list)
            if count == 1:
                title = "Aufgabe faellig"
                body = f"Heute faellig: {task_list[0].title}"
            else:
                title = f"{count} Aufgaben faellig"
                body = "Heute faellig: " + ", ".join(t.title for t in task_list[:3])
                if count > 3:
                    body += f" (+{count - 3} weitere)"

            try:
                send_push_to_user(user_id, title, body, url="/tasks")
            except Exception:
                logger.exception(
                    "Fehler beim Senden der Due-Today-Push an User %d.", user_id
                )


def _run_overdue_push(app):
    """Sendet Push-Erinnerungen fuer ueberfaellige Aufgaben."""
    with app.app_context():
        from .extensions import db
        from .models.task import Task
        from .models.user import User
        from .services.push_service import send_push_to_user

        today = datetime.now(timezone.utc).date()

        tasks = (
            Task.query.filter(
                Task.due_date < today,
                Task.is_done == False,  # noqa: E712
                Task.assigned_to.isnot(None),
            )
            .all()
        )

        user_tasks = {}
        for task in tasks:
            user_tasks.setdefault(task.assigned_to, []).append(task)

        for user_id, task_list in user_tasks.items():
            user = db.session.get(User, user_id)
            if not user or not user.overdue_reminders_enabled:
                continue

            count = len(task_list)
            if count == 1:
                title = "Ueberfaellige Aufgabe"
                body = f"Ueberfaellig: {task_list[0].title}"
            else:
                title = f"{count} ueberfaellige Aufgaben"
                body = "Ueberfaellig: " + ", ".join(t.title for t in task_list[:3])
                if count > 3:
                    body += f" (+{count - 3} weitere)"

            try:
                send_push_to_user(user_id, title, body, url="/tasks")
            except Exception:
                logger.exception(
                    "Fehler beim Senden der Overdue-Push an User %d.", user_id
                )
