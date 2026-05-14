"""SQLite database helpers for Pflanzer tool.

Single shared connection per process. Audit logging + prompt retention
honor DORA 7-year retention requirements (devil's advocate Útok 8).
"""
from __future__ import annotations

import json
import sqlite3
import subprocess
from contextlib import contextmanager
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Iterator

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "tool" / "db" / "schema.sql"
DORA_RETENTION = timedelta(days=365 * 7 + 2)  # 7 years + leap days buffer


def _resolve_db_path() -> Path:
    """Resolve DB location.

    Order:
    1. PFLANZER_DB env var (explicit override)
    2. ~/.pflanzer/pflanzer.db if ~/.pflanzer/ exists (installed plugin path)
    3. <repo>/data/pflanzer.db (dev mode — running from cloned source)
    """
    import os
    if env := os.environ.get("PFLANZER_DB"):
        return Path(env).expanduser()
    user_dir = Path.home() / ".pflanzer"
    if user_dir.exists():
        return user_dir / "pflanzer.db"
    return REPO_ROOT / "data" / "pflanzer.db"


DB_PATH = _resolve_db_path()


def get_connection() -> sqlite3.Connection:
    """Return a SQLite connection with row_factory and FK enforcement."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


@contextmanager
def transaction() -> Iterator[sqlite3.Connection]:
    """Atomic transaction context manager."""
    conn = get_connection()
    try:
        conn.execute("BEGIN")
        yield conn
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()


def current_actor() -> str:
    """Resolve current actor for audit/decision attribution.

    Per devil's advocate Útok 8: human attribution for DORA/AI Act/GDPR.
    Until SSO arrives, we use git config user.email + user.name.
    """
    try:
        email = subprocess.check_output(
            ["git", "config", "user.email"], cwd=REPO_ROOT, text=True
        ).strip()
        name = subprocess.check_output(
            ["git", "config", "user.name"], cwd=REPO_ROOT, text=True
        ).strip()
        return f"{name} <{email}>"
    except subprocess.CalledProcessError:
        return "unknown"


def audit(
    conn: sqlite3.Connection,
    *,
    actor: str | None = None,
    action: str,
    target_type: str | None = None,
    target_id: int | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    """Append an audit log row."""
    conn.execute(
        """
        INSERT INTO audit_log (actor, action, target_type, target_id, payload_json, retention_until)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            actor or current_actor(),
            action,
            target_type,
            target_id,
            json.dumps(payload, ensure_ascii=False) if payload else None,
            (date.today() + DORA_RETENTION).isoformat(),
        ),
    )


def log_prompt(
    conn: sqlite3.Connection,
    *,
    project_id: int | None,
    role_id: int | None,
    model: str,
    prompt_text: str,
    response_text: str,
) -> None:
    """Persist prompt + response with 7-year retention (devil's advocate Útok 8)."""
    conn.execute(
        """
        INSERT INTO prompts (project_id, role_id, model, prompt_text, response_text, retention_until)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            project_id,
            role_id,
            model,
            prompt_text,
            response_text,
            (date.today() + DORA_RETENTION).isoformat(),
        ),
    )
