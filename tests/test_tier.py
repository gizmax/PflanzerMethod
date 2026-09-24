"""projects.tier: stupeň Quick / Lean / Full (00-lean-pflanzer.md § Tři stupně, ADR-0021)."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pytest
from conftest import bootstrap_project, file_url

from tool.cli.charter import CharterInput, persist_charter, render_charter_md
from tool.cli.db import transaction
from tool.cli.tier import default_tier, validate_tier
from tool.db.migrate import apply_schema

FIXTURE = Path(__file__).parent / "fixtures" / "schema-v0.sql"


def _tier(slug: str) -> str | None:
    with transaction() as conn:
        return conn.execute("SELECT tier FROM projects WHERE slug = ?", (slug,)).fetchone()[0]


def _charter(**overrides: Any) -> CharterInput:
    base: dict[str, Any] = dict(
        slug="tier-demo", name="Tier demo", xyz_hypothesis="X % z Y udělá Z",
        decider_name="Dana", decider_mandate_from="CPO", cpo_escalation_contact="CPO",
        sponsor_name="Dana", primary_lagging_metric="m", leading_metric="m",
        guardrail_metric="m", kill_criteria="k", capacity_profile="default",
        capacity_person_days=10, ai_act_tier="minimal", data_class="L2",
        reinforcement_t7="a", reinforcement_t30="b", reinforcement_t60="c",
        reinforcement_t90="d", reinforcement_budget_pd=2.0,
    )
    base.update(overrides)
    return CharterInput(**base)


@pytest.mark.parametrize(("capacity", "quick", "risk", "expected"), [
    ("default", False, None, "lean"),
    ("regulated", False, None, "lean"),
    ("audit-grade", False, None, "full"),
    ("default", True, "pilot", "quick"),
    ("regulated", True, "production", "lean"),
    ("audit-grade", True, "pilot", "full"),
])
def test_default_tier(capacity: str, quick: bool, risk: str | None, expected: str) -> None:
    assert default_tier(capacity, quick_bootstrap=quick, risk_profile=risk) == expected


def test_validate_tier_rejects_unknown_and_quick_audit_grade() -> None:
    assert validate_tier(" Lean ") == "lean"
    with pytest.raises(ValueError, match="tier must be one of"):
        validate_tier("medium")
    with pytest.raises(ValueError, match="audit-grade"):
        validate_tier("quick", "audit-grade")


def test_charter_defaults_and_persists_tier(tmp_db: Path) -> None:
    lean = _charter()
    assert lean.tier == "lean"
    persist_charter(lean, render_charter_md(lean))
    assert _tier("tier-demo") == "lean"
    assert "**Stupeň**: **Lean**" in render_charter_md(lean)

    full = _charter(slug="audit", capacity_profile="audit-grade")
    assert full.tier == "full"
    explicit = _charter(slug="explicit", tier="full")
    persist_charter(explicit, render_charter_md(explicit))
    assert _tier("explicit") == "full"


def test_charter_rejects_invalid_tier() -> None:
    with pytest.raises(ValueError):
        _charter(tier="huge")
    with pytest.raises(ValueError, match="audit-grade"):
        _charter(capacity_profile="audit-grade", tier="quick")


def test_bootstrap_tier(tmp_db: Path, bare_repo: Path) -> None:
    url = file_url(bare_repo)
    bootstrap_project(slug="pilot-q", target_repo_url=url)
    bootstrap_project(slug="prod-l", risk_profile="production", target_repo_url=url)
    bootstrap_project(slug="explicit-f", target_repo_url=url, tier="full")
    assert (_tier("pilot-q"), _tier("prod-l"), _tier("explicit-f")) == ("quick", "lean", "full")


def test_migrate_backfills_tier_for_legacy_projects(isolated_env: dict[str, Path]) -> None:
    db = isolated_env["db"]
    conn = sqlite3.connect(db)
    conn.executescript(FIXTURE.read_text(encoding="utf-8"))
    rows = [
        (1, "quick-one", "default"),
        (2, "lean-one", "regulated"),
        (3, "full-one", "audit-grade"),
    ]
    conn.executemany(
        "INSERT INTO projects (id, slug, name, capacity_profile) VALUES (?, ?, ?, ?)",
        [(i, s, s, c) for i, s, c in rows],
    )
    conn.execute(
        "INSERT INTO audit_log (actor, action, target_type, target_id) "
        "VALUES ('t', 'quick.bootstrap', 'project', 1)"
    )
    conn.commit()
    conn.close()

    apply_schema()
    apply_schema()  # idempotent
    conn = sqlite3.connect(db)
    tiers = dict(conn.execute("SELECT slug, tier FROM projects").fetchall())
    conn.close()
    assert tiers == {"quick-one": "quick", "lean-one": "lean", "full-one": "full"}
