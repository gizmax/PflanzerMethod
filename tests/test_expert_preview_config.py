"""Preview config: fallback na hlavní repo, Flask autodetekce, alias `--tunnel off`."""
from __future__ import annotations

import subprocess
from pathlib import Path

from tool.cli import apprun, preview

GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false"]


def _git(cwd: Path, *a: str) -> None:
    subprocess.run([*GIT, *a], cwd=cwd, check=True, capture_output=True)


def _toml(root: Path, url: str, preview_cmd: str | None) -> None:
    d = root / ".pflanzer"
    d.mkdir(exist_ok=True)
    body = f'[project]\ntarget_repo_url = "{url}"\n'
    if preview_cmd:
        body += f'\n[preview]\ncommand = "{preview_cmd}"\n'
    (d / "project.toml").write_text(body, encoding="utf-8")


def _setup(tmp_path: Path, main_cmd: str | None, clone_cmd: str | None):
    origin = tmp_path / "origin.git"
    subprocess.run(["git", "init", "--bare", "-b", "main", str(origin)], check=True,
                   capture_output=True)
    seed = tmp_path / "seed"
    seed.mkdir()
    _git(seed, "init", "-b", "main")
    _toml(seed, str(origin), clone_cmd)
    _git(seed, "add", "-A")
    _git(seed, "commit", "-m", "init")
    _git(seed, "remote", "add", "origin", str(origin))
    _git(seed, "push", "origin", "main")
    wt = tmp_path / "wt"
    subprocess.run(["git", "clone", str(origin), str(wt)], check=True, capture_output=True)
    main = tmp_path / "main"
    subprocess.run(["git", "clone", str(origin), str(main)], check=True, capture_output=True)
    _toml(main, str(origin), main_cmd)
    return main, wt


def test_worktree_without_preview_uses_main_repo(tmp_path, monkeypatch):
    main, wt = _setup(tmp_path, "python app.py {port}", None)
    monkeypatch.chdir(main)
    assert apprun.read_preview_config(wt)["command"] == "python app.py {port}"
    spec = apprun.detect_run(wt, 5555)
    assert spec and spec.command == "python app.py 5555"


def test_untouched_worktree_copy_loses_to_main(tmp_path, monkeypatch):
    main, wt = _setup(tmp_path, "new {port}", "old {port}")
    monkeypatch.chdir(main)
    assert apprun.read_preview_config(wt)["command"] == "new {port}"


def test_changed_worktree_overrides_main(tmp_path, monkeypatch):
    main, wt = _setup(tmp_path, "main {port}", "old {port}")
    _toml(wt, str(tmp_path / "origin.git"), "mine {port}")
    monkeypatch.chdir(main)
    assert apprun.read_preview_config(wt)["command"] == "mine {port}"


def test_unrelated_cwd_repo_is_ignored(tmp_path, monkeypatch):
    _main, wt = _setup(tmp_path, "main {port}", None)
    other = tmp_path / "other"
    other.mkdir()
    _git(other, "init", "-b", "main")
    _toml(other, "/nekde/jinde.git", "cizi {port}")
    monkeypatch.chdir(other)
    assert apprun.read_preview_config(wt) == {}


def test_flask_autodetect(tmp_path):
    (tmp_path / "requirements.txt").write_text("Flask==3.0\n", encoding="utf-8")
    (tmp_path / "app.py").write_text("from flask import Flask\napp = Flask(__name__)\n",
                                     encoding="utf-8")
    spec = apprun.detect_run(tmp_path, 5600)
    assert spec and spec.argv[1:4] == ["-m", "flask", "--app"]
    assert spec.argv[4:6] == ["app", "run"] and "5600" in spec.argv
    assert "flask" in spec.source


def test_tunnel_off_is_alias_for_none(monkeypatch):
    seen = {}

    def fake_up(slug, **kw):
        seen.update(kw)
        raise ValueError("stop")

    monkeypatch.setattr(preview, "up", fake_up)
    try:
        preview.main(["up", "--slug", "x", "--tunnel", "off"])
    except SystemExit:
        pass
    assert seen.get("tunnel") == "none"
