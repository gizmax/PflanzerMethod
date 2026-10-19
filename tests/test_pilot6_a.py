"""Pilot 6 (Pekárna Kvásek), část A: preview s vlajkami, Kickoff vs. Constitution, title,
status přebitého critical, sjednocené texty, worktree/init/help."""
from __future__ import annotations

import subprocess
import threading
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

import pytest
from conftest import bootstrap_project

from tool.cli import apprun, preview, quick_session, session_2, status, worktree
from tool.cli.db import transaction

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "tool" / "templates"


# ------------------------------------------------------------ 1 (a) šablony, (b) env, (c) prompt


@pytest.mark.parametrize("name", ["INTEGRATION_GUIDE.md.template",
                                  "INTEGRATION_GUIDE.python.md.template"])
def test_guide_says_flags_on_in_preview(name: str) -> None:
    text = (TEMPLATES / name).read_text(encoding="utf-8")
    assert "PFLANZER_PREVIEW=1" in text
    assert "FEATURE_FLAGS=all" in text
    assert "dosažitelná odkazem z `/`" in text


@pytest.mark.parametrize("name", ["INTEGRATION_GUIDE.md.template",
                                  "INTEGRATION_GUIDE.python.md.template"])
def test_guide_trailers_have_no_placeholders(name: str) -> None:
    text = (TEMPLATES / name).read_text(encoding="utf-8")
    assert "<AI>" not in text
    assert "Pflanzer-Variant: <slug>-A" in text  # pilot 12: placeholder


def test_start_app_sets_preview_env(tmp_path: Path) -> None:
    out = tmp_path / "env.txt"
    spec = apprun.RunSpec(
        "env", ["sh", "-c", f'echo "$PFLANZER_PREVIEW|$FEATURE_FLAGS|$PORT" > {out}'],
        {"PORT": "4321"}, tmp_path, "test")
    proc = apprun.start_app(spec, tmp_path / "log")
    proc.wait(timeout=10)
    assert out.read_text().strip() == "1|all|4321"


def test_builder_prompt_requires_reachable_feature_and_kickoff_precedence(
        project: dict[str, Any]) -> None:
    rules = quick_session._builder_rules("checkout", "hook", "A", False)
    assert "dosažitelná odkazem z `/`" in rules
    assert "zapnutá v preview" in rules
    assert "přednost zadání z Kickoffu" in rules
    assert "nezastavuj se" in rules


def test_prompts_have_no_irrelevant_ai_or_tv_remarks(project: dict[str, Any]) -> None:
    out = quick_session.builder_prompts(project["slug"], "Rychlejší checkout", 3)
    blob = "\n".join(p["prompt_text"] for p in out["prompts"])
    assert "recent activity" not in blob
    assert "port-forward" not in blob
    assert "watermark" not in blob
    assert "chytrými výchozími hodnotami" in blob


# ------------------------------------------------------------ 1 (d) dosažitelnost na /


class _Home(BaseHTTPRequestHandler):
    body = b"<a href='/menu'>Menu</a>"

    def do_GET(self) -> None:  # noqa: N802
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(self.body)

    def log_message(self, *a: Any) -> None:
        pass


def _serve(body: bytes) -> tuple[HTTPServer, int]:
    handler = type("H", (_Home,), {"body": body})
    srv = HTTPServer(("127.0.0.1", 0), handler)
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


def test_check_reachable_warns_when_new_route_not_linked(tmp_path: Path) -> None:
    wt = _repo_with_route(tmp_path)
    srv, port = _serve(b"<a href='/menu'>Menu</a>")
    try:
        msg = preview.check_reachable("B", wt, port)
    finally:
        srv.shutdown()
    assert msg and "varianta B na / nenabízí nic nového" in msg
    assert "/objednavka" in msg and "za vypnutým přepínačem" in msg


def test_check_reachable_silent_when_linked(tmp_path: Path) -> None:
    wt = _repo_with_route(tmp_path)
    srv, port = _serve(b"<a href='/objednavka'>Objednat</a>")
    try:
        assert preview.check_reachable("A", wt, port) is None
    finally:
        srv.shutdown()


def test_check_reachable_silent_without_git(tmp_path: Path) -> None:
    assert preview.check_reachable("A", tmp_path, 9) is None


# ------------------------------------------------------------ 2 Constitution vs. zadání


def _constitution(tmp_path: Path, text: str) -> Path:
    d = tmp_path / ".pflanzer"
    d.mkdir(exist_ok=True)
    (d / "CONSTITUTION.md").write_text(text, encoding="utf-8")
    return tmp_path


def test_constitution_conflict_warns(tmp_path: Path) -> None:
    _constitution(tmp_path, "# C\n- Aplikace nesmí sbírat osobní údaje (L1).\n")
    w = quick_session.constitution_conflicts(
        "Online objednávka s jménem a telefonem", None, None, cwd=tmp_path)
    assert w and "CONSTITUTION" in w[0] and "commitněte" in w[0]
    assert "telefon" in w[0]


def test_constitution_default_template_no_warning(tmp_path: Path) -> None:
    _constitution(tmp_path, (TEMPLATES / "CONSTITUTION.md.template").read_text(encoding="utf-8"))
    assert quick_session.constitution_conflicts(
        "Online objednávka s telefonem", None, None, cwd=tmp_path) == []


def test_constitution_no_conflict_when_brief_has_no_personal_data(tmp_path: Path) -> None:
    _constitution(tmp_path, "- nesmí sbírat osobní údaje\n")
    assert quick_session.constitution_conflicts("Rychlejší načítání menu", cwd=tmp_path) == []


# ------------------------------------------------------------ 9 title


def test_short_title_from_hook() -> None:
    t = quick_session.short_title(
        "Zákazníci si nemohou objednat chleba předem, proto stojí fronty ráno")
    assert t == "Zákazníci si nemohou objednat chleba předem"
    assert len(quick_session.short_title("A" * 30 + " " + "b" * 40)) <= 50
    assert quick_session.short_title("Online objednávka — rychleji") == "Online objednávka"


def test_bootstrap_uses_title_or_derives(tmp_db: Path, bare_repo: Path) -> None:
    from conftest import file_url
    out = bootstrap_project(slug="t1", target_repo_url=file_url(bare_repo),
                            title="Online objednávka")
    assert out["name"] == "Online objednávka"
    out2 = bootstrap_project(slug="t2", target_repo_url=file_url(bare_repo))
    assert out2["name"] == "Rychlejší checkout pro B2B zákazníky"
    with pytest.raises(ValueError, match="title je moc dlouhý"):
        bootstrap_project(slug="t3", target_repo_url=file_url(bare_repo), title="x" * 51)


# ------------------------------------------------------------ 3 přebité critical na vítězi


def test_override_deadline() -> None:
    assert status._override_deadline("Oprava do 15. 11. po pilotu") == "15. 11."
    assert status._override_deadline("zavřeme do konce týdne") == "konce týdne"
    assert status._override_deadline("jen interní pilot") is None


def test_status_override_on_winner_is_not_loser(project: dict[str, Any],
                                                vote: Callable[..., Any]) -> None:
    slug = project["slug"]
    vote(slug)
    with transaction() as conn:
        vid = conn.execute(
            "SELECT v.id FROM variants v JOIN sessions s ON s.id = v.session_id "
            "JOIN projects p ON p.id = s.project_id WHERE p.slug = ? AND v.name = 'A'",
            (slug,)).fetchone()[0]
        conn.execute(
            "INSERT INTO feedback (variant_id, severity, department, category, score, "
            "rationale, submitted_by) VALUES (?, 'critical', 'security', 'auth', 0.1, "
            "'Chybí kontrola', 'Test')", (vid,))
    session_2.record_decision(slug=slug, decision="go", winner="A", rationale="Jdeme",
                              override_critical="Oprava do 15. 11. po pilotu")
    d = status.project_detail(slug)
    text = " ".join(d["info"])
    assert "Kritické na vítězi A přebil Decider" in text
    assert "dořešte do 15. 11." in text
    assert "poražené" not in text
    assert "Critical na" not in text


# ------------------------------------------------------------ 8 sjednocení Ship / Rozhodnutí


def test_design_confirmation_wording_unified() -> None:
    charter = (ROOT / ".claude" / "commands" / "pflanzer-charter.md").read_text(encoding="utf-8")
    assert "potvrďte před Rozhodnutím; u pilotu Ship neblokuje" in charter
    assert "title" in charter
    from tool.cli.ux import TIPS
    assert any("před Rozhodnutím" in t and "u pilotu Ship neblokuje" in t
               for _, t in TIPS["kickoff"])


# ------------------------------------------------------------ 11 preview URL v jednom řádku


def test_vote_without_urls_one_warning(project: dict[str, Any]) -> None:
    pref = {"role_idx": 1, "user_value": 0.8, "rationale": "rychlé"}
    out = quick_session.record_voting(
        slug=project["slug"], facilitator="Fanda",
        votes=[{"name": n, "builder": "claude-code", "role_preferences": [pref]}
               for n in "ABC"],
        decider_call={"shortlist": ["A"], "rationale": "r"})
    hits = [w for w in out["warnings"] if "preview URL" in w]
    assert len(hits) == 1
    assert "varianty A, B, C zatím nemají preview URL" in hits[0]
    assert "pflanzer preview up" in hits[0]


# ------------------------------------------------------------ 12 worktree / help


def test_git_identity_copied_from_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    src, clone = tmp_path / "src", tmp_path / "clone"
    for d in (src, clone):
        d.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=d, check=True)
    subprocess.run(["git", "config", "user.name", "Pekař"], cwd=src, check=True)
    subprocess.run(["git", "config", "user.email", "p@k.cz"], cwd=src, check=True)
    monkeypatch.chdir(src)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", "/dev/null")
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", "/dev/null")
    assert worktree._ensure_git_identity(clone) == ["user.name", "user.email"]
    out = subprocess.run(["git", "config", "user.name"], cwd=clone, capture_output=True,
                         text=True).stdout.strip()
    assert out == "Pekař"
    assert worktree._ensure_git_identity(clone) == []


def test_setup_summary_mentions_npm_and_no_pair_phrase() -> None:
    s = worktree.WorktreeSetup(
        slug="x", target_repo_url="u", target_branch="main", target_clone_path=Path("/c"),
        worktrees=[Path("/w/A"), Path("/w/B"), Path("/w/C")], package_manager="npm",
        install_results=[], mode="parallel",
        repos=[{"role": "app", "primary": True, "branch": "main", "workspace": None,
                "worktrees": {"A": "/w/A", "B": "/w/B", "C": "/w/C"}, "package_manager": "npm",
                "install_results": [{"path": f"/w/{v}", "status": "ok"} for v in "ABC"],
                "hook": {"status": "installed"}}],
        guard=[], init_missing=[], copied_inputs=[])
    _title, lines, nxt = worktree._setup_view(s)
    blob = "\n".join(lines) + nxt
    assert "npm závislosti nainstalované ve 3 složkách" in blob
    assert "každá dvojice jedna" not in blob


def test_help_lists_all_checkpoint_windows() -> None:
    text = (ROOT / "tool" / "bin" / "pflanzer").read_text(encoding="utf-8")
    assert "zadani|bezpecnost|pravo|provoz|design" in text
