"""Apply schema.sql to the SQLite database.

Usage:
    python3 tool/db/migrate.py            # apply (idempotent)
    python3 tool/db/migrate.py --reset    # drop & recreate (destructive)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tool.cli.db import DB_PATH, SCHEMA_PATH, audit, get_connection  # noqa: E402


def apply_schema(reset: bool = False) -> None:
    if reset and DB_PATH.exists():
        DB_PATH.unlink()
        print(f"[migrate] removed existing db: {DB_PATH}")

    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn = get_connection()
    try:
        conn.executescript(schema_sql)
        audit(
            conn,
            action="migrate.apply",
            target_type="schema",
            payload={"schema_file": str(SCHEMA_PATH), "reset": reset},
        )
        tables = [
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
        ]
        print(f"[migrate] applied schema. tables: {', '.join(tables)}")
        print(f"[migrate] db at: {DB_PATH}")
    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument(
        "--reset", action="store_true", help="Destructive: drop & recreate database."
    )
    args = parser.parse_args()
    apply_schema(reset=args.reset)
