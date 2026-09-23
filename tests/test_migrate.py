"""migrate.py upgrades a DB created from the v0 schema (commit 27326c6)."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from tool.db.migrate import apply_schema

FIXTURE = Path(__file__).parent / "fixtures" / "schema-v0.sql"


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}


def _tables(conn: sqlite3.Connection) -> set[str]:
    return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def _extracted_ddl(conn: sqlite3.Connection) -> str:
    return conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='extracted_code'"
    ).fetchone()[0]


@pytest.fixture
def old_db(isolated_env: dict[str, Path]) -> Path:
    """DB built from the v0 schema, with one extracted_code row + gate row."""
    db = isolated_env["db"]
    conn = sqlite3.connect(db)
    conn.executescript(FIXTURE.read_text(encoding="utf-8"))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("INSERT INTO projects (id, slug, name) VALUES (1, 'legacy', 'Legacy')")
    conn.execute("INSERT INTO sessions (id, project_id, type) VALUES (1, 1, 1)")
    conn.execute(
        "INSERT INTO variants (id, session_id, name, builder, prototype_url) "
        "VALUES (1, 1, 'A', 'claude-code', 'local://a')"
    )
    conn.execute(
        "INSERT INTO extracted_code (id, variant_id, source_url, local_path, "
        "extraction_method, extracted_by) VALUES (7, 1, 'local://a', '/tmp/a', "
        "'in_repo_branch', 'tester')"
    )
    conn.execute(
        "INSERT INTO quality_gates (extracted_id, gate_type, status) VALUES (7, 'build', 'pass')"
    )
    conn.commit()
    conn.close()
    return db


def test_v0_schema_lacks_new_things(old_db: Path) -> None:
    conn = sqlite3.connect(old_db)
    assert "worktree" not in _extracted_ddl(conn)
    assert "outcomes" not in _tables(conn)
    assert "target_repos" not in _columns(conn, "projects")
    conn.close()


def test_migration_upgrades_v0_db(old_db: Path) -> None:
    apply_schema()
    conn = sqlite3.connect(old_db)
    conn.execute("PRAGMA foreign_keys = ON")
    project_cols = _columns(conn, "projects")
    assert {"throwaway_rationale", "target_repos", "acceptance_criteria_md",
            "session_mode"} <= project_cols
    assert "diff_summary_md" in _columns(conn, "variants")
    assert "outcomes" in _tables(conn)
    assert "'worktree'" in _extracted_ddl(conn)

    # Data survived the rebuild, child rows were not cascade-deleted.
    row = conn.execute(
        "SELECT id, extraction_method FROM extracted_code WHERE id = 7"
    ).fetchone()
    assert row == (7, "in_repo_branch")
    gates = conn.execute("SELECT COUNT(*) FROM quality_gates WHERE extracted_id = 7")
    assert gates.fetchone()[0] == 1
    assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
    idx = {r[1] for r in conn.execute("PRAGMA index_list(extracted_code)")}
    assert "idx_extracted_variant" in idx

    # New CHECK accepts 'worktree' and still rejects garbage.
    conn.execute(
        "INSERT INTO extracted_code (variant_id, source_url, local_path, extraction_method, "
        "extracted_by) VALUES (1, 'u', '/tmp/w', 'worktree', 't')"
    )
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO extracted_code (variant_id, source_url, local_path, "
            "extraction_method, extracted_by) VALUES (1, 'u', '/tmp/w', 'bogus', 't')"
        )
    conn.close()


def test_migration_is_idempotent(old_db: Path, capsys: pytest.CaptureFixture[str]) -> None:
    apply_schema()
    first = capsys.readouterr().out
    assert "rebuilt tables (CHECK update): extracted_code" in first
    conn = sqlite3.connect(old_db)
    ddl_before = _extracted_ddl(conn)
    conn.close()

    apply_schema()
    second = capsys.readouterr().out
    assert "rebuilt tables" not in second
    assert "applied additive columns" not in second
    conn = sqlite3.connect(old_db)
    assert _extracted_ddl(conn) == ddl_before
    assert conn.execute("SELECT COUNT(*) FROM extracted_code").fetchone()[0] == 1
    conn.close()


def test_fresh_db_needs_no_rebuild(tmp_db: Path, capsys: pytest.CaptureFixture[str]) -> None:
    apply_schema()
    assert "rebuilt tables" not in capsys.readouterr().out
