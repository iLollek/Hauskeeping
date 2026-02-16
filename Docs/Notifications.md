# Dokumentation des Notification Services in Hauskeeping

Push-Notifications sind wichtig. Damit können User über Tasks erinnert werden. Es wurde schon über eine Kalender-Integration nachgedacht, jedoch sprengt das den Designrahmen von Hauskeeping. Außerdem hätte der User dann einmal den Handy-Kalender und einmal den Kalender in Hauskeeping.

## Welche Notifications gibt es?

### 1. E-Mail Notification
Wir senden dem User eine E-Mail

**Vorteile:**
- ✅ Funktioniert auf allen Plattformen (iOS, Android, Desktop)
- ✅ Keine App-Installation oder Homescreen-Hinzufügung nötig
- ✅ Sehr einfache Implementierung (Flask-Mail, SMTP)
- ✅ Keine Browser-Einschränkungen
- ✅ User können E-Mails archivieren/durchsuchen
- ✅ Hohe Zustellrate (99%+)

**Nachteile:**
- ❌ Nicht so "sofort" wie Push (User checkt E-Mails unregelmäßig)
- ❌ Kann im Spam landen
- ❌ Weniger auffällig als System-Benachrichtigung
- ❌ User muss E-Mail-App öffnen

**Wann sinnvoll:** Tägliche Zusammenfassungen, wichtige Updates, Erinnerungen die nicht zeitkritisch sind

---

### 2. Web Push Notification (Progressive Web App)
Web-App wird zum Homescreen hinzugefügt, Push via Web Push API

**Vorteile:**
- ✅ Kein nativer App-Store nötig
- ✅ Kein Mac/Xcode für iOS nötig
- ✅ Eine Code-Base für alle Plattformen
- ✅ System-Benachrichtigungen wie native Apps
- ✅ Funktioniert auch wenn Browser geschlossen ist
- ✅ Kostenlos (kein Apple Developer Account nötig)
- ✅ Standard-Technologie (W3C)

**Nachteile:**
- ❌ **iOS: Nur wenn App zum Homescreen hinzugefügt wurde** (großer Friction)
- ❌ iOS: Erst ab Version 16.4 (März 2023)
- ❌ iOS: Nur Safari, nicht Chrome/Firefox
- ❌ User muss aktiv "Add to Homescreen" machen
- ❌ Komplexere Implementierung (Service Worker, VAPID Keys, Subscriptions)
- ❌ Keine garantierte Zustellung bei schlechter Netzverbindung

**Wann sinnvoll:** Wenn du bereits eine PWA hast, Desktop-User, Android-Heavy User-Base

---

### 3. Native Mobile Push Notification (via Firebase Cloud Messaging)
Native Apps für iOS/Android mit FCM/APNs

**Vorteile:**
- ✅ Beste User Experience auf Mobile
- ✅ Höchste Zustellrate und Zuverlässigkeit
- ✅ Funktioniert sofort nach Installation
- ✅ Volle Kontrolle über Design/Sound/Badges
- ✅ iOS + Android mit einer Lösung (FCM)
- ✅ Rich Notifications (Bilder, Actions, etc.)
- ✅ Funktioniert auch bei App-Kill

**Nachteile:**
- ❌ **Braucht native Apps** (iOS + Android separat entwickeln)
- ❌ iOS: Braucht Mac + Xcode + Apple Developer Account (99€/Jahr)
- ❌ Mehr Entwicklungsaufwand (2 Apps pflegen)
- ❌ App Store Review-Prozess
- ❌ User muss App installieren (Download-Hürde)

**Wann sinnvoll:** Wenn du ein professionelles Produkt baust, Mobile-First, Budget für Entwicklung vorhanden

---

### 4. Discord DM Notification
Wir senden dem User eine Notification über eine Discord-DM

**Vorteile:**
- ✅ Sehr einfache Integration (Discord Bot API)
- ✅ User, die Discord nutzen, sehen es sofort
- ✅ Funktioniert auf allen Plattformen (wo Discord läuft)
- ✅ Kann mit Discord-Community kombiniert werden
- ✅ Rich Formatting (Embeds, Buttons) möglich

**Nachteile:**
- ❌ **User muss Discord haben und nutzen**
- ❌ Nicht jeder hat/will Discord
- ❌ User muss Hauskeeping-Bot autorisieren
- ❌ Abhängigkeit von Discord (Drittanbieter)
- ❌ Discord könnte API ändern/einschränken
- ❌ Wirkt unprofessionell für manche User

**Wann sinnvoll:** Tech-affine Zielgruppe, Gaming-/Developer-Community, als **zusätzliche** Option

---

## Warum dann der zweite Weg mit Mobile?

**Die Realität für Hauskeeping:**

Für eine Flask-basierte Haushalts-App würde ich empfehlen:

1. **Start mit E-Mail** (Pflicht)
   - Jeder hat E-Mail, funktioniert überall
   - Schnell implementiert

2. **+ Web Push als "Nice-to-have"** (Optional)
   - Für Power-User die die PWA installieren
   - Gut für Desktop-User
   - Relativ wenig Aufwand

3. **Discord DM als Zusatz-Feature** (Optional)
   - Nur wenn deine Zielgruppe techaffin ist
   - Als Opt-in Feature

4. **Native Mobile Apps nur wenn...**
   - Du Budget/Zeit hast
   - Du Mobile-First bist
   - Du ein professionelles Produkt willst
   - Du zahlende Kunden hast

**Pragmatische Empfehlung für Hauskeeping:**
```
Phase 1: E-Mail Notifications (MUST)
Phase 2: Web Push für PWA-User (SHOULD)
Phase 3: Discord als Fun-Feature (COULD)
Phase 4: Native Apps (WON'T - zu viel Aufwand für Flask-App)
```

## Entscheidungsmatrix

| Kriterium | E-Mail | Web Push | Native Mobile | Discord |
|-----------|--------|----------|---------------|---------|
| iOS Support | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Android Support | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Implementierungsaufwand | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐ |
| Sofortige Zustellung | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| User Adoption | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| Kosten | Kostenlos | Kostenlos | 99€/Jahr | Kostenlos |
