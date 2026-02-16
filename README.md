# 🏠 Hauskeeping

Eine moderne Web-Anwendung zur Verwaltung von Haushaltsaufgaben für Wohngemeinschaften, Familien oder Einzelpersonen.

## Features

- 📅 **Kalenderansicht als Hauptscreen** – Behalte alle Hausarbeiten im Überblick
- 🔄 **Wiederkehrende Aufgaben** – Setze Aufgaben wie "Einkaufen jeden Donnerstag" automatisch
- 🛒 **Interaktive Einkaufsliste** – Gemeinsam Artikel hinzufügen und abhaken
- 📋 Aufgabenverwaltung mit Prioritäten und Deadlines
- 👥 Mehrbenutzer-Support mit Aufgabenverteilung
- ✅ Fortschrittstracking und Erledigungshistorie
- 🔔 Erinnerungen für anstehende Aufgaben
- 📱 Responsive Design für Mobile & Desktop

## Tech Stack

- **Backend:** Flask (Python)
- **Frontend:** Bootstrap 5
- **Datenbank:** PostgreSQL/SQLite
- **Deployment:** Raspbian/Linux ready

## Hauptfunktionen

### 📅 Kalenderansicht
- Zentrale Übersicht aller Haushaltsaufgaben
- Wochenansicht
- Verschiedene Aufgaben werden Farbig markiert

### 🔄 Wiederkehrende Aufgaben
- Flexible Wiederholungsregeln (täglich, wöchentlich, monatlich)
- Beispiel: "Einkaufen jeden Donnerstag", "Müll rausbringen jeden Montag"
- Automatische Generierung zukünftiger Termine

### 🛒 Gemeinsame Einkaufsliste
- Mehrere Benutzer können gleichzeitig Artikel hinzufügen
- Echtzeit-Updates beim Abhaken
- Kategorisierung (Lebensmittel, Haushalt, Drogerie, etc.)
- Artikel können direkt zu Einkaufs-Aufgaben verknüpft werden

## Installation
```bash
# Repository klonen
git clone https://github.com/dein-username/hauskeeping.git
cd hauskeeping

# Virtual Environment erstellen
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate  # Windows

# Dependencies installieren
pip install -r requirements.txt

# Umgebungsvariablen konfigurieren
cp .env.example .env
# .env bearbeiten und anpassen

# Datenbank initialisieren
flask init-db

# Admin-Benutzer erstellen
flask create-admin

# App starten
python run.py
```

Die App ist nun unter `http://localhost:5000` erreichbar.

## Deployment auf einem Raspbian-System (nicht Raspberry Pi, nur Raspberry OS)

Vollständige Anleitung siehe [INSTALL.md](INSTALL.md)

## Lizenz

[MIT License](LICENSE) - Frei für private und kommerzielle Nutzung

---

**Hinweis:** Dieses Projekt befindet sich in aktiver Entwicklung.
