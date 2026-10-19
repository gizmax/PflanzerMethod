"""Nálezy z pilotu „Pojišťovna Kotva" (stupeň Full): triage od AI, stav po blokaci, atribuce."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tool.cli import init, status, triage
from tool.cli.db import transaction


def _track(slug: str, track: str) -> tuple[str, str]:
    with transaction() as conn:
        row = conn.execute(
            "SELECT t.status, t.signed_by FROM triage t JOIN projects p ON p.id = t.project_id "
            "WHERE p.slug = ? AND t.track = ?", (slug, track)).fetchone()
    return row[0], row[1]


def _results(**over: Any) -> list[dict[str, Any]]:
    base = {"discovery": ("ok", "Petr"), "security": ("ok", "Igor"),
            "legal": ("deferred", "Renata"), "platform": ("ok", "Karel")}
    base.update(over)
    return [{"track": t, "status": s, "signed_by": who, "artefact_md": f"# {t}"}
            for t, (s, who) in base.items()]


def test_ai_suggested_ok_is_pending_not_signed(project: dict[str, Any]) -> None:
    slug = project["slug"]
    proposed = ("ok", "PENDING — Karel; navrhl platform-triage agent")
    triage.aggregate(slug, _results(platform=proposed))
    assert _track(slug, "platform")[0] == "pending"
    assert _track(slug, "security")[0] == "ok"          # podepsal člověk


def test_blocked_triage_status_says_what_to_unblock(project: dict[str, Any]) -> None:
    slug = project["slug"]
    triage.aggregate(slug, _results(discovery=("blocked", "Petr")))
    d = status.project_detail(slug)
    assert "triage blokuje: discovery" in d["phase"]
    assert f"/pm triage {slug}" in d["next_step"]


def test_init_disables_ai_coauthor(tmp_path: Path) -> None:
    repo = tmp_path / "r"
    repo.mkdir()
    from conftest import git
    git(repo, "init", "-q", "-b", "main")
    git(repo, "remote", "add", "origin", "https://github.com/acme/r.git")
    init.init(repo)
    cfg = json.loads((repo / ".claude" / "settings.json").read_text(encoding="utf-8"))
    assert cfg["includeCoAuthoredBy"] is False
    assert ".claude/settings.json" in init.git_add_command(repo)


def test_security_sign_keeps_deferred_dpia_and_pravo_window(project: dict[str, Any]) -> None:
    from tool.cli import checkpoint

    slug = project["slug"]
    triage.aggregate(slug, _results())                  # legal deferred (Renata, DPIA)
    out = checkpoint.sign(slug, "bezpecnost", by="Igor", note="SMS ověření")
    assert out["tracks"] == ["security"]
    assert _track(slug, "legal")[0] == "deferred"       # DPIA se nepřepsala
    with transaction() as conn:
        pid = conn.execute("SELECT id FROM projects WHERE slug = ?", (slug,)).fetchone()[0]
        wins = {w["window"]: w for w in triage.triage_windows(conn, pid)}
    assert wins["pravo"]["owner"] == "Renata"
    res = checkpoint.sign(slug, "pravo", by="Renata", note="DPIA hotová")
    assert res["signed_by_role"] == "zástupce"
    assert _track(slug, "legal")[0] == "ok"


def test_python_feature_without_tests_is_unverified(tmp_path: Path) -> None:
    from tool.cli import quality_gates

    repo = tmp_path / "py"
    (repo / "tests" / "acceptance").mkdir(parents=True)
    (repo / "pyproject.toml").write_text('[project]\nname = "x"\n', encoding="utf-8")
    (repo / "tests" / "acceptance" / "x.feature").write_text("Požadavek: x\n", encoding="utf-8")
    ctx, _, _ = quality_gates._make_ctx(repo)
    res = quality_gates.gate_acceptance(ctx)
    assert "NEOVĚŘENO" in res.details and "akceptační testy" in res.details
