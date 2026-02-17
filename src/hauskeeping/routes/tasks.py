from datetime import datetime, timezone

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..models.task import Task
from ..models.user import User

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
    return render_template("tasks/list.html", tasks=tasks, show=show)


@tasks_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    """
    Erstellt eine neue Aufgabe.

    GET: Zeigt das Erstellungsformular an.
    POST: Validiert und speichert die neue Aufgabe.
    """
    users = User.query.order_by(User.username).all()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip() or None
        due_date_str = request.form.get("due_date", "")
        priority = request.form.get("priority", "medium")
        assigned_to = request.form.get("assigned_to", type=int) or None
        recurrence_rule = request.form.get("recurrence_rule", "").strip() or None

        if not title:
            flash("Titel ist erforderlich.", "danger")
            return render_template("tasks/create.html", users=users)

        try:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
        except ValueError:
            flash("Ungueltiges Datum.", "danger")
            return render_template("tasks/create.html", users=users)

        task = Task(
            title=title,
            description=description,
            due_date=due_date,
            priority=priority,
            assigned_to=assigned_to,
            created_by=current_user.id,
            recurrence_rule=recurrence_rule,
        )
        db.session.add(task)
        db.session.commit()

        flash("Aufgabe erstellt.", "success")
        return redirect(url_for("tasks.task_list"))

    return render_template("tasks/create.html", users=users)


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

    if request.method == "POST":
        task.title = request.form.get("title", "").strip()
        task.description = request.form.get("description", "").strip() or None
        due_date_str = request.form.get("due_date", "")
        task.priority = request.form.get("priority", "medium")
        task.assigned_to = request.form.get("assigned_to", type=int) or None
        task.recurrence_rule = (
            request.form.get("recurrence_rule", "").strip() or None
        )

        if not task.title:
            flash("Titel ist erforderlich.", "danger")
            return render_template("tasks/edit.html", task=task, users=users)

        try:
            task.due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
        except ValueError:
            flash("Ungueltiges Datum.", "danger")
            return render_template("tasks/edit.html", task=task, users=users)

        db.session.commit()
        flash("Aufgabe aktualisiert.", "success")
        return redirect(url_for("tasks.task_list"))

    return render_template("tasks/edit.html", task=task, users=users)


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
