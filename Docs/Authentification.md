# Authentifizierung & Rollen – Hauskeeping

Dieses Dokument beschreibt, wie User sich in Hauskeeping identifizieren, wie neue Konten entstehen und welche Berechtigungen die zwei Rollen **Mitglied** und **Hausmeister** haben.

---

## 1. Ersteinrichtung

Wenn eine neue Hauskeeping-Instanz aufgesetzt wird, existiert noch kein einziges Konto. Der erste Schritt ist deshalb die Erstellung eines initialen Hausmeister-Kontos über die CLI:

```bash
flask create-admin
```

Dieser Befehl erstellt einen ersten User mit der Rolle **Hausmeister**. Ab diesem Punkt ist die Instanz betriebsbereit und weitere User können über das Invite-System hinzugefügt werden.

---

## 2. Registrierung per Invite-Code

Hauskeeping ist nicht öffentlich zugänglich. Es gibt keine offene Registrierung – ein neues Konto kann nur mit einem gültigen **Invite-Code** erstellt werden.

### Ablauf

1. Ein Hausmeister generiert einen Invite-Code in den Einstellungen
2. Der Invite-Code wird an die einzuladende Person weitergegeben (z. B. per Messenger)
3. Die Person öffnet die Registrierungsseite und gibt den Code ein
4. Nach erfolgreicher Validierung kann sie ein Konto mit Benutzername und Passwort anlegen
5. Das neue Konto erhält automatisch die Rolle **Mitglied**
6. Der Invite-Code wird nach einmaliger Verwendung ungültig

### Eigenschaften von Invite-Codes

| Eigenschaft | Wert |
|---|---|
| Gültigkeitsdauer | Konfigurierbar (Standard: 7 Tage) |
| Verwendungen | Einmalig |
| Erstellt von | Hausmeister |
| Ablauf nach Nutzung | Code wird deaktiviert |

> **Hinweis:** Invite-Codes sollten nicht öffentlich geteilt werden. Wer einen Code erhält, kann sich ein vollwertiges Konto anlegen.

---

## 3. Rollen

Hauskeeping kennt zwei Rollen. Der Grundsatz ist: **Alles, was das Mitglied kann, kann der Hausmeister auch.** Die Trennung ist bewusst schlank gehalten – es gibt keine feingranulare Rechteverwaltung. Der Hausmeister hat zusätzlich Zugriff auf administrative Funktionen.

### Mitglied

Die Standardrolle für alle über Invite-Code registrierten User.

**Berechtigungen (Beispiele):**
- Aufgaben erstellen, bearbeiten und als erledigt markieren
- Einkaufsliste verwalten
- Eigenes Profil bearbeiten
- Benachrichtigungseinstellungen verwalten

### Hausmeister

Der Hausmeister ist die Vertrauensrolle der Instanz. Er kann alles, was ein Mitglied kann – zusätzlich hat er Zugriff auf administrative Funktionen.

**Zusätzliche Berechtigungen (Beispiele):**
- Invite-Codes erstellen und verwalten
- Mitglieder entfernen
- Andere User zur Rolle Hausmeister ernennen
- Zukünftige administrative Funktionen

> **Wichtig:** Wer zum Hausmeister ernannt wird, erhält dieselben Rechte wie der ernennende Hausmeister – einschließlich der Möglichkeit, weitere Hausmeister zu ernennen. Diese Rolle sollte nur an Personen vergeben werden, denen man vollständig vertraut.

### Übersicht

| Funktion | Mitglied | Hausmeister |
|---|---|---|
| Aufgaben verwalten | ✅ | ✅ |
| Einkaufsliste verwalten | ✅ | ✅ |
| Eigenes Profil bearbeiten | ✅ | ✅ |
| Invite-Codes erstellen | ❌ | ✅ |
| Mitglieder entfernen | ❌ | ✅ |
| Hausmeister ernennen | ❌ | ✅ |
| Zukünftige Admin-Funktionen | ❌ | ✅ |

---

## 4. Datenbankmodell

### User-Tabelle (relevante Felder)

| Feld | Typ | Bedeutung |
|---|---|---|
| `id` | Integer PK | Eindeutige User-ID |
| `username` | String | Anzeigename |
| `password_hash` | String | Gehashtes Passwort (z. B. bcrypt) |
| `role` | Enum / String | `"member"` oder `"hausmeister"` |
| `created_at` | DateTime | Registrierungszeitpunkt |
| `invited_by` | FK → User | Der User, dessen Invite-Code verwendet wurde |

### InviteCode-Tabelle

| Feld | Typ | Bedeutung |
|---|---|---|
| `id` | Integer PK | |
| `code` | String | Zufällig generierter Code (z. B. UUID) |
| `created_by` | FK → User | Der Hausmeister, der den Code erstellt hat |
| `created_at` | DateTime | Erstellungszeitpunkt |
| `expires_at` | DateTime | Ablaufzeitpunkt |
| `used_by` | FK → User (nullable) | Der User, der den Code eingelöst hat |
| `used_at` | DateTime (nullable) | Einlösezeitpunkt |
| `is_active` | Boolean | `False`, sobald der Code verwendet wurde oder abgelaufen ist |

---

## 5. Passwörter & Sicherheit

- Passwörter werden **niemals im Klartext** gespeichert
- Hashing erfolgt mit **bcrypt** über `flask-bcrypt` oder `werkzeug.security`
- Sessions werden über **Flask-Login** verwaltet
- Es gibt keine passwortlose Authentifizierung oder OAuth – Hauskeeping ist eine Self-Hosted-App für den privaten Gebrauch

---

## Kurzübersicht

| Thema | Vorgehen |
|---|---|
| Erster User | `flask create-admin` bei der Ersteinrichtung |
| Registrierung | Nur mit gültigem Invite-Code möglich |
| Standardrolle | Mitglied |
| Admin-Rolle | Hausmeister |
| Rollen-Vergabe | Hausmeister kann andere User zum Hausmeister ernennen |
| Passwort-Hashing | bcrypt |
| Session-Management | Flask-Login |