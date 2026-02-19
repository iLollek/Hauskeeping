import atexit
import calendar
import logging
from datetime import date, datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import or_

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

    # Job 4: Wiederkehrende Aufgaben fuer die aktuelle Woche erzeugen.
    # Laeuft taeglich um 00:01 UTC.  Die Funktion ist idempotent (State-Check),
    # d.h. sie tut nichts, wenn die Woche schon verarbeitet wurde.
    scheduler.add_job(
        func=_run_recurrence_spawn,
        trigger="cron",
        hour=0,
        minute=1,
        id="recurrence_spawn",
        replace_existing=True,
        kwargs={"app": app},
    )

    scheduler.start()
    logger.info("APScheduler gestartet mit %d Jobs.", len(scheduler.get_jobs()))

    # Direkt beim Startup ausfuehren: behandelt den Downtime-Fall.
    # War die App am Montag nicht aktiv, wird der Spawn beim naechsten
    # Start sofort nachgeholt.
    _run_recurrence_spawn(app)


# ---------------------------------------------------------------------------
# Recurrence Spawn
# ---------------------------------------------------------------------------

def _run_recurrence_spawn(app):
    """
    Erzeugt wiederkehrende Aufgaben fuer die aktuelle Woche, sofern noch
    nicht geschehen.

    Idempotent: Wird die Funktion mehrfach in derselben Woche aufgerufen,
    passiert beim zweiten Mal nichts (State-Check via app_state-Tabelle).
    Downtime-sicher: Beim Startup wird sie sofort ausgefuehrt, sodass
    ein verpasster Montag beim naechsten App-Start aufgeholt wird.
    """
    with app.app_context():
        from .extensions import db
        from .models.app_state import AppState
        from .models.task import Task

        today = date.today()
        monday = today - timedelta(days=today.weekday())

        # Wurde diese Woche bereits verarbeitet?
        state = db.session.get(AppState, "last_recurrence_monday")
        if state and date.fromisoformat(state.value) >= monday:
            return

        # Alle Template-Tasks: haben recurrence_rule, aber keinen parent
        templates = Task.query.filter(
            Task.recurrence_rule.isnot(None),
            Task.parent_task_id.is_(None),
        ).all()

        for template in templates:
            for occ_date in _get_week_occurrences(template, monday):
                # Duplikat-Check: existiert schon eine Instanz (oder das Template
                # selbst) fuer dieses Datum?
                exists = Task.query.filter(
                    or_(
                        Task.id == template.id,
                        Task.parent_task_id == template.id,
                    ),
                    Task.due_date == occ_date,
                ).first()

                if not exists:
                    new_task = Task(
                        title=template.title,
                        description=template.description,
                        due_date=occ_date,
                        category_id=template.category_id,
                        assigned_to=template.assigned_to,
                        created_by=template.created_by,
                        recurrence_rule=template.recurrence_rule,
                        parent_task_id=template.id,
                    )
                    db.session.add(new_task)
                    logger.debug(
                        "Neue Instanz fuer Template #%d erzeugt: '%s' am %s.",
                        template.id,
                        template.title,
                        occ_date,
                    )

        # Woche als verarbeitet markieren
        if state is None:
            state = AppState(key="last_recurrence_monday", value=str(monday))
            db.session.add(state)
        else:
            state.value = str(monday)

        db.session.commit()
        logger.info("Recurrence-Spawn abgeschlossen fuer Woche ab %s.", monday)


def _get_week_occurrences(template, monday):
    """
    Gibt die Daten zurueck, an denen ein Template in der angegebenen Woche
    vorkommen soll.

    Beruecksichtigt nur Daten >= template.due_date, damit keine Instanzen
    vor dem urspruenglichen Faelligkeitsdatum erzeugt werden.

    :param template: Task-Objekt mit gesetzter recurrence_rule
    :param monday: Montag der zu verarbeitenden Woche (date)
    :return: Liste von date-Objekten
    """
    occurrences = []

    if template.recurrence_rule == "daily":
        for i in range(7):
            d = monday + timedelta(days=i)
            if d >= template.due_date:
                occurrences.append(d)

    elif template.recurrence_rule == "weekly":
        # Gleicher Wochentag wie das Template (0 = Montag, 6 = Sonntag)
        target_date = monday + timedelta(days=template.due_date.weekday())
        if target_date >= template.due_date:
            occurrences.append(target_date)

    elif template.recurrence_rule == "monthly":
        # Gleicher Tag im Monat; bei kuerzeren Monaten wird auf den letzten
        # gueltigen Tag geklemmt (z.B. 31. -> 28./29. im Februar).
        target_day = template.due_date.day
        for i in range(7):
            d = monday + timedelta(days=i)
            max_day = calendar.monthrange(d.year, d.month)[1]
            if d.day == min(target_day, max_day) and d >= template.due_date:
                occurrences.append(d)

    return occurrences


# ---------------------------------------------------------------------------
# Bestehende Jobs
# ---------------------------------------------------------------------------

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
