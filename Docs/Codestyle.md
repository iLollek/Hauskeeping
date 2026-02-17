# Codestyle – Hauskeeping

Dieses Dokument beschreibt die Coding-Guidelines für Hauskeeping. Sie gelten für alle Beiträge – ob vom Maintainer selbst oder von externen Contributors. Ziel ist ein konsistenter, lesbarer Codestand, der langfristig wartbar bleibt.

---

## Toolchain

Hauskeeping verwendet zwei Tools für Formatierung und Linting:

| Tool | Aufgabe |
|---|---|
| **Black** | Automatische Code-Formatierung |
| **Ruff** | Linting + Import-Sortierung |

Beide Tools sind in der `pyproject.toml` konfiguriert und sollten lokal installiert sein, bevor an Hauskeeping gearbeitet wird:

```bash
pip install black ruff
```

---

## Black – Formatierung

Black ist der maßgebliche Formatter für Hauskeeping. Er wird ohne Ausnahmen und ohne manuelle Overrides eingesetzt – Black entscheidet, Black formatiert.

**Konfiguration in `pyproject.toml`:**

```toml
[tool.black]
line-length = 88
target-version = ["py311"]
```

Code wird vor einem Commit formatiert:

```bash
black .
```

Black ist nicht verhandelbar. Formatierungsdiskussionen entfallen dadurch vollständig.

---

## Ruff – Linting & Import-Sortierung

Ruff übernimmt zwei Aufgaben: Linting (Codequalität, potenzielle Fehler) und die automatische Sortierung von Imports – kompatibel mit Black.

**Konfiguration in `pyproject.toml`:**

```toml
[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I"]
# E = pycodestyle Fehler
# F = Pyflakes (undefined names, unused imports etc.)
# I = isort-kompatible Import-Sortierung
```

Linting und Import-Sortierung werden ausgeführt mit:

```bash
ruff check --fix .
```

---

## Pre-Commit-Hook (empfohlen)

Es wird empfohlen, Black und Ruff als Pre-Commit-Hook einzurichten, damit der Code automatisch vor jedem Commit geprüft und formatiert wird.

**Installation:**

```bash
pip install pre-commit
```

**`.pre-commit-config.yaml`:**

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.3.0
    hooks:
      - id: black

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.1
    hooks:
      - id: ruff
        args: [--fix]
```

**Hook aktivieren:**

```bash
pre-commit install
```

Danach läuft Black und Ruff automatisch bei jedem `git commit`. Der Hook ist nicht verpflichtend, wird aber für alle Contributors empfohlen.

---

## Docstrings

Alle **öffentlichen** Funktionen und Methoden – also alle, die nicht mit einem Unterstrich (`_`) beginnen – müssen mit einem Docstring im **reStructuredText-Format (ReST)** versehen sein.

Private Hilfsfunktionen (z. B. `_build_query()`, `_format_date()`) sind davon ausgenommen, dürfen aber ebenfalls dokumentiert werden.

### Format

```python
def funktion(param1, param2):
    """
    Kurze Zusammenfassung in einem Satz.

    Optionale längere Beschreibung, wenn die Funktion komplexer ist
    und mehr Kontext benötigt.

    :param param1: Beschreibung von param1
    :type param1: str
    :param param2: Beschreibung von param2
    :type param2: int
    :return: Beschreibung des Rückgabewerts
    :rtype: bool
    :raises ValueError: Wenn param1 leer ist
    """
```

### Beispiele aus dem Hauskeeping-Kontext

**Einfache Funktion ohne Rückgabewert:**

```python
def send_weekly_summary(user):
    """
    Sendet die wöchentliche Zusammenfassungs-E-Mail an einen User.

    :param user: Der User, an den die E-Mail gesendet wird
    :type user: User
    """
    ...
```

**Funktion mit Rückgabewert:**

```python
def get_overdue_tasks(user_id):
    """
    Gibt alle überfälligen Tasks eines Users zurück.

    :param user_id: Die ID des Users
    :type user_id: int
    :return: Liste der überfälligen Tasks
    :rtype: list[Task]
    """
    ...
```

**Funktion mit Fehlerbehandlung:**

```python
def register_push_subscription(user_id, subscription_data):
    """
    Speichert eine neue PushSubscription für einen User in der Datenbank.

    :param user_id: Die ID des Users
    :type user_id: int
    :param subscription_data: Das PushSubscription-Objekt aus dem Browser
    :type subscription_data: dict
    :return: Die erstellte PushSubscription-Instanz
    :rtype: PushSubscription
    :raises ValueError: Wenn subscription_data keinen gültigen Endpoint enthält
    """
    ...
```

---

## Kurzübersicht

| Thema | Vorgehen |
|---|---|
| Formatter | Black (`line-length = 88`) |
| Linter | Ruff (`E`, `F`, `I`) |
| Import-Sortierung | Ruff (isort-kompatibel) |
| Docstring-Format | reStructuredText (ReST) |
| Docstring-Pflicht | Alle öffentlichen Funktionen & Methoden |
| Pre-Commit-Hook | Empfohlen, nicht verpflichtend |