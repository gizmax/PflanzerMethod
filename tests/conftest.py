"""Shared fixtures for the Pflanzer tool test-suite.

Hermetic by construction: every test gets its own HOME, SQLite DB
(`PFLANZER_DB`), target clone cache (`PFLANZER_TARGETS_DIR`) and output
directories under `tmp_path`. Nothing touches `~/.pflanzer`, the repo's
`data/` / `extracted/` directories or the network.
"""
from __future__ import annotations

import importlib
import json
import subprocess
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# Modules whose module-level output dirs (REPO_ROOT/data/..., REPO_ROOT/extracted)
# get redirected into tmp_path.
CLI_MODULES = (
    "db", "charter", "roles", "triage", "builder_decision", "session", "session_2",
    "session_3", "quick_session", "quality_gates", "extract", "worktree",
    "handoff", "handoff_pr", "retro", "feedback_pull", "init",
)
REDIRECT_ROOTS = (REPO_ROOT / "data", REPO_ROOT / "extracted")

GIT_USER = ("Test Dev", "dev@example.com")


def git(cwd: Path, *args: str, check: bool = True) -> str:
    """Run git in `cwd` and return stripped stdout."""
    res = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=60)
    if check and res.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed in {cwd}: {res.stderr}")
    return res.stdout.strip()


@pytest.fixture(autouse=True)
def isolated_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    home = tmp_path / "home"
    home.mkdir()
    (home / ".gitconfig").write_text(
        "[user]\n"
        f"\tname = {GIT_USER[0]}\n"
        f"\temail = {GIT_USER[1]}\n"
        "[init]\n\tdefaultBranch = main\n"
        "[commit]\n\tgpgsign = false\n"
        "[protocol \"file\"]\n\tallow = always\n",
        encoding="utf-8",
    )
    db_path = tmp_path / "pflanzer.db"
    targets = tmp_path / "targets"
    out_root = tmp_path / "out"

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("PFLANZER_DB", str(db_path))
    monkeypatch.setenv("PFLANZER_TARGETS_DIR", str(targets))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    # CLAUDE_CONFIG_DIR / PFLANZER_AI_PRICES: ai_usage.py must read only the test HOME.
    for var in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "XDG_CONFIG_HOME",
                "CLAUDE_CONFIG_DIR", "PFLANZER_AI_PRICES"):
        monkeypatch.delenv(var, raising=False)

    # Module-level constants were computed at import time — repoint them.
    for name in CLI_MODULES:
        mod = importlib.import_module(f"tool.cli.{name}")
        for attr, value in list(vars(mod).items()):
            if not isinstance(value, Path) or not attr.isupper():
                continue
            for root in REDIRECT_ROOTS:
                try:
                    rel = value.relative_to(root)
                except ValueError:
                    continue
                monkeypatch.setattr(mod, attr, out_root / root.name / rel)
                break
        if hasattr(mod, "TARGETS_CACHE"):
            monkeypatch.setattr(mod, "TARGETS_CACHE", targets)
    db_mod = importlib.import_module("tool.cli.db")
    monkeypatch.setattr(db_mod, "DB_PATH", db_path)
    return {"home": home, "db": db_path, "targets": targets, "out": out_root}


@pytest.fixture
def tmp_db(isolated_env: dict[str, Path]) -> Path:
    """Fresh DB with the current schema applied."""
    from tool.db.migrate import apply_schema

    apply_schema()
    return isolated_env["db"]


@pytest.fixture
def tmp_targets(isolated_env: dict[str, Path]) -> Path:
    return isolated_env["targets"]


def make_bare_repo(root: Path, name: str, files: dict[str, str] | None = None) -> Path:
    """Local bare repo with `main` and one commit; returns the bare path."""
    src = root / f"{name}-src"
    src.mkdir(parents=True)
    git(src, "init", "-q", "-b", "main")
    content = {
        "package.json": json.dumps({"name": name, "version": "0.0.0", "private": True},
                                   indent=2) + "\n",
        ".gitignore": "node_modules/\n",
        "README.md": f"# {name}\n",
    }
    content.update(files or {})
    for rel, text in content.items():
        p = src / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    git(src, "add", "-A")
    git(src, "commit", "-q", "-m", "chore: initial commit")
    bare = root / "origin" / f"{name}.git"
    bare.parent.mkdir(parents=True, exist_ok=True)
    git(root, "clone", "-q", "--bare", str(src), str(bare))
    return bare


@pytest.fixture
def bare_repo(tmp_path: Path) -> Path:
    return make_bare_repo(tmp_path / "repos", "demo-app")


def push_files(bare: Path, files: dict[str, str], message: str = "chore: update") -> None:
    """Commit files onto `main` of a bare repo (via a throwaway clone)."""
    work = bare.parent / f"_push-{bare.stem}"
    if not work.exists():
        git(bare.parent, "clone", "-q", str(bare), str(work))
    git(work, "pull", "-q", "origin", "main")
    for rel, text in files.items():
        p = work / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    git(work, "add", "-A")
    git(work, "commit", "-q", "-m", message)
    git(work, "push", "-q", "origin", "main")


def file_url(path: Path) -> str:
    return f"file://{path}"


def bootstrap_project(*, risk_profile: str = "pilot", slug: str = "checkout",
                      target_repo_url: str | None = None, **kw: Any) -> dict[str, Any]:
    from tool.cli.quick_session import bootstrap

    return bootstrap(
        hook="Rychlejší checkout pro B2B zákazníky", decider_name="Dana Deciderová",
        room_role_idx=[1, 2, 3, 4, 6], risk_profile=risk_profile, slug=slug,
        role_owners={4: "Petr Frontend"}, target_repo_url=target_repo_url, **kw,
    )


@pytest.fixture
def project(tmp_db: Path, bare_repo: Path) -> dict[str, Any]:
    out = bootstrap_project(target_repo_url=file_url(bare_repo))
    out["bare_repo"] = bare_repo
    return out


def _pref(user_value: float, rationale: str = "Test rationale — rychlejší flow") -> dict[str, Any]:
    return {"role_idx": 1, "user_value": user_value, "effort": 0.4, "risk": 0.2,
            "strategic_fit": 0.7, "commitment_level": 2, "rationale": rationale}


@pytest.fixture
def vote() -> Callable[..., dict[str, Any]]:
    """Record a Session 1 vote with variants A/B/C (A preferred)."""
    from tool.cli.quick_session import record_voting

    def _vote(slug: str, *, names: tuple[str, ...] = ("A", "B", "C"),
              builder: str = "claude-code", diff_summary: Any = None,
              status: str | None = None) -> dict[str, Any]:
        scores = {"A": 0.9, "B": 0.6, "C": 0.3}
        votes = [{
            "name": n, "builder": builder, "description": f"Varianta {n}",
            "diff_summary": diff_summary if n == "A" else None,
            "role_preferences": [_pref(scores.get(n, 0.5))],
        } for n in names]
        out = record_voting(
            slug=slug, facilitator="Fanda Facilitátor", votes=votes,
            decider_call={"shortlist": list(names[:2]), "rationale": "A je nejrychlejší",
                          "veto_register": [], "parking_lot": []},
        )
        if status:
            set_status(slug, status)
        return out

    return _vote


def set_status(slug: str, status: str) -> None:
    from tool.cli.db import transaction

    with transaction() as conn:
        conn.execute("UPDATE projects SET status = ? WHERE slug = ?", (status, slug))


def worktree_path(targets: Path, slug: str, variant: str) -> Path:
    return targets / f"{slug}-{variant}"


GATES_ADAPTER_INSUFFICIENT = (
    "# Pflanzer gate adapter (test) — only 2 gates -> gates:insufficient\n"
    "build: {cmd: \"true\"}\n"
    "tests: {cmd: \"true\"}\n"
)


@pytest.fixture
def worktree_project(project: dict[str, Any], tmp_targets: Path) -> Iterator[dict[str, Any]]:
    """Pilot project + gate adapter on the base branch + A/B/C worktrees (no install)."""
    from tool.cli import worktree

    push_files(project["bare_repo"], {"pflanzer.gates.yml": GATES_ADAPTER_INSUFFICIENT},
               "ci: add pflanzer gate adapter")
    worktree.setup(project["slug"], install_deps=False, run_guard=False)
    wts = {v: worktree_path(tmp_targets, project["slug"], v) for v in ("A", "B", "C")}
    for wt in wts.values():
        # Pre-created node_modules keeps quality_gates from running `npm install`.
        (wt / "node_modules").mkdir(exist_ok=True)
    yield {**project, "worktrees": wts}
