"""retro.py: LOC reuse measurement, readouts, report, ICS reminders (audit N4)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest
from conftest import git

from tool.cli import retro
from tool.cli.db import transaction


@pytest.fixture
def merged_repo(project: dict[str, Any], tmp_path: Path) -> dict[str, Any]:
    """Local target repo: winner branch adds 50 lines, the merge edits 5 of them."""
    slug = project["slug"]
    repo = tmp_path / "target-local"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    (repo / "README.md").write_text("# target\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "chore: base")

    branch = f"pflanzer/{slug}-A"
    git(repo, "checkout", "-q", "-b", branch)
    lines = [f"line {i}" for i in range(50)]
    (repo / "feature.py").write_text("\n".join(lines) + "\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "feat: winner")

    git(repo, "checkout", "-q", "main")
    git(repo, "merge", "-q", "--no-ff", "--no-commit", branch)
    for i in range(5):
        lines[i] = f"line {i} (reviewed)"
    (repo / "feature.py").write_text("\n".join(lines) + "\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "Merge winner with review fixes")
    merge_sha = git(repo, "rev-parse", "HEAD")

    go = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat(timespec="seconds")
    with transaction() as conn:
        conn.execute(
            "INSERT INTO sessions (project_id, type, decision, decision_ts) "
            "VALUES (?, 2, 'go', ?)", (project["project_id"], go),
        )
    return {**project, "repo": repo, "merge_sha": merge_sha}


def test_measure_reuse(merged_repo: dict[str, Any]) -> None:
    out = retro.measure(
        slug=merged_repo["slug"], merge_commit=merged_repo["merge_sha"],
        repo_path=str(merged_repo["repo"]), winner="A", fetch=False,
    )
    assert out["loc_winner"] == 50
    assert out["loc_merged_unchanged"] == 45
    assert out["loc_reused_pct"] == 90.0
    assert out["winner_commits"] == 1
    assert out["targets"]["reuse_ok"] is True
    assert out["days_to_prod"] in (2, 3, 4)  # tz-tolerant
    with transaction() as conn:
        metrics = dict(conn.execute(
            "SELECT metric, value FROM outcomes WHERE milestone = 'ship'"
        ).fetchall())
    assert metrics["loc_reused_pct"] == 90.0

    # Recomputable: a second measure replaces, not duplicates, ship rows.
    retro.measure(slug=merged_repo["slug"], merge_commit=merged_repo["merge_sha"],
                  repo_path=str(merged_repo["repo"]), winner="A", fetch=False)
    with transaction() as conn:
        n = conn.execute(
            "SELECT COUNT(*) FROM outcomes WHERE milestone='ship' AND metric='loc_reused_pct'"
        ).fetchone()[0]
    assert n == 1


def test_record_and_report(merged_repo: dict[str, Any]) -> None:
    slug = merged_repo["slug"]
    retro.measure(slug=slug, merge_commit=merged_repo["merge_sha"],
                  repo_path=str(merged_repo["repo"]), winner="A", fetch=False)
    rec = retro.record(slug=slug, milestone="t7", metric="t7_bugs", value=2,
                       evidence="https://example.invalid/issues?q=label:pflanzer")
    assert rec["outcome_id"] > 0
    with pytest.raises(ValueError):
        retro.record(slug=slug, milestone="t8", metric="t7_bugs", value=1)

    path, data, md = retro.write_report(slug)
    assert path.is_file()
    assert md.startswith("Pflanzer Method | pflanzer.cz/method")
    assert "90 %" in md
    assert "t7_bugs" in md
    assert len(data["rows"]) >= 5


def test_reminders_ics(project: dict[str, Any]) -> None:
    ics = retro.render_reminders(project["slug"], "ics", from_date="2026-09-01")
    assert ics.endswith("\r\n")
    assert "\n" not in ics.replace("\r\n", "")  # CRLF only
    lines = ics.split("\r\n")
    assert lines[0] == "BEGIN:VCALENDAR"
    assert lines[-2] == "END:VCALENDAR"
    assert ics.count("BEGIN:VEVENT") == 4
    assert ics.count("END:VEVENT") == 4
    assert "DTSTART;VALUE=DATE:20260908" in ics   # T+7
    assert "DTSTART;VALUE=DATE:20261130" in ics   # T+90
    assert all(len(line.encode("utf-8")) <= 75 for line in lines)


def test_reminders_need_start_date(project: dict[str, Any]) -> None:
    with pytest.raises(ValueError, match="--from"):
        retro.render_reminders(project["slug"], "md")
