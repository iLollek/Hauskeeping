# Commit Guidelines – Hauskeeping

Hauskeeping folgt dem **Conventional Commits**-Standard für alle Commit-Nachrichten. Das sorgt für eine lesbare Git-History, erleichtert das Erstellen von Changelogs und macht die Auswirkung jedes Commits auf einen Blick klar.

Spezifikation: [conventionalcommits.org](https://www.conventionalcommits.org/en/v1.0.0/)

---

## Format

```
<type>(<scope>): <beschreibung>

[optionaler Body]

[optionaler Footer]
```

- **`type`** – Art der Änderung (siehe unten)
- **`scope`** – Betroffener Bereich des Projekts (optional, aber empfohlen)
- **`beschreibung`** – Kurze Zusammenfassung im Imperativ, Kleinschreibung, kein Punkt am Ende
- **Body** – Ausführlichere Erklärung, falls nötig (durch Leerzeile vom Header getrennt)
- **Footer** – Referenz auf Issues oder Breaking Changes

---

## Types

| Type | Bedeutung | Wann verwenden |
|---|---|---|
| `feat` | Neues Feature | Eine neue Funktion wird hinzugefügt |
| `fix` | Bugfix | Ein Fehler wird behoben |
| `docs` | Dokumentation | Nur Änderungen an `.md`-Dateien oder Docstrings |
| `style` | Formatierung | Black, Ruff – kein funktionaler Unterschied |
| `refactor` | Refactoring | Umstrukturierung ohne funktionale Änderung |
| `test` | Tests | Tests hinzufügen oder anpassen |
| `chore` | Wartung | Dependencies, Konfiguration, Build-System |
| `db` | Datenbank | Neue Migration, Schemaänderung |

---

## Scopes

Der Scope gibt an, welcher Teil von Hauskeeping betroffen ist. Empfohlene Scopes:

| Scope | Bereich |
|---|---|
| `auth` | Authentifizierung, Rollen, Invite-Codes |
| `tasks` | Aufgabenverwaltung |
| `shopping` | Einkaufsliste |
| `notifications` | E-Mail, Web Push, Android Push |
| `calendar` | Kalenderansicht |
| `db` | Datenbankmodelle, Migrationen |
| `config` | Konfiguration, `.env`, `config.py` |
| `ui` | Templates, CSS, Frontend |
| `ci` | GitHub Actions, Workflows |

---

## Beispiele

**Neues Feature:**
```
feat(auth): invite-code system hinzugefügt
```

**Bugfix:**
```
fix(notifications): push subscription wird nach 410 korrekt gelöscht
```

**Datenbankänderung:**
```
db(tasks): spalte recurrence_rule zur task-tabelle hinzugefügt
```

**Refactoring mit Body:**
```
refactor(auth): passwort-hashing in eigene hilfsfunktion ausgelagert

Die Logik war bisher in zwei Routen dupliziert. Sie liegt jetzt
zentral in auth/utils.py und wird von beiden Stellen importiert.
```

**Breaking Change:**
```
feat(config): proxy-konfiguration auf USE_PROXY und PROXY_PREFIX umgestellt

BREAKING CHANGE: Die bisherige Variable FLASK_PROXY_URL wird nicht mehr
unterstützt. Bestehende .env-Dateien müssen angepasst werden.
```

**Issue referenzieren:**
```
fix(shopping): artikel-kategorie wird beim bearbeiten nicht zurückgesetzt

Closes #42
```

---

## Regeln

- Beschreibung im **Imperativ** und **Kleinschreibung**: `add feature` nicht `added feature` oder `Feature hinzugefügt`
- Kein Punkt am Ende der Beschreibung
- Beschreibung auf **Deutsch oder Englisch** – Hauptsache konsistent innerhalb eines Commits
- Breaking Changes werden im Footer mit `BREAKING CHANGE:` markiert und wirken sich auf die **Major-Version** aus (SemVer)
- Kein `feat` für reine Formatierungs- oder Tipp-Korrekturen → `style` oder `docs` verwenden

---

## Zusammenhang mit SemVer

Conventional Commits und Semantic Versioning (SemVer) greifen ineinander:

| Commit-Type | SemVer-Auswirkung |
|---|---|
| `fix` | PATCH (`1.0.0` → `1.0.1`) |
| `feat` | MINOR (`1.0.0` → `1.1.0`) |
| `BREAKING CHANGE` (Footer) | MAJOR (`1.0.0` → `2.0.0`) |
| Alles andere | Kein Release erforderlich |