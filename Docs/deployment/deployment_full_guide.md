# Hauskeeping – Vollständiger Deployment-Guide

Dieser Guide beschreibt die vollständige Installation und Konfiguration von Hauskeeping auf einem Linux-System (Debian/Raspbian/Ubuntu). Er deckt alle verfügbaren Funktionen ab: Datenbank, E-Mail-Benachrichtigungen, Web Push / VAPID, Reverse Proxy (Nginx und Apache) sowie den Betrieb als systemd-Dienst.

> Raspberry Pi OS basiert auf Debian und verhält sich identisch zu anderen Debian-Systemen. Dieser Guide gilt für beide.

---

## Inhaltsverzeichnis

1. [Voraussetzungen](#1-voraussetzungen)
2. [Repository holen](#2-repository-holen)
3. [Python-Umgebung einrichten](#3-python-umgebung-einrichten)
4. [Dependencies installieren](#4-dependencies-installieren)
5. [Konfiguration – die `.env`-Datei](#5-konfiguration--die-env-datei)
6. [Datenbank einrichten](#6-datenbank-einrichten)
7. [Admin-Account erstellen](#7-admin-account-erstellen)
8. [Anwendung starten (Test)](#8-anwendung-starten-test)
9. [VAPID-Keys generieren (Push Notifications)](#9-vapid-keys-generieren-push-notifications)
10. [E-Mail-Benachrichtigungen konfigurieren](#10-e-mail-benachrichtigungen-konfigurieren)
11. [Reverse Proxy einrichten](#11-reverse-proxy-einrichten)
    - [11a. Nginx](#11a-nginx)
    - [11b. Apache](#11b-apache)
    - [11c. TLS-Zertifikat mit Let's Encrypt](#11c-tls-zertifikat-mit-lets-encrypt)
12. [Systemd-Dienst einrichten](#12-systemd-dienst-einrichten)
13. [Vollständige `.env`-Referenz](#13-vollständige-env-referenz)
14. [Sicherheitshinweise](#14-sicherheitshinweise)
15. [Fehlerbehebung](#15-fehlerbehebung)

---

## 1. Voraussetzungen

### Systemanforderungen

- Linux-System (Debian 11+, Raspberry Pi OS, Ubuntu 20.04+)
- **64-Bit OS** empfohlen – einige Python-Packages (z. B. `pywebpush`) sind unter 32-Bit nicht verfügbar oder instabil
- Internetzugang für Paketinstallation und (optional) Let's Encrypt

### Benötigte Software

```bash
sudo apt update && sudo apt install -y python3 python3-pip python3-venv git
```

Versionen prüfen:

```bash
python3 --version   # 3.10 oder neuer erforderlich
pip3 --version
git --version
```

### Optional, aber empfohlen

| Komponente | Grund |
|---|---|
| Nginx oder Apache | HTTPS, Subpath-Betrieb, Lastverteilung |
| PostgreSQL | Performanter und robuster als SQLite im Produktivbetrieb |
| Certbot | Automatische TLS-Zertifikate via Let's Encrypt |

---

## 2. Repository holen

### Per Git (empfohlen)

```bash
git clone https://github.com/iLollek/hauskeeping.git /opt/hauskeeping
cd /opt/hauskeeping
```

### Als ZIP-Download

Auf der [GitHub-Seite](https://github.com/iLollek/hauskeeping) oben rechts auf **Code → Download ZIP** klicken, dann:

```bash
unzip hauskeeping-main.zip -d /opt/
mv /opt/hauskeeping-main /opt/hauskeeping
cd /opt/hauskeeping
```

---

## 3. Python-Umgebung einrichten

Es wird dringend empfohlen, ein Virtual Environment zu verwenden, um Abhängigkeitskonflikte mit dem System-Python zu vermeiden.

```bash
cd /opt/hauskeeping
python3 -m venv venv
source venv/bin/activate
```

> Das `(venv)`-Präfix in der Shell zeigt an, dass die Umgebung aktiv ist. Alle folgenden Befehle sollten innerhalb dieser Umgebung ausgeführt werden.

---

## 4. Dependencies installieren

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Installierte Pakete:**

| Paket | Version | Zweck |
|---|---|---|
| Flask | 3.1.0 | Web-Framework |
| Flask-SQLAlchemy | 3.1.1 | ORM / Datenbankanbindung |
| Flask-Migrate | 4.0.7 | Datenbankmigrationen (Alembic) |
| Flask-Login | 0.6.3 | Session-Verwaltung |
| Flask-Bcrypt | 1.0.1 | Passwort-Hashing |
| Flask-Mail | 0.10.0 | E-Mail via SMTP |
| python-dotenv | 1.0.1 | `.env`-Datei laden |
| pywebpush | 2.0.1 | Web Push / VAPID |
| APScheduler | 3.10.4 | Geplante Jobs (E-Mail, Push) |
| psycopg2-binary | 2.9.10 | PostgreSQL-Treiber |

---

## 5. Konfiguration – die `.env`-Datei

Hauskeeping liest seine gesamte Konfiguration aus einer `.env`-Datei im Projektverzeichnis. Diese Datei **darf niemals in Git eingecheckt werden** – sie enthält Secrets.

### `.env` anlegen

```bash
cp .env.example .env
nano .env   # oder einen anderen Editor verwenden
```

Die `.env.example` enthält Platzhalter. Die folgenden Abschnitte erklären alle Variablen im Detail.

---

### 5.1 Flask-Grundkonfiguration

```env
# Pflichtfeld – niemals leer lassen, niemals den Standard-Wert behalten
SECRET_KEY=ersetze-mich-durch-einen-echten-zufaelligen-string

# Bind-Adresse – 0.0.0.0 erlaubt Verbindungen von außen
HOST=0.0.0.0

# Port, auf dem Hauskeeping lauscht
PORT=5000
```

**`SECRET_KEY` generieren:**

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Den ausgegebenen String direkt in die `.env` kopieren. Dieser Schlüssel sichert Flask-Sessions und CSRF-Tokens. Bei Verlust oder Bekanntwerden müssen alle Nutzer sich erneut anmelden.

---

### 5.2 Datenbank

Hauskeeping unterstützt zwei Datenbank-Backends:

#### SQLite (Entwicklung / einfache Setups)

```env
DATABASE_URL=sqlite:///hauskeeping.db
```

Die Datei `hauskeeping.db` wird im Projektverzeichnis angelegt. Kein weiterer Setup erforderlich.

> **Achtung:** SQLite ist nicht für Mehrbenutzer-Produktivbetrieb mit gleichzeitigen Schreibzugriffen optimiert. Für den Heimgebrauch mit wenigen Nutzern ist es jedoch ausreichend.

#### PostgreSQL (Produktivbetrieb – empfohlen)

```env
DATABASE_URL=postgresql://hauskeeping_user:sicheres_passwort@localhost:5432/hauskeeping
```

PostgreSQL-Datenbank und Nutzer einrichten (als `root` oder `postgres`):

```bash
sudo apt install -y postgresql postgresql-contrib
sudo systemctl enable --now postgresql

sudo -u postgres psql <<'SQL'
CREATE USER hauskeeping_user WITH PASSWORD 'sicheres_passwort';
CREATE DATABASE hauskeeping OWNER hauskeeping_user;
GRANT ALL PRIVILEGES ON DATABASE hauskeeping TO hauskeeping_user;
SQL
```

> Das Passwort in obigem Befehl muss mit dem in `DATABASE_URL` übereinstimmen. Wähle ein starkes, einzigartiges Passwort.

---

### 5.3 Reverse Proxy

Wenn Hauskeeping hinter einem Nginx oder Apache unter einem Subpath betrieben wird (z. B. `https://meinserver.de/hauskeeping`), müssen diese Variablen gesetzt werden:

```env
USE_PROXY=true
PROXY_PREFIX=/hauskeeping
```

Ohne Reverse Proxy (direkter Zugriff auf Port 5000):

```env
USE_PROXY=false
```

> Diese Einstellung aktiviert den `ProxyFix`-Middleware in Werkzeug. Ohne sie generiert Flask falsche URLs für Redirects und statische Dateien, wenn es hinter einem Proxy betrieben wird.

---

### 5.4 E-Mail (SMTP)

E-Mail-Benachrichtigungen sind optional. Ohne SMTP-Konfiguration ist die Funktion schlicht deaktiviert – die Anwendung läuft trotzdem.

```env
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USERNAME=user@example.com
MAIL_PASSWORD=dein-passwort-oder-app-passwort
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_DEFAULT_SENDER=hauskeeping@example.com
```

Die vollständige SMTP-Konfiguration mit Beispielen für gängige Anbieter folgt in [Abschnitt 10](#10-e-mail-benachrichtigungen-konfigurieren).

---

### 5.5 VAPID / Web Push Notifications

VAPID-Keys ermöglichen browser-native Push-Benachrichtigungen auf Android und iOS (PWA). Ohne diese Konfiguration sind Push-Notifications deaktiviert.

```env
VAPID_PRIVATE_KEY=dein-privater-key
VAPID_PUBLIC_KEY=dein-oeffentlicher-key
VAPID_CLAIM_EMAIL=admin@example.com
```

Wie die Keys generiert werden, erklärt [Abschnitt 9](#9-vapid-keys-generieren-push-notifications).

---

## 6. Datenbank einrichten

Nachdem die `.env` konfiguriert ist, muss das Datenbankschema initialisiert werden.

```bash
cd /opt/hauskeeping
source venv/bin/activate

# Alle ausstehenden Migrationen anwenden (legt Tabellen an)
flask db upgrade
```

> `flask db upgrade` ist idempotent – es kann problemlos mehrfach ausgeführt werden und wendet nur fehlende Migrationen an. Nach jedem Update von Hauskeeping sollte dieser Befehl erneut ausgeführt werden.

**Bei Fehlern:** Sicherstellen, dass `DATABASE_URL` korrekt gesetzt ist und der Datenbankserver erreichbar ist (bei PostgreSQL).

---

## 7. Admin-Account erstellen

Nach der Datenbankinitialisierung den ersten Hausmeister-Account (Administrator) anlegen:

```bash
flask create-admin
```

Das Kommando fragt interaktiv nach Benutzername, E-Mail und Passwort. Dieser Account erhält die Rolle `hausmeister` und hat Zugriff auf den Admin-Bereich.

> Mit dem Hausmeister-Account können Einladungscodes generiert werden, mit denen weitere Nutzer sich registrieren können.

---

## 8. Anwendung starten (Test)

Zum Testen der Installation:

```bash
cd /opt/hauskeeping
source venv/bin/activate
python run.py
```

Die Anwendung ist nun unter `http://<server-ip>:5000` erreichbar. Mit `Strg+C` beenden.

> Für den dauerhaften Betrieb wird ein systemd-Dienst empfohlen – siehe [Abschnitt 12](#12-systemd-dienst-einrichten).

---

## 9. VAPID-Keys generieren (Push Notifications)

Web Push Notifications (für Android und iOS-PWA) erfordern VAPID-Keys. Diese werden einmalig generiert und müssen dauerhaft in der `.env` gespeichert bleiben.

**Wichtig:** Bei Verlust der Keys müssen sich alle Nutzer erneut für Push-Benachrichtigungen registrieren (Browser-Subscriptions werden ungültig).

### Keys generieren

```bash
cd /opt/hauskeeping
source venv/bin/activate

python3 - <<'EOF'
from py_vapid import Vapid
vapid = Vapid()
vapid.generate_keys()
print("VAPID_PRIVATE_KEY=" + vapid.private_key.private_bytes(
    encoding=__import__('cryptography.hazmat.primitives.serialization', fromlist=['Encoding']).Encoding.PEM,
    format=__import__('cryptography.hazmat.primitives.serialization', fromlist=['PrivateFormat']).PrivateFormat.TraditionalOpenSSL,
    encryption_algorithm=__import__('cryptography.hazmat.primitives.serialization', fromlist=['NoEncryption']).NoEncryption()
).decode().strip())
print("VAPID_PUBLIC_KEY=" + vapid.public_key.public_bytes(
    encoding=__import__('cryptography.hazmat.primitives.serialization', fromlist=['Encoding']).Encoding.X962,
    format=__import__('cryptography.hazmat.primitives.serialization', fromlist=['PublicFormat']).PublicFormat.UncompressedPoint
).__import__('base64').b64encode().decode())
EOF
```

Alternativ – einfacher via `pywebpush`-CLI:

```bash
vapid --gen
```

Dies erzeugt zwei Dateien: `private_key.pem` und `public_key.pem`. Deren Inhalte in die `.env` übernehmen:

```bash
# Private Key (einzeilig, PEM-Header entfernen):
VAPID_PRIVATE_KEY=$(cat private_key.pem | grep -v -- '-----' | tr -d '\n')

# Public Key (einzeilig):
VAPID_PUBLIC_KEY=$(cat public_key.pem | grep -v -- '-----' | tr -d '\n')
```

Die `.env` entsprechend anpassen:

```env
VAPID_PRIVATE_KEY=<ausgabe-des-obigen-befehls>
VAPID_PUBLIC_KEY=<ausgabe-des-obigen-befehls>
VAPID_CLAIM_EMAIL=admin@meinserver.de
```

> `VAPID_CLAIM_EMAIL` ist die Kontakt-E-Mail, die bei Push-Diensten (Google, Apple) hinterlegt wird, falls es Probleme mit dem Push-Endpunkt gibt. Sie wird nicht an Nutzer übermittelt.

### Push Notifications aktivieren (Nutzerseite)

Nutzer aktivieren Push-Benachrichtigungen in den **Einstellungen** innerhalb von Hauskeeping. Der Browser zeigt dann einen Erlaubnis-Dialog. Ohne Nutzer-Opt-in werden keine Benachrichtigungen gesendet.

**Plattform-Anforderungen:**

| Plattform | Voraussetzung |
|---|---|
| Android (Chrome, Firefox, Samsung Internet) | Browser-Erlaubnis genügt |
| iOS (Safari) | iOS 16.4+, Hauskeeping als PWA zum Homescreen hinzufügen |
| iOS (Chrome, Firefox) | Nicht unterstützt (Apple-Einschränkung) |

---

## 10. E-Mail-Benachrichtigungen konfigurieren

E-Mail-Notifications senden wöchentliche Zusammenfassungen an Nutzer (offene, überfällige und bald fällige Aufgaben). Der Versand erfolgt über einen SMTP-Server.

### 10.1 Gmail (Google Mail)

Google erfordert ein **App-Passwort**, wenn 2-Faktor-Authentifizierung aktiviert ist (empfohlen).

App-Passwort erstellen: [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)

```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=deine-adresse@gmail.com
MAIL_PASSWORD=xxxx-xxxx-xxxx-xxxx   # App-Passwort, nicht dein Google-Passwort
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_DEFAULT_SENDER=deine-adresse@gmail.com
```

### 10.2 Microsoft Outlook / Office 365

```env
MAIL_SERVER=smtp.office365.com
MAIL_PORT=587
MAIL_USERNAME=deine-adresse@outlook.com
MAIL_PASSWORD=dein-passwort
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_DEFAULT_SENDER=deine-adresse@outlook.com
```

### 10.3 Eigener SMTP-Server (z. B. Postfix, Mailcow)

```env
MAIL_SERVER=mail.meinserver.de
MAIL_PORT=587
MAIL_USERNAME=hauskeeping@meinserver.de
MAIL_PASSWORD=smtp-passwort
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_DEFAULT_SENDER=hauskeeping@meinserver.de
```

Für SMTP über Port 465 (SMTPS / implizites SSL):

```env
MAIL_PORT=465
MAIL_USE_TLS=false
MAIL_USE_SSL=true
```

### 10.4 Deaktivieren von E-Mail

Wenn `MAIL_SERVER` leer ist oder nicht gesetzt wird, ist die E-Mail-Funktion deaktiviert. Nutzer sehen in den Einstellungen keinen Fehler – die Option ist schlicht inaktiv.

### 10.5 Versandzeitplan

E-Mails werden automatisch durch APScheduler gesendet. Der Standard-Versandzeitpunkt ist **montags um 07:00 Uhr UTC**. Nutzer können in den Einstellungen den Wochentag anpassen.

---

## 11. Reverse Proxy einrichten

Ein Reverse Proxy (Nginx oder Apache) ist für den Produktivbetrieb empfohlen. Er übernimmt:

- **TLS-Terminierung** (HTTPS via Let's Encrypt)
- **Subpath-Routing** (z. B. `/hauskeeping` neben anderen Apps)
- **Sicherheits-Header** und Zugangskontrolle

Hauskeeping muss im Proxy-Modus gestartet werden:

```env
USE_PROXY=true
PROXY_PREFIX=/hauskeeping
```

---

### 11a. Nginx

#### Installation

```bash
sudo apt install -y nginx
sudo systemctl enable --now nginx
```

#### Konfigurationsdatei anlegen

```bash
sudo nano /etc/nginx/sites-available/hauskeeping
```

Inhalt:

```nginx
server {
    listen 80;
    server_name meinserver.de;

    # Temporär für HTTP (wird nach Certbot auf HTTPS umgeleitet)
    location /hauskeeping {
        proxy_pass         http://127.0.0.1:5000;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_set_header   X-Forwarded-Prefix /hauskeeping;

        # WebSocket-Unterstützung (für zukünftige Erweiterungen)
        proxy_http_version 1.1;
        proxy_set_header   Upgrade    $http_upgrade;
        proxy_set_header   Connection "upgrade";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout    60s;
        proxy_read_timeout    60s;
    }
}
```

Konfiguration aktivieren und testen:

```bash
sudo ln -s /etc/nginx/sites-available/hauskeeping /etc/nginx/sites-enabled/
sudo nginx -t          # Syntaxprüfung
sudo systemctl reload nginx
```

Nach dem Einrichten von Let's Encrypt (Abschnitt 11c) wird Certbot die Konfiguration automatisch für HTTPS erweitern.

#### Fertige HTTPS-Konfiguration (nach Certbot)

```nginx
server {
    listen 443 ssl;
    server_name meinserver.de;

    ssl_certificate     /etc/letsencrypt/live/meinserver.de/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/meinserver.de/privkey.pem;

    # Sicherheits-Header
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options SAMEORIGIN always;
    add_header X-Content-Type-Options nosniff always;

    location /hauskeeping {
        proxy_pass         http://127.0.0.1:5000;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_set_header   X-Forwarded-Prefix /hauskeeping;

        proxy_http_version 1.1;
        proxy_set_header   Upgrade    $http_upgrade;
        proxy_set_header   Connection "upgrade";

        proxy_connect_timeout 60s;
        proxy_send_timeout    60s;
        proxy_read_timeout    60s;
    }
}

# HTTP → HTTPS Redirect
server {
    listen 80;
    server_name meinserver.de;
    return 301 https://$host$request_uri;
}
```

---

### 11b. Apache

#### Installation und Module aktivieren

```bash
sudo apt install -y apache2
sudo a2enmod proxy proxy_http headers ssl rewrite
sudo systemctl enable --now apache2
sudo systemctl restart apache2
```

#### VirtualHost-Konfiguration anlegen

```bash
sudo nano /etc/apache2/sites-available/hauskeeping.conf
```

Inhalt:

```apache
<VirtualHost *:80>
    ServerName meinserver.de

    # Temporäre HTTP-Konfiguration (wird nach Certbot angepasst)
    ProxyPreserveHost On
    ProxyPass        /hauskeeping http://127.0.0.1:5000/hauskeeping
    ProxyPassReverse /hauskeeping http://127.0.0.1:5000/hauskeeping

    RequestHeader set X-Forwarded-Proto "http"
    RequestHeader set X-Forwarded-For "%{REMOTE_ADDR}s"
</VirtualHost>
```

Aktivieren:

```bash
sudo a2ensite hauskeeping.conf
sudo apache2ctl configtest
sudo systemctl reload apache2
```

#### Fertige HTTPS-Konfiguration (nach Certbot)

```apache
<VirtualHost *:443>
    ServerName meinserver.de

    SSLEngine on
    SSLCertificateFile    /etc/letsencrypt/live/meinserver.de/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/meinserver.de/privkey.pem

    # Sicherheits-Header
    Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"
    Header always set X-Frame-Options SAMEORIGIN
    Header always set X-Content-Type-Options nosniff

    ProxyPreserveHost On
    ProxyPass        /hauskeeping http://127.0.0.1:5000/hauskeeping
    ProxyPassReverse /hauskeeping http://127.0.0.1:5000/hauskeeping

    RequestHeader set X-Forwarded-Proto "https"
    RequestHeader set X-Forwarded-For "%{REMOTE_ADDR}s"
</VirtualHost>

<VirtualHost *:80>
    ServerName meinserver.de
    Redirect permanent / https://meinserver.de/
</VirtualHost>
```

---

### 11c. TLS-Zertifikat mit Let's Encrypt

Let's Encrypt stellt kostenlose, automatisch erneuerbare TLS-Zertifikate aus.

#### Voraussetzungen

- Domain, die auf die Server-IP zeigt (A-Record gesetzt)
- Port 80 und 443 im Router weitergeleitet
- Nginx oder Apache bereits installiert und konfiguriert

#### Nginx

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d meinserver.de
```

Certbot erkennt die Nginx-Konfiguration automatisch, beantragt das Zertifikat und richtet die HTTPS-Umleitung ein.

#### Apache

```bash
sudo apt install -y certbot python3-certbot-apache
sudo certbot --apache -d meinserver.de
```

#### Automatische Erneuerung testen

Certbot richtet automatisch einen Cron-Job ein. Erneuerung testen:

```bash
sudo certbot renew --dry-run
```

---

## 12. Systemd-Dienst einrichten

Ein systemd-Dienst sorgt dafür, dass Hauskeeping automatisch beim Systemstart gestartet wird und nach einem Absturz neu startet.

### Service-Datei erstellen

```bash
sudo nano /etc/systemd/system/hauskeeping.service
```

Inhalt:

```ini
[Unit]
Description=Hauskeeping Web App
Documentation=https://github.com/iLollek/hauskeeping
After=network.target
# Bei PostgreSQL: nach dem Datenbankdienst starten
# After=network.target postgresql.service

[Service]
Type=simple
User=www-data
Group=www-data

WorkingDirectory=/opt/hauskeeping
EnvironmentFile=/opt/hauskeeping/.env
ExecStart=/opt/hauskeeping/venv/bin/python run.py

# Automatischer Neustart bei Absturz
Restart=always
RestartSec=5

# Sicherheitseinschränkungen
NoNewPrivileges=true
PrivateTmp=true

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=hauskeeping

[Install]
WantedBy=multi-user.target
```

### Berechtigungen setzen

```bash
# Projektverzeichnis dem www-data-Nutzer zugänglich machen
sudo chown -R www-data:www-data /opt/hauskeeping
sudo chmod 750 /opt/hauskeeping
sudo chmod 640 /opt/hauskeeping/.env   # .env nur für Eigentümer lesbar
```

### Dienst aktivieren und starten

```bash
sudo systemctl daemon-reload
sudo systemctl enable hauskeeping
sudo systemctl start hauskeeping
```

### Status und Logs prüfen

```bash
# Status anzeigen
sudo systemctl status hauskeeping

# Live-Logs verfolgen
sudo journalctl -u hauskeeping -f

# Letzte 100 Zeilen
sudo journalctl -u hauskeeping -n 100

# Neustart
sudo systemctl restart hauskeeping

# Stoppen
sudo systemctl stop hauskeeping
```

### Bei PostgreSQL: Startreihenfolge

Wenn PostgreSQL auf demselben Server läuft, muss Hauskeeping erst nach dem Datenbankdienst starten. Die `After`-Zeile in der Service-Datei anpassen:

```ini
After=network.target postgresql.service
```

---

## 13. Vollständige `.env`-Referenz

Eine vollständige, kommentierte `.env` mit allen verfügbaren Variablen:

```env
# =============================================================
# FLASK
# =============================================================

# Sicherheitsschlüssel für Sessions und CSRF-Tokens
# Generieren: python3 -c "import secrets; print(secrets.token_hex(32))"
# PFLICHTFELD – niemals leer lassen!
SECRET_KEY=ersetze-mich-durch-einen-echten-zufaelligen-string

# Bind-Adresse (0.0.0.0 = alle Interfaces, 127.0.0.1 = nur lokal)
HOST=0.0.0.0

# Port
PORT=5000

# =============================================================
# DATENBANK
# =============================================================

# SQLite (einfach, für kleine Setups)
DATABASE_URL=sqlite:///hauskeeping.db

# PostgreSQL (empfohlen für Produktivbetrieb)
# DATABASE_URL=postgresql://hauskeeping_user:sicheres_passwort@localhost:5432/hauskeeping

# =============================================================
# REVERSE PROXY
# =============================================================

# Auf true setzen, wenn Hauskeeping hinter Nginx/Apache läuft
USE_PROXY=false

# Subpath, unter dem Hauskeeping erreichbar ist
# Nur relevant wenn USE_PROXY=true
PROXY_PREFIX=/hauskeeping

# =============================================================
# E-MAIL (SMTP) – optional
# =============================================================

# SMTP-Server (leer lassen = E-Mail deaktiviert)
MAIL_SERVER=smtp.example.com

# SMTP-Port (587 für STARTTLS, 465 für SSL, 25 für unverschlüsselt)
MAIL_PORT=587

# SMTP-Anmeldedaten
MAIL_USERNAME=user@example.com
MAIL_PASSWORD=geheim

# TLS-Modus: STARTTLS (Port 587) oder SSL (Port 465)
MAIL_USE_TLS=true
MAIL_USE_SSL=false

# Absenderadresse der Benachrichtigungs-E-Mails
MAIL_DEFAULT_SENDER=hauskeeping@example.com

# =============================================================
# VAPID / WEB PUSH NOTIFICATIONS – optional
# =============================================================

# Privater VAPID-Key (einzeilig, Base64-kodiert)
VAPID_PRIVATE_KEY=

# Öffentlicher VAPID-Key (einzeilig, Base64-kodiert)
VAPID_PUBLIC_KEY=

# Kontakt-E-Mail für Push-Dienste (wird nicht an Nutzer übermittelt)
VAPID_CLAIM_EMAIL=admin@example.com
```

---

## 14. Sicherheitshinweise

### `.env`-Datei schützen

```bash
# Nur für den Eigentümer lesbar
chmod 600 /opt/hauskeeping/.env
chown www-data:www-data /opt/hauskeeping/.env
```

Die `.env` enthält Passwörter und kryptografische Schlüssel. Sie darf **niemals** in Git eingecheckt oder öffentlich zugänglich sein. Sie ist in `.gitignore` eingetragen.

### `SECRET_KEY`

- Muss ein langer, zufälliger String sein (mindestens 32 Bytes)
- Niemals den Beispielwert aus `.env.example` verwenden
- Bei Kompromittierung sofort austauschen (alle Sessions werden ungültig)

### Datenbank-Passwort (PostgreSQL)

- Starkes, einzigartiges Passwort verwenden
- Dem Datenbanknutzer nur die notwendigen Rechte auf `hauskeeping`-Datenbank geben
- Kein Zugriff von außen auf Port 5432 erlauben (Firewall)

### Firewall

```bash
# Nur notwendige Ports öffnen
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

Flask-Port `5000` **nicht** nach außen öffnen – der Zugriff läuft ausschließlich über den Proxy.

### HTTPS

Niemals Hauskeeping ohne TLS öffentlich betreiben. Alle Passwörter und Session-Tokens werden im Klartext übertragen, wenn kein HTTPS verwendet wird. Let's Encrypt bietet kostenlose Zertifikate.

### Updates

```bash
cd /opt/hauskeeping
source venv/bin/activate

# Neuesten Code holen
git pull

# Neue Dependencies installieren
pip install -r requirements.txt

# Datenbankmigrationen anwenden
flask db upgrade

# Dienst neustarten
sudo systemctl restart hauskeeping
```

---

## 15. Fehlerbehebung

### Anwendung startet nicht

```bash
# Logs prüfen
sudo journalctl -u hauskeeping -n 50

# Manuell starten (zeigt Fehler direkt)
cd /opt/hauskeeping
source venv/bin/activate
python run.py
```

**Häufige Ursachen:**

| Fehler | Ursache | Lösung |
|---|---|---|
| `SECRET_KEY not set` | `.env` fehlt oder `SECRET_KEY` leer | `.env` prüfen und `SECRET_KEY` setzen |
| `ModuleNotFoundError` | Dependencies nicht installiert | `pip install -r requirements.txt` |
| `OperationalError: unable to open database` | SQLite-Pfad falsch oder keine Schreibrechte | Verzeichnis-Rechte prüfen |
| `connection refused` (PostgreSQL) | Datenbankdienst nicht gestartet | `systemctl status postgresql` |
| `FATAL: password authentication failed` | Falsches Datenbankpasswort | `DATABASE_URL` in `.env` prüfen |

### Proxy / Weiterleitung funktioniert nicht

- `USE_PROXY=true` und `PROXY_PREFIX=/hauskeeping` in `.env` gesetzt?
- Nginx/Apache-Konfiguration neu geladen? (`sudo systemctl reload nginx`)
- Nginx-Syntaxfehler? (`sudo nginx -t`)
- Häufiger Fehler: Bei Nginx muss `proxy_pass http://127.0.0.1:5000;` **ohne** Subpath angegeben werden – Flask übernimmt den Subpath selbst.

### E-Mail-Versand schlägt fehl

```bash
# Manuell testen (im venv)
python3 - <<'EOF'
from flask_mail import Mail, Message
from src.hauskeeping import create_app
app = create_app()
with app.app_context():
    from src.hauskeeping.extensions import mail
    msg = Message("Test", sender=app.config["MAIL_DEFAULT_SENDER"], recipients=["test@example.com"])
    msg.body = "Hauskeeping SMTP Test"
    mail.send(msg)
    print("E-Mail erfolgreich gesendet!")
EOF
```

**Häufige Ursachen:**

| Fehler | Ursache | Lösung |
|---|---|---|
| `Authentication failed` | Falsches Passwort | Bei Gmail: App-Passwort verwenden |
| `Connection refused` | Falscher Port oder Server | `MAIL_SERVER` und `MAIL_PORT` prüfen |
| `SSL: WRONG_VERSION_NUMBER` | TLS/SSL-Modus falsch | `MAIL_USE_TLS` und `MAIL_USE_SSL` prüfen |
| `SMTPSenderRefused` | Absenderadresse nicht erlaubt | `MAIL_DEFAULT_SENDER` auf dieselbe Adresse wie `MAIL_USERNAME` setzen |

### Push Notifications kommen nicht an

- VAPID-Keys korrekt gesetzt? Keys dürfen keine Zeilenumbrüche enthalten.
- Hauskeeping muss per **HTTPS** erreichbar sein – Push-APIs funktionieren nur über sichere Verbindungen.
- iOS: Hauskeeping muss als PWA zum Homescreen hinzugefügt worden sein.
- Android: Energiesparmodus kann Benachrichtigungen verzögern – App in Akku-Einstellungen ausnehmen.

### Datenbankmigrationen schlagen fehl

```bash
# Migrationsstatus anzeigen
flask db current
flask db history

# Bei Konflikten: Heads anzeigen
flask db heads
```

---

## Kurzübersicht – Checkliste

| Schritt | Minimal | Produktiv |
|---|---|---|
| Repository klonen | ✅ | ✅ |
| venv + Dependencies | ✅ | ✅ |
| `SECRET_KEY` setzen | ✅ | ✅ |
| SQLite konfigurieren | ✅ | – |
| PostgreSQL konfigurieren | – | ✅ |
| `flask db upgrade` | ✅ | ✅ |
| `flask create-admin` | ✅ | ✅ |
| VAPID-Keys generieren | – | ✅ |
| SMTP konfigurieren | – | ✅ |
| `USE_PROXY=true` setzen | – | ✅ |
| Nginx/Apache einrichten | – | ✅ |
| Let's Encrypt / TLS | – | ✅ |
| systemd-Dienst | – | ✅ |
| Firewall konfigurieren | – | ✅ |
