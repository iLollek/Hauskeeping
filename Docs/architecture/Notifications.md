# Notification Service – Hauskeeping

Hauskeeping setzt auf drei aufeinander aufbauende Notification-Kanäle, die User über fällige Aufgaben und Haushaltszusammenfassungen informieren. Alle Notifications sind optional – jede Funktion kann vom User jederzeit in den Einstellungen aktiviert oder deaktiviert werden.

**Die drei Kanäle:**
- E-Mail – wöchentliche Zusammenfassung
- Web Push – Echtzeit-Benachrichtigungen für iOS-User mit PWA
- Android Push – Echtzeit-Benachrichtigungen direkt im Chrome/Firefox-Browser

> **Hinweis:** Alle drei Notification-Typen sind standardmäßig deaktiviert. Der User aktiviert sie explizit in den Einstellungen und kann sie jederzeit wieder abschalten.

---

## 1. E-Mail Notification – Wöchentliche Zusammenfassung

Die E-Mail-Notification ist der einfachste und verlässlichste Kanal. Sie eignet sich für nicht zeitkritische Zusammenfassungen, die dem User einen Überblick über offene, erledigte und bald fällige Aufgaben geben.

### Inhalt der wöchentlichen E-Mail

Die E-Mail wird einmal pro Woche – standardmäßig montags früh – versandt. Sie enthält:

- Offene Aufgaben der laufenden Woche
- Aufgaben, die in der Vorwoche fällig waren und noch nicht erledigt wurden (überfällig)
- Vorschau auf die nächste Woche
- Kurze Statistik: erledigte Aufgaben der Vorwoche

*Beispiel-Betreffzeile: „Deine Hauskeeping-Woche – 3 Aufgaben stehen an"*

### Sendezeitpunkt & Frequenz

| Einstellung | Standardwert |
|---|---|
| Versandzeitpunkt | Montag, 07:00 Uhr (Zeitzone des Users) |
| Frequenz | Wöchentlich |
| Aktiviert by Default | Nein – User muss aktiv aktivieren |
| Abbestellbar | Ja – in den Einstellungen und per Link in der Mail |

### Technische Implementierung

**Stack:**
- Flask-Mail mit SMTP. Die SMTP-Daten sind in der .env Einstellbar.
- APScheduler oder Celery Beat für den wöchentlichen Cron-Job
- Jinja2 HTML-Templates für das E-Mail-Layout

**Datenbankmodell** – neue Spalte in der User-Tabelle:

```python
email_notifications_enabled = db.Column(db.Boolean, default=False)
```

**Ablauf:**

1. Cron-Job läuft wöchentlich montags um 07:00 Uhr
2. Alle User mit `email_notifications_enabled = True` werden geladen
3. Für jeden User werden offene und überfällige Tasks aus der DB abgefragt
4. Jinja2-Template wird mit Task-Daten gerendert
5. E-Mail wird über Flask-Mail versandt

---

## 2. Web Push Notification – PWA & iOS

Web Push ermöglicht echte System-Benachrichtigungen für User, die Hauskeeping als Progressive Web App (PWA) auf dem Homescreen installiert haben. Dieser Kanal ist insbesondere für iOS-User relevant, da Safari seit iOS 16.4 Web Push in installierten PWAs unterstützt.

### Voraussetzungen für den User

- iOS 16.4 oder neuer
- Safari als Browser
- Hauskeeping muss zum Homescreen hinzugefügt worden sein („Add to Home Screen")
- Der User muss die Benachrichtigungserlaubnis im Browser-Dialog bestätigen

> **Hinweis iOS:** Die Homescreen-Installation ist auf iOS eine harte technische Anforderung von Apple. Ohne diesen Schritt ist Web Push auf iOS nicht möglich. Hauskeeping sollte den User in der Onboarding-Phase klar darüber informieren.

### Wann werden Notifications gesendet?

Im Gegensatz zur wöchentlichen E-Mail sind Web Push Notifications ereignisgetrieben (Beispiele, nicht vollständige Liste):

- Eine Aufgabe wird am Fälligkeitstag um 08:00 Uhr gemeldet
- Überfällige Aufgaben erhalten eine tägliche Erinnerung (optional, vom User einstellbar)


### Technische Implementierung

Hauskeeping bleibt eine Flask-Web-App. Web Push wird über den W3C Web Push Standard mit VAPID-Authentifizierung implementiert. Kein externer Dienst ist für diesen Kanal erforderlich.

**Ablauf:**

1. User öffnet Hauskeeping in Safari (nach Homescreen-Installation)
2. Browser zeigt Benachrichtigungs-Dialog – User erteilt Erlaubnis
3. Browser generiert PushSubscription-Objekt (Endpoint + Keys)
4. Subscription wird ans Flask-Backend übermittelt und in der DB gespeichert
5. Bei einem Task-Event sendet Flask eine Push-Nachricht via `pywebpush`
6. Service Worker im Hintergrund empfängt die Nachricht und zeigt die Notification an

**VAPID-Keys** werden einmalig generiert und als Umgebungsvariablen gespeichert:

```
VAPID_PRIVATE_KEY, VAPID_PUBLIC_KEY, VAPID_CLAIM_EMAIL → in .env / config.py
```

**Datenbankmodell – PushSubscription:**

| Feld | Typ | Beschreibung |
|---|---|---|
| id | Integer PK | |
| user_id | FK → User | Zugehöriger User |
| endpoint | Text | Browser-seitige Push-URL |
| p256dh | Text | Öffentlicher Verschlüsselungskey |
| auth | Text | Auth-Secret des Browsers |
| platform | String | z. B. `ios`, `android`, `desktop` |
| created_at | DateTime | Erstellungszeitpunkt |

**Abgelaufene Subscriptions:** Wenn der Push-Dienst einen HTTP `410 Gone` zurückgibt, ist die Subscription abgelaufen. Hauskeeping löscht sie automatisch aus der Datenbank.

### iOS-Einschränkungen im Überblick

| Einschränkung | Details |
|---|---|
| Mindest-iOS-Version | iOS 16.4 (März 2023) |
| Nur Safari | Chrome und Firefox auf iOS unterstützen kein Web Push |
| Homescreen-Pflicht | PWA muss installiert sein – kein Browser-Push ohne Installation |
| Hintergrundprozesse | Apple kann Notifications auf älteren Geräten verzögern |

---

## 3. Android Push Notification – Web Push ohne native App

Für Android-User gibt es einen pragmatischen Mittelweg, der echte System-Benachrichtigungen ermöglicht, ohne eine vollständige native App entwickeln zu müssen. Android-Browser wie Chrome und Firefox unterstützen den Web Push Standard vollständig – auch ohne Homescreen-Installation.

### Voraussetzungen für den User

- Android-Smartphone mit Chrome, Firefox oder Samsung Internet
- Einmalige Bestätigung des Benachrichtigungs-Dialogs im Browser
- Keine PWA-Installation notwendig

> **Vorteil gegenüber iOS:** Auf Android entfällt die Homescreen-Pflicht vollständig. Der User muss nur einmal die Browser-Erlaubnis erteilen – danach funktioniert die Notification auch bei geschlossenem Tab oder minimiertem Browser.

### Browser-Kompatibilität

| Browser | Support | Anmerkung |
|---|---|---|
| Chrome (Android) | ✅ Vollständig | Beste Wahl, kein Homescreen nötig |
| Firefox (Android) | ✅ Vollständig | Funktioniert zuverlässig |
| Samsung Internet | ✅ Vollständig | Weit verbreitet auf Samsung-Geräten |
| Brave (Android) | ⚠️ Eingeschränkt | Abhängig von Datenschutz-Einstellungen des Users |

*Hinweis: Manche Android-Geräte (insbesondere Xiaomi, Huawei, OnePlus) verwalten Hintergrundprozesse aggressiv. Notifications können dadurch verzögert werden. Der User muss ggf. in den Akku-Einstellungen eine Ausnahme für den Browser einrichten – darauf hat Hauskeeping keinen Einfluss.*

### Geteilte Codebasis mit Web Push

Android Push verwendet denselben technischen Stack wie Web Push (iOS). Service Worker, VAPID-Keys und das PushSubscription-Modell sind identisch – es ist keine separate Implementierung notwendig.

| Komponente | Web Push (iOS) | Android Push |
|---|---|---|
| Service Worker (`sw.js`) | ✅ Identisch | ✅ Identisch |
| VAPID-Keys | ✅ Identisch | ✅ Identisch |
| PushSubscription-Modell | ✅ Identisch | ✅ Identisch |
| `send_push_notification()` | ✅ Identisch | ✅ Identisch |
| Homescreen-Installation | Erforderlich | Nicht erforderlich |

---

## 4. Einstellungen & Optionalität

Kein User erhält ungefragt Notifications. Alle drei Kanäle sind opt-in und können jederzeit in den Einstellungen verwaltet werden.

### User-Einstellungsseite

| Notification-Typ | Standard | User-Kontrolle |
|---|---|---|
| E-Mail Zusammenfassung | Aus | Toggle + Wochentag-Auswahl |
| Web Push (iOS PWA) | Aus | Toggle + Browser-Erlaubnis-Dialog |
| Android Push | Aus | Toggle + Browser-Erlaubnis-Dialog |

### Abmeldung & Datenlöschung

- E-Mail: Abmeldung per Link in der E-Mail oder Toggle in den Einstellungen
- Web Push / Android: Deaktivieren des Toggles löscht die gespeicherte PushSubscription aus der Datenbank
- Wenn ein User seinen Account löscht, werden alle Subscriptions und Präferenzen entfernt

### Datenbankmodell – User

| Feld | Typ | Bedeutung |
|---|---|---|
| email_notifications_enabled | Boolean | Wöchentliche E-Mail aktiv |
| email_notification_day | Integer (0–6) | Wochentag für den Versand (0 = Mo) |
| push_notifications_enabled | Boolean | Web Push / Android Push aktiv |

Push-Subscriptions werden separat in der `PushSubscription`-Tabelle gespeichert, da ein User mehrere Geräte registriert haben kann.

---

## 5. Implementierungs-Phasen

| Phase | Kanal | Aufwand | Priorität |
|---|---|---|---|
| 1 | E-Mail Zusammenfassung | Gering – Flask-Mail + Cron | MUST |
| 2 | Web Push (iOS PWA) | Mittel – Service Worker + VAPID | SHOULD |
| 3 | Android Push | Sehr gering – gleicher Stack wie Phase 2 | SHOULD |

Native Mobile Apps (iOS/Android) sind für Hauskeeping als Flask-App nicht geplant.