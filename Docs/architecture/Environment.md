# Hosting & Environment – Hauskeeping

Dieses Dokument beschreibt, wie Hauskeeping gehostet wird, welche Deployment-Varianten es gibt und wie die Umgebungsvariablen konfiguriert werden.

---

## 1. Deployment-Varianten

### Variante A: Direktes Hosting mit Port-Forwarding

Die einfachste Möglichkeit ist, Hauskeeping direkt auf einem Server zu betreiben und den Flask-Port (Standard: `5000`) im Router weiterzuleiten.

**Nachteile:**
- Kein HTTPS ohne zusätzlichen Aufwand (Let's Encrypt direkt auf Flask ist möglich, aber umständlich)
- Port-Forwarding ist nicht in jeder Netzwerkumgebung möglich (z. B. Carrier-Grade NAT, restriktive Router)
- Nicht-Standard-Port (z. B. `5000`) muss nach außen freigegeben werden

Diese Variante eignet sich allenfalls für lokale Netzwerke ohne externen Zugriff.

---

### Variante B: Reverse Proxy (empfohlen)

Die empfohlene Betriebsweise ist ein **Reverse Proxy** (Apache oder Nginx), der vor Hauskeeping sitzt. Der Proxy übernimmt TLS-Terminierung (HTTPS) und leitet Anfragen intern an Flask weiter. Nach außen ist nur Port `443` geöffnet.

**Vorteile:**
- HTTPS out of the box (z. B. via Let's Encrypt / Certbot), wenn bereits konfiguriert
- Nur Port `443` muss weitergeleitet werden
- Hauskeeping kann unter einem Subpath betrieben werden (z. B. `https://meinserver.de/hauskeeping`)
- Mehrere Webapps können parallel auf demselben Server laufen

---

## 2. Proxy-Konfiguration in Hauskeeping

Wenn Hauskeeping hinter einem Reverse Proxy läuft und unter einem Subpath erreichbar ist (z. B. `/hauskeeping`), muss Flask darüber informiert werden. Andernfalls generiert Flask falsche URLs für Redirects, statische Dateien und Blueprints.

Dafür wird die **Werkzeug `DispatcherMiddleware`** oder **`ProxyFix`** eingesetzt. Hauskeeping konfiguriert dies automatisch anhand von zwei Umgebungsvariablen:

### Umgebungsvariablen

| Variable | Typ | Bedeutung |
|---|---|---|
| `USE_PROXY` | Boolean (`true` / `false`) | Aktiviert den Proxy-Modus |
| `PROXY_PREFIX` | String | Der URL-Subpath, unter dem Hauskeeping erreichbar ist |

**Beispiel `.env`:**

```env
USE_PROXY=true
PROXY_PREFIX=/hauskeeping
```

Wenn `USE_PROXY=false` oder nicht gesetzt ist, läuft Hauskeeping ohne Proxy-Konfiguration – z. B. direkt unter `http://localhost:5000`.

### Implementierung in `app.py` / `run.py`

```python
import os
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple

if os.getenv("USE_PROXY", "false").lower() == "true":
    prefix = os.getenv("PROXY_PREFIX", "")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    app.config["APPLICATION_ROOT"] = prefix
```

> **Hinweis:** `ProxyFix` sorgt dafür, dass Flask die korrekten Header (`X-Forwarded-For`, `X-Forwarded-Proto`) des Proxys versteht und HTTPS-URLs korrekt generiert.

---

## 3. Apache-Konfiguration

### Voraussetzungen

```bash
sudo a2enmod proxy proxy_http headers ssl
sudo systemctl restart apache2
```

### VirtualHost-Konfiguration

```apache
<VirtualHost *:443>
    ServerName meinserver.de
    
    SSLEngine on
    SSLCertificateFile    /etc/letsencrypt/live/meinserver.de/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/meinserver.de/privkey.pem

    # Hauskeeping unter /hauskeeping
    ProxyPass        /hauskeeping http://127.0.0.1:5000/hauskeeping
    ProxyPassReverse /hauskeeping http://127.0.0.1:5000/hauskeeping

    # Korrekte Header an Flask weiterleiten
    RequestHeader set X-Forwarded-Proto "https"
    RequestHeader set X-Forwarded-For "%{REMOTE_ADDR}s"
</VirtualHost>

# HTTP → HTTPS Redirect
<VirtualHost *:80>
    ServerName meinserver.de
    Redirect permanent / https://meinserver.de/
</VirtualHost>
```

### TLS-Zertifikat mit Certbot

```bash
sudo apt install certbot python3-certbot-apache
sudo certbot --apache -d meinserver.de
```

Certbot passt die Apache-Konfiguration automatisch an und richtet eine automatische Erneuerung ein.

---

## 4. Nginx-Konfiguration

### Voraussetzungen

```bash
sudo apt install nginx certbot python3-certbot-nginx
```

### Server-Block-Konfiguration

```nginx
server {
    listen 443 ssl;
    server_name meinserver.de;

    ssl_certificate     /etc/letsencrypt/live/meinserver.de/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/meinserver.de/privkey.pem;

    # Hauskeeping unter /hauskeeping
    location /hauskeeping {
        proxy_pass         http://127.0.0.1:5000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }
}

# HTTP → HTTPS Redirect
server {
    listen 80;
    server_name meinserver.de;
    return 301 https://$host$request_uri;
}
```

### TLS-Zertifikat mit Certbot

```bash
sudo certbot --nginx -d meinserver.de
```

---

## 5. Hauskeeping als Systemdienst

Damit Hauskeeping automatisch startet und nach einem Absturz neu gestartet wird, empfiehlt sich ein **systemd-Service**.

```ini
# /etc/systemd/system/hauskeeping.service

[Unit]
Description=Hauskeeping Web App
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/hauskeeping
EnvironmentFile=/opt/hauskeeping/.env
ExecStart=/opt/hauskeeping/venv/bin/python run.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable hauskeeping
sudo systemctl start hauskeeping
```

---

## 6. Umgebungsvariablen – Übersicht

Alle Konfiguration erfolgt über die `.env`-Datei im Projektverzeichnis. Eine `.env.example` liegt dem Repository bei.

| Variable | Beispielwert | Bedeutung |
|---|---|---|
| `SECRET_KEY` | `ein-langer-zufaelliger-string` | Flask Session-Key – niemals öffentlich teilen |
| `DATABASE_URL` | `sqlite:///hauskeeping.db` | Datenbankverbindung |
| `USE_PROXY` | `true` | Reverse-Proxy-Modus aktivieren |
| `PROXY_PREFIX` | `/hauskeeping` | Subpath des Proxys |
| `MAIL_SERVER` | `smtp.example.com` | SMTP-Server für E-Mail-Notifications |
| `MAIL_PORT` | `587` | SMTP-Port |
| `MAIL_USERNAME` | `user@example.com` | SMTP-Login |
| `MAIL_PASSWORD` | `geheim` | SMTP-Passwort |
| `VAPID_PRIVATE_KEY` | `...` | Push Notification Key (privat) |
| `VAPID_PUBLIC_KEY` | `...` | Push Notification Key (öffentlich) |
| `VAPID_CLAIM_EMAIL` | `admin@example.com` | Kontakt-E-Mail für VAPID |

> **Hinweis:** Die `.env`-Datei darf **niemals** in das Git-Repository eingecheckt werden. Sie ist in `.gitignore` eingetragen.

---

## Kurzübersicht

| Thema | Empfehlung |
|---|---|
| Deployment | Reverse Proxy (Apache oder Nginx) |
| TLS | Let's Encrypt via Certbot |
| Subpath-Betrieb | `USE_PROXY=true` + `PROXY_PREFIX=/hauskeeping` |
| Prozessverwaltung | systemd |
| Konfiguration | `.env`-Datei (nicht in Git einchecken) |