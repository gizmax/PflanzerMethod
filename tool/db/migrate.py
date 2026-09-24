"""Apply schema.sql to the SQLite database.

Usage:
    python3 tool/db/migrate.py            # apply (idempotent)
    python3 tool/db/migrate.py --reset    # drop & recreate (destructive)
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tool.cli import db as _db  # noqa: E402
from tool.cli.db import SCHEMA_PATH, audit, get_connection  # noqa: E402

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
        # Mob mode autoresearch (Sprint 4 — ADR-0011)
        ("session_mode", "TEXT DEFAULT 'parallel'"),
        # ADR-0005 v0.4 (audit N2): throwaway is opt-in and needs a rationale
        ("throwaway_rationale", "TEXT"),
        # Audit N8: multi-repo (FE / BE / monorepo workspace) as JSON array
        ("target_repos", "TEXT"),
        # Stupeň metody Quick / Lean / Full (ADR-0021); backfilled below
        ("tier", "TEXT CHECK (tier IN ('quick','lean','full'))"),
    ],
    "variants": [
        # Audit N10: diff walkthrough summary per variant (markdown)
        ("diff_summary_md", "TEXT"),
    ],
}


# Additive tables — unlike columns, new tables need no ALTER: the
# `CREATE TABLE IF NOT EXISTS` in schema.sql creates them on an existing DB
# during executescript. Listed here only so migrate reports when a table
# was newly created on an older database.
ADDITIVE_TABLES: tuple[str, ...] = (
    # Audit N4: outcome measurement (tool/cli/retro.py)
    "outcomes",
    # Audit N16: Claude Code token usage snapshots (tool/cli/ai_usage.py)
    "ai_usage",
)


# CHECK-constraint rebuilds — SQLite cannot ALTER a CHECK, so the table is
# recreated from its current DDL in schema.sql. Each entry maps a table to a
# marker string that the up-to-date DDL contains; a DB whose stored DDL lacks
# the marker gets rebuilt (idempotent: a second run finds the marker).
CHECK_REBUILDS: dict[str, str] = {
    # Audit N3: worktree extraction is a first-class extraction_method
    "extracted_code": "'worktree'",
}


def _existing_tables(conn) -> set[str]:
    return {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
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


def _backfill_tier(conn) -> int:
    """Fill projects.tier for rows created before the column existed."""
    from tool.cli.tier import infer_tier

    rows = conn.execute(
        "SELECT id, capacity_profile FROM projects WHERE tier IS NULL"
    ).fetchall()
    for row in rows:
        conn.execute(
            "UPDATE projects SET tier = ? WHERE id = ?",
            (infer_tier(conn, int(row[0]), row[1]), int(row[0])),
        )
    return len(rows)


def _schema_ddl(schema_sql: str, table: str) -> tuple[str, list[str]]:
    """Return (CREATE TABLE statement, CREATE INDEX statements) for `table`."""
    m = re.search(
        rf"CREATE TABLE IF NOT EXISTS {table} \((.*?)\n\);", schema_sql, re.DOTALL
    )
    if not m:
        raise RuntimeError(f"schema.sql has no CREATE TABLE for {table}")
    indexes = re.findall(
        rf"CREATE (?:UNIQUE )?INDEX IF NOT EXISTS \w+ ON {table}\([^)]*\);", schema_sql
    )
    return m.group(0), indexes


def _rebuild_check_tables(conn, schema_sql: str) -> list[str]:
    """Recreate tables whose stored DDL predates a CHECK change.

    Standard SQLite 12-step procedure: FKs off (outside the transaction, so
    DROP does not cascade into child tables such as quality_gates), create
    the new table, copy shared columns, drop, rename, recreate indexes,
    foreign_key_check, commit.
    """
    rebuilt: list[str] = []
    for table, marker in CHECK_REBUILDS.items():
        row = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone()
        if row is None or marker in (row[0] or ""):
            continue
        ddl, indexes = _schema_ddl(schema_sql, table)
        tmp = f"{table}__new"
        new_ddl = ddl.replace(
            f"CREATE TABLE IF NOT EXISTS {table} (", f"CREATE TABLE {tmp} (", 1
        )
        conn.execute("PRAGMA foreign_keys = OFF")
        try:
            conn.execute("BEGIN")
            try:
                conn.execute(new_ddl)
                old_cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})")]
                new_cols = {r[1] for r in conn.execute(f"PRAGMA table_info({tmp})")}
                cols = ", ".join(c for c in old_cols if c in new_cols)
                conn.execute(f"INSERT INTO {tmp} ({cols}) SELECT {cols} FROM {table}")
                conn.execute(f"DROP TABLE {table}")
                conn.execute(f"ALTER TABLE {tmp} RENAME TO {table}")
                for idx in indexes:
                    conn.execute(idx)
                violations = conn.execute("PRAGMA foreign_key_check").fetchall()
                if violations:
                    raise RuntimeError(
                        f"foreign_key_check failed after rebuilding {table}: {violations[:5]}"
                    )
                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                raise
        finally:
            conn.execute("PRAGMA foreign_keys = ON")
        rebuilt.append(table)
    return rebuilt


def apply_schema(reset: bool = False) -> None:
    db_path = _db.DB_PATH  # read at call time (tests / callers may repoint it)
    if reset and db_path.exists():
        db_path.unlink()
        print(f"[migrate] removed existing db: {db_path}")

    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn = get_connection()
    try:
        tables_before = _existing_tables(conn)
        conn.executescript(schema_sql)
        if tables_before:
            created = [t for t in ADDITIVE_TABLES if t not in tables_before]
            if created:
                print(f"[migrate] created additive tables: {', '.join(created)}")
        applied_alters = _apply_additive(conn)
        if applied_alters:
            print(f"[migrate] applied additive columns: {', '.join(applied_alters)}")
        backfilled = _backfill_tier(conn)
        if backfilled:
            print(f"[migrate] backfilled projects.tier for {backfilled} project(s)")
        rebuilt = _rebuild_check_tables(conn, schema_sql)
        if rebuilt:
            print(f"[migrate] rebuilt tables (CHECK update): {', '.join(rebuilt)}")
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
        print(f"[migrate] db at: {db_path}")
    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument(
        "--reset", action="store_true", help="Destructive: drop & recreate database."
    )
    args = parser.parse_args()
    apply_schema(reset=args.reset)
