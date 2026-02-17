from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..models.shopping import ShoppingCategory, ShoppingListItem

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
    categories = ShoppingCategory.query.order_by(ShoppingCategory.position).all()

    # Kategorie-Lookup fuer schnellen Zugriff im Template
    category_map = {c.slug: c for c in categories}

    return render_template(
        "shopping/list.html",
        items=items,
        categories=categories,
        category_map=category_map,
    )


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


# --- Kategorie-Verwaltung ---


@shopping_bp.route("/categories/add", methods=["POST"])
@login_required
def add_category():
    """Erstellt eine neue Einkaufskategorie."""
    name = request.form.get("name", "").strip()
    color = request.form.get("color", "#6c757d").strip()

    if not name:
        flash("Kategoriename ist erforderlich.", "danger")
        return redirect(url_for("shopping.shopping_list"))

    slug = ShoppingCategory.make_slug(name)

    # Pruefen ob Slug bereits existiert
    existing = ShoppingCategory.query.filter_by(slug=slug).first()
    if existing:
        flash("Eine Kategorie mit diesem Namen existiert bereits.", "warning")
        return redirect(url_for("shopping.shopping_list"))

    # Position: ans Ende setzen
    max_pos = db.session.query(db.func.max(ShoppingCategory.position)).scalar() or 0

    category = ShoppingCategory(
        name=name,
        slug=slug,
        color=color,
        position=max_pos + 1,
    )
    db.session.add(category)
    db.session.commit()

    flash(f'Kategorie "{name}" erstellt.', "success")
    return redirect(url_for("shopping.shopping_list"))


@shopping_bp.route("/categories/<int:category_id>/edit", methods=["POST"])
@login_required
def edit_category(category_id):
    """Bearbeitet eine bestehende Einkaufskategorie."""
    category = db.get_or_404(ShoppingCategory, category_id)
    old_slug = category.slug

    name = request.form.get("name", "").strip()
    color = request.form.get("color", category.color).strip()

    if not name:
        flash("Kategoriename ist erforderlich.", "danger")
        return redirect(url_for("shopping.shopping_list"))

    new_slug = ShoppingCategory.make_slug(name)

    # Pruefen ob neuer Slug bereits von anderer Kategorie belegt ist
    existing = ShoppingCategory.query.filter(
        ShoppingCategory.slug == new_slug, ShoppingCategory.id != category_id
    ).first()
    if existing:
        flash("Eine Kategorie mit diesem Namen existiert bereits.", "warning")
        return redirect(url_for("shopping.shopping_list"))

    category.name = name
    category.slug = new_slug
    category.color = color

    # Slug in bestehenden Items aktualisieren
    if old_slug != new_slug:
        ShoppingListItem.query.filter_by(category=old_slug).update(
            {"category": new_slug}
        )

    db.session.commit()

    flash(f'Kategorie "{name}" aktualisiert.', "success")
    return redirect(url_for("shopping.shopping_list"))


@shopping_bp.route("/categories/<int:category_id>/delete", methods=["POST"])
@login_required
def delete_category(category_id):
    """Loescht eine Einkaufskategorie. Items werden auf keine Kategorie gesetzt."""
    category = db.get_or_404(ShoppingCategory, category_id)

    # Items mit dieser Kategorie auf None setzen
    ShoppingListItem.query.filter_by(category=category.slug).update(
        {"category": None}
    )

    db.session.delete(category)
    db.session.commit()

    flash(f'Kategorie "{category.name}" entfernt.', "success")
    return redirect(url_for("shopping.shopping_list"))
