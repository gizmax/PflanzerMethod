"""Pilot 17 (Kladivo, production, Full, FastAPI): podpis vs. stav okna, podmínky z triage."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
from conftest import bootstrap_project, file_url

from tool.cli import charter, checkpoint, feedback, handoff, quick_session, status, triage, worktree
from tool.cli._compat import conditions_checklist
from tool.cli.db import transaction
from tool.cli.ux import async_days

OWNERS = {"byznys": "Karel Dvořák", "produkt": "Petra Nováková", "design": "Lucie Svobodová",
          "vyvoj": "Martin Kos", "bezpecnost": "Ondřej Beneš", "provoz": "Radek Černý"}

SEC_MD = """# Security Triage
Data class L3 (jméno, telefon, číslo OP).

## Podmínky
- [K1] AES-256-GCM, envelope encryption
- [K2] logy bez OP (test s canary hodnotou)
- [K3] mazání včetně záloh

Požadavky: K4 TLS a rate limit; K5 sandbox jen syntetická data
"""
LEGAL_MD = """# Legal Triage
Status: deferred do dokončení DPIA.
- [D1] číslo OP online nesbírat, na pobočce jen příznak ověřeno
- [D2] DPIA včetně LIA
RoPA (návrh): základ 6/1/b (jméno, telefon); retence vrácení + 30 dní.
"""


def _boot(bare: Path, slug: str = "kladivo", **kw: Any) -> dict[str, Any]:
    kw.setdefault("path_owners", dict(OWNERS))
    kw.setdefault("core", ["Petra Nováková", "Martin Kos", "Lucie Svobodová"])
    kw.setdefault("risk_profile", "production")
    kw.setdefault("tier", "full")
    return bootstrap_project(slug=slug, target_repo_url=file_url(bare), **kw)


def _results(**over: Any) -> list[dict[str, Any]]:
    base: dict[str, dict[str, Any]] = {
        "discovery": {"status": "deferred", "signed_by": "Karel Dvořák",
                      "rationale": "opt-out: persony známe z 10 let telefonních rezervací",
                      "artefact_md": "disc", "conditions": [
                          {"id": "C1", "text": "persona do 30 dní"}]},
        "security": {"status": "pending", "signed_by": "AI security-triage",
                     "artefact_md": SEC_MD},
        "legal": {"status": "deferred",
                  "signed_by": "NOT SIGNED — navržený signer Ondřej Beneš",
                  "artefact_md": LEGAL_MD},
        "platform": {"status": "pending", "signed_by": "AI platform-triage",
                     "artefact_md": "plat", "production_blockers": [
                         "rollback do 10 minut", {"id": "PROD-B2", "text": "alert na chybovost"}]},
    }
    for k, v in over.items():
        base[k] = {**base[k], **v}
    return [{"track": t, **v} for t, v in base.items()]


def _states(slug: str) -> dict[str, dict[str, Any]]:
    return {r["window"]: r for r in checkpoint.list_checkpoints(slug)}


# --- 1: stav okna podle vlastních tracků ---------------------------------------------------


def test_security_signed_legal_deferred_shows_waiting_for_law(
        tmp_db: Path, bare_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _boot(bare_repo)
    triage.aggregate("kladivo", _results())
    checkpoint.sign("kladivo", "bezpecnost", by="Ondřej Beneš", note="data syntetická")
    rows = _states("kladivo")
    assert rows["bezpecnost"]["state"] == "ok"
    text = rows["bezpecnost"]["state_text"]
    assert text.startswith("Bezpečnost podepsána (Ondřej Beneš, ")
    assert "čeká Právo (DPIA) — Ondřej Beneš" in text
    assert rows["pravo"]["state"] == "čeká" and rows["pravo"]["designated"] == "Ondřej Beneš"
    checkpoint.main(["--slug", "kladivo", "--list"])
    out = capsys.readouterr().out
    assert "Bezpečnost podepsána" in out
    assert 'bezpecnost --by' not in out.split("Další krok")[1]
    # status ukazuje totéž
    detail = status.project_detail("kladivo")
    assert "Bezpečnost podepsána" in "\n".join(status.detail_lines(detail))


def test_pravo_signature_closes_the_window_text(tmp_db: Path, bare_repo: Path) -> None:
    _boot(bare_repo)
    triage.aggregate("kladivo", _results())
    checkpoint.sign("kladivo", "bezpecnost", by="Ondřej Beneš", note="ok")
    checkpoint.sign("kladivo", "pravo", by="Ondřej Beneš", note="DPIA hotová")
    rows = _states("kladivo")
    assert rows["bezpecnost"]["state_text"] == "podepsáno"
    assert rows["pravo"]["state"] == "ok"


def test_resign_merges_conditions_and_reports_it(
        tmp_db: Path, bare_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _boot(bare_repo, tier="lean")
    first = checkpoint.sign("kladivo", "bezpecnost", by="Lucie", note="OK",
                            conditions="CSRF; rate limit")
    assert first["resigned"] is False
    second = checkpoint.sign("kladivo", "bezpecnost", by="Lucie", note="doplněno",
                             conditions="rate limit; DPA")
    assert second["resigned"] is True and second["added_conditions"] == ["DPA"]
    assert second["conditions"] == ["CSRF", "rate limit", "DPA"]
    again = checkpoint.sign("kladivo", "bezpecnost", by="Lucie", note="znovu")
    assert again["conditions"] == ["CSRF", "rate limit", "DPA"]
    texts = [c["text"] for c in checkpoint.signature_conditions("kladivo")]
    assert texts == ["CSRF", "rate limit", "DPA"]
    with transaction() as conn:
        art = conn.execute("SELECT artefact_md FROM triage t JOIN projects p ON p.id = "
                           "t.project_id WHERE p.slug = 'kladivo' AND t.track = 'security'"
                           ).fetchone()[0]
    assert "- CSRF" in art and "- DPA" in art
    checkpoint.main(["--slug", "kladivo", "bezpecnost", "--by", "Lucie", "--note", "x",
                     "--conditions", "audit log"])
    assert "Okno už bylo podepsané; doplněné podmínky: audit log" in capsys.readouterr().out


# --- 2: podmínky z triage ------------------------------------------------------------------


def test_extract_conditions_structured_markdown_and_prose() -> None:
    sec = triage.extract_conditions({"track": "security", "status": "deferred",
                                     "artefact_md": SEC_MD})
    assert [c["id"] for c in sec] == ["K1", "K2", "K3", "K4", "K5"]
    assert sec[3]["text"] == "TLS a rate limit"
    plat = triage.extract_conditions({
        "track": "platform", "status": "ok", "artefact_md": "- [x] hotovo\n- [ ] nic",
        "production_blockers": ["rollback", {"id": "PROD-B2", "text": "alert"}]})
    assert [(c["id"], c["text"]) for c in plat] == [("P1", "rollback"), ("PROD-B2", "alert")]
    assert triage.extract_conditions({"track": "legal", "status": "ok",
                                      "artefact_md": "žádné"}) == []


def test_conditions_stored_taken_by_signature_and_waived(
        tmp_db: Path, bare_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _boot(bare_repo)
    out = triage.aggregate("kladivo", _results())
    assert out["conditions"]["security"][0]["id"] == "K1"
    assert "## Podmínky a blokace z triage" in Path(out["summary_path"]).read_text("utf-8")
    assert any("podmínek/blokací" in w for w in out["warnings"])
    open_now = [c["state"] for c in checkpoint.signature_conditions("kladivo")]
    assert set(open_now) == {"open"}
    assert "z triage, zatím nepotvrzeno" in conditions_checklist("kladivo")[0]

    with pytest.raises(ValueError, match="--rationale"):
        checkpoint.sign("kladivo", "bezpecnost", by="Ondřej Beneš", note="ok", waive="K3")
    with pytest.raises(ValueError, match="není"):
        checkpoint.sign("kladivo", "bezpecnost", by="Ondřej Beneš", note="ok", waive="K99",
                        rationale="x")
    res = checkpoint.sign("kladivo", "bezpecnost", by="Ondřej Beneš", note="ok",
                          waive="K3", rationale="mazání zálohy řeší infra tým")
    assert [c["id"] for c in res["triage_conditions"]] == ["K1", "K2", "K4", "K5"]
    assert [w["id"] for w in res["waived_conditions"]] == ["K3"]
    # právo je odložené a odděleně: jeho podmínky zůstávají otevřené
    by_state: dict[str, list[str]] = {}
    for c in checkpoint.signature_conditions("kladivo"):
        by_state.setdefault(c["state"], []).append(c["text"])
    assert any(t.startswith("[K1]") for t in by_state["taken"])
    assert any(t.startswith("[D1]") for t in by_state["open"])
    assert any(t.startswith("[PROD-B2]") for t in by_state["open"])
    lines = conditions_checklist("kladivo")
    assert any(ln.startswith("- [x] [K3]") and "odpuštěno: mazání zálohy" in ln for ln in lines)
    assert any(ln.startswith("- [ ] [K1]") and "Bezpečnost" in ln for ln in lines)
    # DPO podpis práva převezme D1–D2
    checkpoint.sign("kladivo", "pravo", by="Ondřej Beneš", note="DPIA hotová")
    st = {c["text"].split("]")[0] + "]": c["state"]
          for c in checkpoint.signature_conditions("kladivo")}
    assert st["[D1]"] == "taken" and st["[PROD-B2]"] == "open"
    # CLI řádek
    checkpoint.main(["--slug", "kladivo", "provoz", "--by", "Radek Černý", "--note", "rollback ok"])
    assert "Podmínky z triage převzaté podpisem (2)" in capsys.readouterr().out


def test_retriage_replaces_conditions_of_track(tmp_db: Path, bare_repo: Path) -> None:
    _boot(bare_repo)
    triage.aggregate("kladivo", _results())
    triage.aggregate("kladivo", _results(security={"artefact_md": "- [K1] jen jedna"}))
    with transaction() as conn:
        pid = conn.execute("SELECT id FROM projects WHERE slug='kladivo'").fetchone()[0]
        sec = [c for c in triage.triage_conditions(conn, pid) if c["track"] == "security"]
    assert [c["id"] for c in sec] == ["K1"]


def test_checklist_and_compliance_show_triage_conditions(
        tmp_db: Path, bare_repo: Path) -> None:
    _boot(bare_repo)
    triage.aggregate("kladivo", _results())
    checkpoint.sign("kladivo", "bezpecnost", by="Ondřej Beneš", note="ok")
    lines = conditions_checklist("kladivo")
    assert any("[K2] logy bez OP" in ln for ln in lines)
    p = (1, "Kladivo", "kladivo", "handoff", "h", "Karel", "Karel", None, "minimal", "L3",
         "evolve", None, None, "m", "l", "g", "k", None, None)
    comp = handoff.render_compliance({
        "project_tuple": p, "triage": [], "decisions": [], "risk_profile": "production",
        "path_owners": {}})
    assert "- [ ] [K1] AES-256-GCM" in comp
    assert "z triage, zatím nepotvrzeno" in comp


# --- 3: omezení z triage v promptech a ve statusu ------------------------------------------


def test_prompts_and_status_carry_triage_constraints(
        tmp_db: Path, bare_repo: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    _boot(bare_repo)
    assert status.project_detail("kladivo")["info"] == [] or not any(
        "Triage změnila zadání" in i for i in status.project_detail("kladivo")["info"])
    triage.aggregate("kladivo", _results())
    info = " ".join(status.project_detail("kladivo")["info"])
    assert "Triage změnila zadání: security K1–K5, legal D1–D2" in info
    assert "prompty to už obsahují" in info and "Charteru" in info
    out = quick_session.builder_prompts("kladivo", "Online rezervace")
    assert not out.get("blocked")
    assert any("[D1] číslo OP online nesbírat" in c for c in out["triage_constraints"])
    for p in out["prompts"]:
        assert "Omezení z triage" in p["ai_prompt"]
        assert "číslo OP online nesbírat" in p["ai_prompt"]
        assert "[C1]" not in p["ai_prompt"]       # discovery se do Buildu nepřenáší
    # odpuštěná podmínka z promptu zmizí
    checkpoint.sign("kladivo", "pravo", by="Ondřej Beneš", note="ok", waive="D1",
                    rationale="DPO připustil pole nepovinné")
    out2 = quick_session.builder_prompts("kladivo", "Online rezervace")
    assert not any("[D1]" in c for c in out2["triage_constraints"])


# --- 4: jedno okno Asyncu podle stupně -----------------------------------------------------


def test_async_days_follow_tier(tmp_db: Path, bare_repo: Path) -> None:
    _boot(bare_repo, slug="plny", tier="full")
    _boot(bare_repo, slug="stredni", tier="lean")
    assert async_days("plny") == "5–7 dní"
    assert async_days("stredni") == "3–5 dní"
    assert "5–7 dní" in "\n".join(status.detail_lines(status.project_detail("plny")))


# --- 5: testovací klient FastAPI/Starlette --------------------------------------------------


def test_worktree_setup_reports_missing_starlette_testclient(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    wt = tmp_path / "wt"
    wt.mkdir()
    (wt / "pyproject.toml").write_text(
        '[project]\nname = "x"\nversion = "0"\ndependencies = ["fastapi", "uvicorn"]\n',
        encoding="utf-8")
    calls: list[list[str]] = []

    def fake_run(cmd: list[str], cwd: Path | None = None, timeout: int = 300,
                 env: dict[str, str] | None = None) -> tuple[int, str, str]:
        calls.append(cmd)
        if cmd[-2:] == ["-c", "import starlette.testclient"]:
            return 1, "", "RuntimeError: starlette.testclient requires the httpx2 package"
        return 0, "", ""

    monkeypatch.setattr(worktree, "_run", fake_run)
    monkeypatch.setattr(worktree, "_exclude_locally", lambda *a, **k: None)
    res = worktree._install_python(wt)
    assert res["testclient_missing"] == "httpx2"
    assert any(c[-1] == "httpx2" and "install" in c for c in calls)
    assert "httpx2" in worktree._testclient_hint("httpx2")


# --- 6: opt-out z Discovery a validace specu ------------------------------------------------


@pytest.mark.parametrize("over,needle", [
    ({"status": "ok"}, "nezapisuje jako `ok`"),
    ({"rationale": "opt-out:"}, "chybí důvod"),
    ({"discovery_debt_score": 42}, "0–10"),
    ({"status": "hotovo"}, "neexistuje"),
])
def test_triage_spec_validation_is_czech_with_example(
        tmp_db: Path, bare_repo: Path, over: dict[str, Any], needle: str) -> None:
    _boot(bare_repo)
    with pytest.raises(ValueError) as exc:
        triage.aggregate("kladivo", _results(discovery=over))
    assert needle in str(exc.value)
    if "opt-out" in needle or "důvod" in needle:
        assert "Příklad" in str(exc.value) and '"track": "discovery"' in str(exc.value)


def test_unknown_or_duplicate_track_rejected(tmp_db: Path, bare_repo: Path) -> None:
    _boot(bare_repo)
    bad = _results() + [{"track": "ux", "status": "ok"}]
    with pytest.raises(ValueError, match="neznámý track"):
        triage.aggregate("kladivo", bad)
    dup = _results() + [{"track": "legal", "status": "ok"}]
    with pytest.raises(ValueError, match="víckrát"):
        triage.aggregate("kladivo", dup)


def test_valid_opt_out_passes_and_warns_when_not_signed_by_human(
        tmp_db: Path, bare_repo: Path) -> None:
    _boot(bare_repo)
    out = triage.aggregate("kladivo", _results(discovery={"signed_by": "AI (discovery-readiness)"}))
    assert out["opt_out_discovery"] is True
    assert any("nepotvrdil jmenovitě člověk" in w for w in out["warnings"])


# --- 7: compliance a Charter -----------------------------------------------------------------


def test_compliance_filled_from_legal_and_author_from_db(tmp_db: Path, bare_repo: Path) -> None:
    _boot(bare_repo)
    triage.aggregate("kladivo", _results())
    checkpoint.sign("kladivo", "bezpecnost", by="Ondřej Beneš", note="ok")
    checkpoint.sign("kladivo", "pravo", by="Ondřej Beneš",
                    note="DPIA hotová; OP jen s čl. 6/1/b, retence 30 dní")
    with transaction() as conn:
        conn.execute("UPDATE decisions SET atribuce_user = 'unknown' WHERE type = 'charter'")
        proj = conn.execute("SELECT * FROM projects WHERE slug = 'kladivo'").fetchone()
        decisions = [dict(r) for r in conn.execute(
            "SELECT type, atribuce_user, atribuce_ts FROM decisions").fetchall()]
        tri = [dict(r) for r in conn.execute(
            "SELECT track, artefact_md FROM triage WHERE project_id = ?", (proj["id"],))]
    p = (proj["id"], proj["name"], "kladivo", "handoff", "h", "Zákazníci si rezervují nářadí",
         "Karel Dvořák", None, "limited", "L3", "evolve", None, None, "m", "l", "g", "k",
         None, None)
    comp = handoff.render_compliance({
        "project_tuple": p, "triage": tri, "decisions": decisions,
        "risk_profile": "production", "path_owners": dict(OWNERS)})
    assert "by unknown" not in comp
    assert "**charter** by Karel Dvořák (Decider, Kickoff)" in comp
    assert "- Právní základ: čl. 6/1/b GDPR (podle podpisu okna Právo: Ondřej Beneš)" in comp
    assert "doplnit (z Legal triage)" not in comp
    assert "jméno, telefon, číslo OP (L3, ze Security triage)" in comp
    assert "zákazníci" in comp.split("Subjekty údajů:")[1].split("\n")[0]
    assert re.search(r"Retence: retence 30 dní", comp)
    assert "- [x] DPIA dokončeno — podepsáno oknem Právo (Ondřej Beneš)" in comp


def _charter(**kw: Any) -> charter.CharterInput:
    base: dict[str, Any] = dict(
        slug="c17", name="C17", xyz_hypothesis="X", decider_name="Dana",
        decider_mandate_from="CPO", cpo_escalation_contact="CPO", sponsor_name="Dana",
        primary_lagging_metric="m", leading_metric="l", guardrail_metric="g",
        kill_criteria="k", capacity_profile="regulated", capacity_person_days=10,
        ai_act_tier="limited", data_class="L3", reinforcement_t7="a", reinforcement_t30="b",
        reinforcement_t60="c", reinforcement_t90="d", reinforcement_budget_pd=1.0)
    base.update(kw)
    return charter.CharterInput(**base)


def test_charter_threshold_follows_risk_profile_and_sponsor_line() -> None:
    prod = charter.render_charter_md(_charter())
    assert "quality gates ≥ 85/100" in prod and "≥ 80/100" not in prod
    assert "Sponsor podpis" not in prod and "PENDING_\n- Sponsor" not in prod
    assert "Sponsor: bez samostatného sponzora" in prod
    pilot = charter.render_charter_md(_charter(capacity_profile="default",
                                               sponsor_name="Soňa Sponzorová"))
    assert "quality gates ≥ 80/100" in pilot
    assert "Sponsor: Soňa Sponzorová" in pilot and "Sponsor podpis: _PENDING_" in pilot
    thr = charter.render_charter_md(_charter(
        capacity_profile="default", throwaway_or_evolve="throwaway",
        throwaway_rationale="discovery-only pilot (XYZ falsification, no production intent)",
        sponsor_name="—"))
    assert "≥ 80/100" not in thr and "bez samostatného sponzora" in thr


# --- kosmetika ---------------------------------------------------------------------------------


def test_feedback_counts_split_open_and_resolved() -> None:
    rows = [{"severity": "critical", "resolved_at": "2026-10-20"},
            {"severity": "critical", "resolved_at": None},
            {"severity": "high", "resolved_at": None}]
    assert feedback._counts(rows[:1]) == "Kritické vyřešené 1"
    assert feedback._counts(rows) == "Kritické otevřené 1, vyřešené 1, Důležité 1"
    assert feedback._counts([rows[2]]) == "Důležité 1"


def test_feedback_pull_example_uses_variant_in_play(tmp_db: Path, bare_repo: Path) -> None:
    from tool.cli import feedback_pull
    _boot(bare_repo, slug="hra", tier="lean")
    assert feedback_pull.variant_in_play("hra", {"focus_variants": ["C"]}) == "C"
    assert feedback_pull.variant_in_play("hra", {}) == "A"
