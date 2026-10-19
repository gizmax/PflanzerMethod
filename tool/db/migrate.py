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

# Additive ALTER TABLE migrations — applied AFTER executescript so they
# work even when the table already exists (CREATE TABLE IF NOT EXISTS skips
# new columns added to existing tables).
ADDITIVE_COLUMNS: dict[str, list[tuple[str, str]]] = {
    "projects": [
        ("target_repo_url", "TEXT"),
        ("target_branch", "TEXT DEFAULT 'main'"),
        ("production_readiness_target", "INTEGER DEFAULT 80"),
        ("gate_score_latest", "INTEGER DEFAULT 0"),
        # Autoresearch Sprint 1 (T2): acceptance criteria jako Charter input
        ("acceptance_criteria_md", "TEXT"),
        # Autoresearch Sprint 1 (T3): INTEGRATION_GUIDE.md path
        ("integration_guide_path", "TEXT"),
        # Autoresearch Sprint 3 (perspektiva 02): ship contract fields
        ("target_branch_owner", "TEXT"),
        ("shadow_pm", "TEXT"),
        # Mob mode autoresearch (Sprint 4 — ADR-0016)
        ("session_mode", "TEXT DEFAULT 'parallel'"),
        # v0.5 (ADR-0021): jména 6 kroků cesty + jádro (3–4 lidé, max 5 naráz)
        ("path_owners_json", "TEXT"),
        ("core_json", "TEXT"),
    ],
    # v0.5 Rozhodnutí: vítěz + override critical (session_2.py)
    "sessions": [
        ("winner_variant", "TEXT"),
        ("override_critical_reason", "TEXT"),
    ],
    # v0.5 Build/Ship: větev a HEAD SHA varianty z worktree (session.py / extract.py)
    "variants": [
        ("branch", "TEXT"),
        ("head_sha", "TEXT"),
    ],
    # v0.5 Ship: velikost diffu vítěze proti základní větvi (metriky pilotu)
    "extracted_code": [
        ("diff_loc_added", "INTEGER"),
        ("diff_loc_removed", "INTEGER"),
        ("diff_files", "INTEGER"),
    ],
    # v0.5 Async: vyřešený critical feedback už neblokuje Rozhodnutí
    "feedback": [
        ("resolved_at", "TIMESTAMP"),
        ("resolved_note", "TEXT"),
    ],
}


def _apply_additive(conn) -> list[str]:
    applied: list[str] = []
    for table, cols in ADDITIVE_COLUMNS.items():
        existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        for name, type_ in cols:
            if name not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {type_}")
                applied.append(f"{table}.{name}")
    return applied


def apply_schema(reset: bool = False) -> None:
    if reset and DB_PATH.exists():
        DB_PATH.unlink()
        print(f"[migrate] removed existing db: {DB_PATH}")

    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn = get_connection()
    try:
        conn.executescript(schema_sql)
        applied_alters = _apply_additive(conn)
        if applied_alters:
            print(f"[migrate] applied additive columns: {', '.join(applied_alters)}")
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
