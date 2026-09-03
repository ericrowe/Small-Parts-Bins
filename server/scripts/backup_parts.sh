#!/usr/bin/env bash
# ==============================================================================
# backup_parts.sh - Automated Application-Consistent SQLite Backup Pipeline
# Node 09 (pi-lab / parts) -> Node 04 (pi-backup:/srv/backups/restic/parts-database)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_DIR="$(dirname "$SCRIPT_DIR")"
DATA_DIR="${DATA_DIR:-$SERVER_DIR/data}"
DB_FILE="$DATA_DIR/parts.db"

BACKUP_HOST="${BACKUP_HOST:-pi-backup.local}"
BACKUP_USER="${BACKUP_USER:-detour}"
RESTIC_REPO="${RESTIC_REPO:-sftp:${BACKUP_USER}@${BACKUP_HOST}:/srv/backups/restic/parts-database}"
PASSWORD_FILE="${PASSWORD_FILE:-$SERVER_DIR/.restic_password}"
LOG_FILE="${LOG_FILE:-$SERVER_DIR/logs/backup.log}"
STAGING_DIR="$(mktemp -d -t parts_backup_staging_XXXXXX)"

DRY_RUN=0
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=1
fi

cleanup() {
    if [ -d "$STAGING_DIR" ]; then
        rm -rf "$STAGING_DIR"
    fi
}
trap cleanup EXIT INT TERM

log() {
    local msg="[$(date +"%Y-%m-%d %H:%M:%S")] $1"
    echo "$msg"
    mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || true
    echo "$msg" >> "$LOG_FILE" 2>/dev/null || true
}

log "=== Starting Parts-Database Backup Pipeline ==="
log "Source data: $DATA_DIR"
log "Target repository: $RESTIC_REPO"

# 1. Verify source database
if [ ! -f "$DB_FILE" ]; then
    log "WARNING: Database file $DB_FILE does not exist yet. Nothing to backup."
    exit 0
fi

# 2. Stage Atomic SQLite Snapshot (VACUUM INTO)
mkdir -p "$STAGING_DIR/data" "$STAGING_DIR/config"
dest_snapshot="$STAGING_DIR/data/parts.db"

log "  -> Capturing atomic snapshot via SQLite VACUUM INTO..."
if command -v sqlite3 >/dev/null 2>&1; then
    sqlite3 "$DB_FILE" "VACUUM INTO '$dest_snapshot';" 2>/dev/null || {
        log "  -> VACUUM INTO failed, falling back to copy..."
        cp "$DB_FILE" "$dest_snapshot"
    }
    
    # 3. Verify Snapshot Integrity
    integrity=$(sqlite3 "$dest_snapshot" "PRAGMA integrity_check;" 2>/dev/null || echo "failed")
    if [ "$integrity" != "ok" ]; then
        log "ERROR: Snapshot integrity check failed ($integrity)! Aborting backup."
        exit 1
    fi
    log "  -> Snapshot integrity check passed (ok)."
else
    cp "$DB_FILE" "$dest_snapshot"
fi

# 4. Stage Configuration Files
if [ -f "$SERVER_DIR/.env" ]; then
    cp "$SERVER_DIR/.env" "$STAGING_DIR/config/" 2>/dev/null || true
fi
if [ -f "$SERVER_DIR/requirements.txt" ]; then
    cp "$SERVER_DIR/requirements.txt" "$STAGING_DIR/config/" 2>/dev/null || true
fi

if [ "$DRY_RUN" -eq 1 ]; then
    log "DRY RUN: Staged snapshot and configuration verified successfully. Exiting dry run."
    exit 0
fi

# 5. Check Restic and Credentials
if ! command -v restic >/dev/null 2>&1; then
    log "ERROR: restic is not installed. Please install restic (brew install restic or apt install restic)."
    exit 1
fi

if [ ! -f "$PASSWORD_FILE" ]; then
    log "WARNING: Password file $PASSWORD_FILE not found. Checking RESTIC_PASSWORD env var."
    if [ -z "${RESTIC_PASSWORD:-}" ]; then
        log "ERROR: Neither $PASSWORD_FILE nor RESTIC_PASSWORD is set. Cannot proceed."
        exit 1
    fi
    RESTIC_PASS_OPT=""
else
    RESTIC_PASS_OPT="--password-file $PASSWORD_FILE"
fi

# 6. Initialize Restic Repo if not present
if ! restic -r "$RESTIC_REPO" $RESTIC_PASS_OPT snapshots >/dev/null 2>&1; then
    log "Initializing fresh restic repository at $RESTIC_REPO..."
    restic -r "$RESTIC_REPO" $RESTIC_PASS_OPT init
fi

# 7. Execute Backup
log "Executing restic backup of staged snapshot..."
restic -r "$RESTIC_REPO" $RESTIC_PASS_OPT backup \
    --tag parts-database \
    --tag automated \
    --host parts-server \
    "$STAGING_DIR/data" "$STAGING_DIR/config"

# 8. Enforce 14D / 8W / 12M Retention Pruning
log "Applying snapshot retention policy (14 daily, 8 weekly, 12 monthly)..."
restic -r "$RESTIC_REPO" $RESTIC_PASS_OPT forget \
    --tag parts-database \
    --keep-daily 14 \
    --keep-weekly 8 \
    --keep-monthly 12 \
    --prune

log "=== Parts-Database Backup Pipeline Completed Successfully ==="
