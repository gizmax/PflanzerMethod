"""Kolo 3 (CLI vrstva): wrapper `pflanzer`, české chyby, Kill ve statusu, throwaway,
dedupe tipů, doctor bez opakování, prompty, tier a targets dir."""
from __future__ import annotations

import os
import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from conftest import REPO_ROOT, bootstrap_project, file_url

from tool.cli import checkpoint, doctor, quick_session, retro, session_2, status, tier, ux, worktree
from tool.cli.db import transaction
from tool.cli.triage import ship_triage_gate

PFLANZER_BIN = REPO_ROOT / "tool" / "bin" / "pflanzer"
OWNERS = {"byznys": "Dana", "produkt": "Petr", "design": "Eva", "vyvoj": "Tomáš",
          "bezpecnost": "Lucie", "provoz": "Karel"}


def _run_bin(*args: str) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PFLANZER_PLUGIN_DIR": str(REPO_ROOT)}
    return subprocess.run(["bash", str(PFLANZER_BIN), *args], capture_output=True, text=True,
                          env=env, timeout=60)


def _main(monkeypatch: pytest.MonkeyPatch, module: Any, *argv: str) -> int:
    monkeypatch.setattr(sys, "argv", [module.__name__, *argv])
    try:
        module.main()
    except SystemExit as exc:
        return int(exc.code or 0)
    return 0


@pytest.fixture
def repo_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    repo = tmp_path / "target-repo"
    (repo / ".pflanzer").mkdir(parents=True)
    monkeypatch.chdir(repo)
    return repo


# --- 1. wrapper bin/pflanzer ---------------------------------------------------------------


def test_bin_typo_suggests_status_and_fails() -> None:
    res = _run_bin("statsu")
    assert res.returncode != 0
    assert "Myslel jste ‚status‘?" in res.stderr
    assert "Neznámý příkaz" in res.stderr


def test_bin_unknown_without_near_match_has_no_suggestion() -> None:
    res = _run_bin("qqqqqqqq")
    assert res.returncode != 0
    assert "Neznámý příkaz" in res.stderr and "Myslel jste" not in res.stderr


def test_bin_without_args_is_short_overview() -> None:
    res = _run_bin()
    assert res.returncode == 0
    assert "pflanzer status" in res.stdout and "pflanzer doctor" in res.stdout
    assert "pflanzer.cz/method" in res.stdout
    assert len(res.stdout.splitlines()) < 20


# --- 2. ux: české chyby, did_you_mean, project_not_found -----------------------------------


def _parser() -> ux.CzechArgumentParser:
    p = ux.CzechArgumentParser(prog="pflanzer demo")
    p.add_argument("--slug", required=True)
    p.add_argument("mode", choices=["status", "doctor", "checkpoint"], nargs="?")
    return p


def test_czech_parser_missing_required(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        _parser().parse_args([])
    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert "CHYBA: Chybí povinný parametr --slug" in err
    assert "the following" not in err


def test_czech_parser_invalid_choice_has_did_you_mean(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        _parser().parse_args(["--slug", "x", "statuss"])
    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert "Neznámý příkaz ‚statuss‘. Myslel jste ‚status‘?" in err
    assert "Možnosti: status, doctor, checkpoint." in err


def test_czech_parser_unrecognized_and_missing_value(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        _parser().parse_args(["--slug", "x", "--nope"])
    assert "Neznámý parametr: --nope" in capsys.readouterr().err
    with pytest.raises(SystemExit):
        _parser().parse_args(["--slug"])
    assert "potřebuje hodnotu" in capsys.readouterr().err


def test_did_you_mean() -> None:
    assert ux.did_you_mean("statsu", ["status", "doctor"]) == "status"
    assert ux.did_you_mean("zzzzzz", ["status", "doctor"]) is None
    assert ux.did_you_mean("x", []) is None


def test_project_not_found_message_lists_slugs(project: dict[str, Any]) -> None:
    msg = ux.project_not_found_message("checkou")
    assert "Projekt „checkou“ neexistuje." in msg
    assert "Myslel jste „checkout“?" in msg
    assert "Existující projekty: checkout." in msg
    assert "pflanzer status" in msg


def test_project_not_found_message_empty_db(tmp_db: Path) -> None:
    msg = ux.project_not_found_message("nic")
    assert "Zatím žádný projekt" in msg and "/pm start" in msg


def test_project_not_found_exits_2_in_czech(project: dict[str, Any],
                                            capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        ux.project_not_found("neni")
    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert err.startswith(ux.BRAND_LINE) and "CHYBA: Projekt „neni“ neexistuje." in err
    assert "checkout" in err


# --- 3. Kill ve statusu --------------------------------------------------------------------


def _add_critical(slug: str, variant: str) -> None:
    with transaction() as conn:
        vid = conn.execute(
            "SELECT v.id FROM variants v JOIN sessions s ON s.id = v.session_id "
            "JOIN projects p ON p.id = s.project_id WHERE p.slug = ? AND v.name = ?",
            (slug, variant)).fetchone()[0]
        conn.execute(
            "INSERT INTO feedback (variant_id, severity, department, category, score, "
            "rationale, submitted_by) VALUES (?, 'critical', 'legal', 'privacy', 0.1, "
            "'osobní údaje', 'Jana')", (vid,))


def test_status_after_kill_hides_blockers_and_points_to_lesson(
        project: dict[str, Any], vote: Callable[..., Any], repo_cwd: Path,
        monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    slug = project["slug"]
    vote(slug)
    _add_critical(slug, "A")
    session_2.record_decision(slug=slug, decision="kill", rationale="Nikdo to nechce")
    capsys.readouterr()

    d = status.project_detail(slug)
    assert d["phase"].startswith("Ukončeno (Kill)")
    assert d["blockers"] == [] and d["feedback"]["critical"] == 0
    assert d["checkpoints"] == [] and not d["lesson_recorded"]
    assert d["next_step"] == f'pflanzer retro lesson --slug {slug} --text "…"'

    assert _main(monkeypatch, status, "--slug", slug) == 0
    out = capsys.readouterr().out
    assert "Ukončeno (Kill)" in out
    assert "⚠" not in out and "Podpisy" not in out and "BLOKOVÁNO" not in out
    assert "retro lesson" in out and "Poučení: zatím nezapsáno" in out

    retro.lesson(slug=slug, text="Problém trápí jen vedení")
    d2 = status.project_detail(slug)
    assert d2["lesson_recorded"] and d2["next_step"] == "—"
    capsys.readouterr()
    _main(monkeypatch, status, "--slug", slug)
    out2 = capsys.readouterr().out
    assert "Poučení: zapsáno" in out2 and "poučení je zapsáno" in out2


def test_checkpoint_after_kill_is_error(project: dict[str, Any], vote: Callable[..., Any],
                                        repo_cwd: Path, monkeypatch: pytest.MonkeyPatch,
                                        capsys: pytest.CaptureFixture[str]) -> None:
    slug = project["slug"]
    vote(slug)
    session_2.record_decision(slug=slug, decision="kill", rationale="Nikdo to nechce")
    capsys.readouterr()
    with pytest.raises(ValueError, match="je ukončen"):
        checkpoint.sign(slug, "provoz", by="Karel", note="x")
    code = _main(monkeypatch, checkpoint, "--slug", slug, "provoz", "--by", "Karel",
                 "--note", "x")
    assert code != 0
    assert "je ukončen" in capsys.readouterr().err


# --- 4. Throwaway --------------------------------------------------------------------------


def _gate(slug: str) -> dict[str, Any]:
    with transaction() as conn:
        pid = conn.execute("SELECT id FROM projects WHERE slug = ?", (slug,)).fetchone()[0]
        return ship_triage_gate(conn, int(pid))


def test_throwaway_ai_checkpoint_signed_and_gate_not_blocked(tmp_db: Path) -> None:
    bootstrap_project(risk_profile="throwaway", slug="thr",
                      path_owners={**OWNERS, "bezpecnost": "AI", "provoz": "AI"})
    for window in ("bezpecnost", "provoz"):
        res = checkpoint.sign("thr", window, ai=True, note="AI pre-check")
        assert res["status"] == "ok" and not res["ai_draft"]
    assert not [b for b in _gate("thr")["blocked_by"] if "security" in b or "legal" in b]


def test_throwaway_status_has_no_human_signature_nags(tmp_db: Path, monkeypatch: pytest.MonkeyPatch,
                                                      capsys: pytest.CaptureFixture[str]) -> None:
    bootstrap_project(risk_profile="throwaway", slug="thr",
                      path_owners={**OWNERS, "bezpecnost": "AI", "provoz": "AI"})
    assert _main(monkeypatch, status, "--slug", "thr") == 0
    out = capsys.readouterr().out
    assert "u pilotu může podepsat Decider" not in out
    assert "AI draft není podpis" not in out and "Ship zůstane zablokovaný" not in out
    assert "bez nich pilot nepůjde" not in out


def test_throwaway_tips_skip_human_signature_tips() -> None:
    ctx = {"throwaway": True, "ai_pending": True, "ai_stand_ins": True,
           "missing_signatures": True}
    assert ux.tips_for("ai_stand_in", ctx) == []
    assert not any("podpis" in t.lower() for t in ux.tips_for("status", ctx))
    assert not any("podpisy oken" in t for t in ux.tips_for("ship", ctx))
    assert not any("Kroky s AI náhradou" in t for t in ux.tips_for("kickoff", ctx))
    # pilot je dostane
    pilot = {"ai_pending": True, "missing_signatures": True}
    assert any("AI draft není podpis" in t for t in ux.tips_for("status", pilot))
    assert any("podpisy oken" in t for t in ux.tips_for("ship", pilot))


def test_throwaway_project_tips_filtered_via_db(tmp_db: Path) -> None:
    bootstrap_project(risk_profile="throwaway", slug="thr")
    assert ux.tips_for_project("thr", "ai_stand_in") == []


# --- 5. tips_for_project dedupe ------------------------------------------------------------


def test_tips_for_project_same_phase_three_times_only_first(tmp_db: Path,
                                                            bare_repo: Path) -> None:
    bootstrap_project(slug="dd", target_repo_url=file_url(bare_repo))
    first = ux.tips_for_project("dd", "after_kill")
    assert first
    assert ux.tips_for_project("dd", "after_kill") == []
    assert ux.tips_for_project("dd", "after_kill") == []
    # jiná fáze se stejným textem se neopakuje, nový text projde
    with transaction() as conn:
        n = conn.execute("SELECT COUNT(*) FROM audit_log WHERE action = 'tip.shown'"
                         ).fetchone()[0]
    assert n == 1


def test_tips_for_project_limit_then_remaining(tmp_db: Path, bare_repo: Path) -> None:
    bootstrap_project(slug="lim", target_repo_url=file_url(bare_repo))
    a = ux.tips_for_project("lim", "after_kill", limit=1)
    b = ux.tips_for_project("lim", "after_kill", limit=2)
    assert len(a) == 1 and len(b) == 2 and not set(a) & set(b)


# --- 6. doctor -----------------------------------------------------------------------------


def test_doctor_tip_does_not_repeat_warning_rows(tmp_path: Path) -> None:
    repo = tmp_path / "bare"
    repo.mkdir()
    rows = [doctor.check_ci(repo), doctor.check_preview(repo)]
    assert all(r["status"] == doctor.WARN for r in rows)
    _title, lines, _nxt, _warns, tips = doctor._human(repo, rows)
    assert any("CI konfigurace" in ln for ln in lines)
    assert any("Preview deploy" in ln for ln in lines)
    blob = " ".join(tips).lower()
    for needle in ("ci ", "github actions", "preview", "vercel", "netlify"):
        assert needle not in blob
    assert ux.TIPS["doctor"] == []


# --- 7. quick_session prompts --------------------------------------------------------------


def test_prompts_human_output_is_short_and_setup_once(
        project: dict[str, Any], tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    repo = tmp_path / "pyapp"
    repo.mkdir()
    (repo / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    monkeypatch.chdir(repo)
    code = _main(monkeypatch, quick_session, "prompts", "--slug", project["slug"],
                 "--hook", "Rychlejší checkout")
    assert code == 0
    out = capsys.readouterr().out
    assert len(out.splitlines()) < 60
    assert out.count("Setup worktree") == 1
    for v in ("A", "B", "C"):
        assert f"Varianta {v}" in out
    assert "Prompty pro buildery" in out


# --- 8. tier -------------------------------------------------------------------------------


def test_validate_tier_pilot_is_czech_risk_profile_error() -> None:
    with pytest.raises(ValueError, match="risk profil") as exc:
        tier.validate_tier("pilot")
    assert "quick|lean|full" in str(exc.value)
    with pytest.raises(ValueError, match="Myslel jste ‚lean‘"):
        tier.validate_tier("lan")


def test_bootstrap_tier_pilot_rejected(tmp_db: Path) -> None:
    with pytest.raises(ValueError, match="risk profil"):
        bootstrap_project(slug="bad", tier="pilot")


def test_default_tier_pilot_lean_throwaway_quick(tmp_db: Path, bare_repo: Path) -> None:
    assert bootstrap_project(slug="p", target_repo_url=file_url(bare_repo))["tier"] == "lean"
    assert bootstrap_project(slug="t", risk_profile="throwaway")["tier"] == "quick"


# --- 9. targets dir ------------------------------------------------------------------------


def test_default_targets_dir_under_data_root(monkeypatch: pytest.MonkeyPatch,
                                             tmp_path: Path) -> None:
    from tool.cli import db
    monkeypatch.delenv("PFLANZER_TARGETS_DIR", raising=False)
    monkeypatch.setattr(db, "DATA_ROOT", tmp_path / "dataroot")
    assert worktree.default_targets_dir() == tmp_path / "dataroot" / "targets"
    monkeypatch.setattr(db, "DATA_ROOT", tmp_path / "other")
    assert worktree.default_targets_dir() == tmp_path / "other" / "targets"


def test_default_targets_dir_env_override(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("PFLANZER_TARGETS_DIR", str(tmp_path / "custom"))
    assert worktree.default_targets_dir() == tmp_path / "custom"


# --- 10. plural rozsahů a status s jedním projektem -----------------------------------------


def test_window_label_plurals() -> None:
    assert tier.window_label("quick") == "3 dny"
    assert tier.window_label("lean") == "3–5 dní"
    assert tier.window_label("full") == "5–7 dní"
    assert status.tier_label("lean") == "Lean (okno 3–5 dní)"
    assert status.tier_label("quick") == "Quick (okno 3 dny)"


def test_status_single_project_shows_detail(project: dict[str, Any],
                                            monkeypatch: pytest.MonkeyPatch,
                                            capsys: pytest.CaptureFixture[str]) -> None:
    assert _main(monkeypatch, status) == 0
    out = capsys.readouterr().out
    assert "Fáze:" in out and "Kroky cesty" in out
    assert re.search(r"^## .*`checkout`", out, re.M)
    assert "## Projekty" not in out


def test_status_two_projects_is_list(project: dict[str, Any], bare_repo: Path,
                                     monkeypatch: pytest.MonkeyPatch,
                                     capsys: pytest.CaptureFixture[str]) -> None:
    bootstrap_project(slug="druhy", target_repo_url=file_url(bare_repo))
    assert _main(monkeypatch, status) == 0
    out = capsys.readouterr().out
    assert "## Projekty" in out and "`druhy`" in out and "`checkout`" in out
