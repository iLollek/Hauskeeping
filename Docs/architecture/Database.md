# Datenbank – Hauskeeping

Dieses Dokument beschreibt, welche Datenbanken Hauskeeping unterstützt, wie die Verbindung konfiguriert wird, wie Migrationen funktionieren und welche Modelle existieren.

---

## 1. Unterstützte Datenbanken

Hauskeeping unterstützt zwei Datenbank-Backends:

| Backend | Einsatzzweck | Konfiguration |
|---|---|---|
| **PostgreSQL** | Produktivbetrieb (empfohlen) | `DATABASE_URL` in `.env` |
| **SQLite** | Entwicklung & lokales Testen | Fallback, wenn kein PostgreSQL konfiguriert |

### PostgreSQL (Standard)

PostgreSQL ist das empfohlene Backend für jeden produktiven Einsatz. Es ist zuverlässig, unterstützt parallele Zugriffe und skaliert problemlos für den Hauskeeping-Anwendungsfall.

```env
DATABASE_URL=postgresql://user:passwort@localhost:5432/hauskeeping
```

### SQLite (Fallback)

SQLite wird automatisch verwendet, wenn keine `DATABASE_URL` gesetzt ist. Es eignet sich für Entwickler, die Hauskeeping lokal testen möchten, ohne eine PostgreSQL-Instanz aufzusetzen.

```env
# .env leer lassen oder DATABASE_URL weglassen → SQLite wird verwendet
DATABASE_URL=sqlite:///hauskeeping.db
```

> **Hinweis:** SQLite ist nicht für den Produktivbetrieb geeignet. Es unterstützt keine echten parallelen Schreibzugriffe und hat Einschränkungen bei Migrationen (z. B. kein `ALTER COLUMN`). Für alles außer lokalem Testen sollte PostgreSQL verwendet werden.

---

## 2. Konfiguration

Die Datenbankverbindung wird ausschließlich über die Umgebungsvariable `DATABASE_URL` gesteuert. Flask-SQLAlchemy liest diese automatisch aus, wenn sie korrekt gesetzt ist.

**`config.py`:**

```python
import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///hauskeeping.db"  # Fallback für lokale Entwicklung
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
```

> **Hinweis PostgreSQL mit psycopg2:** Manche Deployment-Umgebungen liefern eine `DATABASE_URL` mit dem Präfix `postgres://` statt `postgresql://`. SQLAlchemy erwartet `postgresql://`. Falls nötig, kann dies in `config.py` korrigiert werden:
>
> ```python
> uri = os.getenv("DATABASE_URL", "sqlite:///hauskeeping.db")
> if uri.startswith("postgres://"):
>     uri = uri.replace("postgres://", "postgresql://", 1)
> SQLALCHEMY_DATABASE_URI = uri
> ```

---

## 3. Migrationen mit Flask-Migrate

Hauskeeping verwendet **Flask-Migrate** (basierend auf Alembic) für Datenbankmigrationen. Jede Änderung am Datenbankschema – neue Tabellen, neue Spalten, geänderte Typen – wird als Migration versioniert und kann reproduzierbar angewendet werden.

### Installation

```bash
pip install flask-migrate
```

### Initialisierung (einmalig)

```bash
flask db init
```

Dieser Befehl erstellt den `migrations/`-Ordner im Projektverzeichnis. Er wird nur einmal ausgeführt und danach in Git eingecheckt.

### Workflow bei Schemaänderungen

**1. Modell in Python anpassen** (z. B. neue Spalte in einem Model ergänzen)

**2. Migration generieren:**

```bash
flask db migrate -m "Kurze Beschreibung der Änderung"
```

Alembic erkennt die Differenz zwischen dem aktuellen Datenbankschema und den definierten Modellen und generiert automatisch ein Migrationsskript unter `migrations/versions/`.

**3. Migration prüfen:**

Das generierte Skript sollte immer manuell geprüft werden, bevor es angewendet wird – insbesondere bei komplexen Änderungen (z. B. Umbenennen von Spalten), die Alembic nicht immer korrekt erkennt.

**4. Migration anwenden:**

```bash
flask db upgrade
```

**Rollback einer Migration:**

```bash
flask db downgrade
```

> **Hinweis:** Die `migrations/`-Ordner gehören in das Git-Repository. Sie sind Teil des Projekts und ermöglichen es, das Schema auf jedem System reproduzierbar aufzubauen.

---

## 4. Datenbankmodelle

Im Folgenden sind alle Modelle von Hauskeeping aufgeführt. Detaillierte Informationen zu einzelnen Modellen finden sich in den jeweiligen Feature-Dokumenten.

### User

Zentrale Tabelle für alle registrierten User.

| Feld | Typ | Beschreibung |
|---|---|---|
| `id` | Integer PK | Eindeutige User-ID |
| `username` | String | Anzeigename (eindeutig) |
| `password_hash` | String | Gehashtes Passwort (bcrypt) |
| `role` | String | `"member"` oder `"hausmeister"` |
| `email_notifications_enabled` | Boolean | Wöchentliche E-Mail aktiv |
| `email_notification_day` | Integer (0–6) | Wochentag für den E-Mail-Versand |
| `push_notifications_enabled` | Boolean | Web Push / Android Push aktiv |
| `invited_by` | FK → User | User, dessen Invite-Code verwendet wurde |
| `created_at` | DateTime | Registrierungszeitpunkt |

### InviteCode

Einladungscodes, die von Hausmeistern generiert werden.

| Feld | Typ | Beschreibung |
|---|---|---|
| `id` | Integer PK | |
| `code` | String | Zufällig generierter Code (UUID) |
| `created_by` | FK → User | Hausmeister, der den Code erstellt hat |
| `created_at` | DateTime | Erstellungszeitpunkt |
| `expires_at` | DateTime | Ablaufzeitpunkt |
| `used_by` | FK → User (nullable) | User, der den Code eingelöst hat |
| `used_at` | DateTime (nullable) | Einlösezeitpunkt |
| `is_active` | Boolean | `False` nach Verwendung oder Ablauf |

### Task

Haushaltsaufgaben – das Kernmodell von Hauskeeping.

| Feld | Typ | Beschreibung |
|---|---|---|
| `id` | Integer PK | |
| `title` | String | Titel der Aufgabe |
| `description` | Text (nullable) | Optionale Beschreibung |
| `due_date` | Date | Fälligkeitsdatum |
| `is_done` | Boolean | Erledigt-Status |
| `priority` | String | z. B. `"low"`, `"medium"`, `"high"` |
| `assigned_to` | FK → User (nullable) | Zugewiesener User |
| `created_by` | FK → User | Ersteller der Aufgabe |
| `recurrence_rule` | String (nullable) | Wiederholungsregel (z. B. `"weekly"`) |
| `created_at` | DateTime | Erstellungszeitpunkt |

### ShoppingListItem

Einträge der gemeinsamen Einkaufsliste.

| Feld | Typ | Beschreibung |
|---|---|---|
| `id` | Integer PK | |
| `name` | String | Artikelname |
| `category` | String (nullable) | z. B. `"Lebensmittel"`, `"Drogerie"` |
| `is_checked` | Boolean | Abgehakt-Status |
| `added_by` | FK → User | User, der den Artikel hinzugefügt hat |
| `created_at` | DateTime | Erstellungszeitpunkt |

### PushSubscription

Browser-seitige Push-Subscriptions für Web Push Notifications.

| Feld | Typ | Beschreibung |
|---|---|---|
| `id` | Integer PK | |
| `user_id` | FK → User | Zugehöriger User |
| `endpoint` | Text | Browser-seitige Push-URL |
| `p256dh` | Text | Öffentlicher Verschlüsselungskey |
| `auth` | Text | Auth-Secret des Browsers |
| `platform` | String | z. B. `"ios"`, `"android"`, `"desktop"` |
| `created_at` | DateTime | Erstellungszeitpunkt |

---

## 5. Ersteinrichtung

Beim ersten Start einer neuen Hauskeeping-Instanz wird die Datenbank wie folgt initialisiert:

```bash
# Migrationshistorie auf den aktuellen Stand bringen
flask db upgrade

# Ersten Hausmeister-Account anlegen
flask create-admin
```

`flask db upgrade` wendet alle vorhandenen Migrationen an und erstellt das vollständige Schema. Danach ist die Datenbank bereit.

---

## Kurzübersicht

| Thema | Vorgehen |
|---|---|
| ORM | Flask-SQLAlchemy |
| Produktiv-Backend | PostgreSQL |
| Entwicklungs-Fallback | SQLite |
| Konfiguration | `DATABASE_URL` in `.env` |
| Migrationen | Flask-Migrate (Alembic) |
| Schema initialisieren | `flask db upgrade` |
| Neues Schema einpflegen | `flask db migrate` → prüfen → `flask db upgrade` |