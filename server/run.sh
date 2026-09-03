#!/usr/bin/env bash
# ==============================================================================
# Parts-Database Web Catalog Server Launcher
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$SCRIPT_DIR"

# Check virtual environment
if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Initializing .venv..."
    python3 -m venv .venv
    .venv/bin/python -m pip install --upgrade pip
    .venv/bin/python -m pip install -r requirements.txt
fi

echo "Starting Parts-Database Web Catalog Server on http://0.0.0.0:8090..."
export PYTHONPATH="$ROOT_DIR:${PYTHONPATH:-}"
exec .venv/bin/python -m uvicorn server.app.main:app --host 0.0.0.0 --port 8090 --reload
