"""Pilot 15 (Ponk, Quick + mob + throwaway), část B: discovery audit podle stupně, práh Shipu
u throwaway, lehký handoff a retro dema, doctor, status (vote spec), kosmetika."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
from conftest import bootstrap_project

from tool.cli import doctor, feedback_pull, handoff, handoff_pr, retro, session_3, status, ux
from tool.cli.db import transaction

REPO = Path(__file__).resolve().parents[1]


# --- 2. discovery audit respektuje stupeň a risk profil -----


def test_discovery_policy_by_tier_and_risk() -> None:
    assert feedback_pull.discovery_policy("quick", "pilot") == "info"
    assert feedback_pull.discovery_policy("lean", "throwaway") == "info"
    assert feedback_pull.discovery_policy("lean", "pilot") == "lean"
    assert feedback_pull.discovery_policy("full", "production") == "full"


def test_feedback_aggregate_reports_policy_for_throwaway(tmp_db: Path) -> None:
    bootstrap_project(slug="ponk", risk_profile="throwaway")
    agg = feedback_pull.aggregate("ponk")
    assert agg["risk_profile"] == "throwaway"
    assert agg["discovery_policy"] == "info"


def test_detector_agent_documents_policy() -> None:
    md = (REPO / ".claude" / "agents" / "discovery-debt-detector.md").read_text(encoding="utf-8")
    assert "discovery_policy" in md
    assert "u dema se discovery nevyžaduje" in md
    assert "Quick" in md and "throwaway" in md


# --- 3. práh Shipu u throwaway v docs -----


@pytest.mark.parametrize("doc", ["docs/zacni.md", "docs/postup.md"])
def test_docs_state_throwaway_ship_threshold(doc: str) -> None:
    text = (REPO / doc).read_text(encoding="utf-8")
    assert re.search(r"throwaway:\s+skóre informativně,\s+Ship neblokuje", text)


# --- 4. hlavička Shipu u throwaway -----


def _ship_out(**over: Any) -> dict[str, Any]:
    out = {
        "slug": "ponk", "risk_profile": "throwaway", "production_readiness_target": 0,
        "production_ready": False, "informational": False, "threshold_override": None,
        "decided_winner": "mob", "warnings": [], "report_nice_path": "~/x/ship.md",
        "triage": {"human_blockers": [], "windows": []},
        "winner": {"variant": "mob", "gate_score": 100, "summary_line": "build ok",
                   "failures": [], "next_step": "PR"},
    }
    out.update(over)
    return out


def test_ship_header_throwaway_not_unconfirmable() -> None:
    title, lines, _w, _n, _c = session_3._human_ship(_ship_out(), "ponk")
    assert "Throwaway" in title and "informativní" in title and "Ship neblokuje" in title
    assert "nelze potvrdit" not in title
    assert not any("nelze potvrdit" in x for x in lines)


def test_ship_header_pilot_unchanged() -> None:
    out = _ship_out(risk_profile="pilot", production_readiness_target=80)
    out["winner"]["gate_score"] = 90
    title, *_ = session_3._human_ship(out, "ponk")
    assert "nelze potvrdit" in title


def test_ship_next_step_throwaway_says_informative() -> None:
    winner = {"gates": {"gate_score": 100}}
    txt = session_3._next_step(winner, True, 0, "ponk")
    assert txt.startswith("Throwaway: skóre 100/100 je informativní, Ship neblokuje")


# --- 6b. throwaway handoff a retro -----


def _ctx(**over: Any) -> dict[str, Any]:
    p = (1, "Ponk", "ponk", "handoff", "", "Lidi chtějí rychlý přehled", "Jana", "Petr", "minimal",
         "internal", "throwaway", "standard", 5, "10 lidí otevře přehled do 14 dní", "lead",
         "guard", "méně než 3 lidi do 14 dní")
    ctx = {"project_tuple": p, "project": {"throwaway_rationale": "demo pro vedení"},
           "winner": "mob", "extracted_by_variant": {}}
    ctx.update(over)
    return ctx


def test_demo_readme_has_show_run_fake() -> None:
    md = handoff.render_demo_readme(_ctx())
    for head in ("## Co ukázat", "## Jak spustit", "## Co je fake"):
        assert head in md
    assert "demo pro vedení" in md
    assert "10 lidí otevře přehled do 14 dní" in md


def test_ship_measure_throwaway_has_no_loc_survival() -> None:
    pr = {"target": 0, "metrics": ["10 lidí otevře přehled", None, None], "kill": "méně než 3"}
    md = handoff_pr._measure_md("ponk", pr)
    assert "T+7/30/60/90" not in md and "retro measure" not in md
    assert "10 lidí otevře přehled" in md and "méně než 3" in md
    pr["target"] = 80
    assert "retro measure" in handoff_pr._measure_md("ponk", pr)


def test_throwaway_retro_has_single_reminder(tmp_db: Path) -> None:
    bootstrap_project(slug="ponk", risk_profile="throwaway")
    md = retro.render_reminders("ponk", "md", "2026-01-01")
    assert md.count("- [ ]") == 1
    assert "T+60" not in md and "T+90" not in md
    assert re.search(r"\*\*[^*]+\*\* — 2026-\d\d-\d\d", md)


def test_pilot_retro_keeps_four_milestones(tmp_db: Path) -> None:
    bootstrap_project(slug="pil", risk_profile="pilot", target_repo_url="https://github.com/o/r")
    md = retro.render_reminders("pil", "md", "2026-01-01")
    for label in ("T+7", "T+30", "T+60", "T+90"):
        assert label in md


def test_throwaway_report_is_light(tmp_db: Path) -> None:
    bootstrap_project(slug="ponk", risk_profile="throwaway")
    with transaction() as conn:
        conn.execute("UPDATE projects SET status = 'handoff' WHERE slug = 'ponk'")
    data = retro.build_report("ponk")
    assert data["throwaway"] is True
    md = retro.render_report_md("ponk", data)
    assert "throwaway" in md and "loc_reused_pct" not in md


# --- 10. doctor -----


def _row(check: str, st: str) -> dict[str, str]:
    return {"check": check, "status": st, "detail": "x", "advice": "oprav", "impact": ""}


def test_doctor_throwaway_softens_guide_ci_lockfile() -> None:
    rows = [_row("INTEGRATION_GUIDE.md", doctor.FAIL), _row("CI konfigurace", doctor.WARN),
            _row("Package manager / lockfile", doctor.WARN), _row("Test skript", doctor.FAIL)]
    out = {r["check"]: r for r in doctor.soften_for_throwaway(rows)}
    assert out["INTEGRATION_GUIDE.md"]["status"] == doctor.WARN
    assert "jen doporučení" in out["INTEGRATION_GUIDE.md"]["advice"]
    assert out["CI konfigurace"]["status"] == doctor.OK
    assert out["Package manager / lockfile"]["status"] == doctor.OK
    assert out["Test skript"]["status"] == doctor.FAIL        # ostatní blokace zůstávají


def test_doctor_resolves_risk_from_project_toml(tmp_path: Path) -> None:
    (tmp_path / ".pflanzer").mkdir()
    (tmp_path / ".pflanzer" / "project.toml").write_text(
        'default_risk_profile = "throwaway"\n', encoding="utf-8")
    assert doctor.resolve_risk_profile(tmp_path) == "throwaway"
    assert doctor.resolve_risk_profile(tmp_path / "nikde") is None


def test_doctor_guide_template_blocks_pilot_not_throwaway(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "INTEGRATION_GUIDE.md").write_text(
        doctor.GUIDE_TEMPLATE.read_text(encoding="utf-8"), encoding="utf-8")
    row = doctor.check_guide(tmp_path)
    assert row["status"] == doctor.FAIL
    soft = doctor.soften_for_throwaway([row])[0]
    assert soft["status"] == doctor.WARN


# --- 11. status: vote spec -----


def test_status_vote_hint_inline_when_template_missing(tmp_path: Path,
                                                       monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    hint = status._vote_spec_hint("neexistuje-xyz")
    assert "předvyplněná šablona" not in hint
    assert '"votes"' in hint and "neexistuje-xyz" in hint


def test_status_vote_hint_mentions_existing_template(tmp_path: Path,
                                                     monkeypatch: pytest.MonkeyPatch) -> None:
    specs = tmp_path / ".pflanzer" / "specs"
    specs.mkdir(parents=True)
    (specs / "ponk-vote.json").write_text("{}", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    hint = status._vote_spec_hint("ponk")
    assert "předvyplněná šablona v .pflanzer/specs/ponk-vote.json" in hint


# --- kosmetika -----


def test_mob_skips_thank_the_losers_tip() -> None:
    assert any("Poraženým" in t for t in ux.tips_for("after_go", {}, limit=5))
    assert not any("Poraženým" in t for t in ux.tips_for("after_go", {"mob": True}, limit=5))


def test_install_sh_path_hint_gives_exact_commands() -> None:
    text = (REPO / "install.sh").read_text(encoding="utf-8")
    assert ">> ~/.zshrc" in text and ">> ~/.bashrc" in text
    assert 'export PATH=\\"\\$HOME/.local/bin:\\$PATH\\"' in text
