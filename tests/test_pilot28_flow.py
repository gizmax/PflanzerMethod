"""Pilot 28: negace v CONSTITUTION, builder manual, status další krok, tón feedback_pull, role."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tool.cli import feedback_pull, quick_session, status, worktree


def _constitution(tmp_path: Path) -> Path:
    d = tmp_path / ".pflanzer"
    d.mkdir()
    (d / "CONSTITUTION.md").write_text(
        "# Constitution\n\n- Nesbíráme osobní údaje v produkční aplikaci.\n", encoding="utf-8")
    return tmp_path


def test_constitution_ignores_negated_mention(tmp_path: Path) -> None:
    cwd = _constitution(tmp_path)
    for hook in ("Rychlé objednání bez telefonování", "Objednání, nesbíráme telefon"):
        assert quick_session.constitution_conflicts(hook, cwd=cwd) == [], hook


def test_constitution_still_warns_on_real_mention(tmp_path: Path) -> None:
    cwd = _constitution(tmp_path)
    out = quick_session.constitution_conflicts("Zákazník zadá telefon a e-mail", cwd=cwd)
    assert out and "telefon" in out[0]


def test_vote_template_follows_builder_and_names_roles() -> None:
    tpl = worktree.vote_template("x", ["A"], "manual")
    vote = tpl["votes"][0]
    assert vote["builder"] == "manual"
    assert vote["role_preferences"][0]["role"] == "Zadavatel / Business owner"
    assert worktree.vote_template("x", ["A"])["votes"][0]["builder"] == "claude-code"


def test_vote_template_with_role_field_is_accepted_by_record(project: dict[str, Any],
                                                             tmp_targets: Path) -> None:
    slug = project["slug"]
    worktree.setup(slug, install_deps=False, run_guard=False, builder="manual")
    tpl = worktree.vote_template(slug, ["A", "B", "C"], "manual")
    tpl["facilitator"] = "Fanda"
    tpl["decider_call"]["shortlist"] = ["A"]
    tpl["decider_call"]["rationale"] = "A je nejrychlejší"
    tpl = {k: v for k, v in tpl.items() if not k.startswith("_")}
    for v in tpl["votes"]:
        v["role_preferences"][0].update(rationale="Test", commitment_level=3)
    out = quick_session.record_voting(**tpl)
    assert out and not out.get("error")


def test_setup_manual_next_step_and_template(project: dict[str, Any], tmp_targets: Path,
                                             monkeypatch: Any, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    s = worktree.setup(project["slug"], install_deps=False, run_guard=False, builder="manual")
    _title, _lines, nxt = worktree._setup_view(s)
    assert "claude" not in nxt and "pflanzer record --spec" in nxt and "commitujte" in nxt
    path = worktree.write_vote_template(project["slug"], s.mode, tmp_path, builder=s.builder)
    assert path and json.loads(path.read_text())["votes"][0]["builder"] == "manual"
    s2 = worktree.setup(project["slug"], install_deps=False, run_guard=False)
    assert "&& claude" in worktree._setup_view(s2)[2]


def test_vote_epilog_explains_roles() -> None:
    assert "role?" in quick_session.VOTE_EPILOG
    assert "15 DevOps" in quick_session.VOTE_EPILOG
    assert "nástrojem Write" not in quick_session.BOOTSTRAP_EPILOG


def test_status_next_step_has_slug_in_right_place() -> None:
    _phase, nxt = status._phase("session_1", "none", 0, 0, sharing=True)
    resolved = status._with_slug(nxt, "joga-lotos").replace("<slug>", "joga-lotos")
    assert resolved.startswith("/pm feedback joga-lotos  (")
    assert not resolved.endswith("joga-lotos")
    assert "share down --slug joga-lotos" in resolved
    assert status._with_slug("/pm build", "joga") == "/pm build joga"


def test_feedback_pull_silent_rep_formal_tone() -> None:
    src = Path(feedback_pull.__file__).read_text(encoding="utf-8")
    assert "Ozvěte se:" in src and "ozvi se" not in src and "jeho připomínku" not in src
