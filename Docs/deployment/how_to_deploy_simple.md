# Schnell-Deployment (Simple)

Die einfachste Methode, Hauskeeping lokal oder auf einem Server zum Laufen zu bringen.
Ohne PostgreSQL, ohne Reverse Proxy, ohne Push-Notifications -- nur die Kernfunktionen mit einer SQLite-Datenbank.

---

## Voraussetzungen

- Python 3.10+
- pip
- Git (optional, alternativ ZIP-Download)

---

## Schritte

### 1. Repository holen

**Per Git:**

```bash
git clone https://github.com/iLollek/hauskeeping.git
cd hauskeeping
```

**Oder als ZIP:**

Auf der [GitHub-Seite](https://github.com/iLollek/hauskeeping) oben rechts auf **Code > Download ZIP** klicken, entpacken und in den Ordner wechseln.

### 2. Virtual Environment erstellen und aktivieren

```bash
python3 -m venv venv
source venv/bin/activate       # Linux / macOS
# venv\Scripts\activate        # Windows
```

### 3. Dependencies installieren

```bash
pip install -r requirements.txt
```

### 4. Minimale `.env` anlegen

Fuer das Simple-Deployment reicht eine `.env` mit wenigen Zeilen.
**Nicht** einfach die `.env.example` unbearbeitet kopieren -- sie enthaelt Platzhalter-SMTP-Daten (`smtp.example.com`), die zu fehlgeschlagenen Verbindungsversuchen fuehren wuerden.

Stattdessen eine minimale `.env` erstellen:

```bash
cat <<'EOF' > .env
SECRET_KEY=ein-langer-zufaelliger-string
DATABASE_URL=sqlite:///hauskeeping.db
EOF
```

Das genuegt. SQLite wird als Datenbank verwendet, SMTP und Push-Notifications bleiben deaktiviert.

> Fuer Produktivbetrieb sollte `SECRET_KEY` auf einen echten zufaelligen String gesetzt werden, z. B. via `python3 -c "import secrets; print(secrets.token_hex(32))"`.
> E-Mail- und Push-Benachrichtigungen lassen sich spaeter jederzeit nachkonfigurieren -- siehe `.env.example` fuer alle verfuegbaren Optionen.

### 5. Datenbank initialisieren

```bash
flask init-db
```

### 6. Admin-Benutzer erstellen

```bash
flask create-admin
```

### 7. App starten

```bash
python run.py
```

Hauskeeping laeuft jetzt unter **http://localhost:5000**.

---

## Was ist in diesem Setup enthalten?

| Feature | Status |
|---|---|
| Aufgabenverwaltung & Kalender | Funktioniert |
| Einkaufsliste | Funktioniert |
| Mehrbenutzer | Funktioniert |
| SQLite-Datenbank | Automatisch (kein Setup noetig) |
| E-Mail-Benachrichtigungen | Nur wenn SMTP in `.env` konfiguriert |
| Web Push Notifications | Nur wenn VAPID-Keys in `.env` konfiguriert |
| PostgreSQL | Nicht aktiv (SQLite als Fallback) |
| Reverse Proxy | Nicht aktiv |

---

## Hinweise

- Die SQLite-Datenbank wird automatisch im Projektordner als `hauskeeping.db` angelegt.
- Fuer Produktivbetrieb mit mehreren gleichzeitigen Nutzern wird PostgreSQL empfohlen.
- Host und Port lassen sich ueber die Umgebungsvariablen `HOST` und `PORT` in der `.env` aendern (Standard: `0.0.0.0:5000`).
