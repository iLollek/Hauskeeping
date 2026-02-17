import click
from flask import Flask

from .extensions import bcrypt, db
from .models.user import User


def register_commands(app: Flask):
    """
    Registriert CLI-Commands fuer die Flask-App.

    :param app: Die Flask-App-Instanz
    :type app: Flask
    """

    @app.cli.command("create-admin")
    @click.option("--username", prompt="Benutzername", help="Benutzername des Hausmeisters")
    @click.option(
        "--password",
        prompt="Passwort",
        hide_input=True,
        confirmation_prompt=True,
        help="Passwort des Hausmeisters",
    )
    def create_admin(username, password):
        """Erstellt einen Hausmeister-Account (Admin)."""
        existing = User.query.filter_by(username=username).first()
        if existing:
            click.echo(f"Fehler: Benutzer '{username}' existiert bereits.")
            return

        pw_hash = bcrypt.generate_password_hash(password).decode("utf-8")
        user = User(
            username=username,
            password_hash=pw_hash,
            role="hausmeister",
        )
        db.session.add(user)
        db.session.commit()
        click.echo(f"Hausmeister '{username}' wurde erfolgreich erstellt.")

    @app.cli.command("init-db")
    def init_db():
        """Erstellt alle Datenbanktabellen."""
        db.create_all()
        click.echo("Datenbank wurde initialisiert.")
