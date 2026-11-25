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
    assert "reuse_ok" not in out["targets"]  # ADR-0028: no target for LOC survival
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
    assert "bez cíle" in md and "FLAG" not in md  # LOC survival has no target
    assert "t7_bugs" in md
    assert len(data["rows"]) >= 5


def test_reminders_ics(project: dict[str, Any]) -> None:
    ics = retro.render_reminders(project["slug"], "ics", from_date="2026-09-01")
    assert ics.endswith("\r\n")
    assert "\n" not in ics.replace("\r\n", "")  # CRLF only
    lines = ics.split("\r\n")
    assert lines[0] == "BEGIN:VCALENDAR"
    assert lines[-2] == "END:VCALENDAR"
    assert ics.count("BEGIN:VEVENT") == 5  # T+7/30/60/90 + kill kritérium z Kickoffu
    assert ics.count("END:VEVENT") == 5
    assert "DTSTART;VALUE=DATE:20260908" in ics   # T+7
    assert "DTSTART;VALUE=DATE:20261130" in ics   # T+90
    assert all(len(line.encode("utf-8")) <= 75 for line in lines)


def test_reminders_need_start_date(project: dict[str, Any]) -> None:
    with pytest.raises(ValueError, match="--from"):
        retro.render_reminders(project["slug"], "md")


# --------------------------------------------------------------------------
# ADR-0028 / ADR-0025: baseline, review segments, instability
# --------------------------------------------------------------------------


def _prs(n: int, *, with_review: bool = True) -> list[dict[str, Any]]:
    """n PRs merged in the last weeks: open->merge 10 h + i, open->first review 2 h."""
    now = datetime.now(timezone.utc)
    out = []
    for i in range(n):
        opened = now - timedelta(days=10 + i)
        pr: dict[str, Any] = {
            "number": i, "createdAt": opened.isoformat(),
            "mergedAt": (opened + timedelta(hours=10 + i)).isoformat(), "reviews": [],
        }
        if with_review:
            pr["reviews"] = [{"submittedAt": (opened + timedelta(hours=2)).isoformat()}]
        out.append(pr)
    return out


def _local_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "plain-repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    return repo


def _ship(slug_id: int) -> dict[str, tuple[float | None, str | None]]:
    with transaction() as conn:
        return {r[0]: (r[1], r[2]) for r in conn.execute(
            "SELECT metric, value, notes FROM outcomes WHERE project_id = ? "
            "AND milestone = 'ship' ORDER BY id", (slug_id,)).fetchall()}


def test_baseline_median(project: dict[str, Any], tmp_path: Path,
                         monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(retro, "_gh_pr_list", lambda repo: _prs(11))
    out = retro.baseline(slug=project["slug"], repo_path=str(_local_repo(tmp_path)))
    assert out["stored"] is True and out["after_go"] is False
    rows = _ship(project["project_id"])
    assert rows["baseline_open_to_merge_h"][0] == 15.0   # median of 10..20
    assert rows["baseline_open_to_first_review_h"][0] == 2.0
    assert rows["baseline_pr_count"][0] == 11.0
    assert "baseline_after_go" not in rows


def test_baseline_too_few_prs_stores_nothing_numeric(
        project: dict[str, Any], tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(retro, "_gh_pr_list", lambda repo: _prs(9))
    out = retro.baseline(slug=project["slug"], repo_path=str(_local_repo(tmp_path)))
    assert out["stored"] is False and "jen 9" in out["reason"]
    rows = _ship(project["project_id"])
    assert rows["baseline_open_to_merge_h"][0] is None
    assert rows["baseline_open_to_merge_h"][1].startswith("základna není")
    assert not any(v[0] is not None for v in rows.values())


def test_baseline_gh_failure_is_not_fatal(
        project: dict[str, Any], tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(repo: Path) -> list[dict[str, Any]]:
        raise RuntimeError("`gh` není nainstalované")
    monkeypatch.setattr(retro, "_gh_pr_list", boom)
    out = retro.baseline(slug=project["slug"], repo_path=str(_local_repo(tmp_path)))
    assert out["stored"] is False and "gh" in out["reason"]


def test_baseline_after_go_is_flagged_and_pre_go_kept(
        merged_repo: dict[str, Any], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(retro, "_gh_pr_list", lambda repo: _prs(12))
    out = retro.baseline(slug=merged_repo["slug"], repo_path=str(merged_repo["repo"]))
    assert out["stored"] is True and out["after_go"] is True
    rows = _ship(merged_repo["project_id"])
    assert rows["baseline_after_go"][0] == 1.0 and "ADR-0013" in rows["baseline_after_go"][1]
    # a baseline stored before Go must not be overwritten afterwards
    with transaction() as conn:
        conn.execute("DELETE FROM outcomes WHERE metric = 'baseline_after_go'")
    again = retro.baseline(slug=merged_repo["slug"], repo_path=str(merged_repo["repo"]))
    assert again["kept_existing"] is True and again["stored"] is False


def test_measure_records_review_segments_next_to_baseline(
        merged_repo: dict[str, Any], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(retro, "_gh_pr_list", lambda repo: _prs(10))
    retro.baseline(slug=merged_repo["slug"], repo_path=str(merged_repo["repo"]))
    go = datetime.now(timezone.utc) - timedelta(days=3)
    opened = go + timedelta(hours=5)
    monkeypatch.setattr(retro, "_gh_pr_times", lambda url: {
        "createdAt": opened.isoformat(),
        "mergedAt": (opened + timedelta(hours=30)).isoformat(),
        "reviews": [{"submittedAt": (opened + timedelta(hours=4)).isoformat()}]})
    out = retro.measure(slug=merged_repo["slug"], merge_commit=merged_repo["merge_sha"],
                        repo_path=str(merged_repo["repo"]), winner="A", fetch=False,
                        pr_url="https://example.invalid/pull/1")
    seg = out["segments_h"]
    assert seg["go_to_pr_open_h"] == pytest.approx(5.0, abs=0.1)
    assert seg["pr_open_to_first_review_h"] == 4.0
    assert seg["first_review_to_merge_h"] == 26.0
    assert out["baseline"]["baseline_open_to_first_review_h"] == 2.0
    lines = retro._segment_lines(seg, out["baseline"])
    assert any("základna repa: medián 2 h" in x for x in lines)
    _p, _d, md = retro.write_report(merged_repo["slug"])
    assert "## Úseky review a základna repa" in md and "medián 2 h" in md
    assert "dojem týmu" in md


def test_measure_segments_missing_data_warns_not_crashes(
        merged_repo: dict[str, Any], monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    opened = datetime.now(timezone.utc) - timedelta(days=1)
    monkeypatch.setattr(retro, "_gh_pr_times", lambda url: {
        "createdAt": opened.isoformat(), "mergedAt": None, "reviews": []})
    out = retro.measure(slug=merged_repo["slug"], merge_commit=merged_repo["merge_sha"],
                        repo_path=str(merged_repo["repo"]), winner="A", fetch=False,
                        pr_url="https://example.invalid/pull/1")
    assert "pr_open_to_first_review_h" not in out["segments_h"]
    assert "first_review_to_merge_h" not in out["segments_h"]
    assert "žádné review" in capsys.readouterr().err

    def boom(url: str) -> dict[str, Any]:
        raise RuntimeError("gh selhal")
    monkeypatch.setattr(retro, "_gh_pr_times", boom)
    out = retro.measure(slug=merged_repo["slug"], merge_commit=merged_repo["merge_sha"],
                        repo_path=str(merged_repo["repo"]), winner="A", fetch=False,
                        pr_url="https://example.invalid/pull/1")
    assert out["segments_h"] == {}


def test_classify_subject() -> None:
    assert retro.classify_subject('Revert "feat: x"') == "revert"
    assert retro.classify_subject("HOTFIX: login") == "fix"
    assert retro.classify_subject("fix: typo") == "fix"
    assert retro.classify_subject("Fixes #12 crash") == "fix"
    assert retro.classify_subject("prefix handling") is None
    assert retro.classify_subject("feat: add button") is None


def test_instability_counts_reverts_and_fixes(merged_repo: dict[str, Any]) -> None:
    repo, slug = merged_repo["repo"], merged_repo["slug"]
    retro.measure(slug=slug, merge_commit=merged_repo["merge_sha"], repo_path=str(repo),
                  winner="A", fetch=False)
    feature = repo / "feature.py"
    for subject in ("fix: off by one", "Hotfix: null check", 'Revert "feat: winner"',
                    "chore: tidy"):
        feature.write_text(feature.read_text(encoding="utf-8") + f"# {subject}\n", encoding="utf-8")
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", subject)
    (repo / "README.md").write_text("# target\nunrelated\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "fix: readme only (not a winner file)")

    out = retro.instability(slug=slug, milestone="t7", repo_path=str(repo), fetch=False)
    assert out["reverts"] == 1 and out["fix_commits"] == 2 and out["files"] == 1
    with transaction() as conn:
        got = dict(conn.execute("SELECT metric, value FROM outcomes WHERE milestone = 't7' "
                                "AND metric IN ('reverts','fix_commits')").fetchall())
    assert got == {"reverts": 1.0, "fix_commits": 2.0}
    # recomputable: a second run replaces the rows
    retro.instability(slug=slug, milestone="t7", repo_path=str(repo), fetch=False)
    with transaction() as conn:
        assert conn.execute("SELECT COUNT(*) FROM outcomes WHERE milestone = 't7' "
                            "AND metric = 'reverts'").fetchone()[0] == 1
    _p, _d, md = retro.write_report(slug)
    assert "## Nestabilita po merge" in md and "reverty 1, opravné commity 2" in md


def test_instability_needs_merge_commit(project: dict[str, Any], tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="merge commit"):
        retro.instability(slug=project["slug"], milestone="t7",
                          repo_path=str(_local_repo(tmp_path)), fetch=False)
    with pytest.raises(ValueError, match="milestone"):
        retro.instability(slug=project["slug"], milestone="t60", fetch=False)
