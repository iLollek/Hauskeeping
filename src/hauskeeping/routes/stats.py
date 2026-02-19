from datetime import datetime, timedelta, timezone

from flask import Blueprint, render_template
from flask_login import login_required
from sqlalchemy import extract, func, or_

from ..extensions import db
from ..models.shopping import ShoppingListItem
from ..models.task import Task, TaskCategory
from ..models.user import User

stats_bp = Blueprint("stats", __name__, url_prefix="/stats")


@stats_bp.route("/")
@login_required
def index():
    """Statistik-Uebersicht anzeigen."""
    users = User.query.order_by(User.username).all()
    today = datetime.now(timezone.utc).date()
    monday = today - timedelta(days=today.weekday())

    # IDs von Kategorien, die von der Statistik ausgeschlossen sind
    excluded_cat_ids = [
        c.id for c in TaskCategory.query.filter_by(exclude_from_stats=True).all()
    ]

    def _excl(q):
        """Filtert Aufgaben aus ausgeschlossenen Kategorien heraus."""
        if not excluded_cat_ids:
            return q
        return q.filter(
            or_(Task.category_id.is_(None), Task.category_id.notin_(excluded_cat_ids))
        )

    # --- Pro User Statistiken ---
    user_stats = []
    for user in users:
        tasks_created = _excl(Task.query.filter_by(created_by=user.id)).count()
        tasks_completed = _excl(Task.query.filter_by(completed_by=user.id)).count()
        tasks_assigned = _excl(Task.query.filter_by(assigned_to=user.id)).count()
        tasks_open = _excl(
            Task.query.filter_by(assigned_to=user.id, is_done=False)
        ).count()
        tasks_overdue = _excl(
            Task.query.filter(
                Task.assigned_to == user.id,
                Task.is_done == False,  # noqa: E712
                Task.due_date < today,
            )
        ).count()
        shopping_added = ShoppingListItem.query.filter_by(added_by=user.id).count()

        completion_rate = 0
        if tasks_assigned > 0:
            completion_rate = round(tasks_completed / tasks_assigned * 100)

        user_stats.append(
            {
                "user": user,
                "tasks_created": tasks_created,
                "tasks_completed": tasks_completed,
                "tasks_open": tasks_open,
                "tasks_overdue": tasks_overdue,
                "shopping_added": shopping_added,
                "completion_rate": completion_rate,
            }
        )

    # --- Globale Statistiken ---
    total_tasks = _excl(Task.query).count()
    total_done = _excl(Task.query.filter_by(is_done=True)).count()
    total_open = _excl(Task.query.filter_by(is_done=False)).count()
    total_overdue = _excl(
        Task.query.filter(
            Task.is_done == False,  # noqa: E712
            Task.due_date < today,
        )
    ).count()
    total_shopping = ShoppingListItem.query.count()

    # Aufgaben diese Woche
    tasks_this_week = _excl(
        Task.query.filter(
            Task.due_date >= monday,
            Task.due_date <= monday + timedelta(days=6),
        )
    ).count()
    tasks_done_this_week = _excl(
        Task.query.filter(
            Task.due_date >= monday,
            Task.due_date <= monday + timedelta(days=6),
            Task.is_done == True,  # noqa: E712
        )
    ).count()

    # Aufgaben pro Wochentag (Verteilung)
    day_names = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
    tasks_by_weekday = []
    for i in range(7):
        count = _excl(
            Task.query.filter(extract("dow", Task.due_date) == (i + 1) % 7)
        ).count()
        tasks_by_weekday.append({"day": day_names[i], "count": count})

    # Top-Kategorie (meiste Aufgaben, nur nicht ausgeschlossene)
    top_cat_query = (
        db.session.query(Task.category_id, func.count(Task.id).label("cnt"))
        .filter(Task.category_id.isnot(None))
    )
    if excluded_cat_ids:
        top_cat_query = top_cat_query.filter(
            Task.category_id.notin_(excluded_cat_ids)
        )
    top_category = (
        top_cat_query
        .group_by(Task.category_id)
        .order_by(func.count(Task.id).desc())
        .first()
    )
    top_category_name = None
    if top_category:
        cat = db.session.get(TaskCategory, top_category[0])
        if cat:
            top_category_name = cat.name

    return render_template(
        "stats/index.html",
        user_stats=user_stats,
        total_tasks=total_tasks,
        total_done=total_done,
        total_open=total_open,
        total_overdue=total_overdue,
        total_shopping=total_shopping,
        tasks_this_week=tasks_this_week,
        tasks_done_this_week=tasks_done_this_week,
        tasks_by_weekday=tasks_by_weekday,
        top_category_name=top_category_name,
    )
