"""Pilot 7 (Ledovka, React+Vite SPA), část A: relativní origin, WebSocket přes proxy,
SPA v preview, přípona akceptačních testů, hook z DB, okno právo, shoda skóre."""
from __future__ import annotations

import base64
import json
import socket
import subprocess
import threading
import time
from pathlib import Path
from typing import Any

import pytest
from conftest import bootstrap_project, git

from tool.cli import checkpoint, doctor, init, preview, quick_session, triage, worktree
from tool.cli.db import load_project_toml

# ------------------------------------------------------------------ K1 relativní origin


def _repo_with_relative_origin(tmp_path: Path) -> tuple[Path, Path]:
    bare = tmp_path / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True)
    repo = tmp_path / "app"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "remote", "add", "origin", "../origin.git")
    return repo, bare


def test_init_writes_absolute_origin(tmp_path: Path) -> None:
    repo, bare = _repo_with_relative_origin(tmp_path)
    res = init.init(repo)
    assert res["origin"] == str(bare.resolve())
    toml = (repo / ".pflanzer" / "project.toml").read_text(encoding="utf-8")
    assert f'target_repo_url = "{bare.resolve()}"' in toml
    assert load_project_toml(repo)["target_repo_url"] == str(bare.resolve())


def test_load_project_toml_resolves_relative_url(tmp_path: Path) -> None:
    repo, bare = _repo_with_relative_origin(tmp_path)
    (repo / ".pflanzer").mkdir()
    (repo / ".pflanzer" / "project.toml").write_text(
        '[project]\ntarget_repo_url = "../origin.git"\n', encoding="utf-8")
    assert load_project_toml(repo)["target_repo_url"] == str(bare.resolve())


def test_validate_repo_url_accepts_existing_relative_path(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo, _bare = _repo_with_relative_origin(tmp_path)
    monkeypatch.chdir(repo)
    assert worktree.validate_repo_url("../origin.git")
    assert not worktree.validate_repo_url("../neexistuje.git")


def test_bootstrap_accepts_relative_target_url(
        tmp_db: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo, bare = _repo_with_relative_origin(tmp_path)
    monkeypatch.chdir(repo)
    out = bootstrap_project(target_repo_url="../origin.git")
    assert out["target_repo_url"] == str(bare.resolve())


def test_doctor_fails_on_invalid_origin(tmp_path: Path) -> None:
    repo = tmp_path / "app"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "remote", "add", "origin", "../nikde.git")
    rows, _origin = doctor.check_git(repo)
    assert rows[0]["status"] == doctor.FAIL
    assert "není platná git URL" in rows[0]["detail"] and "set-url" in rows[0]["advice"]


def test_doctor_ok_on_relative_existing_origin(tmp_path: Path) -> None:
    repo, _bare = _repo_with_relative_origin(tmp_path)
    rows, _origin = doctor.check_git(repo)
    assert rows[0]["status"] == doctor.OK


# ------------------------------------------------------------------ D4 git add


def test_doctor_git_add_includes_claude_settings(tmp_path: Path) -> None:
    repo, _bare = _repo_with_relative_origin(tmp_path)
    init.init(repo)
    assert ".claude/settings.json" in doctor._git_add_command(repo)
    steps = " ".join(init.init(repo, force=True)["next_steps"])
    assert ".claude/settings.json" in steps


# ------------------------------------------------------------------ M1 WebSocket přes proxy


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _ws_upstream() -> tuple[socket.socket, int]:
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(5)

    def run() -> None:
        while True:
            try:
                conn, _ = srv.accept()
            except OSError:
                return
            data = b""
            while b"\r\n\r\n" not in data:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                data += chunk
            if b"upgrade: websocket" in data.lower():
                assert b"authorization" not in data.lower()
                conn.sendall(b"HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\n"
                             b"Connection: Upgrade\r\n\r\n")
                while chunk := conn.recv(4096):
                    conn.sendall(b"echo:" + chunk)
            conn.close()

    threading.Thread(target=run, daemon=True).start()
    return srv, int(srv.getsockname()[1])


def test_proxy_tunnels_websocket_upgrade() -> None:
    upstream, app_port = _ws_upstream()
    proxy_port = _free_port()
    threading.Thread(target=preview.serve_proxy,
                     args=("127.0.0.1", proxy_port, app_port, "tajne", "A"), daemon=True).start()
    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", proxy_port), timeout=0.2).close()
            break
        except OSError:
            time.sleep(0.05)
    auth = base64.b64encode(b"pflanzer:tajne").decode()
    req = (f"GET /?token=x HTTP/1.1\r\nHost: 127.0.0.1:{proxy_port}\r\nUpgrade: websocket\r\n"
           f"Connection: Upgrade\r\nSec-WebSocket-Key: abc\r\nSec-WebSocket-Version: 13\r\n"
           f"Authorization: Basic {auth}\r\n\r\n").encode()
    try:
        # bez hesla: 401, žádný tunel
        with socket.create_connection(("127.0.0.1", proxy_port), timeout=5) as c:
            c.sendall(req.replace(auth.encode(), b"eHh4"))
            assert c.recv(4096).startswith(b"HTTP/1.0 401")
        with socket.create_connection(("127.0.0.1", proxy_port), timeout=5) as c:
            c.sendall(req)
            buf = b""
            while b"\r\n\r\n" not in buf:
                buf += c.recv(4096)
            assert buf.startswith(b"HTTP/1.1 101")
            c.sendall(b"ping")
            assert c.recv(4096) == b"echo:ping"
    finally:
        upstream.close()


# ------------------------------------------------------------------ štítek (SPA, bez zdvojení)


def test_label_injected_into_spa_skeleton_with_dedup_script() -> None:
    html = b'<html><body><div id="root"></div><script src="/src/main.tsx"></script></body></html>'
    out = preview.inject_label(html, "B")
    assert out.count(b"data-pflanzer-label") >= 1 and b"Varianta B k rozhodnut" in out
    assert b"MutationObserver" in out          # skryje se, když štítek vykreslí appka sama


def test_label_not_doubled_when_page_has_it() -> None:
    html = "<body><p>Varianta A k rozhodnutí</p></body>".encode()
    assert preview.inject_label(html, "A") == html


# ------------------------------------------------------------------ M2 SPA bez falešného varování


def _spa_repo(tmp_path: Path) -> Path:
    def g(*a: str) -> None:
        subprocess.run(["git", *a], cwd=tmp_path, check=True, capture_output=True)
    g("init", "-q", "-b", "main")
    g("config", "user.email", "t@t.cz")
    g("config", "user.name", "T")
    (tmp_path / "index.html").write_text('<div id="root"></div>')
    (tmp_path / "package.json").write_text(json.dumps(
        {"dependencies": {"react": "18", "react-router-dom": "6"},
         "devDependencies": {"vite": "5"}}))
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "App.tsx").write_text("export const A = 1\n")
    g("add", ".")
    g("commit", "-qm", "base")
    g("checkout", "-qb", "feat")
    (tmp_path / "src" / "Rezervace.tsx").write_text(
        "export const R = () => null\n")
    (tmp_path / "src" / "App.tsx").write_text(
        'export const A = 1\nconst r = [{ path: "/rezervace" }]\n')
    g("add", ".")
    g("commit", "-qm", "feat")
    return tmp_path


def test_spa_detected_and_routes_only_from_router(tmp_path: Path) -> None:
    wt = _spa_repo(tmp_path)
    assert preview.is_spa(wt)
    assert preview._added_routes(wt) == ["/rezervace"]      # Rezervace.tsx není cesta navíc
    assert preview.check_reachable("A", wt, 9) is None      # SPA: kontrola se vynechá


def test_new_tsx_file_is_not_a_route_in_spa(tmp_path: Path) -> None:
    wt = _spa_repo(tmp_path)
    (wt / "src" / "Nove.tsx").write_text("export const N = 1\n")
    subprocess.run(["git", "add", "."], cwd=wt, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-qm", "x"], cwd=wt, check=True, capture_output=True)
    assert "/nove" not in preview._added_routes(wt)
    assert "/nove" in preview._added_routes(wt, spa=False)   # bez SPA by to heuristika uhodla


# ------------------------------------------------------------------ prompt: přípona testů


@pytest.mark.parametrize(("pkg", "ts", "expected"), [
    ({"devDependencies": {"vitest": "1", "typescript": "5"}, "dependencies": {"react": "18"}},
     True, "tests/acceptance/*.test.ts(x)"),
    ({"devDependencies": {"jest": "29", "typescript": "5"}}, True, "tests/acceptance/*.test.ts"),
    ({"devDependencies": {"vitest": "1"}}, False, "tests/acceptance/*.test.js"),
    ({"scripts": {"test": "node --test"}}, False, "tests/acceptance/*.test.js"),
])
def test_node_acceptance_glob(tmp_path: Path, pkg: dict[str, Any], ts: bool, expected: str) -> None:
    (tmp_path / "package.json").write_text(json.dumps(pkg))
    if ts:
        (tmp_path / "tsconfig.json").write_text("{}")
    prof = quick_session.stack_profile(tmp_path)
    assert prof.acceptance_glob == expected
    text = quick_session._builder_rules("s", "hook", "A", True, stack=prof)
    assert expected in text


def test_python_acceptance_glob_unchanged() -> None:
    prof = quick_session.StackProfile(stack="python", commands=["pytest"])
    text = quick_session._builder_rules("s", "h", "A", True, stack=prof)
    assert "tests/acceptance/test_*.py" in text


# ------------------------------------------------------------------ D2 prompts bez --hook


def test_prompts_hook_from_project(project: dict[str, Any]) -> None:
    hook = quick_session._hook_from_project(project["slug"])
    assert hook == "Rychlejší checkout pro B2B zákazníky"
    with pytest.raises(ValueError, match="nenalezen|neexistuje|Projekt"):
        quick_session._hook_from_project("neni-takovy")


def test_prompts_cli_without_hook(project: dict[str, Any], monkeypatch: pytest.MonkeyPatch,
                                  capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(
        "sys.argv", ["quick_session", "prompts", "--slug", project["slug"], "--json"])
    quick_session.main()
    assert "Rychlejší checkout" in capsys.readouterr().out


# ------------------------------------------------------------------ D3 okno právo


def test_pravo_window_refused_when_not_separate(project: dict[str, Any]) -> None:
    slug = project["slug"]
    with pytest.raises(ValueError, match="Právo se podepisuje spolu s bezpečností") as ei:
        checkpoint.sign(slug, "pravo", by="Renata", note="DPIA")
    assert f"checkpoint --slug {slug} bezpecnost" in str(ei.value)


def test_pravo_window_allowed_when_deferred(project: dict[str, Any]) -> None:
    slug = project["slug"]
    base = {"discovery": ("ok", "Petr"), "security": ("ok", "Igor"),
            "legal": ("deferred", "Renata"), "platform": ("ok", "Karel")}
    triage.aggregate(slug, [{"track": t, "status": s, "signed_by": w, "artefact_md": f"# {t}"}
                            for t, (s, w) in base.items()])
    assert checkpoint.sign(slug, "pravo", by="Renata", note="DPIA hotová")["status"]


def test_checkpoint_help_lists_all_windows(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        checkpoint.main(["--help"])
    assert "zadani | bezpecnost | pravo | provoz | design" in capsys.readouterr().out


# ------------------------------------------------------------------ shoda skóre


def test_tie_line() -> None:
    v = [{"name": "A", "preference_score": 0.61}, {"name": "B", "preference_score": 0.40},
         {"name": "C", "preference_score": 0.615}]
    assert quick_session._tie_lines(v) == ["A a C mají stejné skóre — rozhodne diskuse/Decider."]
    assert quick_session._tie_lines(
        [{"name": "A", "preference_score": 0.7}, {"name": "B", "preference_score": 0.4}]) == []
