import logging
from datetime import datetime, timezone

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..models.task import Task, TaskCategory
from ..models.user import User
from ..services.push_service import send_push_to_user

logger = logging.getLogger(__name__)

tasks_bp = Blueprint("tasks", __name__, url_prefix="/tasks")


@tasks_bp.route("/")
@login_required
def task_list():
    """
    Listet alle Aufgaben auf, sortiert nach Faelligkeitsdatum.

    Unterstuetzt Filterung nach Status (``show``: all, open, done).
    """
    show = request.args.get("show", "open")

    query = Task.query
    if show == "open":
        query = query.filter_by(is_done=False)
    elif show == "done":
        query = query.filter_by(is_done=True)

    tasks = query.order_by(Task.due_date).all()
    categories = TaskCategory.query.order_by(TaskCategory.position).all()
    return render_template(
        "tasks/list.html", tasks=tasks, show=show, categories=categories
    )


@tasks_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    """
    Erstellt eine neue Aufgabe.

    GET: Zeigt das Erstellungsformular an.
    POST: Validiert und speichert die neue Aufgabe.
    """
    users = User.query.order_by(User.username).all()
    categories = TaskCategory.query.order_by(TaskCategory.position).all()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip() or None
        due_date_str = request.form.get("due_date", "")
        category_id = request.form.get("category_id", type=int) or None
        assigned_to = request.form.get("assigned_to", type=int) or None
        recurrence_rule = request.form.get("recurrence_rule", "").strip() or None

        if not title:
            flash("Titel ist erforderlich.", "danger")
            return render_template(
                "tasks/create.html", users=users, categories=categories
            )

        try:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
        except ValueError:
            flash("Ungueltiges Datum.", "danger")
            return render_template(
                "tasks/create.html", users=users, categories=categories
            )

        task = Task(
            title=title,
            description=description,
            due_date=due_date,
            category_id=category_id,
            assigned_to=assigned_to,
            created_by=current_user.id,
            recurrence_rule=recurrence_rule,
        )
        db.session.add(task)
        db.session.commit()

        # Push an zugewiesenen User (wenn nicht selbst zugewiesen)
        if assigned_to and assigned_to != current_user.id:
            try:
                formatted_date = due_date.strftime("%d.%m.%Y")
                send_push_to_user(
                    assigned_to,
                    "Neue Aufgabe",
                    f"{current_user.username} hat eine Aufgabe fuer den "
                    f"{formatted_date} hinzugefuegt: {title}",
                    url="/tasks",
                )
            except Exception:
                logger.exception("Push-Benachrichtigung fuer neue Aufgabe fehlgeschlagen.")

        flash("Aufgabe erstellt.", "success")
        return redirect(url_for("tasks.task_list"))

    return render_template("tasks/create.html", users=users, categories=categories)


@tasks_bp.route("/<int:task_id>/edit", methods=["GET", "POST"])
@login_required
def edit(task_id):
    """
    Bearbeitet eine bestehende Aufgabe.

    :param task_id: ID der zu bearbeitenden Aufgabe
    :type task_id: int
    """
    task = db.get_or_404(Task, task_id)
    users = User.query.order_by(User.username).all()
    categories = TaskCategory.query.order_by(TaskCategory.position).all()

    if request.method == "POST":
        task.title = request.form.get("title", "").strip()
        task.description = request.form.get("description", "").strip() or None
        due_date_str = request.form.get("due_date", "")
        task.category_id = request.form.get("category_id", type=int) or None
        task.assigned_to = request.form.get("assigned_to", type=int) or None
        task.recurrence_rule = (
            request.form.get("recurrence_rule", "").strip() or None
        )

        if not task.title:
            flash("Titel ist erforderlich.", "danger")
            return render_template(
                "tasks/edit.html", task=task, users=users, categories=categories
            )

        try:
            task.due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
        except ValueError:
            flash("Ungueltiges Datum.", "danger")
            return render_template(
                "tasks/edit.html", task=task, users=users, categories=categories
            )

        db.session.commit()
        flash("Aufgabe aktualisiert.", "success")
        return redirect(url_for("tasks.task_list"))

    return render_template(
        "tasks/edit.html", task=task, users=users, categories=categories
    )


@tasks_bp.route("/<int:task_id>/toggle", methods=["POST"])
@login_required
def toggle(task_id):
    """
    Markiert eine Aufgabe als erledigt oder offen.

    :param task_id: ID der Aufgabe
    :type task_id: int
    """
    task = db.get_or_404(Task, task_id)
    task.is_done = not task.is_done
    if task.is_done:
        task.completed_by = current_user.id
        task.completed_at = datetime.now(timezone.utc)
    else:
        task.completed_by = None
        task.completed_at = None
    db.session.commit()

    status = "erledigt" if task.is_done else "offen"
    flash(f"Aufgabe als {status} markiert.", "success")
    return redirect(request.referrer or url_for("tasks.task_list"))


@tasks_bp.route("/<int:task_id>/delete", methods=["POST"])
@login_required
def delete(task_id):
    """
    Loescht eine Aufgabe.

    :param task_id: ID der zu loeschenden Aufgabe
    :type task_id: int
    """
    task = db.get_or_404(Task, task_id)
    db.session.delete(task)
    db.session.commit()

    flash("Aufgabe geloescht.", "success")
    return redirect(url_for("tasks.task_list"))


# --- Kategorie-Verwaltung ---


@tasks_bp.route("/categories/add", methods=["POST"])
@login_required
def add_category():
    """Erstellt eine neue Aufgabenkategorie."""
    name = request.form.get("name", "").strip()
    color = request.form.get("color", "#6c757d").strip()
    exclude_from_stats = request.form.get("exclude_from_stats") == "on"

    if not name:
        flash("Kategoriename ist erforderlich.", "danger")
        return redirect(url_for("tasks.task_list"))

    slug = TaskCategory.make_slug(name)

    existing = TaskCategory.query.filter_by(slug=slug).first()
    if existing:
        flash("Eine Kategorie mit diesem Namen existiert bereits.", "warning")
        return redirect(url_for("tasks.task_list"))

    max_pos = db.session.query(db.func.max(TaskCategory.position)).scalar() or 0

    category = TaskCategory(
        name=name,
        slug=slug,
        color=color,
        position=max_pos + 1,
        exclude_from_stats=exclude_from_stats,
    )
    db.session.add(category)
    db.session.commit()

    flash(f'Kategorie "{name}" erstellt.', "success")
    return redirect(url_for("tasks.task_list"))


@tasks_bp.route("/categories/<int:category_id>/edit", methods=["POST"])
@login_required
def edit_category(category_id):
    """Bearbeitet eine bestehende Aufgabenkategorie."""
    category = db.get_or_404(TaskCategory, category_id)

    name = request.form.get("name", "").strip()
    color = request.form.get("color", category.color).strip()
    exclude_from_stats = request.form.get("exclude_from_stats") == "on"

    if not name:
        flash("Kategoriename ist erforderlich.", "danger")
        return redirect(url_for("tasks.task_list"))

    new_slug = TaskCategory.make_slug(name)

    existing = TaskCategory.query.filter(
        TaskCategory.slug == new_slug, TaskCategory.id != category_id
    ).first()
    if existing:
        flash("Eine Kategorie mit diesem Namen existiert bereits.", "warning")
        return redirect(url_for("tasks.task_list"))

    category.name = name
    category.slug = new_slug
    category.color = color
    category.exclude_from_stats = exclude_from_stats
    db.session.commit()

    flash(f'Kategorie "{name}" aktualisiert.', "success")
    return redirect(url_for("tasks.task_list"))


@tasks_bp.route("/categories/<int:category_id>/delete", methods=["POST"])
@login_required
def delete_category(category_id):
    """Loescht eine Aufgabenkategorie. Tasks werden auf keine Kategorie gesetzt."""
    category = db.get_or_404(TaskCategory, category_id)

    Task.query.filter_by(category_id=category.id).update({"category_id": None})

    db.session.delete(category)
    db.session.commit()

    flash(f'Kategorie "{category.name}" entfernt.', "success")
    return redirect(url_for("tasks.task_list"))
