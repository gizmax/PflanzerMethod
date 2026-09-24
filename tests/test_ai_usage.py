"""ai_usage.py (audit N16): Claude Code token usage per variant, SHIP.md section.

All transcripts are synthetic and live under the test HOME (conftest).
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import pytest
from conftest import bootstrap_project

from tool.cli import ai_usage, handoff_pr


@pytest.fixture(autouse=True)
def no_repo_price_list(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A developer's local `pflanzer.prices.json` must not leak into the tests."""
    monkeypatch.setattr(ai_usage, "PRICES_FILE", tmp_path / "no-prices.json")


def _assistant(mid: str, model: str, ts: str, *, inp: int = 0, out: int = 0,
               cw: int = 0, cr: int = 0) -> dict[str, Any]:
    return {
        "type": "assistant", "timestamp": ts, "sessionId": "s",
        "message": {"id": mid, "model": model, "role": "assistant",
                    "content": [{"type": "text", "text": "synthetic"}],
                    "usage": {"input_tokens": inp, "output_tokens": out,
                              "cache_creation_input_tokens": cw,
                              "cache_read_input_tokens": cr}},
    }


def _write_jsonl(path: Path, records: list[Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [r if isinstance(r, str) else json.dumps(r) for r in records]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _project_dir(home: Path, worktree: Path) -> Path:
    return home / ".claude" / "projects" / ai_usage.escape_project_dir(worktree)


def _seed_variant_a(home: Path, wt: Path) -> Path:
    """Two sessions + one subagent transcript with noise; returns the project dir."""
    d = _project_dir(home, wt)
    _write_jsonl(d / "s1.jsonl", [
        {"type": "user", "timestamp": "2026-09-01T09:00:00.000Z",
         "message": {"role": "user", "content": "synthetic prompt"}},
        # One streamed response = two records with the same message.id.
        _assistant("msg_1", "claude-opus-test", "2026-09-01T09:00:05.000Z",
                   inp=100, out=50, cw=1000, cr=2000),
        _assistant("msg_1", "claude-opus-test", "2026-09-01T09:00:06.000Z",
                   inp=100, out=50, cw=1000, cr=2000),
        "{not json at all",
        {"type": "summary", "summary": "synthetic"},
        {"type": "assistant", "timestamp": "2026-09-01T09:01:00.000Z",
         "message": {"id": "msg_nousage", "model": "claude-opus-test"}},
        _assistant("msg_syn", "<synthetic>", "2026-09-01T09:01:30.000Z", inp=999),
        _assistant("msg_2", "claude-haiku-test", "2026-09-01T09:02:00.000Z",
                   inp=10, out=5),
        [1, 2, 3],
    ])
    _write_jsonl(d / "s2.jsonl", [
        _assistant("msg_3", "claude-opus-test", "2026-09-02T10:00:00.000Z",
                   inp=1, out=2, cw=3, cr=4),
    ])
    _write_jsonl(d / "s1" / "subagents" / "agent-x.jsonl", [
        _assistant("msg_4", "claude-haiku-test", "2026-09-01T09:03:00.000Z",
                   inp=20, out=10),
    ])
    return d


def test_escape_project_dir() -> None:
    assert (ai_usage.escape_project_dir("/home/u/.pflanzer/targets/checkout-A")
            == "-home-u--pflanzer-targets-checkout-A")
    assert ai_usage.escape_project_dir(Path("/a/b_c.d/x y")) == "-a-b-c-d-x-y"


def test_find_and_summarize(isolated_env: dict[str, Path], tmp_path: Path) -> None:
    home = isolated_env["home"]
    wt = tmp_path / "targets" / "checkout-A"
    _seed_variant_a(home, wt)
    # Sibling worktree (another repo role) must not be picked up.
    _write_jsonl(_project_dir(home, tmp_path / "targets" / "checkout-A-be") / "x.jsonl",
                 [_assistant("msg_be", "claude-opus-test", "2026-09-03T00:00:00Z", inp=7)])

    paths = ai_usage.find_transcripts(wt)
    assert sorted(p.name for p in paths) == ["agent-x.jsonl", "s1.jsonl", "s2.jsonl"]

    s = ai_usage.summarize_usage(paths)
    assert s["sessions"] == 2          # subagent belongs to session s1
    assert s["files"] == 3
    assert s["messages"] == 4          # msg_1 once, msg_2, msg_3, msg_4
    assert (s["input"], s["output"], s["cache_creation"], s["cache_read"]) == (131, 67, 1003, 2004)
    assert s["models"]["claude-opus-test"] == {
        "messages": 2, "input": 101, "output": 52, "cache_creation": 1003,
        "cache_read": 2004, "sessions": 2,
    }
    assert s["models"]["claude-haiku-test"]["messages"] == 2
    assert s["models"]["claude-haiku-test"]["sessions"] == 1
    assert "<synthetic>" not in s["models"]
    assert s["skipped_lines"] == 1
    assert s["first_ts"] == "2026-09-01T09:00:00.000Z"
    assert s["last_ts"] == "2026-09-02T10:00:00.000Z"
    assert s["est_usd"] is None


def test_claude_config_dir_override(isolated_env: dict[str, Path], tmp_path: Path,
                                    monkeypatch: pytest.MonkeyPatch) -> None:
    alt = tmp_path / "alt-claude"
    wt = tmp_path / "targets" / "checkout-B"
    _write_jsonl(alt / "projects" / ai_usage.escape_project_dir(wt) / "s.jsonl",
                 [_assistant("m", "claude-opus-test", "2026-09-01T00:00:00Z", out=3)])
    assert ai_usage.find_transcripts(wt) == []
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(alt))
    assert len(ai_usage.find_transcripts(wt)) == 1


def test_missing_claude_home_is_empty(tmp_path: Path) -> None:
    assert ai_usage.find_transcripts(tmp_path / "nowhere") == []
    assert ai_usage.summarize_usage([tmp_path / "missing.jsonl"])["messages"] == 0


def test_prices_via_env(isolated_env: dict[str, Path], tmp_path: Path,
                        monkeypatch: pytest.MonkeyPatch) -> None:
    wt = tmp_path / "targets" / "checkout-A"
    _seed_variant_a(isolated_env["home"], wt)
    prices = tmp_path / "prices.json"
    prices.write_text(json.dumps({
        "_comment": "synthetic test prices",
        "claude-opus": {"input": 1.0, "output": 1.0, "cache_write": 1.0, "cache_read": 1.0},
        "claude-opus-test": {"input": 10.0, "output": 20.0, "cache_write": 1.0,
                             "cache_read": 0.5},
        "claude-sonnet": {"input": None, "output": None},
    }), encoding="utf-8")
    monkeypatch.setenv("PFLANZER_AI_PRICES", str(prices))
    loaded, source = ai_usage.load_prices()
    assert source == str(prices)
    assert loaded is not None and "claude-sonnet" not in loaded  # null rates ignored

    s = ai_usage.summarize_usage(ai_usage.find_transcripts(wt), loaded)
    # Longest prefix wins: 101*10 + 52*20 + 1003*1 + 2004*0.5 = 4055 per 1M tokens.
    assert s["models"]["claude-opus-test"]["est_usd"] == pytest.approx(0.004055)
    assert s["est_usd"] == pytest.approx(0.004055)
    assert s["unpriced_models"] == ["claude-haiku-test"]


def test_template_prices_are_not_active(monkeypatch: pytest.MonkeyPatch) -> None:
    tpl = ai_usage.REPO_ROOT / "tool" / "templates" / "pflanzer.prices.json.template"
    monkeypatch.setenv("PFLANZER_AI_PRICES", str(tpl))
    assert ai_usage.load_prices() == (None, None)


@pytest.fixture
def multi_project(tmp_db: Path) -> dict[str, Any]:
    return bootstrap_project(slug="multi", target_repos=[
        {"role": "fe", "url": "https://github.com/example/web"},
        {"role": "be", "url": "https://github.com/example/api"},
    ])


def test_usage_for_project_all_repos(multi_project: dict[str, Any],
                                     isolated_env: dict[str, Path]) -> None:
    home, targets = isolated_env["home"], isolated_env["targets"]
    _seed_variant_a(home, targets / "multi-A")
    _write_jsonl(_project_dir(home, targets / "multi-A-be") / "be.jsonl",
                 [_assistant("msg_be", "claude-opus-test", "2026-09-03T00:00:00Z",
                             inp=1000, out=100)])
    _write_jsonl(_project_dir(home, targets / "multi-C") / "c.jsonl",
                 [_assistant("msg_c", "claude-opus-test", "2026-09-03T00:00:00Z", out=9)])

    usage = ai_usage.usage_for_project("multi")
    assert sorted(usage) == ["A", "C"]
    assert usage["A"]["sessions"] == 3
    assert usage["A"]["input"] == 131 + 1000
    assert len(usage["A"]["worktrees"]) == 2
    assert usage["A"]["est_usd"] is None
    assert ai_usage.cycle_totals(usage)["output"] == 67 + 100 + 9


def _ai_rows(db: Path, slug: str) -> list[tuple]:
    conn = sqlite3.connect(db)
    try:
        return conn.execute(
            "SELECT a.variant, a.model, a.sessions, a.messages, a.input_tokens, "
            "a.output_tokens, a.est_usd, a.source FROM ai_usage a "
            "JOIN projects p ON p.id = a.project_id WHERE p.slug = ? "
            "ORDER BY a.variant, a.model", (slug,),
        ).fetchall()
    finally:
        conn.close()


def test_cli_record_replaces_snapshot(project: dict[str, Any], isolated_env: dict[str, Path],
                                      capsys: pytest.CaptureFixture[str]) -> None:
    slug = project["slug"]
    home, targets = isolated_env["home"], isolated_env["targets"]
    d = _seed_variant_a(home, targets / f"{slug}-A")

    assert ai_usage.main(["--slug", slug, "--record"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("Pflanzer Method | pflanzer.cz/method")
    assert "| `A` |" in out and "Celkem za cyklus" in out
    rows = _ai_rows(isolated_env["db"], slug)
    assert [(r[0], r[1], r[3], r[4]) for r in rows] == [
        ("A", "claude-haiku-test", 2, 30), ("A", "claude-opus-test", 2, 101)]
    assert all(r[6] is None and r[7].startswith("claude-code-jsonl@") for r in rows)

    # New activity -> a second --record overwrites, never duplicates.
    _write_jsonl(d / "s3.jsonl", [_assistant("msg_5", "claude-opus-test",
                                             "2026-09-04T00:00:00Z", inp=1000)])
    assert ai_usage.main(["--slug", slug, "--record", "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["variants"]["A"]["sessions"] == 3
    assert data["recorded"]["rows"] == 2
    rows = _ai_rows(isolated_env["db"], slug)
    assert len(rows) == 2
    assert rows[1][1:5] == ("claude-opus-test", 3, 3, 1101)


def test_cli_unknown_slug(tmp_db: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert ai_usage.main(["--slug", "nope"]) == 2
    assert "chyba" in capsys.readouterr().err


def test_ship_md_without_logs(project: dict[str, Any]) -> None:
    md = handoff_pr.render_ship_md(project["slug"])
    assert "## AI náklady (viditelnost)" in md
    assert ("Žádné session logy Claude Code pro worktrees tohoto projektu na tomto stroji."
            in md)


def test_ship_md_with_logs_and_snapshot_fallback(
    project: dict[str, Any], isolated_env: dict[str, Path], tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import shutil

    slug = project["slug"]
    d = _seed_variant_a(isolated_env["home"], isolated_env["targets"] / f"{slug}-A")

    md = handoff_pr.render_ship_md(slug)
    assert "## AI náklady (viditelnost)" in md
    assert "| `A` | 2 | 4 | 131 | 67 | 1 003 | 2 004 |" in md
    assert "| **Celkem za cyklus** | 2 | 4 |" in md
    assert "na tomto stroji" in md
    assert "Cena se nevykazuje" in md and "USD (odhad)" not in md

    prices = tmp_path / "p.json"
    prices.write_text(json.dumps({"claude-": {"input": 1000000, "output": 0}}),
                      encoding="utf-8")
    monkeypatch.setenv("PFLANZER_AI_PRICES", str(prices))
    md = handoff_pr.render_ship_md(slug)
    assert "USD (odhad)" in md and "$131.00" in md

    ai_usage.record_snapshot(slug)
    shutil.rmtree(d)
    md = handoff_pr.render_ship_md(slug)
    assert "poslední snapshot z DB" in md
    assert "| `A` | 2 | 4 | 131 |" in md


def test_ship_md_never_fails_on_usage_error(project: dict[str, Any],
                                            monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*_a: Any, **_k: Any) -> Any:
        raise RuntimeError("synthetic failure")

    monkeypatch.setattr(ai_usage, "usage_for_project", boom)
    monkeypatch.setattr(ai_usage, "load_snapshot", boom)
    md = handoff_pr.render_ship_md(project["slug"])
    assert "Žádné session logy Claude Code" in md
