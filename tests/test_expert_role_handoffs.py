"""Role handoffy: čeština bez žargonu, akční sekce nahoře, zdroj a čas v patičce."""
from __future__ import annotations

from typing import Any

import pytest

from tool.cli import handoff

ROLES = ["be", "fe", "qa", "platform", "data", "support", "compliance"]
PROJECT = (1, "Úsměv", "usmev", "handoff", "Zadání", "Hypotéza", "Dana", "Petr", "minimal", "L2",
           "evolve", None, None, "objednávky", "konverze", "chyby", "méně než 5 %", None, None)


def _ctx() -> dict[str, Any]:
    return {"project_tuple": PROJECT, "triage": [], "decisions": [], "risk_profile": "production",
            "path_owners": {}, "variants": [], "extracted_by_variant": {}, "repos": [],
            "repo_gates": [], "gate_score": 85, "production_readiness_target": 80,
            "winner": None, "project_id": 1, "roles": []}


@pytest.mark.parametrize("role", ROLES)
def test_role_handoff_starts_with_actions_and_has_czech_footer(
        role: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(handoff, "_predicted_issues", lambda ctx, limit=3: [])
    md = handoff.RENDERERS[role](_ctx())
    lines = md.splitlines()
    assert lines[0].startswith("# ")
    assert lines[2] == "## Co máte udělat"
    bullets = []
    for ln in lines[3:]:
        if ln.startswith("## "):
            break
        if ln.startswith("- "):
            bullets.append(ln)
    assert 3 <= len(bullets) <= 5
    for bad in ("Given valid input z", "actionable", "Per `", "P2P"):
        assert bad not in md
    assert "Generated:" not in "\n".join(lines[:10])
    assert "Generated:" not in md
    assert lines[-1].startswith("<sub>Zdroj: ") and "Vygenerováno " in lines[-1]
    assert "02-role-catalog.md" in lines[-1]
