"""worktree.py: setup, trailer hook, data leakage guard, set-session, init-pr."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest
from conftest import git, worktree_path

from tool.cli import worktree


def _cli(monkeypatch: pytest.MonkeyPatch, *args: str) -> int:
    """Run `worktree.py <args>` in-process; returns the exit code."""
    monkeypatch.setattr(sys, "argv", ["worktree.py", *args])
    try:
        worktree.main()
    except SystemExit as exc:
        return int(exc.code or 0)
    return 0


@pytest.fixture
def setup_done(project: dict[str, Any], tmp_targets: Path,
               monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
               ) -> dict[str, Any]:
    rc = _cli(monkeypatch, "setup", "--slug", project["slug"], "--skip-install",
              "--no-guard", "--json")
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    return {**project, "setup": out}


def test_setup_creates_three_worktrees_and_hook(setup_done: dict[str, Any],
                                                tmp_targets: Path) -> None:
    slug = setup_done["slug"]
    for v in ("A", "B", "C"):
        wt = worktree_path(tmp_targets, slug, v)
        assert wt.is_dir()
        assert git(wt, "branch", "--show-current") == f"pflanzer/{slug}-{v}"
        assert git(wt, "config", "--worktree", "--get", "pflanzer.variant") == f"{slug}-{v}"
        assert git(wt, "config", "--worktree", "--get", "pflanzer.session") == "1"
        assert "Pflanzer session rules" in (wt / "CLAUDE.md").read_text(encoding="utf-8")
        assert git(wt, "status", "--porcelain") == ""  # CLAUDE.md excluded locally

    clone = Path(setup_done["setup"]["target_clone_path"])
    hooks = Path(git(clone, "rev-parse", "--git-common-dir"))
    hooks = (hooks if hooks.is_absolute() else clone / hooks) / "hooks"
    for name in ("prepare-commit-msg", "commit-msg", worktree.HOOK_CORE_NAME):
        assert (hooks / name).is_file()
        assert worktree.HOOK_MARKER in (hooks / name).read_text(encoding="utf-8")
    assert setup_done["setup"]["repos"][0]["hook"]["status"] == "installed"


def test_commit_in_worktree_gets_trailers(setup_done: dict[str, Any], tmp_targets: Path) -> None:
    slug = setup_done["slug"]
    wt = worktree_path(tmp_targets, slug, "A")
    (wt / "feature.js").write_text("export const answer = 42;\n", encoding="utf-8")
    git(wt, "add", "feature.js")
    git(wt, "commit", "-q", "-m", "feat: add answer")
    body = git(wt, "log", "-1", "--format=%B")
    assert f"Pflanzer-Variant: {slug}-A" in body
    assert "Pflanzer-Session: 1" in body
    assert "AI-Assisted: claude-code" in body
    assert "Co-Authored-By" not in body


def test_guard_finds_secret_and_tracked_env(setup_done: dict[str, Any], tmp_targets: Path,
                                            monkeypatch: pytest.MonkeyPatch,
                                            capsys: pytest.CaptureFixture[str]) -> None:
    slug = setup_done["slug"]
    wt = worktree_path(tmp_targets, slug, "B")
    (wt / "config.js").write_text('const key = "AKIAABCDEFGHIJKLMNOP";\n', encoding="utf-8")
    (wt / ".env").write_text("DB_URL=postgres://prod\n", encoding="utf-8")
    git(wt, "add", "-f", ".env")
    git(wt, "commit", "-q", "-m", "chore: oops")

    rows = worktree.guard(slug, fix_gitignore=False)
    b_rows = {r["check"]: r for r in rows if r["variant"] == "B"}
    secrets = next(r for c, r in b_rows.items() if c.startswith("secrets"))
    assert secrets["status"] == "FAIL"
    assert "config.js" in secrets["detail"]
    assert b_rows[".env* trackované"]["status"] == "FAIL"
    # clean variant stays OK on secrets
    a_secrets = next(r for r in rows if r["variant"] == "A" and r["check"].startswith("secrets"))
    assert a_secrets["status"] == "OK"

    capsys.readouterr()
    assert _cli(monkeypatch, "guard", "--slug", slug, "--strict", "--no-fix") != 0
    assert "Data leakage guard" in capsys.readouterr().out


def test_set_session_ship(setup_done: dict[str, Any], tmp_targets: Path,
                          monkeypatch: pytest.MonkeyPatch,
                          capsys: pytest.CaptureFixture[str]) -> None:
    slug = setup_done["slug"]
    assert _cli(monkeypatch, "set-session", "--slug", slug, "--session", "ship") == 0
    res = json.loads(capsys.readouterr().out)
    assert {r["variant"] for r in res} == {"A", "B", "C"}
    assert all(r["status"] == "ok" for r in res)
    for v in ("A", "B", "C"):
        wt = worktree_path(tmp_targets, slug, v)
        assert git(wt, "config", "--worktree", "--get", "pflanzer.session") == "ship"


def test_init_pr_is_idempotent(setup_done: dict[str, Any], tmp_targets: Path,
                               monkeypatch: pytest.MonkeyPatch,
                               capsys: pytest.CaptureFixture[str]) -> None:
    slug = setup_done["slug"]
    assert _cli(monkeypatch, "init-pr", "--slug", slug, "--json") == 0
    first = json.loads(capsys.readouterr().out)[0]
    assert first["status"] == "committed"
    assert first["branch"] == f"pflanzer/{slug}-init"
    assert "docs/INTEGRATION_GUIDE.md" in first["changed"]
    assert "CLAUDE.md" in first["changed"]

    wt = Path(first["worktree"])
    assert (wt / "docs" / "INTEGRATION_GUIDE.md").is_file()
    assert "<!-- pflanzer:start -->" in (wt / "CLAUDE.md").read_text(encoding="utf-8")
    files = git(wt, "show", "--name-only", "--format=", "HEAD").splitlines()
    assert {"docs/INTEGRATION_GUIDE.md", "CLAUDE.md"} <= set(files)
    head = git(wt, "rev-parse", "HEAD")
    assert Path(first["pr_body"]).is_file()

    assert _cli(monkeypatch, "init-pr", "--slug", slug, "--json") == 0
    second = json.loads(capsys.readouterr().out)[0]
    assert second["status"] == "already-on-branch"
    assert second["changed"] == []
    assert git(wt, "rev-parse", "HEAD") == head


def test_verify_rejects_foreign_repo(setup_done: dict[str, Any], tmp_path: Path) -> None:
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    git(foreign, "init", "-q")
    git(foreign, "remote", "add", "origin", "https://github.com/other/repo.git")
    ok, _msg = worktree.verify_cwd_in_target(setup_done["slug"], foreign)
    assert ok is False
    ok, msg = worktree.verify_cwd_in_target(
        setup_done["slug"], Path(setup_done["setup"]["worktrees"][0]))
    assert ok, msg


def _commit_in_a(setup_done: dict[str, Any], tmp_targets: Path) -> None:
    wt = worktree_path(tmp_targets, setup_done["slug"], "A")
    (wt / "feature.txt").write_text("variant A\n", encoding="utf-8")
    git(wt, "add", "feature.txt")
    git(wt, "commit", "-m", "feat: variant A")


def test_preview_run_refuses_without_consent(setup_done: dict[str, Any], tmp_targets: Path,
                                             monkeypatch: pytest.MonkeyPatch,
                                             capsys: pytest.CaptureFixture[str]) -> None:
    """`preview --run` pushes to the customer's remote: non-interactive without --yes = refuse."""
    _commit_in_a(setup_done, tmp_targets)
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    called: list[bool] = []
    monkeypatch.setattr(worktree, "preview_draft_pr",
                        _spy(worktree.preview_draft_pr, called))
    rc = _cli(monkeypatch, "preview", "--slug", setup_done["slug"], "--run")
    assert rc == 2
    err = capsys.readouterr().err
    assert "zrušen" in err and "--yes" in err and "remote:" in err
    assert called == [False]  # only the dry-run plan ran, never run=True


def test_confirm_preview_push_interactive(setup_done: dict[str, Any], tmp_targets: Path) -> None:
    _commit_in_a(setup_done, tmp_targets)
    slug = setup_done["slug"]
    assert worktree.confirm_preview_push(slug, input_fn=lambda _: "ne", isatty=True) is False
    assert worktree.confirm_preview_push(slug, input_fn=lambda _: "ano", isatty=True) is True
    assert worktree.confirm_preview_push(slug, assume_yes=True, isatty=False) is True


def _spy(fn: Any, calls: list[bool]) -> Any:
    def wrapper(slug: str, *, run: bool = False) -> Any:
        calls.append(run)
        return fn(slug, run=run)
    return wrapper
