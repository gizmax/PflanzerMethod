"""Expertní panel (EM): `pflanzer report summary|portfolio` a blok „Pro vedení: 4 čísla“ v retru."""
from __future__ import annotations

import csv
import json
import os
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from conftest import bootstrap_project, file_url

from tool.cli import report, retro, session_2
from tool.cli.db import transaction

REPO_ROOT = Path(__file__).resolve().parents[1]
BIN = REPO_ROOT / "tool" / "bin" / "pflanzer"
BRAND = "**Pflanzer Method | pflanzer.cz/method**"


@pytest.fixture(autouse=True)
def _cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    work = tmp_path / "work"
    work.mkdir()
    monkeypatch.chdir(work)         # decision log (.pflanzer/decisions) nesmí do repa toolu


def _pid(slug: str) -> int:
    with transaction() as conn:
        return int(conn.execute("SELECT id FROM projects WHERE slug = ?", (slug,)).fetchone()[0])


def _add_gates(slug: str, variant: str, statuses: dict[str, str]) -> None:
    with transaction() as conn:
        vid = conn.execute(
            "SELECT v.id FROM variants v JOIN sessions s ON s.id = v.session_id "
            "WHERE s.project_id = ? AND v.name = ?", (_pid(slug), variant)).fetchone()[0]
        eid = conn.execute(
            "INSERT INTO extracted_code (variant_id, source_url, local_path, extraction_method, "
            "extracted_by) VALUES (?, 'x', '/tmp/x', 'worktree', 'test')", (vid,)).lastrowid
        for gate, status in statuses.items():
            details = "NEOVĚŘENO: chybí @playwright/test — akceptační testy" \
                if status == "skipped" and gate == "acceptance" else ""
            conn.execute("INSERT INTO quality_gates (extracted_id, gate_type, status, details_md) "
                         "VALUES (?, ?, ?, ?)", (eid, gate, status, details))


def _outcome(slug: str, metric: str, value: float, milestone: str = "ship") -> None:
    with transaction() as conn:
        conn.execute("INSERT INTO outcomes (project_id, milestone, metric, value, recorded_by) "
                     "VALUES (?, ?, ?, ?, 'test')", (_pid(slug), milestone, metric, value))


def _usage(slug: str, usd: float | None = 4.2) -> None:
    with transaction() as conn:
        conn.execute("INSERT INTO ai_usage (project_id, variant, model, input_tokens, "
                     "output_tokens, est_usd) VALUES (?, 'A', 'claude-x', 800000, 400000, ?)",
                     (_pid(slug), usd))


def _go(slug: str) -> None:
    session_2.record_decision(slug=slug, decision="go", winner="A",
                              decider_attribution="Dana Deciderová",
                              rationale="A je nejrychlejší a pokrývá hlavní scénář. Zbytek počká.")


def test_summary_before_go_shows_state_and_gaps(project: dict[str, Any]) -> None:
    md = report.render_summary_md(report.collect(project["slug"]))
    assert md.startswith(BRAND)
    assert "Zatím nepadlo" in md
    assert "Brány zatím neběžely" in md
    assert "AI: neměřeno" in md and "Ještě neměřeno, měří se T+30" in md
    assert "## Další krok" in md
    assert len(md.splitlines()) <= 40
    assert "doplň" not in md.lower() and "<" not in md


def test_summary_after_go_with_numbers(project: dict[str, Any], vote: Callable[..., Any],
                                      monkeypatch: pytest.MonkeyPatch) -> None:
    slug = project["slug"]
    monkeypatch.setenv("PFLANZER_USD_CZK", "23")
    vote(slug)
    _go(slug)
    _add_gates(slug, "A", {"build": "pass", "tests": "pass", "lint": "pass", "types": "pass",
                           "smoke": "pass", "acceptance": "skipped"})
    _usage(slug)
    _outcome(slug, "days_to_prod", 9)
    _outcome(slug, "loc_reused_pct", 85)
    data = report.collect(slug)
    md = report.render_summary_md(data)
    assert "**Go** (vítěz A) — Dana Deciderová (Decider)" in md
    assert "Proč: A je nejrychlejší a pokrývá hlavní scénář. Zbytek počká." in md
    assert "Zbytek počká" in md                                      # celý důvod, ne první věta
    assert "1,2 M tokenů, odhad ≈ $4.20 (≈ 97 Kč)" in md
    assert "Skóre" in md and "Neověřeno" in md
    assert "Neověřeno: akceptační testy" in md
    assert "9 dní (cíl ≤ 14) — cíl splněn" in md
    assert "85 % (cíl ≥ 80 %) — cíl splněn" in md
    assert len(md.splitlines()) <= 40
    assert data["outcome"]["days_to_prod"]["ok"] is True


def test_summary_without_price_does_not_invent_money(project: dict[str, Any]) -> None:
    _usage(project["slug"], usd=None)
    md = report.render_summary_md(report.collect(project["slug"]))
    assert "1,2 M tokenů, cena nenastavená" in md
    assert "$" not in md and "Kč" not in md


def test_summary_risks_and_cap(project: dict[str, Any], vote: Callable[..., Any]) -> None:
    slug = project["slug"]
    vote(slug)
    with transaction() as conn:
        vid = conn.execute("SELECT v.id FROM variants v JOIN sessions s ON s.id = v.session_id "
                           "WHERE s.project_id = ? AND v.name = 'A'", (_pid(slug),)).fetchone()[0]
        for i in range(8):
            conn.execute("INSERT INTO feedback (variant_id, severity, department, category, "
                         "score, rationale, submitted_by) "
                         "VALUES (?, 'high', 'ux', 'flow', 0.4, ?, 'Test')",
                         (vid, f"Důležitá připomínka číslo {i}."))
    md = report.render_summary_md(report.collect(slug))
    assert "Důležité otevřené: 8" in md and "a dalších 5" in md
    assert len(md.splitlines()) <= 40


def test_summary_killed_shows_lesson(project: dict[str, Any], vote: Callable[..., Any]) -> None:
    slug = project["slug"]
    vote(slug)
    session_2.record_decision(slug=slug, decision="kill", rationale="Nikdo to nechtěl.")
    retro.lesson(slug=slug, text="Ověřit zájem dřív než stavět.", by="Dana")
    md = report.render_summary_md(report.collect(slug))
    assert "**Kill**" in md
    assert "Do produkce nic nešlo. Poučení: Ověřit zájem dřív než stavět." in md


def test_summary_unknown_project_is_czech_error(
        tmp_db: Path, capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        report.main(["summary", "--slug", "nic"])
    assert exc.value.code == 2
    assert "neexistuje" in capsys.readouterr().err


def test_leadership_numbers_single_source(project: dict[str, Any]) -> None:
    slug = project["slug"]
    _outcome(slug, "days_to_prod", 20)
    _outcome(slug, "loc_reused_pct", 60)
    nums = retro.leadership_numbers(slug)
    assert nums["days_to_prod"]["ok"] is False and nums["loc_survival_pct"]["ok"] is False
    lines = retro.leadership_lines(nums)
    assert len(lines) == 4 and "pod cílem" in lines[0] and "AI náklad na Go: neměřeno" in lines[2]
    with transaction() as conn:
        conn.execute("UPDATE projects SET path_owners_json = ? WHERE slug = ?",
                     (json.dumps({"byznys": "Dana", "design": "AI:ux-expert", "vyvoj": "Petr",
                                  "produkt": "Pavla"}), slug))
    share = retro.leadership_numbers(slug)["ai_share"]
    assert share["pct"] == 25 and share["ai_steps"] == ["design"]


def test_retro_report_starts_with_leadership_block(project: dict[str, Any]) -> None:
    slug = project["slug"]
    _outcome(slug, "days_to_prod", 9)
    md = retro.render_report_md(slug)
    head = md.split("## Cíle metody")[0]
    assert "## Pro vedení: 4 čísla" in head
    for label in ("Dny do produkce", "Kód vítěze, který přežil", "AI náklad na Go",
                  "Podíl kroků se zástupcem AI"):
        assert label in head
    assert "9 dní (cíl ≤ 14)" in head


def test_portfolio_rows_order_dashes_and_lessons(tmp_db: Path, bare_repo: Path, tmp_path: Path,
                                                 vote: Callable[..., Any]) -> None:
    older = bootstrap_project(slug="stary", target_repo_url=file_url(bare_repo))["slug"]
    newer = bootstrap_project(slug="novy", target_repo_url=file_url(bare_repo))["slug"]
    with transaction() as conn:
        for slug, ts in ((older, "2026-01-01 10:00:00"), (newer, "2026-02-01 10:00:00")):
            conn.execute("UPDATE projects SET created_at = ? WHERE slug = ?", (ts, slug))
    vote(older)
    session_2.record_decision(slug=older, decision="kill", rationale="Bez zájmu.")
    retro.lesson(slug=older, text="Zeptat se uživatelů předem.", by="Dana")
    _outcome(newer, "days_to_prod", 11)

    rows = report.portfolio_rows()
    assert [r["slug"] for r in rows] == ["novy", "stary"]
    new, old = rows
    assert new["days_to_prod"] == 11 and new["loc_survival_pct"] is None
    assert new["gate_score"] is None
    md = report.render_portfolio_md(rows)
    assert md.startswith(BRAND)
    assert "| novy |" in md and "11" in md and "—" in md
    assert "Poučení z killnutých projektů" in md and "Zeptat se uživatelů předem." in md
    assert old["lessons"] == ["Zeptat se uživatelů předem."]

    out = tmp_path / "out" / "p.csv"
    report.main(["portfolio", "--csv", str(out)])
    parsed = list(csv.reader(out.open(encoding="utf-8")))
    assert parsed[0][0] == "projekt" and parsed[1][0] == "novy" and parsed[2][0] == "stary"
    assert parsed[2][-1] == "Zeptat se uživatelů předem."


def test_portfolio_empty(tmp_db: Path) -> None:
    md = report.render_portfolio_md(report.portfolio_rows())
    assert "Zatím žádný projekt" in md


def test_cli_json_and_out(project: dict[str, Any], tmp_path: Path,
                          capsys: pytest.CaptureFixture[str]) -> None:
    slug = project["slug"]
    out = tmp_path / "r" / "summary.md"
    report.main(["summary", "--slug", slug, "--out", str(out)])
    assert out.read_text(encoding="utf-8").startswith(BRAND)
    capsys.readouterr()
    report.main(["summary", "--slug", slug, "--json"])
    data = json.loads(capsys.readouterr().out)
    assert data["slug"] == slug and data["markdown"].startswith(BRAND)
    report.main(["portfolio", "--json"])
    assert json.loads(capsys.readouterr().out)["projects"][0]["slug"] == slug


def test_bin_help_mentions_report(tmp_path: Path) -> None:
    env = {**os.environ, "HOME": str(tmp_path), "PFLANZER_DATA": str(tmp_path / "data"),
           "PFLANZER_DB": str(tmp_path / "data" / "t.db"), "TZ": "UTC"}
    res = subprocess.run([str(BIN)], capture_output=True, text=True, timeout=60, env=env)
    assert "Pro vedení: pflanzer report summary --slug S · pflanzer report portfolio" in res.stdout
    helped = subprocess.run([str(BIN), "report", "--help"], capture_output=True, text=True,
                            timeout=60, env=env)
    assert helped.returncode == 0 and "portfolio" in helped.stdout
