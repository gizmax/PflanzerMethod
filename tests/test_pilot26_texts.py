"""Pilot 26: data_class bez osobních dat, Provoz u ostrého, zdroj kapacity, termín, --by."""
from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

from conftest import bootstrap_project, file_url

from tool.cli import charter, preview, report, share
from tool.cli.db import transaction

ROOT = Path(__file__).resolve().parent.parent


def _dc(slug: str) -> str:
    with transaction() as conn:
        return conn.execute("SELECT data_class FROM projects WHERE slug = ?", (slug,)).fetchone()[0]


def test_explicit_no_personal_data_is_l2_even_for_production(tmp_db: Path, bare_repo: Path) -> None:
    bootstrap_project(risk_profile="production", personal_data=False,
                      target_repo_url=file_url(bare_repo),
                      slug="p26a")
    assert _dc("p26a") == "L2"
    assert preview.has_personal_data("p26a") is False


def test_defaults_and_personal_data_unchanged(tmp_db: Path, bare_repo: Path) -> None:
    bootstrap_project(risk_profile="production", target_repo_url=file_url(bare_repo),
                      slug="p26b")
    assert _dc("p26b") == "L3"
    bootstrap_project(risk_profile="pilot", personal_data=True, target_repo_url=file_url(bare_repo),
                      slug="p26c")
    assert _dc("p26c") == "L3"


def test_net_warning_speaks_of_sensitive_class() -> None:
    w = preview.PERSONAL_DATA_NET_WARNING
    assert w.startswith("Projekt má citlivou třídu dat (L3+)")


OWNERS = {"byznys": "Dana Deciderová", "produkt": "Petr Produkt", "design": "Eva Design",
          "vyvoj": "Tomáš Vývoj", "bezpecnost": "Jana Bezpečná", "provoz": "AI"}


def _provoz_warnings(profile: str, signers: dict[str, str] | None) -> list[str]:
    _, warns = charter.validate_ai_stand_ins(OWNERS, risk_profile=profile, tier="lean",
                                             ai_signers=signers)
    return [w for w in warns if w.startswith(("Provoz", "Ostré"))]


def test_production_provoz_warning_text_and_named_signer_silent() -> None:
    w = _provoz_warnings("production", None)
    assert any("Ostré nasazení: okno Provoz podepisuje člověk z provozu" in x
               and "jen u pilotu" in x for x in w)
    assert not any("Ostré" in x for x in _provoz_warnings("production", {"provoz": "Karel Provoz"}))


def test_pilot_keeps_core_developer_hint() -> None:
    assert any("vývojář z jádra stačí u pilotu" in x for x in _provoz_warnings("pilot", None))


def test_report_capacity_note_names_source() -> None:
    assert report._capacity_note("lean", 85) == "plán z Kickoffu pro Lean · ostré"
    assert report._capacity_note("lean", 80).endswith("· pilot")


def test_share_message_has_computed_deadline(
        tmp_db: Path, bare_repo: Path, monkeypatch: Any) -> None:
    bootstrap_project(target_repo_url=file_url(bare_repo),
                      slug="p26d")
    monkeypatch.setattr(preview, "_today", lambda: dt.date(2026, 10, 19))  # pondělí
    d = preview.default_deadline("p26d")           # lean 3–5 dní -> 5 pracovních dnů
    assert d == "pondělí 26. 10."
    msg = share.share_text("http://h", None, "p26d")
    assert "[doplňte" not in msg and "pondělí 26. 10." in msg
    assert "Do kdy: pátek 17:00" in share.share_text("http://h", "pátek 17:00", "p26d")
    res = {"variants": {"A": {"url": "http://a"}}, "user": "u", "password": "p",
           "slug": "p26d", "deadline": None}
    assert "[doplňte" not in preview.share_message(res, None)


def test_hints_use_by_and_docs_mention_deadline() -> None:
    src = (ROOT / "tool/cli/feedback_pull.py").read_text("utf-8")
    assert "--author" not in src
    zacni = (ROOT / "docs/zacni.md").read_text("utf-8")
    assert "--deadline" in zacni and "feedback_pull" in zacni
    assert len(zacni.splitlines()) <= 170
    assert "feedback_pull" in (ROOT / "tool/bin/pflanzer").read_text("utf-8")
