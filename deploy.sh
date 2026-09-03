#!/usr/bin/env bash
# ==============================================================================
# deploy.sh - Production Deployment Script for Parts-Database on Node 02 (tasker-pi)
# Synchronizes code, installs venv dependencies, configures systemd, and starts :8090
# ==============================================================================
set -euo pipefail

PI_USER="${PI_USER:-detour}"
PI_HOST="${PI_HOST:-tasker-pi.local}"
TARGET_DIR="/opt/parts-database"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

DRY_RUN=""
if [[ "${1:-}" == "--dry-run" || "${1:-}" == "-n" ]]; then
  DRY_RUN="--dry-run"
  echo "🔍 Running deployment DRY-RUN (no remote files will be modified)..."
else
  echo "🚀 Deploying Parts-Database to Node 02 ($PI_HOST)..."
fi

# 1. Ensure target directory structure exists with correct permissions
if [[ -z "$DRY_RUN" ]]; then
  ssh "$PI_USER@$PI_HOST" "sudo mkdir -p $TARGET_DIR /srv/database/parts && sudo chown -R $PI_USER:www-data $TARGET_DIR /srv/database/parts && sudo chmod 775 /srv/database/parts"
fi

# 2. Synchronize Application Files
rsync -avz $DRY_RUN \
  --exclude '.git' \
  --exclude '.gitignore' \
  --exclude '.DS_Store' \
  --exclude '*/.DS_Store' \
  --exclude '__pycache__' \
  --exclude '*/__pycache__' \
  --exclude '*.pyc' \
  --exclude '.venv' \
  --exclude 'venv' \
  --exclude 'server/data/*.db' \
  --exclude 'server/data/*.db-wal' \
  --exclude 'server/data/*.db-shm' \
  --exclude 'server/logs' \
  --exclude '.pytest_cache' \
  "$SCRIPT_DIR/" "$PI_USER@$PI_HOST:$TARGET_DIR/"

if [[ -z "$DRY_RUN" ]]; then
  echo "📦 Provisioning Python virtual environment & dependencies on $PI_HOST..."
  ssh "$PI_USER@$PI_HOST" bash << 'REMOTE_EXEC'
set -euo pipefail
APP_DIR="/opt/parts-database"

# Ensure venv exists
if [ ! -d "$APP_DIR/server/.venv" ]; then
    python3 -m venv "$APP_DIR/server/.venv"
fi

# Install dependencies
"$APP_DIR/server/.venv/bin/python" -m pip install --upgrade -q pip
if [ -f "$APP_DIR/server/requirements.txt" ]; then
    "$APP_DIR/server/.venv/bin/python" -m pip install -q -r "$APP_DIR/server/requirements.txt"
fi

# Install systemd unit
sudo tee /etc/systemd/system/parts-database.service >/dev/null << SYSTEMD_UNIT
[Unit]
Description=Parts-Database Web Catalog Microservice
After=network.target

[Service]
Type=simple
User=detour
Group=www-data
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/server/.venv/bin/python -m uvicorn server.app.main:app --host 0.0.0.0 --port 8090
Restart=always
RestartSec=5s
Environment=PYTHONPATH=$APP_DIR
Environment=DATABASE_URL=sqlite+aiosqlite:////srv/database/parts/parts.db

[Install]
WantedBy=multi-user.target
SYSTEMD_UNIT

sudo systemctl daemon-reload
sudo systemctl enable parts-database.service
sudo systemctl restart parts-database.service

# Setup automated backup cron if not present
CRON_JOB="0 3 * * * /bin/bash $APP_DIR/server/scripts/backup_parts.sh >> $APP_DIR/server/logs/backup.log 2>&1"
(crontab -l 2>/dev/null | grep -v "backup_parts.sh" ; echo "$CRON_JOB") | crontab -

echo "Waiting for service to bind on :8090..."
sleep 2

# Verify local endpoint
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8090/ || echo "failed")
echo "HTTP response status on :8090: $HTTP_STATUS"
REMOTE_EXEC

  echo "======================================================================"
  echo "✅ Parts-Database successfully deployed to Node 02 (tasker-pi)!"
  echo "   Catalog URL: http://tasker-pi.local:8090"
  echo "   Fastener Specs: http://tasker-pi.local:8090/parts"
  echo "   Bin Landing: http://tasker-pi.local:8090/b/BIN-001"
  echo "======================================================================"
else
  echo "✅ Dry-run complete. Run './deploy.sh' without flags to deploy."
fi
