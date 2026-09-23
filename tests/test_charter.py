"""Charter: ADR-0005 v0.4 — `evolve` default, `throwaway` needs a rationale."""
from __future__ import annotations

from pathlib import Path

import pytest

from tool.cli.charter import CharterInput, persist_charter, render_charter_md
from tool.cli.db import transaction


def _charter(**overrides: object) -> CharterInput:
    base: dict[str, object] = dict(
        slug="charter-demo", name="Charter demo", xyz_hypothesis="X pro Y díky Z",
        decider_name="Dana", decider_mandate_from="CPO", cpo_escalation_contact="CPO",
        sponsor_name="Sponzor", primary_lagging_metric="konverze",
        leading_metric="CTR", guardrail_metric="NPS", kill_criteria="žádný lift po 4 t.",
        capacity_profile="default", capacity_person_days=10, ai_act_tier="minimal",
        data_class="L2", reinforcement_t7="retro", reinforcement_t30="metrika",
        reinforcement_t60="—", reinforcement_t90="—", reinforcement_budget_pd=2.0,
    )
    base.update(overrides)
    return CharterInput(**base)  # type: ignore[arg-type]


def test_default_output_mode_is_evolve() -> None:
    c = _charter()
    assert c.throwaway_or_evolve == "evolve"
    assert c.throwaway_rationale is None


def test_throwaway_without_rationale_is_rejected() -> None:
    with pytest.raises(ValueError, match="throwaway_rationale"):
        _charter(throwaway_or_evolve="throwaway")
    with pytest.raises(ValueError, match="throwaway_rationale"):
        _charter(throwaway_or_evolve="throwaway", throwaway_rationale="   ")


def test_unknown_output_mode_is_rejected() -> None:
    with pytest.raises(ValueError, match="throwaway_or_evolve"):
        _charter(throwaway_or_evolve="prototype")


def test_throwaway_with_rationale_is_persisted(tmp_db: Path) -> None:
    rationale = "discovery-only pilot (XYZ falsification, no production intent)"
    c = _charter(throwaway_or_evolve="throwaway", throwaway_rationale=rationale)
    project_id = persist_charter(c, render_charter_md(c))
    with transaction() as conn:
        row = conn.execute(
            "SELECT throwaway_or_evolve, throwaway_rationale, status FROM projects WHERE id = ?",
            (project_id,),
        ).fetchone()
        decisions = conn.execute(
            "SELECT COUNT(*) FROM decisions WHERE project_id = ? AND type = 'charter'",
            (project_id,),
        ).fetchone()[0]
    assert tuple(row) == ("throwaway", rationale, "charter")
    assert decisions == 1


def test_evolve_charter_persisted_by_default(tmp_db: Path) -> None:
    c = _charter(slug="evolve-demo")
    project_id = persist_charter(c, render_charter_md(c))
    with transaction() as conn:
        mode = conn.execute(
            "SELECT throwaway_or_evolve FROM projects WHERE id = ?", (project_id,),
        ).fetchone()[0]
    assert mode == "evolve"
