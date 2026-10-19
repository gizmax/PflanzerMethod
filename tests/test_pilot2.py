"""Nálezy z pilotu „Šnek Servis“: ai_signers (G1), doctor bez závislostí (G3),
Python .venv ve worktrees (G4)."""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest
from conftest import bootstrap_project, file_url, git, set_status

from tool.cli import checkpoint, doctor, status, worktree
from tool.cli.db import transaction

OWNERS = {"byznys": "Dana", "produkt": "Petr", "design": "Eva", "vyvoj": "Tomáš",
          "bezpecnost": "AI:security-expert", "provoz": "Karel"}


def _boot(bare_repo: Path, slug: str = "snek", **kw: Any) -> dict[str, Any]:
    return bootstrap_project(slug=slug, target_repo_url=file_url(bare_repo), **kw)


# ------------------------------------------------------------------ G1


def test_ai_signers_field_shown_in_status(tmp_db: Path, bare_repo: Path) -> None:
    out = _boot(bare_repo, path_owners=dict(OWNERS), ai_signers={"bezpecnost": "Pavel Šnek"})
    assert out["ai_signers"] == {"bezpecnost": "Pavel Šnek"}
    assert any(a["signer"] == "Pavel Šnek" for a in out["ai_stand_ins"])
    d = status.project_detail("snek")
    assert d["ai_signers"] == {"bezpecnost": "Pavel Šnek"}
    cp = next(c for c in d["checkpoints"] if c["window"] == "bezpecnost")
    assert cp["designated"] == "Pavel Šnek"
    assert any("podepíše Pavel Šnek" in ln for ln in status.detail_lines(d))
    assert not any("určete kdo" in n for n in status.ai_notes(d))
    assert "podepisuje Pavel Šnek" in (Path(out["charter_path"]).read_text(encoding="utf-8"))


@pytest.mark.parametrize("sep", [" / ", "|", " | "])
def test_ai_signers_shorthand_in_path_owners(tmp_db: Path, bare_repo: Path, sep: str) -> None:
    owners = {**OWNERS, "bezpecnost": f"AI:security-expert{sep}Pavel Šnek"}
    out = _boot(bare_repo, path_owners=owners)
    assert out["path_owners"]["bezpecnost"] == "AI:security-expert"
    assert out["ai_signers"] == {"bezpecnost": "Pavel Šnek"}
    with transaction() as conn:
        raw = conn.execute("SELECT ai_signers_json FROM projects WHERE slug='snek'").fetchone()[0]
    assert "Pavel Šnek" in raw


def test_ai_signers_pending_draft_names_signer_in_log(tmp_db: Path, bare_repo: Path,
                                                      tmp_path: Path,
                                                      monkeypatch: pytest.MonkeyPatch) -> None:
    _boot(bare_repo, path_owners=dict(OWNERS), ai_signers={"bezpecnost": "Pavel Šnek"})
    repo = tmp_path / "target"
    (repo / ".pflanzer").mkdir(parents=True)
    monkeypatch.chdir(repo)
    out = checkpoint.sign("snek", "bezpecnost", ai=True, note="AI pre-check")
    assert out["status"] == "pending"
    assert not any("nikdo zatím není určen" in w for w in out["warnings"])
    assert "Pavel Šnek" in out["next_step"]
    log = (repo / ".pflanzer" / "decisions" / "snek.md").read_text(encoding="utf-8")
    assert "čeká na podpis: Pavel Šnek" in log
    set_status("snek", "handoff")
    d = status.project_detail("snek")
    assert any("podepíše Pavel Šnek" in b["text"] for b in d["blockers"])
    # určený člověk potvrdí bez varování
    ok = checkpoint.sign("snek", "bezpecnost", by="Pavel Šnek", note="ověřeno")
    assert ok["status"] == "ok" and ok["countersigned_ai_draft"]
    assert not [w for w in ok["warnings"] if "určený" in w]
    summ = {r["window"]: r for r in checkpoint.checkpoint_summary("snek")}
    assert summ["bezpecnost"]["designated_signer"] == "Pavel Šnek"


def test_sign_by_other_human_warns_designated(tmp_db: Path, bare_repo: Path) -> None:
    _boot(bare_repo, path_owners=dict(OWNERS), ai_signers={"bezpecnost": "Pavel Šnek"})
    out = checkpoint.sign("snek", "bezpecnost", by="Dana", note="ok")
    assert any("Pavel Šnek" in w and "určený" in w for w in out["warnings"])


def test_ai_signer_code_author_warns(tmp_db: Path, bare_repo: Path) -> None:
    out = _boot(bare_repo, path_owners=dict(OWNERS), ai_signers={"bezpecnost": "Tomáš"})
    assert any("autor kódu" in w and "Tomáš" in w for w in out["warnings"])


def test_ai_signers_validation(tmp_db: Path, bare_repo: Path) -> None:
    with pytest.raises(ValueError, match="neznámý krok"):
        _boot(bare_repo, path_owners=dict(OWNERS), ai_signers={"vyvoj": "Pavel"})
    with pytest.raises(ValueError, match="člověk"):
        _boot(bare_repo, path_owners=dict(OWNERS), ai_signers={"bezpecnost": "AI"})
    out = _boot(bare_repo, slug="snek2", path_owners=dict(OWNERS),
                ai_signers={"provoz": "Pavel"})   # provoz zastupuje člověk -> ignorováno
    assert any("ignoruji" in w for w in out["warnings"])
    assert out["ai_signers"] is None


# ------------------------------------------------------------------ G3


def _check(repo: Path) -> dict[str, str]:
    return doctor.check_package_manager(repo)


def test_doctor_python_without_dependencies_no_lockfile_warning(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "x"\nversion = "0.1"\n', encoding="utf-8")
    res = _check(tmp_path)
    assert res["status"] == doctor.OK and "bez závislostí" in res["detail"]


def test_doctor_python_with_dependencies_still_warns(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "x"\nversion = "0.1"\ndependencies = ["requests"]\n', encoding="utf-8")
    assert _check(tmp_path)["status"] == doctor.WARN
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\n', encoding="utf-8")
    (tmp_path / "requirements-dev.txt").write_text("pytest\n", encoding="utf-8")
    assert _check(tmp_path)["status"] == doctor.WARN


def test_doctor_node_without_dependencies(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text('{"name": "x", "scripts": {}}', encoding="utf-8")
    assert _check(tmp_path)["status"] == doctor.OK
    (tmp_path / "package.json").write_text('{"name": "x", "devDependencies": {"vitest": "1"}}',
                                           encoding="utf-8")
    assert _check(tmp_path)["status"] == doctor.WARN


# ------------------------------------------------------------------ G4


def _fake_run(calls: list[list[str]]):
    real = subprocess.run

    def run(cmd: list[str], cwd: Path | None = None, timeout: int = 300,
            env: dict[str, str] | None = None) -> tuple[int, str, str]:
        calls.append(list(cmd))
        if "pip" in cmd:       # pip by šel na síť; venv a git jsou lokální
            return 0, "", ""
        r = real(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr

    return run


def _py_worktree(tmp_path: Path, name: str = "wt", pyproject: str | None = None) -> Path:
    wt = tmp_path / name
    wt.mkdir()
    (wt / "pyproject.toml").write_text(pyproject or '[project]\nname = "x"\nversion = "0.1"\n',
                                       encoding="utf-8")
    (wt / "Makefile").write_text("test:\n\t.venv/bin/python -m pytest -q\n"
                                 "lint:\n\t.venv/bin/python -m ruff check .\n", encoding="utf-8")
    return wt


def test_worktree_python_creates_venv_and_hints_dev_tools(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []
    monkeypatch.setattr(worktree, "_run", _fake_run(calls))
    wt = _py_worktree(tmp_path)
    res = worktree._install_deps([wt], None)
    assert res[0]["status"] == "ok" and res[0]["kind"] == "python"
    assert (wt / ".venv" / "bin" / "python").exists()
    pip = [c for c in calls if "pip" in c]
    assert pip and pip[-1][-2:] == ["pytest", "ruff"]
    assert res[0]["dev_tools_missing"] == ["pytest", "ruff"]


def test_worktree_python_declared_dev_extra_installed_editable(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []
    monkeypatch.setattr(worktree, "_run", _fake_run(calls))
    wt = _py_worktree(tmp_path, pyproject=(
        '[project]\nname = "x"\nversion = "0.1"\n'
        '[project.optional-dependencies]\ndev = ["pytest", "ruff"]\n'))
    (wt / "requirements.txt").write_text("requests\n", encoding="utf-8")
    res = worktree._install_deps([wt], None)[0]
    assert res["status"] == "ok" and "dev_tools_missing" not in res
    flat = [" ".join(c) for c in calls if "pip" in c]
    assert any("-r requirements.txt" in c for c in flat)
    assert any("-e .[dev]" in c for c in flat)


def test_worktree_python_pip_failure_reports_cmd(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    real_fake = _fake_run([])

    def run(cmd: list[str], **kw: Any) -> tuple[int, str, str]:
        if "pip" in cmd:
            return 1, "", "no network"
        return real_fake(cmd, **kw)

    monkeypatch.setattr(worktree, "_run", run)
    res = worktree._install_deps([_py_worktree(tmp_path)], None)[0]
    assert res["status"] == "failed" and "pip install" in res["cmd"]


def test_worktree_setup_python_repo(tmp_db: Path, tmp_path: Path, tmp_targets: Path,
                                    monkeypatch: pytest.MonkeyPatch) -> None:
    src = tmp_path / "pysrc"
    src.mkdir()
    git(src, "init", "-q", "-b", "main")
    (src / "pyproject.toml").write_text('[project]\nname = "x"\nversion = "0.1"\n',
                                        encoding="utf-8")
    (src / "Makefile").write_text("test:\n\tpytest -q\n", encoding="utf-8")
    git(src, "add", "-A")
    git(src, "commit", "-q", "-m", "init")
    bare = tmp_path / "origin" / "py.git"
    bare.parent.mkdir()
    git(tmp_path, "clone", "-q", "--bare", str(src), str(bare))
    bootstrap_project(slug="pyproj", target_repo_url=file_url(bare))

    calls: list[list[str]] = []
    monkeypatch.setattr(worktree, "_run", _fake_run(calls))
    s = worktree.setup("pyproj", install_deps=False, run_guard=False)
    assert not any((w / ".venv").exists() for w in s.worktrees)
    assert not [c for c in calls if "venv" in c]

    s2 = worktree.setup("pyproj", install_deps=True, run_guard=False)
    assert all((w / ".venv" / "bin" / "python").exists() for w in s2.worktrees)
    _, lines, _ = worktree._setup_view(s2)
    assert any(ln.startswith("Python:") for ln in lines)
    assert any("Dev nástroje (pytest) nejsou v pyproject" in ln for ln in lines)
    assert not any("⚠" in ln for ln in lines + worktree._setup_warnings(s2))
