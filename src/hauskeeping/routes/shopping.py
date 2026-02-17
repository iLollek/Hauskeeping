from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..models.shopping import ShoppingListItem

shopping_bp = Blueprint("shopping", __name__, url_prefix="/shopping")


@shopping_bp.route("/")
@login_required
def shopping_list():
    """
    Zeigt die gemeinsame Einkaufsliste an.

    Nicht abgehakte Artikel stehen oben, abgehakte unten.
    """
    items = ShoppingListItem.query.order_by(
        ShoppingListItem.is_checked, ShoppingListItem.created_at.desc()
    ).all()
    categories = ShoppingListItem.CATEGORIES
    return render_template("shopping/list.html", items=items, categories=categories)


@shopping_bp.route("/add", methods=["POST"])
@login_required
def add_item():
    """Fuegt einen neuen Artikel zur Einkaufsliste hinzu."""
    name = request.form.get("name", "").strip()
    category = request.form.get("category", "sonstiges")

    if not name:
        flash("Artikelname ist erforderlich.", "danger")
        return redirect(url_for("shopping.shopping_list"))

    item = ShoppingListItem(
        name=name,
        category=category,
        added_by=current_user.id,
    )
    db.session.add(item)
    db.session.commit()

    flash("Artikel hinzugefuegt.", "success")
    return redirect(url_for("shopping.shopping_list"))


@shopping_bp.route("/<int:item_id>/toggle", methods=["POST"])
@login_required
def toggle_item(item_id):
    """
    Hakt einen Artikel ab oder entfernt den Haken.

    :param item_id: ID des Artikels
    :type item_id: int
    """
    item = db.get_or_404(ShoppingListItem, item_id)
    item.is_checked = not item.is_checked
    db.session.commit()
    return redirect(url_for("shopping.shopping_list"))


@shopping_bp.route("/<int:item_id>/delete", methods=["POST"])
@login_required
def delete_item(item_id):
    """
    Loescht einen Artikel von der Einkaufsliste.

    :param item_id: ID des zu loeschenden Artikels
    :type item_id: int
    """
    item = db.get_or_404(ShoppingListItem, item_id)
    db.session.delete(item)
    db.session.commit()

    flash("Artikel entfernt.", "success")
    return redirect(url_for("shopping.shopping_list"))


@shopping_bp.route("/clear-checked", methods=["POST"])
@login_required
def clear_checked():
    """Entfernt alle abgehakten Artikel von der Einkaufsliste."""
    ShoppingListItem.query.filter_by(is_checked=True).delete()
    db.session.commit()

    flash("Abgehakte Artikel entfernt.", "success")
    return redirect(url_for("shopping.shopping_list"))
