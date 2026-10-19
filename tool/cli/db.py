"""SQLite database helpers for Pflanzer tool.

Single shared connection per process. Audit logging + prompt retention
honor DORA 7-year retention requirements (devil's advocate Útok 8).
"""
from __future__ import annotations

import json
import re
import sqlite3
import subprocess
from contextlib import contextmanager
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Iterator

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "tool" / "db" / "schema.sql"
DORA_RETENTION = timedelta(days=365 * 7 + 2)  # 7 years + leap days buffer


def _resolve_data_root() -> Path:
    """Resolve the single data folder (DB + charters + feedback + quick + ...).

    Order:
    1. PFLANZER_DATA env var (explicit override of the whole data dir)
    2. ~/.pflanzer/ if ~/.pflanzer/pflanzer.db exists (installed plugin)
    3. <repo>/data (dev mode — running from cloned source)

    The decision keys on the DB *file*, not on the ~/.pflanzer/ directory:
    A clone cache directory under ~/.pflanzer (e.g. older `targets/`) must not
    silently move a dev-mode DB away from data/pflanzer.db.
    (PFLANZER_DB overrides just the DB file, see `_resolve_db_path`.)
    """
    import os
    if env := os.environ.get("PFLANZER_DATA"):
        return Path(env).expanduser()
    user_dir = Path.home() / ".pflanzer"
    if (user_dir / "pflanzer.db").is_file():
        return user_dir
    return REPO_ROOT / "data"


def _resolve_db_path() -> Path:
    """Resolve DB location: PFLANZER_DB env override, else DATA_ROOT/pflanzer.db."""
    import os
    if env := os.environ.get("PFLANZER_DB"):
        return Path(env).expanduser()
    return _resolve_data_root() / "pflanzer.db"


DATA_ROOT = _resolve_data_root()
DB_PATH = _resolve_db_path()


def resolve_local_repo_url(url: str | None, base: Path | None = None) -> str | None:
    """Relativní cesta k lokálnímu repu (`../origin.git`) -> absolutní (vůči `base`, default cwd).

    URL se schématem, scp-like ssh (`git@host:org/repo`) i absolutní cesty zůstávají beze změny.
    Relativní cesta se převede jen když existuje (jinak ji necháme, ať validace hlásí chybu).
    """
    if not url:
        return url
    u = url.strip()
    if "://" in u or re.match(r"^[\w.-]+@[\w.-]+:", u) or u.startswith(("/", "<", "file:")):
        return u
    cand = Path(u).expanduser()
    if not cand.is_absolute():
        cand = (base or Path.cwd()) / cand
    try:
        cand = cand.resolve()
    except OSError:
        return u
    return str(cand) if cand.is_dir() else u


def load_project_toml(start: Path | None = None) -> dict[str, str]:
    """Read `[project]` defaults from `.pflanzer/project.toml` (written by `pflanzer init`).

    Looks in `start` (default cwd = the target repo). Placeholder values
    like `<@github-handle>` are skipped.
    """
    path = (start or Path.cwd()) / ".pflanzer" / "project.toml"
    if not path.is_file():
        return {}
    out: dict[str, str] = {}
    in_project = False
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line.startswith("["):
            in_project = line == "[project]"
        elif in_project and "=" in line:
            key, val = (x.strip() for x in line.split("=", 1))
            val = val.strip('"')
            if val and not val.startswith("<"):
                out[key] = val
    if "target_repo_url" in out:
        out["target_repo_url"] = resolve_local_repo_url(
            out["target_repo_url"], path.parent.parent) or out["target_repo_url"]
    return out


def display_path(path: Path) -> str:
    """Repo-relative path when inside the method repo, else absolute (e.g. ~/.pflanzer/targets/)."""
    path = Path(path).resolve()
    return str(path.relative_to(REPO_ROOT)) if path.is_relative_to(REPO_ROOT) else str(path)


_SCHEMA_CHECKED: set[str] = set()


def _schema_version() -> int:
    """Fingerprint schématu + migrací (31 bitů) — změna = DB se dorovná sama."""
    import hashlib
    h = hashlib.sha256()
    for f in (SCHEMA_PATH, REPO_ROOT / "tool" / "db" / "migrate.py"):
        h.update(f.read_bytes() if f.exists() else b"")
    return int(h.hexdigest()[:7], 16)


def _ensure_schema(conn: sqlite3.Connection) -> None:
    """Po aktualizaci toolu dorovnej existující DB (bez ručního `pflanzer update`)."""
    key = str(DB_PATH)
    if key in _SCHEMA_CHECKED:
        return
    _SCHEMA_CHECKED.add(key)
    want = _schema_version()
    have = conn.execute("PRAGMA user_version").fetchone()[0]
    has_tables = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='projects'").fetchone()
    if have == want or not has_tables:
        return  # aktuální, nebo prázdná DB (tu zakládá migrate/fixture)
    import contextlib
    import io

    from tool.db import migrate  # noqa: PLC0415 — lazy, avoids import cycle
    with contextlib.redirect_stdout(io.StringIO()):
        migrate.apply_schema()
    conn.execute(f"PRAGMA user_version = {want}")


def get_connection() -> sqlite3.Connection:
    """Return a SQLite connection with row_factory and FK enforcement."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    _ensure_schema(conn)
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


def _git_config(key: str, *, cwd: Path | None = None, global_only: bool = False) -> str:
    cmd = ["git", "config"] + (["--global"] if global_only else []) + [key]
    try:
        res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return ""
    return res.stdout.strip() if res.returncode == 0 else ""


def current_actor() -> str:
    """Resolve current actor for audit/decision attribution.

    Per devil's advocate Útok 8: human attribution for DORA/AI Act/GDPR.
    Until SSO arrives, we use git config user.name/user.email. Order: git
    config seen from cwd (the target repo: local, then global values), then
    explicit global config, then `unknown`.
    """
    name = _git_config("user.name") or _git_config("user.name", global_only=True)
    email = _git_config("user.email") or _git_config("user.email", global_only=True)
    if name and email:
        return f"{name} <{email}>"
    return name or email or "unknown"


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
