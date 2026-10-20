"""Pilot 21 (novacek): krátký slug, constitution, checkpoint, feedback a share bez šumu."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from tool.cli import feedback, preview, quick_session, share
from tool.cli.checkpoint import USAGE
from tool.cli.quick_session import auto_slug, constitution_conflicts, recommend_mode

HOOK = "Předobjednávky chleba pro pekárnu Kvásek"


def test_auto_slug_is_short_without_prepositions() -> None:
    slug = auto_slug(HOOK)
    assert slug == "predobjednavky-chleba"
    assert len(slug) <= 24 and "-pro-" not in slug
    assert auto_slug("Rychlejší checkout pro B2B zákazníky") == "rychlejsi-checkout-b2b"


def test_auto_slug_collision_gets_suffix() -> None:
    assert auto_slug(HOOK, {"predobjednavky-chleba"}) == "predobjednavky-chleba-2"


def test_bootstrap_auto_slug_and_explicit_unchanged(tmp_db: Path) -> None:
    out = quick_session.bootstrap(hook=HOOK, decider_name="Jana", risk_profile="throwaway")
    assert out["slug"] == "predobjednavky-chleba" and out["slug_auto"]
    out2 = quick_session.bootstrap(hook=HOOK, decider_name="Jana", risk_profile="throwaway",
                                   slug="moje-dlouhe-explicitni-slug")
    assert out2["slug"] == "moje-dlouhe-explicitni-slug" and not out2["slug_auto"]
    out3 = quick_session.bootstrap(hook=HOOK, decider_name="Jana", risk_profile="throwaway")
    assert out3["slug"] == "predobjednavky-chleba"   # stejný hook = stejný projekt


def _constitution(tmp_path: Path, rule: str) -> Path:
    d = tmp_path / ".pflanzer"
    d.mkdir()
    (d / "CONSTITUTION.md").write_text(f"# Constitution\n\n- {rule}\n", encoding="utf-8")
    return tmp_path


def test_constitution_l1_name_and_count_is_no_conflict(tmp_path: Path) -> None:
    cwd = _constitution(tmp_path, "Data: L1, jen jméno a počet")
    assert constitution_conflicts(HOOK, "20 objednávek týdně", None, cwd=cwd) == []


def test_constitution_real_conflict_is_still_warned(tmp_path: Path) -> None:
    cwd = _constitution(tmp_path, "Bez osobních dat, L1")
    out = constitution_conflicts("Platba kartou a rodné číslo zákazníka", None, None, cwd=cwd)
    assert out and "odporuje zadání" in out[0]
    cwd2 = _constitution(tmp_path / "x" if (tmp_path / "x").mkdir() is None else tmp_path,
                         "Data: L1, jen jméno a počet")
    assert constitution_conflicts("Platba kartou za objednávku", None, None, cwd=cwd2)


def test_mob_reason_is_czech_without_internal_reference() -> None:
    _mode, why = recommend_mode(production_target=0, risk_profile="pilot", room_size=7,
                                has_veto_role=False)
    assert "Hunter" not in why and "7" in why


def test_checkpoint_usage_lists_merged_window() -> None:
    assert "bezpecnost-provoz" in USAGE


def test_feedback_without_subcommand_prints_help(capsys: pytest.CaptureFixture[str],
                                                 monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.argv", ["pflanzer feedback"])
    feedback.main()
    out = capsys.readouterr().out
    assert "feedback add --slug S --variant A --role Design" in out
    assert "feedback list --slug S" in out


def test_share_message_has_no_empty_bullets(capsys: pytest.CaptureFixture[str],
                                            monkeypatch: pytest.MonkeyPatch) -> None:
    res = {"slug": "s", "hub_url": "http://h/", "password": "pw", "user": "u", "deadline": None,
           "message": share.share_text("http://h/", None), "hub_port": 1, "variants": {},
           "warnings": [], "tunnel": True}
    monkeypatch.setattr(share, "up", lambda *a, **k: res)
    share.main(["--slug", "s"])
    out = capsys.readouterr().out
    assert not [ln for ln in out.splitlines() if ln.strip() == "-"]
    assert "> Adresa: http://h/" in out


def test_preview_share_message_has_no_empty_bullets() -> None:
    res: dict[str, Any] = {"slug": "s", "user": "u", "password": "pw", "variants": {
        "A": {"url": "http://a"}}, "deadline": None}
    lines, _nxt, _msg = preview._up_view(res)
    assert not [ln for ln in lines if not ln.strip()]


def test_feedback_add_critical_does_not_repeat_next_step_as_tip(
        project: dict[str, Any], vote: Any, capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    vote(project["slug"])
    monkeypatch.setattr("sys.argv", ["f", "add", "--slug", project["slug"], "--variant", "A",
                                     "--role", "Design", "--by", "X", "--severity", "critical",
                                     "--text", "t"])
    feedback.main()
    out = capsys.readouterr().out
    assert out.count("decide resolve") == 1
    assert out.count("Doporučení:") <= 1


def test_same_hook_reuses_auto_slug(tmp_db: Path, bare_repo: Path) -> None:
    """Nový Kickoff se stejným hookem (demo → pilot) nezakládá `-2`, jiný hook ano."""
    from conftest import file_url

    def kick(hook: str, risk: str) -> str:
        return quick_session.bootstrap(
            hook=hook, decider_name="Dana Deciderová", room_role_idx=[1, 2, 3, 4, 6],
            risk_profile=risk, slug=None, target_repo_url=file_url(bare_repo))["slug"]

    assert kick(HOOK, "throwaway") == kick(HOOK, "pilot") == "predobjednavky-chleba"
    assert kick("Předobjednávky chleba v sobotu", "pilot") == "predobjednavky-chleba-2"
