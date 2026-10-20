"""Pilot 27: trailer AI-Assisted, počet lidí, demo Ship, redirect, share, guide."""
from __future__ import annotations

import json
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Callable

import pytest
from conftest import bootstrap_project, git, worktree_path

from tool.cli import doctor, init, preview, session_3, status, worktree

# --- 1. trailer builder -----------------------------------------------------------------

def _commit(wt: Path, name: str) -> str:
    (wt / name).write_text("x\n", encoding="utf-8")
    git(wt, "add", name)
    git(wt, "commit", "-q", "-m", f"feat: {name}")
    return git(wt, "log", "-1", "--format=%B")


def test_setup_builder_manual_has_no_ai_trailer(project: dict[str, Any], tmp_targets: Path) -> None:
    s = worktree.setup(project["slug"], install_deps=False, run_guard=False, builder="manual")
    wt = worktree_path(tmp_targets, project["slug"], "A")
    assert git(wt, "config", "--worktree", "--get", "pflanzer.builder") == "manual"
    body = _commit(wt, "a.txt")
    assert "Pflanzer-Variant" in body and "AI-Assisted" not in body
    assert any("manual" in n for n in s.builder_notes)


def test_setup_without_builder_says_which_default(project: dict[str, Any],
                                                  tmp_targets: Path) -> None:
    s = worktree.setup(project["slug"], install_deps=False, run_guard=False)
    assert s.builder_notes and "--builder manual" in s.builder_notes[0]
    assert "AI-Assisted: claude-code" in _commit(worktree_path(tmp_targets, project["slug"], "A"),
                                                  "b.txt")
    title, lines, _nxt = worktree._setup_view(s)
    assert any("Builder zatím není zvolen" in ln for ln in lines)


def test_record_with_other_builder_updates_trailer_and_warns(
        project: dict[str, Any], tmp_targets: Path, vote: Callable[..., dict[str, Any]]) -> None:
    slug = project["slug"]
    worktree.setup(project["slug"], install_deps=False, run_guard=False)
    wt = worktree_path(tmp_targets, slug, "A")
    assert "AI-Assisted: claude-code" in _commit(wt, "c.txt")
    out = vote(slug, builder="manual")
    assert git(wt, "config", "--worktree", "--get", "pflanzer.builder") == "manual"
    warn = " ".join(out["warnings"])
    assert "Varianta A" in warn and "jiný trailer" in warn
    assert "AI-Assisted" not in _commit(wt, "d.txt")


# --- 2. počet lidí ------------------------------------------------------------------------

def test_room_size_counts_only_distinct_humans(tmp_db: Path) -> None:
    out = bootstrap_project(
        slug="demo-lide", risk_profile="throwaway", throwaway_rationale="ukázka",
        path_owners={"byznys": "Anna Nováková", "produkt": "anna nováková", "design": "AI",
                     "vyvoj": "Boris Dvořák", "bezpecnost": "AI:security-expert",
                     "provoz": "AI:devops-platform-expert"})
    assert "V týmu je" not in (out["mode_note"] or "")
    assert "6 lidí" not in json.dumps(out, ensure_ascii=False)


# --- 3. demo Ship -------------------------------------------------------------------------

def _winner() -> dict[str, Any]:
    return {"variant": "A", "gates": {"gate_score": 90, "results": []}}


def test_demo_next_step_has_no_checkpoint_and_pr_is_optional() -> None:
    nxt = session_3._next_step(_winner(), True, 0, "demo")
    assert nxt.startswith("Demo hotové")
    assert "Checkpoint provozu" not in nxt and "nový Kickoff s risk profilem pilot" in nxt
    assert "volitelný" in nxt


def test_demo_ship_md_line_does_not_push_gh_pr_create() -> None:
    out = {"ship_path": "~/x/SHIP.md", "pr_command": "pflanzer handoff_pr --slug d | gh pr create",
           "production_ready": False, "production_readiness_target": 0,
           "risk_profile": "throwaway", "triage": {"human_blockers": []},
           "winner": {"local_path": None}}
    _lines, nxt = session_3._ship_md_lines(out, "d", "x")
    assert nxt.startswith("Demo hotové") and "Volitelně" in nxt
    assert not nxt.startswith("Otevři PR")


# --- 4. redirect na / ---------------------------------------------------------------------

class _Redirecting(BaseHTTPRequestHandler):
    page = b""

    def do_GET(self) -> None:  # noqa: N802
        if self.path in ("/", ""):
            self.send_response(302)
            self.send_header("Location", "/krok/1")
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(self.page)

    def log_message(self, *a: Any) -> None:
        pass


def _serve(page: bytes) -> tuple[HTTPServer, int]:
    srv = HTTPServer(("127.0.0.1", 0), type("H", (_Redirecting,), {"page": page}))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]


def _repo_with_route(tmp_path: Path) -> Path:
    def g(*a: str) -> None:
        subprocess.run(["git", *a], cwd=tmp_path, check=True, capture_output=True)
    g("init", "-q", "-b", "main")
    g("config", "user.email", "t@t.cz")
    g("config", "user.name", "T")
    (tmp_path / "server.js").write_text("app.get('/', h);\n")
    g("add", ".")
    g("commit", "-qm", "base")
    g("checkout", "-qb", "feat")
    (tmp_path / "server.js").write_text("app.get('/', h);\napp.get('/objednavka', o);\n")
    g("commit", "-qam", "feat")
    return tmp_path


def test_check_reachable_follows_redirect_from_root(tmp_path: Path) -> None:
    wt = _repo_with_route(tmp_path)
    srv, port = _serve(b"<a href='/objednavka'>Objednat</a>")
    try:
        assert preview.check_reachable("B", wt, port) is None
    finally:
        srv.shutdown()
        srv.server_close()


def test_check_reachable_still_warns_after_redirect(tmp_path: Path) -> None:
    wt = _repo_with_route(tmp_path)
    srv, port = _serve(b"<a href='/menu'>Menu</a>")
    try:
        msg = preview.check_reachable("B", wt, port)
    finally:
        srv.shutdown()
        srv.server_close()
    assert msg and "/objednavka" in msg


# --- 5. share místo preview up, status při sdílení -----------------------------------------

def test_phase_missing_preview_points_to_share() -> None:
    phase, nxt = status._phase("session_1", "none", 0, 0, missing_preview=True)
    assert "pflanzer share" in nxt and "preview up" not in nxt


def test_phase_sharing_running() -> None:
    phase, nxt = status._phase("session_1", "none", 0, 0, sharing=True)
    assert phase == "Sběr feedbacku běží (sdíleno)"
    assert "/pm feedback" in nxt and "share down" in nxt
    assert "čeká se na sdílení" not in phase


def test_sharing_active_uses_state_and_live_pid(monkeypatch: pytest.MonkeyPatch) -> None:
    from tool.cli import share
    monkeypatch.setattr(share, "load_state", lambda slug: {"hub_pid": 4242, "hub_started": "t"})
    monkeypatch.setattr(preview, "_alive", lambda pid, started: pid == 4242)
    assert status._sharing_active("x") is True
    monkeypatch.setattr(preview, "_alive", lambda pid, started: False)
    assert status._sharing_active("x") is False
    monkeypatch.setattr(share, "load_state", lambda slug: None)
    assert status._sharing_active("x") is False


def test_record_warning_recommends_share(project: dict[str, Any],
                                         vote: Callable[..., dict[str, Any]]) -> None:
    out = vote(project["slug"])
    text = " ".join(out["warnings"])
    assert "preview up" not in text and "pflanzer share" in text


# --- 6. INTEGRATION_GUIDE -----------------------------------------------------------------

def _git_repo(path: Path) -> Path:
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=path, check=True, capture_output=True)
    return path


GUIDE = Path("docs") / "INTEGRATION_GUIDE.md"


def test_init_regenerates_untouched_guide_when_stack_appears(tmp_path: Path) -> None:
    repo = _git_repo(tmp_path)
    init.init(repo)
    first = (repo / GUIDE).read_text(encoding="utf-8")
    assert first == init.GENERIC_TEMPLATE_PATH.read_text(encoding="utf-8")
    (repo / "package.json").write_text(json.dumps({"dependencies": {"express": "4"}}))
    out = init.init(repo)
    assert (repo / GUIDE).read_text(encoding="utf-8") == \
        init.NODE_BACKEND_TEMPLATE_PATH.read_text(encoding="utf-8")
    assert any("přegenerováno" in a for a in out["actions"])


def test_init_keeps_edited_guide_and_warns(tmp_path: Path) -> None:
    repo = _git_repo(tmp_path)
    init.init(repo)
    text = (repo / GUIDE).read_text(encoding="utf-8")
    lines = text.splitlines()
    edited = "\n".join([lines[0], "", "Vyplněný návod bez zástupných míst.", ""])
    (repo / GUIDE).write_text(edited, encoding="utf-8")
    (repo / "package.json").write_text(json.dumps({"dependencies": {"express": "4"}}))
    out = init.init(repo)
    assert (repo / GUIDE).read_text(encoding="utf-8") == edited
    assert any(a.startswith("POZOR") for a in out["actions"])


def test_doctor_warns_when_guide_does_not_match_stack(tmp_path: Path) -> None:
    repo = _git_repo(tmp_path)
    init.init(repo)
    (repo / "package.json").write_text(json.dumps({"dependencies": {"express": "4"}}))
    res = doctor.check_guide(repo)
    assert res["status"] == doctor.WARN and "repo je Node backend" in res["detail"]
