"""Expertní panel (EM + UX): jedna otázka „Jak vážné to je?“ místo čtyř, throwaway bez triage,
pilot bez osobních dat s jedním společným oknem Bezpečnost a provoz, kosmetika Rozhodnutí/Retro.

Jádro metody (ADR-0023: AI připraví, člověk podepisuje) zůstává: production a Full beze změny.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from conftest import bootstrap_project, file_url

from tool.cli import checkpoint, retro, status, tier, triage
from tool.cli.db import transaction

OWNERS = {"byznys": "Dana Deciderová", "produkt": "Petr Produkt", "design": "Eva Design",
          "vyvoj": "Tomáš Vývoj", "bezpecnost": "Jana Bezpečná", "provoz": "Karel Provoz"}


def _row(slug: str, window: str) -> dict:
    return next(r for r in checkpoint.list_checkpoints(slug) if r["window"] == window)


# --- 1. jedna otázka „Jak vážné to je?“ ---------------------------------------------------


@pytest.mark.parametrize("risk,expected", [("throwaway", "quick"), ("pilot", "lean"),
                                           ("production", "lean")])
def test_tier_derived_from_risk_profile(risk: str, expected: str) -> None:
    got, why = tier.derive_tier(risk)
    assert got == expected
    assert "tier" in why and "odvodil" in why           # řekne, že odvodil, a jak přebít


def test_production_with_sensitive_data_is_full() -> None:
    assert tier.derive_tier("production", sensitive=True)[0] == "full"
    assert tier.derive_tier("pilot", sensitive=True)[0] == "lean"
    assert tier.is_sensitive(personal_data=True)
    assert tier.is_sensitive(data_class="L3")
    assert tier.is_sensitive(ai_act_tier="high")
    assert not tier.is_sensitive(data_class="L2", ai_act_tier="limited")


def test_czech_risk_words_accepted() -> None:
    assert tier.normalize_risk_profile("demo") == "throwaway"
    assert tier.normalize_risk_profile("ostre") == "production"
    assert tier.normalize_risk_profile("Ostré") == "production"
    assert tier.normalize_risk_profile("pilot") == "pilot"
    assert tier.normalize_risk_profile("nesmysl") is None


def test_bootstrap_derives_tier_and_says_why(tmp_db: Path, bare_repo: Path) -> None:
    out = bootstrap_project(slug="p1", risk_profile="ostre", target_repo_url=file_url(bare_repo))
    assert out["risk_profile"] == "production" and out["tier"] == "lean"
    assert "odvodil" in out["tier_note"]
    assert out["session_mode"] == "parallel"          # mob jen na výslovné přání
    full = bootstrap_project(slug="p2", risk_profile="production", personal_data=True,
                             target_repo_url=file_url(bare_repo))
    assert full["tier"] == "full"
    assert full["next_step"].startswith("/pm triage")
    demo = bootstrap_project(slug="p3", risk_profile="demo")
    assert demo["risk_profile"] == "throwaway" and demo["tier"] == "quick"


def test_explicit_tier_wins_and_production_quick_is_upgraded(tmp_db: Path,
                                                             bare_repo: Path) -> None:
    out = bootstrap_project(slug="p4", risk_profile="pilot", tier="full",
                            target_repo_url=file_url(bare_repo))
    assert out["tier"] == "full"
    up = bootstrap_project(slug="p5", risk_profile="production", tier="quick",
                           target_repo_url=file_url(bare_repo))
    assert up["tier"] == "lean"
    assert "Ostré nasazení = minimálně Lean" in up["tier_note"]


# --- 2. throwaway bez triage -------------------------------------------------------------


def test_throwaway_has_no_triage_reminders_and_no_windows(tmp_db: Path) -> None:
    out = bootstrap_project(slug="demo", risk_profile="throwaway", path_owners=OWNERS)
    assert "nespouští" in out["defer_note"] and "pilot" in out["defer_note"]
    assert "48 h" not in out["defer_note"]
    windows = {r["window"] for r in checkpoint.list_checkpoints("demo")}
    assert windows == {"zadani"}                       # žádné bezpečnost/provoz/právo
    detail = status.project_detail("demo")
    assert not any(b["kind"] in ("missing_signature", "ai_draft") for b in detail["blockers"])
    # AI pre-check je informativní a zůstane vidět
    checkpoint.sign("demo", "bezpecnost", ai=True, note="AI pre-check")
    assert "bezpecnost" in {r["window"] for r in checkpoint.list_checkpoints("demo")}


def test_throwaway_promotion_to_pilot_needs_full_lean(tmp_db: Path, bare_repo: Path) -> None:
    bootstrap_project(slug="demo2", risk_profile="throwaway", path_owners=OWNERS)
    # nový Kickoff téhož projektu s pilotem = změna risk profilu
    bootstrap_project(slug="demo2", risk_profile="pilot", path_owners=OWNERS,
                      target_repo_url=file_url(bare_repo))
    with transaction() as conn:
        pid = conn.execute("SELECT id FROM projects WHERE slug='demo2'").fetchone()[0]
        notes = [r[0] for r in conn.execute(
            "SELECT artefact_md FROM triage WHERE project_id = ?", (pid,))]
    assert not any("Throwaway demo" in n for n in notes)
    assert _row("demo2", "bezpecnost-provoz")["state"] == "čeká"
    with transaction() as conn:
        assert triage.ship_triage_gate(conn, pid)["gated"] is True


# --- 3. pilot bez osobních dat: jedno okno -------------------------------------------------


def test_pilot_without_personal_data_has_one_window(tmp_db: Path, bare_repo: Path) -> None:
    bootstrap_project(slug="pil", risk_profile="pilot", path_owners=OWNERS,
                      target_repo_url=file_url(bare_repo))
    rows = {r["window"]: r for r in checkpoint.list_checkpoints("pil")}
    assert set(rows) == {"zadani", "bezpecnost-provoz"}
    merged = rows["bezpecnost-provoz"]
    assert merged["label"] == "Bezpečnost a provoz"
    assert merged["owner"] == "Jana Bezpečná"          # vlastník = security owner
    assert merged["minutes"] == 20
    with transaction() as conn:
        pid = conn.execute("SELECT id FROM projects WHERE slug='pil'").fetchone()[0]
        windows = triage.triage_windows(conn, pid)
    assert [w["window"] for w in windows] == ["zadani", "bezpecnost-provoz"]
    assert "bezpecnost-provoz" in triage.checkpoint_command("pil", windows[1])


def test_merged_owner_is_security_owner_else_platform_owner(tmp_db: Path,
                                                            bare_repo: Path) -> None:
    owners = {**OWNERS, "bezpecnost": "AI:security-expert"}
    url = file_url(bare_repo)
    # AI bezpečnost bez určeného podepisujícího -> vlastník je zástupce Provozu
    bootstrap_project(slug="pil2", risk_profile="pilot", path_owners=owners,
                      target_repo_url=url)
    assert _row("pil2", "bezpecnost-provoz")["owner"] == "Karel Provoz"
    # AI bezpečnost s určeným podepisujícím zůstává vlastníkem (podepíše určený člověk)
    bootstrap_project(slug="pil2b", risk_profile="pilot", path_owners=owners,
                      ai_signers={"bezpecnost": "Dana Deciderová"}, target_repo_url=url)
    row = _row("pil2b", "bezpecnost-provoz")
    assert row["designated"] == "Dana Deciderová" and row["ai_signer"] == "Dana Deciderová"


@pytest.mark.parametrize("alias", ["bezpecnost", "provoz", "bezpecnost-provoz"])
def test_old_window_names_sign_the_merged_window(tmp_db: Path, bare_repo: Path,
                                                 alias: str) -> None:
    bootstrap_project(slug="pil3", risk_profile="pilot", path_owners=OWNERS,
                      target_repo_url=file_url(bare_repo))
    out = checkpoint.sign("pil3", alias, by="Jana Bezpečná", note="ověřeno")
    assert out["window"] == "bezpecnost-provoz" and out["status"] == "ok"
    assert set(out["tracks"]) == {"security", "legal", "platform"}
    assert _row("pil3", "bezpecnost-provoz")["state"] == "ok"
    with transaction() as conn:
        pid = conn.execute("SELECT id FROM projects WHERE slug='pil3'").fetchone()[0]
        assert [w["state"] for w in triage.triage_windows(conn, pid)][1] == "ok"
        gate = triage.ship_triage_gate(conn, pid)
        # discovery podepisuje zadání z Kickoffu; po sloučeném okně nezbývá security/legal/platform
        assert not [b for b in gate["raw_blocked_by"] if b != "triage:discovery deferred"]


def test_merged_ai_draft_needs_human(tmp_db: Path, bare_repo: Path) -> None:
    bootstrap_project(slug="pil4", risk_profile="pilot", path_owners=OWNERS,
                      target_repo_url=file_url(bare_repo))
    out = checkpoint.sign("pil4", "provoz", ai=True, note="AI draft")
    assert out["status"] == "pending"
    assert _row("pil4", "bezpecnost-provoz")["state"] == "pending"
    done = checkpoint.sign("pil4", "bezpecnost", by="Jana Bezpečná", note="potvrzeno")
    assert done["countersigned_ai_draft"] and done["status"] == "ok"


def test_pilot_with_personal_data_keeps_separate_windows(tmp_db: Path, bare_repo: Path) -> None:
    bootstrap_project(slug="pd", risk_profile="pilot", path_owners=OWNERS, personal_data=True,
                      target_repo_url=file_url(bare_repo))
    windows = {r["window"] for r in checkpoint.list_checkpoints("pd")}
    assert {"bezpecnost", "provoz"} <= windows and "bezpecnost-provoz" not in windows
    with pytest.raises(ValueError, match="jen pro pilot"):
        checkpoint.sign("pd", "bezpecnost-provoz", by="Jana", note="x")


def test_ai_act_high_and_production_and_full_unchanged(tmp_db: Path, bare_repo: Path) -> None:
    url = file_url(bare_repo)
    bootstrap_project(slug="hi", risk_profile="pilot", path_owners=OWNERS, ai_act_tier="high",
                      target_repo_url=url)
    bootstrap_project(slug="prod", risk_profile="production", path_owners=OWNERS,
                      target_repo_url=url)
    bootstrap_project(slug="fl", risk_profile="pilot", tier="full", path_owners=OWNERS,
                      target_repo_url=url)
    for slug in ("hi", "prod", "fl"):
        windows = {r["window"] for r in checkpoint.list_checkpoints(slug)}
        assert {"bezpecnost", "provoz"} <= windows, slug
        assert "bezpecnost-provoz" not in windows, slug


def test_legacy_split_signatures_stay_split(tmp_db: Path, bare_repo: Path) -> None:
    """Pilot, který už podepsal dílčí okno před sloučením, se zpětně nepřeskládá."""
    bootstrap_project(slug="old", risk_profile="pilot", path_owners=OWNERS, personal_data=True,
                      target_repo_url=file_url(bare_repo))
    checkpoint.sign("old", "bezpecnost", by="Jana Bezpečná", note="ok")
    with transaction() as conn:
        pid = conn.execute("SELECT id FROM projects WHERE slug='old'").fetchone()[0]
        assert not checkpoint.merged_applies(conn, pid)


# --- 4. kosmetika --------------------------------------------------------------------------


def test_retro_reminder_label_matches_recorded_milestone(tmp_db: Path, bare_repo: Path) -> None:
    bootstrap_project(slug="ret", risk_profile="pilot", metric="10 lidí otevře přehled",
                      kill_criteria="méně než 3 lidé po 3 týdnech",
                      target_repo_url=file_url(bare_repo))
    md = retro.render_reminders("ret", "md", "2026-01-01")
    # T+21 se zapisuje do nejbližšího milníku T+30, a připomínka to říká i příkazem
    assert "T+21, zapíše se jako T+30" in md
    assert "--milestone t30" in md


def test_resolve_before_decision_speaks_about_variant(
        project: dict, vote, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    import sys

    from tool.cli import session_2
    slug = project["slug"]
    vote(slug)
    with transaction() as conn:
        vid = conn.execute(
            "SELECT v.id FROM variants v JOIN sessions s ON s.id = v.session_id "
            "JOIN projects p ON p.id = s.project_id WHERE p.slug = ? AND v.name = 'A'",
            (slug,)).fetchone()[0]
        fid = conn.execute(
            "INSERT INTO feedback (variant_id, severity, department, category, score, "
            "rationale, submitted_by) VALUES (?, 'critical', 'security', 'auth', 0.1, "
            "'Chybí kontrola', 'Test')", (vid,)).lastrowid
    monkeypatch.setattr(sys, "argv", ["session_2.py", "resolve", "--slug", slug,
                                      "--feedback-id", str(fid), "--by", "Ondra",
                                      "--note", "opraveno"])
    session_2.main()
    out = capsys.readouterr().out
    assert "Na vítězi (" not in out                   # Rozhodnutí ještě nepadlo (tip v ux.py = C1)
    assert "shortlistu A/B žádný kritický nezbývá" in out
    assert "go --winner A" in out                     # doporučení odpovídá skóre (A vede)


def test_hub_sees_merged_window_through_sqlmodel(tmp_db: Path, bare_repo: Path) -> None:
    """Pilot 21: hub volá CLI pravidlo přes SQLAlchemy spojení bez sqlite3.Row – musí platit."""
    pytest.importorskip("sqlmodel")
    from sqlmodel import Session, create_engine

    from tool.cli.db import DB_PATH
    from tool.web.backend.api import expert
    bootstrap_project(slug="hubmerge", risk_profile="pilot", path_owners=OWNERS,
                      target_repo_url=file_url(bare_repo))
    with transaction() as conn:
        pid = conn.execute("SELECT id FROM projects WHERE slug='hubmerge'").fetchone()[0]
        assert checkpoint.merged_applies(conn, pid)
    with Session(create_engine(f"sqlite:///{DB_PATH}")) as db:
        assert expert._merged_window(db, pid)
