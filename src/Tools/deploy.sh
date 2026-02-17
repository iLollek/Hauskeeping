#!/bin/bash

# Deployment-Skript für Hauskeeping
# Verwendung: sudo ./deploy.sh
#
# Voraussetzung: SSH-Key für GitHub muss eingerichtet sein
# Siehe: https://docs.github.com/en/authentication/connecting-to-github-with-ssh

set -e

# Konfiguration
REPO_URL="git@github.com:iLollek/Hauskeeping.git"
INSTALL_DIR="/opt/hauskeeping"
TEMP_DIR="/tmp/hauskeeping_deploy_$$"
SERVICE_NAME="hauskeeping"
VENV_DIR="$INSTALL_DIR/venv"

# Farben für Ausgaben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging-Funktionen
log() {
    echo -e "${GREEN}[DEPLOY]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Cleanup-Funktion
cleanup() {
    if [ -d "$TEMP_DIR" ]; then
        rm -rf "$TEMP_DIR"
    fi
}
trap cleanup EXIT

# Überprüfen ob als root ausgeführt
if [ "$EUID" -ne 0 ]; then
    error "Bitte als root ausführen: sudo ./deploy.sh"
    exit 1
fi

log "=========================================="
log "Hauskeeping Deployment"
log "=========================================="
log "Zielverzeichnis: $INSTALL_DIR"
log "Datum: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Schritt 1: Service stoppen
log "Schritt 1/6: Service stoppen..."
if systemctl is-active --quiet "$SERVICE_NAME"; then
    systemctl stop "$SERVICE_NAME"
    log "Service $SERVICE_NAME gestoppt."
else
    warn "Service $SERVICE_NAME war nicht aktiv."
fi

# Schritt 2: Repository klonen
log "Schritt 2/6: Neuesten Code von GitHub laden..."
mkdir -p "$TEMP_DIR"
git clone --depth 1 --branch main "$REPO_URL" "$TEMP_DIR"
log "Repository erfolgreich geklont."

# Commit-Info anzeigen
cd "$TEMP_DIR"
COMMIT=$(git rev-parse --short HEAD)
COMMIT_MSG=$(git log -1 --pretty=%B | head -n 1)
log "Neuester Commit: $COMMIT - $COMMIT_MSG"

# Schritt 3: Dateien synchronisieren
log "Schritt 3/6: Dateien aktualisieren..."

# Gesamtes Repo nach $INSTALL_DIR synchronisieren
# Geschuetzt: venv, .env, Datenbank (instance/), deploy.sh (src/Tools/)
mkdir -p "$INSTALL_DIR"
rsync -av --delete \
    --exclude 'venv/' \
    --exclude '.env' \
    --exclude 'instance/' \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    --exclude '*.db' \
    --exclude '.git/' \
    --exclude '.github/' \
    --exclude '.claude/' \
    --exclude '.gitignore' \
    --exclude 'Docs/' \
    --exclude 'src/Tools/' \
    "$TEMP_DIR/" "$INSTALL_DIR/"

log "Dateien erfolgreich synchronisiert."

# Schritt 4: Python-Dependencies aktualisieren
log "Schritt 4/6: Python-Dependencies aktualisieren..."
if [ -d "$VENV_DIR" ]; then
    "$VENV_DIR/bin/pip" install -r "$INSTALL_DIR/requirements.txt" --quiet
    log "Dependencies aktualisiert."
else
    error "Virtuelle Umgebung nicht gefunden: $VENV_DIR"
    error "Bitte zuerst manuell erstellen: python3 -m venv $VENV_DIR"
    exit 1
fi

# Schritt 5: Datenbank-Migrationen ausfuehren
log "Schritt 5/6: Datenbank-Migrationen pruefen..."
cd "$INSTALL_DIR"
export FLASK_APP=run.py
if "$VENV_DIR/bin/flask" db upgrade 2>&1; then
    log "Migrationen erfolgreich ausgefuehrt."
else
    error "Migrationen fehlgeschlagen!"
    error "Bitte manuell pruefen: cd $INSTALL_DIR && $VENV_DIR/bin/flask db upgrade"
    exit 1
fi

# Schritt 6: Service starten
log "Schritt 6/6: Service starten..."
systemctl start "$SERVICE_NAME"
sleep 2

# Status überprüfen
if systemctl is-active --quiet "$SERVICE_NAME"; then
    log "Service $SERVICE_NAME erfolgreich gestartet."
else
    error "Service $SERVICE_NAME konnte nicht gestartet werden!"
    error "Überprüfe mit: systemctl status $SERVICE_NAME"
    exit 1
fi

echo ""
log "=========================================="
log "Deployment erfolgreich abgeschlossen!"
log "Commit: $COMMIT"
log "=========================================="
