"""Checkpointy (v0.5): okna zástupců podepisují triage tracky pro Ship gate."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from conftest import bootstrap_project, file_url

from tool.cli import checkpoint
from tool.cli.db import transaction
from tool.cli.triage import ship_triage_gate

OWNERS = {"byznys": "Dana", "produkt": "Petr", "design": "Eva", "vyvoj": "Tomáš",
          "bezpecnost": "Lucie", "provoz": "Karel"}


def _gate(slug: str) -> dict[str, Any]:
    with transaction() as conn:
        pid = conn.execute("SELECT id FROM projects WHERE slug = ?", (slug,)).fetchone()[0]
        return ship_triage_gate(conn, int(pid))


def test_fresh_pilot_is_blocked_by_deferred_triage(project: dict[str, Any]) -> None:
    assert len(_gate(project["slug"])["blocked_by"]) == 4


def test_windows_sign_all_tracks(tmp_db: Path, bare_repo: Path) -> None:
    bootstrap_project(slug="okna", target_repo_url=file_url(bare_repo),
                      metric="konverze +5 %", kill_criteria="bez liftu po 2 týdnech",
                      path_owners=OWNERS)
    # Kickoff se zadáním podepíše discovery sám.
    assert [b for b in _gate("okna")["blocked_by"] if "discovery" in b] == []

    checkpoint.sign("okna", "bezpecnost", by="Lucie", note="syntetická data, egress jen API")
    checkpoint.sign("okna", "provoz", by="Karel", note="monitoring + rollback OK")
    assert _gate("okna")["blocked_by"] == []
    states = {r["window"]: r["state"] for r in checkpoint.list_checkpoints("okna")}
    assert states == {"zadani": "ok", "bezpecnost": "ok", "provoz": "ok"}


def test_blocked_window_keeps_ship_blocked(project: dict[str, Any]) -> None:
    slug = project["slug"]
    checkpoint.sign(slug, "provoz", by="Karel", note="chybí monitoring", blocked=True)
    assert any("platform" in b for b in _gate(slug)["blocked_by"])


@pytest.mark.parametrize("kw", [{"by": "", "note": "x"}, {"by": "Lucie", "note": ""}])
def test_sign_requires_name_and_note(project: dict[str, Any], kw: dict[str, str]) -> None:
    with pytest.raises(ValueError):
        checkpoint.sign(project["slug"], "bezpecnost", **kw)


def test_unknown_window_rejected(project: dict[str, Any]) -> None:
    with pytest.raises(ValueError, match="Neznámé okno"):
        checkpoint.sign(project["slug"], "marketing", by="X", note="y")
