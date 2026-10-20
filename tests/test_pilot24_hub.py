"""Hub (pilot 24): hlasování v „Moje úloha“, reset formuláře při změně identity,
popisek fáze „Build běží“, okno Zadání mezi okny k podpisu."""
from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("sqlmodel")
pytest.importorskip("httpx")

from sqlmodel import Session  # noqa: E402

from tests.test_pilot22_hub import env  # noqa: E402,F401
from tool.web.backend.audit import write_audit  # noqa: E402
from tool.web.backend.models import Project, Triage  # noqa: E402

SRC = Path(__file__).resolve().parents[1] / "tool" / "web" / "frontend" / "src"


def test_windows_include_zadani_until_signed(env: dict) -> None:  # noqa: F811
    c = env["client"]
    from tests.test_expert_hub import who
    ws = {w["window"]: w for w in c.get(
        "/api/projects/demo/windows", headers=who("x")).json()["windows"]}
    assert ws["zadani"]["label"] == "Zadání"
    assert ws["zadani"]["signer"] == "Tereza Dvořák"
    assert ws["zadani"]["command"].startswith(
        'pflanzer checkpoint --slug demo zadani --by "Tereza Dvořák"')
    with Session(env["engine"]) as s:
        pid = s.exec(__import__("sqlmodel").select(Project)).first().id
        s.add(Triage(project_id=pid, track="discovery", status="ok", artefact_md="x",
                     signed_by="Tereza Dvořák"))
        s.commit()
    ws = {w["window"] for w in c.get(
        "/api/projects/demo/windows", headers=who("x")).json()["windows"]}
    assert "zadani" not in ws


def test_project_detail_reports_build_running(env: dict) -> None:  # noqa: F811
    c = env["client"]
    from tests.test_expert_hub import who
    assert c.get("/api/projects/demo", headers=who("x")).json()["build_running"] is False
    with Session(env["engine"]) as s:
        p = s.exec(__import__("sqlmodel").select(Project)).first()
        write_audit(s, actor="x", action="worktree.setup", target_type="project", target_id=p.id)
        s.commit()
    assert c.get("/api/projects/demo", headers=who("x")).json()["build_running"] is True


def test_phase_label_build_running_source() -> None:
    text = (SRC / "lib" / "text.tsx").read_text(encoding="utf-8")
    assert "Build běží — varianty se ukážou po zápisu Buildu" in text
    assert "buildRunning" in text
    assert "phaseLabel(project.status, !!data.build_running)" in (
        SRC / "pages" / "ProjectPage.tsx").read_text(encoding="utf-8")


def test_vote_card_in_my_task_and_identity_reset_source() -> None:
    page = (SRC / "pages" / "ProjectPage.tsx").read_text(encoding="utf-8")
    assert "<SilentVote compact" in page.split('activeTab === "facilitator"')[0]
    vote = (SRC / "components" / "SilentVote.tsx").read_text(encoding="utf-8")
    assert "Hlasujte: Go / Iterate / Kill" in vote
    assert 'setComment(""); setIter([])' in vote           # reset při změně identity
    fb = (SRC / "pages" / "FeedbackForm.tsx").read_text(encoding="utf-8")
    assert "[variantId, identity?.step, identity?.name]" in fb
