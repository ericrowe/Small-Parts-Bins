#!/usr/bin/env bash
# ==============================================================================
# bootstrap_node.sh - Bare-Metal Bootstrap & Restoration for Parts-Database
# Deployed on Node 02 (tasker-pi) co-located with Personal-Assistant on port :8090
# ==============================================================================
set -euo pipefail

BACKUP_HOST="${BACKUP_HOST:-pi-backup.local}"
BACKUP_USER="${BACKUP_USER:-detour}"
RESTIC_REPO="${RESTIC_REPO:-sftp:${BACKUP_USER}@${BACKUP_HOST}:/srv/backups/restic/parts-database}"
RESTIC_PASSWORD="${RESTIC_PASSWORD:-parts-database-rack-vault-key}"
APP_DIR="/opt/parts-database"
APP_USER="${USER:-detour}"
APP_GROUP="www-data"

# Check for persistent SSD mount on tasker-pi (/srv/database)
if [ -d "/srv/database" ]; then
    DB_DIR="/srv/database/parts"
else
    DB_DIR="$APP_DIR/server/data"
fi

echo "======================================================================"
echo " Starting Automated Bootstrap for Parts-Database (Node 02: tasker-pi)"
echo "======================================================================"

# 1. Install System Packages
echo "[1/6] Installing required APT system packages..."
sudo apt-get update -qq
sudo apt-get install -y -qq python3-venv python3-pip sqlite3 restic curl git rsync
echo "[+] System packages installed."

# 2. Setup Application Directory, SSD Database Path & Virtual Environment
echo "[2/6] Building application directory and Python virtualenv..."
sudo mkdir -p "$APP_DIR" "$APP_DIR/server" "$APP_DIR/server/data" "$APP_DIR/server/logs" "$DB_DIR"
sudo chown -R "$APP_USER:$APP_GROUP" "$APP_DIR" "$DB_DIR"
sudo chmod 775 "$DB_DIR"

if [ ! -d "$APP_DIR/server/.venv" ]; then
    python3 -m venv "$APP_DIR/server/.venv"
fi

echo "  -> Installing Python requirements..."
"$APP_DIR/server/.venv/bin/python" -m pip install --upgrade -q pip
if [ -f "$APP_DIR/server/requirements.txt" ]; then
    "$APP_DIR/server/.venv/bin/python" -m pip install -q -r "$APP_DIR/server/requirements.txt"
fi
echo "[+] Virtual environment ready with FastAPI and Uvicorn."

# 3. Restore Application Configuration & Databases from Node 04 (pi-backup)
echo "[3/6] Restoring latest snapshot from $BACKUP_HOST..."
RESTORE_TMP="$(mktemp -d -t bootstrap_restore_XXXXXX)"
export RESTIC_PASSWORD

if restic -r "$RESTIC_REPO" snapshots >/dev/null 2>&1; then
    restic -r "$RESTIC_REPO" restore latest --target "$RESTORE_TMP" --tag parts-database
    
    # Restore database files to persistent storage
    if [ -d "$RESTORE_TMP/data" ]; then
        rsync -av "$RESTORE_TMP/data/" "$DB_DIR/"
        echo "[+] Database files restored to $DB_DIR."
    fi
    
    # Restore configuration files
    if [ -d "$RESTORE_TMP/config" ]; then
        rsync -av "$RESTORE_TMP/config/" "$APP_DIR/server/"
        echo "[+] Configuration files restored."
    fi
else
    echo "WARNING: Remote restic repository at $RESTIC_REPO not reachable or empty. Fresh database will be created on boot."
fi
rm -rf "$RESTORE_TMP"

# 4. Validate Database Integrity
echo "[4/6] Validating database integrity..."
if [ -f "$DB_DIR/parts.db" ]; then
    integrity=$(sqlite3 "$DB_DIR/parts.db" "PRAGMA integrity_check;" 2>/dev/null || echo "failed")
    if [ "$integrity" != "ok" ]; then
        echo "ERROR: Restored database integrity check failed ($integrity)!"
        exit 1
    fi
    echo "[+] Database integrity check passed (ok)."
fi

# 5. Configure Systemd Service Unit
echo "[5/6] Configuring systemd service unit..."
sudo tee /etc/systemd/system/parts-database.service >/dev/null << SYSTEMD_UNIT
[Unit]
Description=Parts-Database Web Catalog Microservice
After=network.target

[Service]
Type=simple
User=$APP_USER
Group=$APP_GROUP
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/server/.venv/bin/python -m uvicorn server.app.main:app --host 0.0.0.0 --port 8090
Restart=always
RestartSec=5s
Environment=PYTHONPATH=$APP_DIR
Environment=DATABASE_URL=sqlite+aiosqlite:///$DB_DIR/parts.db

[Install]
WantedBy=multi-user.target
SYSTEMD_UNIT

sudo systemctl daemon-reload
sudo systemctl enable parts-database.service
sudo systemctl restart parts-database.service
echo "[+] Systemd service parts-database.service enabled and started on :8090."

# 6. Configure Daily Backup Cron
echo "[6/6] Configuring daily backup cron job..."
CRON_JOB="0 3 * * * /bin/bash $APP_DIR/server/scripts/backup_parts.sh >> $APP_DIR/server/logs/backup.log 2>&1"
(crontab -l 2>/dev/null | grep -v "backup_parts.sh" ; echo "$CRON_JOB") | crontab -
echo "[+] Automated daily backup scheduled for 03:00 AM."

echo "======================================================================"
echo " Bootstrap Complete! Parts-Database is live on http://localhost:8090"
echo "======================================================================"
