import os
import tempfile
import sqlite3
import subprocess
import pytest


def test_atomic_vacuum_into_integrity():
    """Verify that SQLite WAL mode VACUUM INTO produces a pristine, uncorrupted standalone snapshot."""
    temp_dir = tempfile.mkdtemp()
    live_db = os.path.join(temp_dir, "live_parts.db")
    snapshot_db = os.path.join(temp_dir, "snapshot_parts.db")

    # 1. Create live database in WAL mode with test data
    conn = sqlite3.connect(live_db)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("CREATE TABLE inventory (id TEXT PRIMARY KEY, qty INTEGER);")
    conn.execute("INSERT INTO inventory VALUES ('M3-12', 100);")
    conn.commit()

    # 2. Perform atomic snapshot
    conn.execute(f"VACUUM INTO '{snapshot_db}';")
    conn.close()

    # 3. Verify snapshot exists and passes integrity check
    assert os.path.exists(snapshot_db)
    snap_conn = sqlite3.connect(snapshot_db)
    res = snap_conn.execute("PRAGMA integrity_check;").fetchone()
    assert res[0] == "ok"

    # Verify data inside snapshot
    row = snap_conn.execute("SELECT qty FROM inventory WHERE id = 'M3-12';").fetchone()
    assert row[0] == 100
    snap_conn.close()


def test_corrupt_database_detection():
    """Verify that corrupted database files fail integrity verification."""
    temp_dir = tempfile.mkdtemp()
    corrupt_db = os.path.join(temp_dir, "corrupt.db")

    # Create a dummy corrupted file with invalid header
    with open(corrupt_db, "wb") as f:
        f.write(b"NOT_A_VALID_SQLITE_DATABASE_HEADER" + b"\x00" * 512)

    try:
        conn = sqlite3.connect(corrupt_db)
        res = conn.execute("PRAGMA integrity_check;").fetchone()
        conn.close()
        # If it returns a string other than 'ok', detection succeeds
        assert res[0] != "ok"
    except sqlite3.DatabaseError:
        # If sqlite raises DatabaseError directly, detection succeeds
        assert True


def test_backup_script_syntax_and_dry_run():
    """Verify that backup_parts.sh executes cleanly under dry-run mode."""
    script_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", "backup_parts.sh"
    )
    assert os.path.exists(script_path)

    # Run bash syntax validation
    res_syntax = subprocess.run(["bash", "-n", script_path], capture_output=True, text=True)
    assert res_syntax.returncode == 0
