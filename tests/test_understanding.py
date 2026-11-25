"""ADR-0025 (reviewer z Kickoffu, velikost PR) a ADR-0027 (věty proč, vysvětlení zpět)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from conftest import bootstrap_project

from tool.cli import handoff_pr, quick_session, understanding
from tool.cli.db import transaction


def _stored_reviewer(slug: str) -> str | None:
    with transaction() as conn:
        row = conn.execute("SELECT reviewer FROM projects WHERE slug = ?", (slug,)).fetchone()
    return row[0]


def _kickoff(slug: str, **kw: Any) -> dict[str, Any]:
    return bootstrap_project(slug=slug, risk_profile="throwaway", **kw)


# --- ADR-0025 bod 1: reviewer v Kickoffu ---------------------------------------------------


def test_reviewer_is_stored_and_shown(tmp_db: Path) -> None:
    out = _kickoff("rev", reviewer="  Jana   Nová ")
    assert out["reviewer"] == "Jana Nová"
    assert _stored_reviewer("rev") == "Jana Nová"
    assert out["reviewer_note"] is None
    quick_session._render_bootstrap(out, False, {})  # nesmí spadnout


def test_missing_reviewer_gives_advisory_not_error(tmp_db: Path, tmp_path: Path) -> None:
    out = bootstrap_project(slug="norev", risk_profile="pilot",
                            target_repo_url=f"file://{tmp_path}/origin/x.git")
    assert out["reviewer"] is None
    assert "Reviewer vítěze zatím nemá jméno" in out["reviewer_note"]
    assert "reviewer" in out["reviewer_note"]


def test_missing_reviewer_is_silent_for_throwaway(tmp_db: Path) -> None:
    out = _kickoff("demo")
    assert out["reviewer_note"] is None


def test_spec_field_reviewer_is_accepted(tmp_db: Path) -> None:
    out = quick_session._bootstrap_from_spec({
        "hook": "Rychlejší schvalování žádostí", "decider_name": "Dana",
        "risk_profile": "throwaway", "slug": "spec-rev", "reviewer": "@jana-nova"})
    assert out["reviewer"] == "@jana-nova"


def _pr_parts(**over: Any) -> dict[str, Any]:
    parts: dict[str, Any] = {
        "winner_block": {"labels": ["pflanzer"], "trailers": ["Pflanzer-Session: ship"],
                         "work_dir": "~/wt"},
        "pr": {"title": "feat: x", "branch": "pflanzer/x-A", "repos": []},
        "state": {"blocked_by": [], "threshold_override": None},
        "target_branch": "main", "branch_owner": "owner-gh", "reviewer": None, "w": None,
    }
    parts.update(over)
    return parts


def test_pr_command_prefers_kickoff_reviewer_over_branch_owner(tmp_db: Path) -> None:
    _kickoff("pr1")
    md = handoff_pr._pr_command_md("pr1", _pr_parts(reviewer="@jana-nova"))
    assert "--reviewer jana-nova" in md
    assert "owner-gh" not in md
    assert "Reviewer z Kickoffu: `jana-nova`" in md


def test_pr_command_falls_back_to_branch_owner(tmp_db: Path) -> None:
    _kickoff("pr2")
    md = handoff_pr._pr_command_md("pr2", _pr_parts())
    assert "--reviewer owner-gh" in md
    assert "branch owner" in md


def test_kickoff_reviewer_without_handle_is_named_not_inserted(tmp_db: Path) -> None:
    _kickoff("pr3")
    md = handoff_pr._pr_command_md("pr3", _pr_parts(reviewer="Jana Nová"))
    assert "Reviewer z Kickoffu: Jana Nová" in md
    assert "--reviewer owner-gh" not in md
    assert "--reviewer Jana" not in md


# --- ADR-0025 bod 3: velikost PR jako rada -------------------------------------------------


def test_size_advice_only_above_advisory_constant() -> None:
    assert handoff_pr.ADVISORY_PR_LINES == 400
    assert handoff_pr.pr_size_advice(None, None) is None
    assert handoff_pr.pr_size_advice(300, 100) is None          # přesně na hranici
    text = handoff_pr.pr_size_advice(350, 51)
    assert text and "rozřezat PR" in text and "Ship ani skóre to neovlivní" in text
    assert handoff_pr.pr_size_advice(900, None) is not None


# --- ADR-0027 bod 3: věty „proč“ -----------------------------------------------------------


def test_why_add_list_and_render(tmp_db: Path) -> None:
    _kickoff("why1")
    empty = understanding.render_why_md("why1")
    assert "## Proč je to navržené takhle" in empty
    assert "nikdo nezapsal" in empty
    assert 'pflanzer why add --slug why1 --what "…" --why "…"' in empty

    understanding.add_why("why1", "Nová závislost zod", "Validace je jinak ručně a chybová.",
                          by="Petr")
    items = understanding.list_why("why1")
    assert [i["what"] for i in items] == ["Nová závislost zod"]
    md = understanding.render_why_md("why1")
    assert "**Nová závislost zod**: Validace je jinak ručně a chybová. (Petr)" in md
    assert "nikdo nezapsal" not in md


def test_why_requires_text_and_project(tmp_db: Path) -> None:
    _kickoff("why2")
    with pytest.raises(ValueError, match="--why"):
        understanding.add_why("why2", "něco", "   ")
    with pytest.raises(ValueError, match="neexistuje"):
        understanding.add_why("nope", "něco", "protože")


# --- ADR-0027 body 1, 2, 5: vysvětlení zpět ------------------------------------------------


def test_explain_back_missing_is_open_risk(tmp_db: Path) -> None:
    _kickoff("eb0")
    md = understanding.render_understanding_md("eb0")
    assert "## Otevřená rizika" in md
    assert "nikdo mimo autory neprošel" in md
    assert "Ship neblokuje" in md


def test_explain_back_record_and_render(tmp_db: Path) -> None:
    _kickoff("eb1")
    out = understanding.record_explain_back(
        "eb1", by="Marie Reviewerová", change="změnila text chyby validace", minutes=25,
        note="našla překlep v testu")
    assert out["minutes"] == 25
    md = understanding.render_understanding_md("eb1")
    assert "## Vysvětlení vítěze zpět" in md
    assert "Marie Reviewerová" in md and "změnila text chyby validace" in md
    assert "25 min" in md and "našla překlep v testu" in md
    assert "Otevřená rizika" not in md


def test_explain_back_rejects_keyboard_author(tmp_db: Path) -> None:
    out = bootstrap_project(
        slug="eb2", risk_profile="throwaway",
        path_owners={"byznys": "Dana", "produkt": "AI", "design": "AI", "vyvoj": "Tomáš Novák",
                     "bezpecnost": "AI", "provoz": "AI"})
    assert out["path_owners"]["vyvoj"] == "Tomáš Novák"
    with pytest.raises(ValueError, match="neseděl"):
        understanding.record_explain_back("eb2", by="  tomáš  novák", change="x", minutes=10)
    assert understanding.list_explain_back("eb2") == []
    ok = understanding.record_explain_back("eb2", by="Marie", change="x", minutes=10)
    assert ok["by"] == "Marie"


def test_explain_back_validates_minutes(tmp_db: Path) -> None:
    _kickoff("eb3")
    with pytest.raises(ValueError, match="minut"):
        understanding.record_explain_back("eb3", by="Marie", change="x", minutes=0)


def test_explain_back_writes_decision_log_in_target_repo(
        tmp_db: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _kickoff("eb4")
    repo = tmp_path / "target"
    (repo / ".pflanzer").mkdir(parents=True)
    monkeypatch.chdir(repo)
    out = understanding.record_explain_back("eb4", by="Marie", change="změna validace", minutes=20)
    log = repo / ".pflanzer" / "decisions" / "eb4.md"
    assert out["decision_log"] and log.is_file()
    body = log.read_text(encoding="utf-8")
    assert "Vysvětlení vítěze zpět" in body and "Marie" in body and "20 min" in body


def test_cli_json_roundtrip(tmp_db: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _kickoff("cli1")
    understanding.main(["why", "add", "--slug", "cli1", "--what", "model", "--why", "protože",
                        "--json"])
    capsys.readouterr()
    understanding.main(["why", "list", "--slug", "cli1", "--json"])
    assert json.loads(capsys.readouterr().out)[0]["what"] == "model"
    understanding.main(["explain-back", "record", "--slug", "cli1", "--by", "Marie",
                        "--change", "úprava", "--minutes", "15", "--json"])
    capsys.readouterr()
    understanding.main(["explain-back", "show", "--slug", "cli1", "--json"])
    assert json.loads(capsys.readouterr().out)[0]["minutes"] == 15


def test_cli_rejects_author_with_czech_message(
        tmp_db: Path, capsys: pytest.CaptureFixture[str]) -> None:
    bootstrap_project(
        slug="cli2", risk_profile="throwaway",
        path_owners={"byznys": "Dana", "produkt": "AI", "design": "AI", "vyvoj": "Tomáš",
                     "bezpecnost": "AI", "provoz": "AI"})
    with pytest.raises(SystemExit) as exc:
        understanding.main(["explain-back", "record", "--slug", "cli2", "--by", "Tomáš",
                            "--change", "x", "--minutes", "5"])
    assert exc.value.code == 2
    assert "neseděl" in capsys.readouterr().err


def test_list_unknown_project_is_czech_error(tmp_db: Path) -> None:
    with pytest.raises(ValueError, match="neexistuje"):
        understanding.list_why("nope")
    with pytest.raises(ValueError, match="neexistuje"):
        understanding.list_explain_back("nope")
