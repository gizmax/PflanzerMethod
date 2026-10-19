"""Pilot 10 (Záložka, Go, production, Full) A — triage pending, podpisy oken, handoff."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from conftest import bootstrap_project, file_url

from tool.cli import builder_decision, checkpoint, retro, status, triage
from tool.cli import handoff as handoff_mod
from tool.cli._compat import signatures_line
from tool.cli.db import transaction

OWNERS = {"byznys": "Lenka Marešová", "produkt": "Marek Svoboda", "design": "AI:ux-expert",
          "vyvoj": "Ondřej Beneš", "bezpecnost": "Hana Kučerová",
          "provoz": "AI:devops-platform-expert"}


def _boot(bare: Path, slug: str = "zalozka", **kw: Any) -> dict[str, Any]:
    kw.setdefault("path_owners", dict(OWNERS))
    kw.setdefault("core", ["Marek Svoboda", "Ondřej Beneš", "Alena Rybová"])
    return bootstrap_project(slug=slug, target_repo_url=file_url(bare), **kw)


def _triage_results(**over: Any) -> list[dict[str, Any]]:
    base = {
        "discovery": {"status": "ok", "signed_by": "Lenka Marešová", "artefact_md": "disc"},
        "security": {"status": "ok", "signed_by": "Hana Kučerová", "artefact_md": "sec"},
        "legal": {"status": "ok", "signed_by": "Hana Kučerová", "artefact_md": "legal"},
        "platform": {"status": "ok", "signed_by": "AI (platform-triage)", "artefact_md": "plat"},
    }
    for k, v in over.items():
        base[k] = {**base[k], **v}
    return [{"track": t, **v} for t, v in base.items()]


def _row(slug: str, track: str) -> tuple[Any, ...]:
    with transaction() as conn:
        return tuple(conn.execute(
            "SELECT t.status, t.signed_by, t.artefact_md FROM triage t JOIN projects p "
            "ON p.id = t.project_id WHERE p.slug = ? AND t.track = ?", (slug, track)).fetchone())


# --- 1: AI-nepodepsaná stopa = pending, vidět ve výstupu i summary -------------------------


def test_ai_unsigned_track_reported_as_pending_and_sandbox_allowed(
        tmp_db: Path, bare_repo: Path) -> None:
    _boot(bare_repo, risk_profile="production")
    out = triage.aggregate("zalozka", _triage_results())
    assert out["tracks"]["platform"] == "pending"
    assert out["overall_status"] == "pending" and out["pending"] == ["platform"]
    assert any("čeká na podpis" in w for w in out["warnings"])
    summary = Path(out["summary_path"]).read_text(encoding="utf-8")
    assert "| platform | pending |" in summary and "Čeká na podpis" in summary
    rec = builder_decision.recommend_for_slug("zalozka")
    builders = [r["builder"] for r in rec["shortlist"]]
    assert "claude-code" in builders
    assert any("čeká na podpis" in n for n in rec["notes"])


# --- 3: production, AI náhrada Provozu ----------------------------------------------------


def test_production_ai_provoz_cannot_be_confirmed_by_code_author(
        tmp_db: Path, bare_repo: Path) -> None:
    _boot(bare_repo, risk_profile="production", ai_signers={"provoz": "Ondřej Beneš"})
    checkpoint.sign("zalozka", "provoz", ai=True, note="AI předkontrola")
    with pytest.raises(ValueError, match="autor kódu"):
        checkpoint.sign("zalozka", "provoz", by="Ondřej Beneš", note="podepisuji")
    row = next(r for r in checkpoint.list_checkpoints("zalozka") if r["window"] == "provoz")
    assert row["designated"] != "Ondřej Beneš"
    assert row["signer"] == "Lenka Marešová"          # Decider, ne vývojář
    out = checkpoint.sign("zalozka", "provoz", by="Lenka Marešová", note="provoz ověřen")
    assert out["status"] == "ok" and out["countersigned_ai_draft"]


def test_guidance_core_provoz_does_not_mention_dpo() -> None:
    txt = checkpoint.guidance_core("provoz", {"byznys": "Lenka"}, "production")
    assert "DPO" not in txt and "provoz" in txt
    assert "DPO" in checkpoint.guidance_core("pravo", {"byznys": "Lenka"}, "production")


def test_pilot_provoz_still_allows_developer(tmp_db: Path, bare_repo: Path) -> None:
    _boot(bare_repo, slug="pilotni", risk_profile="pilot")
    checkpoint.sign("pilotni", "provoz", ai=True, note="AI předkontrola")
    out = checkpoint.sign("pilotni", "provoz", by="Ondřej Beneš", note="ok")
    assert out["status"] == "ok"


# --- 4: poznámky oken se připojují, Právo v podpisech --------------------------------------


def test_window_notes_append_and_legal_signature_listed(tmp_db: Path, bare_repo: Path) -> None:
    _boot(bare_repo, risk_profile="production")
    triage.aggregate("zalozka", _triage_results(
        legal={"status": "deferred", "signed_by": "AI (legal-triage)",
               "artefact_md": "PLNÝ TRIAGE: DPIA"}))
    checkpoint.sign("zalozka", "pravo", by="Hana Kučerová", note="DPIA zkontrolována")
    checkpoint.sign("zalozka", "bezpecnost", by="Hana Kučerová", note="TLS na vstupu")
    legal = _row("zalozka", "legal")
    assert legal[0] == "ok"
    assert "PLNÝ TRIAGE: DPIA" in legal[2] and "DPIA zkontrolována" in legal[2]
    assert "TLS na vstupu" not in legal[2]            # bezpečnostní text nepřepsal Právo
    sec = _row("zalozka", "security")
    assert "TLS na vstupu" in sec[2] and "sec" in sec[2]
    windows = {r["window"]: r for r in checkpoint.checkpoint_summary("zalozka")}
    assert windows["pravo"]["state"] == "ok"
    line = signatures_line("zalozka") or ""
    assert "Právo: Hana Kučerová" in line and "(zástup)" not in line.split("Právo")[1]


def test_resign_same_window_replaces_only_its_block() -> None:
    a = checkpoint.merge_artefact("orig", "bezpecnost", "Bezpečnost & právo", "**A** první")
    b = checkpoint.merge_artefact(a, "pravo", "Právo (DPIA)", "**B** právo")
    c = checkpoint.merge_artefact(b, "bezpecnost", "Bezpečnost & právo", "**A** druhý")
    assert "orig" in c and "**B** právo" in c and "druhý" in c and "první" not in c


# --- 11: Full -> triage, ne rovnou build ---------------------------------------------------


def test_full_tier_next_step_is_triage_until_it_ran(tmp_db: Path, bare_repo: Path) -> None:
    _boot(bare_repo, slug="plny", risk_profile="production", tier="full")
    d = status.project_detail("plny")
    assert d["next_step"] == "/pm triage plny"
    triage.aggregate("plny", _triage_results())
    assert status.project_detail("plny")["next_step"] != "/pm triage plny"


# --- triage drobnosti ----------------------------------------------------------------------


def test_discovery_opt_out_is_logged_and_kickoff_signature_kept(
        tmp_db: Path, bare_repo: Path) -> None:
    _boot(bare_repo, slug="optout", risk_profile="production",
          metric="30 % rezervací", kill_criteria="bez liftu po 4 týdnech")
    before = _row("optout", "discovery")
    out = triage.aggregate("optout", _triage_results(
        discovery={"status": "deferred", "rationale": "opt-out: interní nástroj",
                   "signed_by": "AI (discovery-readiness)"}))
    assert out["opt_out_discovery"] is True
    assert any("opt-out" in w for w in out["warnings"])
    assert _row("optout", "discovery")[0] == before[0] == "ok"


def test_two_dpia_triggers_with_deferred_legal_warn(tmp_db: Path, bare_repo: Path) -> None:
    _boot(bare_repo, slug="dpia", risk_profile="production")
    out = triage.aggregate("dpia", _triage_results(
        legal={"status": "deferred", "artefact_md": "DPIA trigger 1, DPIA trigger 2",
               "dpia_triggers": ["large scale", "citlivý kontext"]}))
    assert any("DPIA" in w for w in out["warnings"])


# --- 10: handoff podle stacku a domény -----------------------------------------------------


def test_stack_commands_go_not_npm(tmp_path: Path) -> None:
    (tmp_path / "go.mod").write_text("module x\n", encoding="utf-8")
    stack, cmds = handoff_mod.stack_commands(str(tmp_path))
    assert stack == "go" and "go test ./..." in cmds and "npm" not in cmds
    (tmp_path / "go.mod").unlink()
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    assert "npm test" in handoff_mod.stack_commands(str(tmp_path))[1]


def _ctx(hook: str, *, legal: str = "") -> dict[str, Any]:
    p = (1, "Záložka", "zalozka", "handoff", hook, hook, "Lenka", None, "minimal", "L3",
         "evolve", None, None, "m", "l", "g", "k", None, None)
    return {"project_tuple": p, "triage": [{"track": "legal", "artefact_md": legal}]}


def test_dora_only_for_financial_domain() -> None:
    lib = handoff_mod.regulation_text(_ctx("Rezervace knih v knihovně"))
    assert "DORA" not in "".join(lib.values())
    fin = handoff_mod.regulation_text(_ctx("Aplikace pro banku: platební příkazy"))
    assert "DORA" in fin["attrib"] and "7 let" in fin["retention"]


def test_pii_regex_catches_library_card_and_birth_number(tmp_db: Path) -> None:
    ctx = _ctx("Čtenář zadá číslo průkazu a rodné číslo, e-mail a telefon")
    ctx.update({"decisions": [], "risk_profile": "production", "path_owners": {}})
    md = handoff_mod.render_compliance(ctx)
    assert "ano, podle zadání" in md
    assert "DORA" not in md


# --- retro: kill kritérium -----------------------------------------------------------------


def test_kill_horizon_parsed_and_reminder_added() -> None:
    assert retro.kill_horizon_days({"kill_criteria": "< 5 % rezervací po 4 týdnech"})[0] == 28
    assert retro.kill_horizon_days({"kill_criteria": "do 30 dnů bez uživatelů"})[0] == 30
    assert retro.kill_horizon_days({"kill_criteria": "nikdo to nepoužívá"}) is None


def test_full_tier_kickoff_points_to_triage(tmp_db: Path, bare_repo: Path) -> None:
    out = bootstrap_project(slug="fullkick", tier="full", target_repo_url=file_url(bare_repo))
    assert out["next_step"] == "/pm triage fullkick"
