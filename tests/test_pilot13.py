"""Pilot 13 (Mlýnek, Express + EJS) — next step po Buildu, podpisy v charteru, prompty druhého kola
po Iterate, decision log do originu, handoff bez TODO, preview, PyYAML, kosmetika."""
from __future__ import annotations

import builtins
import json
import subprocess
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from conftest import set_status

from tool.cli import (
    checkpoint,
    handoff,
    handoff_pr,
    hub,
    init,
    preview,
    quality_gates,
    quick_session,
    session_2,
    status,
)
from tool.cli.db import transaction
from tool.cli.quick_session import record_voting

HOOK = "Rychlejší checkout pro B2B zákazníky"
REPO = Path(__file__).resolve().parents[1]


def _pref(value: float = 0.8) -> dict[str, Any]:
    return {"role_idx": 1, "user_value": value, "effort": 0.4, "risk": 0.2,
            "strategic_fit": 0.7, "commitment_level": 2, "rationale": "nejrychlejší cesta"}


def _add_feedback(slug: str, variant: str, severity: str, text: str) -> None:
    with transaction() as conn:
        vid = conn.execute(
            "SELECT v.id FROM variants v JOIN sessions s ON s.id = v.session_id "
            "JOIN projects p ON p.id = s.project_id WHERE p.slug = ? AND v.name = ? "
            "ORDER BY v.id DESC LIMIT 1", (slug, variant)).fetchone()[0]
        conn.execute(
            "INSERT INTO feedback (variant_id, severity, department, category, score, rationale, "
            "submitted_by) VALUES (?, ?, 'produkt', 'ux', 0.5, ?, 'Lucie')",
            (vid, severity, text))


# --- 1. next step po Buildu ---------------------------------------------------------------------

def test_phase_build_running_points_to_vote_not_session() -> None:
    _phase, nxt = status._phase("triage", "none", 0, 0, build_running=True)
    assert nxt == "pflanzer record --spec .pflanzer/specs/<slug>-vote.json"
    assert "pflanzer session" not in nxt
    src = (REPO / "tool" / "cli" / "status.py").read_text(encoding="utf-8")
    assert "pflanzer session --spec" not in src


def test_checkpoint_after_build_without_vote_gives_same_vote_step(
        worktree_project: dict[str, Any]) -> None:
    slug = worktree_project["slug"]
    assert status.project_detail(slug)["next_step"] == (
        f"pflanzer record --spec .pflanzer/specs/{slug}-vote.json")
    out = checkpoint.sign(slug, "bezpecnost", by="Lucie", note="syntetická data")
    assert out["next_step"] == f"pflanzer record --spec .pflanzer/specs/{slug}-vote.json"


def test_after_vote_without_preview_urls_next_is_preview_up(
        project: dict[str, Any], vote: Callable[..., Any]) -> None:
    slug = project["slug"]
    vote(slug)
    d = status.project_detail(slug)
    assert d["next_step"] == f"pflanzer share --slug {slug}"
    assert "preview" in d["phase"]


def test_after_vote_with_urls_next_is_feedback(project: dict[str, Any]) -> None:
    slug = project["slug"]
    record_voting(
        slug=slug, facilitator="Fanda", decider_call={"shortlist": ["A"], "rationale": "A"},
        real_urls={n: f"https://example.com/{n}" for n in ("A", "B")},
        votes=[{"name": n, "builder": "claude-code", "description": n,
                "role_preferences": [_pref()]} for n in ("A", "B")])
    assert status.project_detail(slug)["next_step"] == f"pflanzer share --slug {slug}"


# --- 2. podpisy v charteru ----------------------------------------------------------------------

def test_signing_windows_rewrites_charter_signoff(project: dict[str, Any]) -> None:
    slug = project["slug"]
    path = Path(project["charter_path"])
    before = path.read_text(encoding="utf-8")
    assert "_PENDING" in before
    checkpoint.sign(slug, "zadani", by="Dana Deciderová", note="zadání ověřeno")
    lines = path.read_text(encoding="utf-8").splitlines()
    decider = next(ln for ln in lines if ln.startswith("- Decider podpis"))
    assert "PENDING" not in decider and "Dana Deciderová" in decider
    sec = next(ln for ln in lines if ln.startswith("- Checkpoint Bezpečnost"))
    assert "PENDING" in sec                      # to ještě nikdo nepodepsal
    checkpoint.sign(slug, "bezpecnost", by="Lucie", note="ok")
    sec = next(ln for ln in path.read_text(encoding="utf-8").splitlines()
               if ln.startswith("- Checkpoint Bezpečnost"))
    assert "PENDING" not in sec and "Lucie" in sec


def test_blocked_checkpoint_does_not_stamp_charter(project: dict[str, Any]) -> None:
    slug = project["slug"]
    checkpoint.sign(slug, "provoz", by="Karel", note="chybí monitoring", blocked=True)
    text = Path(project["charter_path"]).read_text(encoding="utf-8")
    line = next(ln for ln in text.splitlines() if ln.startswith("- Checkpoint Provoz"))
    assert "PENDING" in line


# --- 3. prompty druhého kola --------------------------------------------------------------------

def test_split_iterate_focus() -> None:
    common, goals = status.split_iterate_focus(
        "A: přidat rychlou volbu; B: zjednodušit formulář", ["A", "B"])
    assert common == "" and goals == {"A": "přidat rychlou volbu", "B": "zjednodušit formulář"}
    common, goals = status.split_iterate_focus("zrychli načítání", ["A", "B"])
    assert common == "zrychli načítání" and goals == {}
    common, goals = status.split_iterate_focus(
        "Oba: oprav kontrast. B+C: jednodušší formulář", ["B", "C"])
    assert goals == {"B": "jednodušší formulář", "C": "jednodušší formulář"}


def test_iterate_prompts_each_variant_gets_only_its_own_goal(
        project: dict[str, Any], vote: Callable[..., Any]) -> None:
    slug = project["slug"]
    vote(slug)
    _add_feedback(slug, "B", "critical", "formulář nejde odeslat na mobilu")
    _add_feedback(slug, "A", "high", "chybí potvrzení objednávky")
    session_2.record_decision(
        slug=slug, decision="iterate", rationale="B a A potřebují opravu",
        iterate_variants="A,B",
        iterate_focus="A: přidat potvrzení objednávky; B: opravit odeslání formuláře")
    out = quick_session.builder_prompts(slug, HOOK)
    by = {p["name"]: p["ai_prompt"] for p in out["prompts"]}
    assert set(by) == {"A", "B"}
    assert "Cíl tohoto kola pro A: přidat potvrzení objednávky" in by["A"]
    assert "opravit odeslání formuláře" not in by["A"]
    assert "Cíl tohoto kola pro B: opravit odeslání formuláře" in by["B"]
    assert "potvrzení objednávky" not in by["B"].split("Nálezy k variantě B")[0]
    for name, text in by.items():
        assert f"Uprav existující variantu {name} podle nálezů" in text
        assert f"Postav variantu {name}" not in text
    assert "[Kritické]" in by["B"] and "formulář nejde odeslat na mobilu" in by["B"]
    assert "chybí potvrzení objednávky" not in by["B"]
    assert "A: přidat" not in by["B"] and "B: opravit" not in by["A"]


def test_iterate_common_focus_goes_to_everyone(
        project: dict[str, Any], vote: Callable[..., Any]) -> None:
    slug = project["slug"]
    vote(slug)
    session_2.record_decision(slug=slug, decision="iterate", rationale="x",
                              iterate_variants="A,B", iterate_focus="zrychlit načítání")
    out = quick_session.builder_prompts(slug, HOOK)
    for p in out["prompts"]:
        assert "Cíl tohoto kola: zrychlit načítání" in p["ai_prompt"]
        assert "pro A:" not in p["ai_prompt"] and "pro B:" not in p["ai_prompt"]


# --- 4. decision log do originu ----------------------------------------------------------------

def test_decide_prints_git_commands_and_does_not_commit(
        project: dict[str, Any], vote: Callable[..., Any], tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch) -> None:
    slug = project["slug"]
    vote(slug)
    repo = tmp_path / "target"
    (repo / ".pflanzer").mkdir(parents=True)
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    monkeypatch.chdir(repo)
    out = session_2.record_decision(slug=slug, decision="go", winner="A", rationale="A vede")
    cmds = out["git_commands"]
    assert cmds[0] == f"git add .pflanzer/decisions/{slug}.md"
    assert cmds[1].startswith("git commit -m ") and cmds[2] == "git push -u origin HEAD"
    assert "zatím jen lokálně" in out["hint"]
    log = subprocess.run(["git", "log", "--oneline"], cwd=repo, capture_output=True, text=True)
    assert log.stdout.strip() == ""              # tool nic necommitnul
    text = (repo / ".pflanzer" / "decisions" / f"{slug}.md").read_text(encoding="utf-8")
    line = text.split("**Decider**")[1].splitlines()[0]
    assert time.strftime("%Y-%m-%d") in line or time.strftime(  # lokální datum, ne vždy UTC
        "%Y-%m-%d", time.localtime(time.time() - 60)) in line


def test_ship_pr_block_has_decision_log_step_and_neutral_origin(tmp_path: Path) -> None:
    parts = {"winner_block": {"labels": [], "trailers": [], "work_dir": "~/wt"},
             "pr": {"repos": [], "title": "t", "branch": "pflanzer/x-A"},
             "state": {"blocked_by": [], "threshold_override": False},
             "target_branch": "main"}
    md = handoff_pr._pr_command_md("x", parts)
    assert "git add .pflanzer/decisions/x.md" in md and "git push -u origin HEAD" in md
    assert md.index("decisions/x.md") < md.index("git push -u origin pflanzer/x-A")
    src = (REPO / "tool" / "cli" / "handoff_pr.py").read_text(encoding="utf-8")
    assert "commitnutý při Rozhodnutí" not in src
    # stav větve na originu se čte z lokálních referencí
    wt = tmp_path / "wt"
    wt.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=wt, check=True)
    subprocess.run(["git", "commit", "-q", "--allow-empty", "-m", "i"], cwd=wt, check=True)
    assert "zatím není na originu" in handoff_pr.origin_branch_state(wt, "feat")
    subprocess.run(["git", "update-ref", "refs/remotes/origin/feat", "HEAD"], cwd=wt, check=True)
    assert "referenci" in handoff_pr.origin_branch_state(wt, "feat")
    assert "neověřen" in handoff_pr.origin_branch_state(None, "feat")


# --- 5. handoff bez holých TODO -----------------------------------------------------------------

def test_handoff_be_fe_support_have_no_bare_todo(
        project: dict[str, Any], vote: Callable[..., Any]) -> None:
    slug = project["slug"]
    vote(slug)
    _add_feedback(slug, "A", "critical", "tlačítko Objednat nereaguje na mobilu")
    set_status(slug, "handoff")
    ctx = handoff._fetch_project_context(slug)
    be, fe, sup = handoff.render_be(ctx), handoff.render_fe(ctx), handoff.render_support(ctx)
    for text in (be, fe, sup):
        assert "TODO" not in text
    assert "doplní Petr Frontend" in be + fe or "doplní Backend lead" in be
    assert "tlačítko Objednat nereaguje na mobilu" in sup
    assert "doplní" in sup


def test_handoff_loc_label_matches_ship_metric() -> None:
    txt = handoff._loc_text({"total_loc": 2502, "diff_loc_added": 425})
    assert "2502 řádků celkem" in txt and "+425 přidáno" in txt
    assert "přidáno" not in handoff._loc_text({"total_loc": 10, "diff_loc_added": None})


# --- 6. preview ---------------------------------------------------------------------------------

def test_preview_status_marks_variants_not_in_play(
        project: dict[str, Any], vote: Callable[..., Any],
        capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    slug = project["slug"]
    vote(slug)
    session_2.record_decision(slug=slug, decision="iterate", rationale="x",
                              iterate_variants="B,C", iterate_focus="x")
    state = {"password": "p", "variants": {
        n: {"url": f"http://localhost/{n}", "local_url": "x", "app_port": 1, "proxy_port": 2}
        for n in ("A", "B", "C")}}
    monkeypatch.setattr(preview, "load_state", lambda s: state)
    preview.main(["status", "--slug", slug])
    out = capsys.readouterr().out
    assert "Varianta A" in out and "NENÍ ve hře" in out
    assert f"preview down --slug {slug} --variants A" in out


# --- 7. čas v init a docs -----------------------------------------------------------------------

def test_init_and_docs_agree_on_time() -> None:
    src = (REPO / "tool" / "cli" / "init.py").read_text(encoding="utf-8")
    docs = (REPO / "docs" / "zacni.md").read_text(encoding="utf-8")
    assert "cca 5 minut" in src and "ručně cca 30" in src
    assert "5 min přes Claude Code" in docs and "~30 min" in docs


# --- 8. PyYAML volitelný ------------------------------------------------------------------------

def test_gates_without_pyyaml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__

    def no_yaml(name: str, *a: Any, **kw: Any) -> Any:
        if name == "yaml":
            raise ImportError("no yaml")
        return real_import(name, *a, **kw)

    monkeypatch.setattr(builtins, "__import__", no_yaml)
    monkeypatch.delitem(__import__("sys").modules, "yaml", raising=False)
    (tmp_path / "package.json").write_text('{"name": "x"}', encoding="utf-8")
    res = init.write_gates_template(tmp_path)
    assert res["path"].endswith("pflanzer.gates.json")
    data = quality_gates.load_gates_adapter(Path(res["path"]))
    assert isinstance(data, dict) and data
    yml = tmp_path / "pflanzer.gates.yml"
    yml.write_text("build: {cmd: 'true'}\n", encoding="utf-8")
    with pytest.raises(ValueError) as exc:
        quality_gates.load_gates_adapter(yml)
    msg = str(exc.value)
    assert "PyYAML" in msg and "--format json" in msg and "venv" in msg


def test_install_sh_says_yaml_is_optional() -> None:
    sh = (REPO / "install.sh").read_text(encoding="utf-8")
    assert "PyYAML není potřeba" in sh and "venv" in sh
    assert "se nepodařilo nainstalovat" not in sh


# --- kosmetika ----------------------------------------------------------------------------------

def test_hub_warning_only_when_not_local(caplog: pytest.LogCaptureFixture,
                                         monkeypatch: pytest.MonkeyPatch) -> None:
    import asyncio

    pytest.importorskip("fastapi")
    pytest.importorskip("sqlmodel")
    from tool.web.backend import main as backend

    async def run() -> None:
        async with backend.lifespan(backend.app):
            pass

    monkeypatch.setenv(backend.AUTH_MODE_ENV, "dev")
    monkeypatch.setenv("PFLANZER_HUB_BIND_HOST", "127.0.0.1")
    caplog.clear()
    asyncio.run(run())
    assert "X-User" not in caplog.text
    monkeypatch.setenv("PFLANZER_HUB_BIND_HOST", "0.0.0.0")
    with caplog.at_level("WARNING"):
        asyncio.run(run())
    assert "X-User" in caplog.text


def test_hub_cmd_sets_bind_host_and_full_url_line() -> None:
    src = (REPO / "tool" / "cli" / "hub.py").read_text(encoding="utf-8")
    assert '"PFLANZER_HUB_BIND_HOST": args.host' in src
    assert '"--log-level", "warning"' in src
    assert 'f"Hub: {url}/method/"' in src
    assert hub.LOCAL_HOSTS


def test_local_date_helper() -> None:
    assert status._local_date("2026-10-20 23:30:00") in ("2026-10-20", "2026-10-21")
    assert status._local_date("nesmysl-datum") == "nesmysl-da"
    json.dumps(status._local_date("2026-10-20T10:00:00Z"))
