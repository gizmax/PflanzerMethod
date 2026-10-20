"""Pilot 22: Full triage bez Claude Code, AI návrh vs. podpis člověka, okno Právo (DPIA)."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest
from conftest import bootstrap_project, file_url

from tool.cli import checkpoint, triage
from tool.cli.db import transaction

ROOT = Path(__file__).resolve().parents[1]
OWNERS = {"byznys": "Dana Nováková", "produkt": "Petr Novák", "design": "AI",
          "vyvoj": "Tomáš Kos", "bezpecnost": "Jana Svobodová", "provoz": "Karel Dvořák"}


def _full(bare: Path, slug: str = "moje-appka") -> dict[str, Any]:
    return bootstrap_project(slug=slug, target_repo_url=file_url(bare), risk_profile="production",
                             personal_data=True, path_owners=dict(OWNERS),
                             core=["Dana Nováková", "Petr Novák", "Tomáš Kos"])


def _faq_spec() -> dict[str, Any]:
    md = (ROOT / "docs" / "faq.md").read_text(encoding="utf-8")
    sec = md.split("### Triage bez Claude Code", 1)[1]
    block = re.search(r"```json\n(.*?)\n```", sec, re.S)
    assert block, "faq.md musí mít JSON ukázku triage"
    return json.loads(block.group(1))


def _status(slug: str, track: str) -> tuple[str, str]:
    with transaction() as conn:
        r = conn.execute("SELECT t.status, t.signed_by FROM triage t JOIN projects p ON p.id = "
                         "t.project_id WHERE p.slug = ? AND t.track = ?", (slug, track)).fetchone()
    return r[0], r[1]


def test_faq_example_runs_on_full_project(tmp_db: Path, bare_repo: Path,
                                          tmp_path: Path) -> None:
    _full(bare_repo)
    spec = _faq_spec()
    assert [r["track"] for r in spec["results"]] == ["discovery", "security", "legal", "platform"]
    assert spec["results"][1]["conditions"] and spec["results"][2]["conditions"]
    f = tmp_path / "triage.json"
    f.write_text(json.dumps(spec), encoding="utf-8")
    out = triage.run_from_json(f)
    assert out["overall_status"] == "ok"
    assert _status("moje-appka", "security") == ("ok", "Jana Svobodová")
    assert _status("moje-appka", "legal")[0] == "deferred"


def test_spec_json_const_matches_faq_and_zacni_mentions_it() -> None:
    assert _faq_spec() == json.loads(triage.TRIAGE_SPEC_JSON)
    zacni = (ROOT / "docs" / "zacni.md").read_text(encoding="utf-8")
    assert "pflanzer triage --spec triage.json" in zacni
    assert len(zacni.splitlines()) <= 170
    assert "triage.json" in (ROOT / "docs" / "faq.md").read_text(encoding="utf-8")


def test_triage_help_has_schema(capsys: pytest.CaptureFixture[str],
                                monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.argv", ["pflanzer triage", "--help"])
    with pytest.raises(SystemExit):
        triage.main()
    out = capsys.readouterr().out
    for word in ("results", "discovery", "security", "legal", "platform", "artefact_md",
                 "signed_by", "rationale", "conditions", "ok | blocked | deferred"):
        assert word in out


def test_ai_does_not_overwrite_human_signature(tmp_db: Path, bare_repo: Path) -> None:
    _full(bare_repo)
    triage.aggregate("moje-appka", _faq_spec()["results"])
    assert _status("moje-appka", "security") == ("ok", "Jana Svobodová")
    with pytest.raises(ValueError) as e:
        checkpoint.sign("moje-appka", "bezpecnost", ai=True, note="AI pre-check")
    msg = str(e.value)
    assert "už podepsal Jana Svobodová" in msg and "AI návrh se nezapíše" in msg
    assert "--by" in msg
    assert _status("moje-appka", "security") == ("ok", "Jana Svobodová")


def test_ai_still_works_on_unsigned_window(tmp_db: Path, bare_repo: Path) -> None:
    _full(bare_repo)
    out = checkpoint.sign("moje-appka", "provoz", ai=True, note="AI pre-check")
    assert out["ai_draft"] is True


def test_pravo_error_explains_when_separate_window_exists(tmp_db: Path, bare_repo: Path) -> None:
    _full(bare_repo)
    spec = _faq_spec()
    for r in spec["results"]:
        if r["track"] == "legal":
            r["status"] = "ok"
    triage.aggregate("moje-appka", spec["results"])
    with pytest.raises(ValueError) as e:
        checkpoint.sign("moje-appka", "pravo", by="Marie", note="DPIA")
    msg = str(e.value)
    assert "Samostatné okno Právo (DPIA) vzniká jen když" in msg
    assert "bezpecnost --by" in msg


def test_deferred_dpia_condition_reaches_pravo_window_and_summary(
        tmp_db: Path, bare_repo: Path) -> None:
    _full(bare_repo)
    triage.aggregate("moje-appka", _faq_spec()["results"])
    rows = {r["window"]: r for r in checkpoint.list_checkpoints("moje-appka")}
    assert rows["pravo"]["state"] != "ok"
    out = checkpoint.sign("moje-appka", "pravo", by="Marie Dvořáková", note="DPIA hotová")
    assert any("DPIA" in c["text"] for c in out["triage_conditions"])
    cond_texts = [c["text"] for c in checkpoint.signature_conditions("moje-appka")]
    assert any("DPIA hotová před Shipem" in t for t in cond_texts)
