#!/usr/bin/env bash
# ==============================================================================
# run_tests.sh - Hermetic Test Runner for Parts-Database
# Automatically resolves Python virtual environment and executes server pytest suite
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 1. Resolve Python virtual environment
PYTHON_BIN=""
if [ -x "$SCRIPT_DIR/server/.venv/bin/python" ]; then
    PYTHON_BIN="$SCRIPT_DIR/server/.venv/bin/python"
elif [ -x "$SCRIPT_DIR/.venv/bin/python" ]; then
    PYTHON_BIN="$SCRIPT_DIR/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
else
    echo "❌ Error: No valid Python interpreter found in server/.venv/, .venv/, or system PATH." >&2
    exit 1
fi

# 2. Execute pytest hermetically
export PYTHONPATH="$SCRIPT_DIR"
echo "🧪 Running Parts-Database tests with: $PYTHON_BIN"
if [ $# -eq 0 ]; then
    set -- server/tests/
fi
exec "$PYTHON_BIN" -m pytest "$@"
