"""Pilot 24: Next.js šablona průvodce, texty doctoru, režimu a buildera."""
from __future__ import annotations

import json
from pathlib import Path

from tool.cli.init import NEXT_TEMPLATE_PATH, TEMPLATE_PATH, guide_template_for
from tool.cli.quick_session import VOTE_EPILOG, StackProfile, _builder_rules, recommend_mode
from tool.cli.session import ALLOWED_BUILDERS


def _repo(tmp_path: Path, deps: dict) -> Path:
    (tmp_path / "package.json").write_text(json.dumps({"dependencies": deps}), encoding="utf-8")
    return tmp_path


def test_next_gets_app_router_guide(tmp_path: Path) -> None:
    assert guide_template_for(_repo(tmp_path, {"next": "15", "react": "19"})) == NEXT_TEMPLATE_PATH
    text = NEXT_TEMPLATE_PATH.read_text(encoding="utf-8")
    assert "app/" in text and "pages/" in text
    assert "export const metadata" in text and '<html lang="cs">' in text


def test_plain_react_keeps_default(tmp_path: Path) -> None:
    assert guide_template_for(_repo(tmp_path, {"react": "19", "vite": "5"})) == TEMPLATE_PATH


def test_next_builder_rules_mention_a11y_only_for_next() -> None:
    nxt = _builder_rules("s", "h", "A", False, stack=StackProfile(stack="node", nextjs=True))
    other = _builder_rules("s", "h", "A", False, stack=StackProfile(stack="node"))
    assert "metadata" in nxt and 'lang=\\"cs\\"' in nxt or 'lang="cs"' in nxt
    assert "metadata" not in other


def test_mode_reason_is_human() -> None:
    _m, why = recommend_mode(production_target=80, risk_profile="pilot", room_size=3)
    assert why.startswith("Pilot má práh 80 ze 100")
    assert "Production target" not in why and "≥" not in why
    _m, why = recommend_mode(production_target=85, risk_profile="production", room_size=3)
    assert "85 ze 100" in why
    _m, why = recommend_mode(production_target=0, risk_profile="throwaway", room_size=3)
    assert "Production" not in why and "target" not in why.lower()


def test_vote_epilog_lists_builders() -> None:
    for b in ALLOWED_BUILDERS:
        assert b in VOTE_EPILOG


def test_doctor_next_step_equal_paths() -> None:
    src = (Path(__file__).resolve().parents[1] / "tool/cli/doctor.py").read_text(encoding="utf-8")
    assert "po restartu, ať načte plugin" in src
    assert "bez Claude Code" in src and "pflanzer start --spec kickoff.json" in src
