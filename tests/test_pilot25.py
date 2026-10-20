"""Pilot 25: personal_data => L3, selhané brány v Rizicích, varianta u critical, docs."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import pytest
from conftest import bootstrap_project as _bp
from conftest import file_url, git

from tool.cli import checkpoint, handoff_pr, preview, session_3
from tool.cli.db import get_connection, transaction

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _repo(bare_repo: Path) -> None:
    globals()["_URL"] = file_url(bare_repo)


def bootstrap_project(**kw: Any) -> dict[str, Any]:
    return _bp(target_repo_url=globals()["_URL"], **kw)


@pytest.fixture
def shipped(worktree_project: dict[str, Any], vote: Callable[..., Any]) -> dict[str, Any]:
    slug = worktree_project["slug"]
    wt = worktree_project["worktrees"]["A"]
    (wt / "checkout.js").write_text("export const f = () => true;\n", encoding="utf-8")
    git(wt, "add", "checkout.js")
    git(wt, "commit", "-q", "-m", "feat: fast checkout")
    vote(slug, status="handoff")
    session_3.hardening_run(slug=slug)
    return worktree_project


def _data_class(slug: str) -> str:
    conn = get_connection()
    try:
        return conn.execute("SELECT data_class FROM projects WHERE slug = ?", (slug,)).fetchone()[0]
    finally:
        conn.close()


def test_personal_data_raises_l2_to_l3_and_warns(tmp_db: Path) -> None:
    out = bootstrap_project(personal_data=True, data_class="L2", slug="pd1")
    assert _data_class("pd1") == "L3"
    assert any("L2 přepsáno na L3" in w and "aspoň L3" in w for w in out["warnings"])
    conn = get_connection()
    try:
        assert checkpoint.merged_applies(conn, out["project_id"]) is False
    finally:
        conn.close()


def test_personal_data_without_class_and_l4_kept(tmp_db: Path) -> None:
    out = bootstrap_project(personal_data=True, slug="pd2")
    assert _data_class("pd2") == "L3"
    assert not any("přepsáno" in w for w in out["warnings"])
    bootstrap_project(personal_data=True, data_class="L4", slug="pd3")
    assert _data_class("pd3") == "L4"


def test_no_personal_data_l2_stays_merged(tmp_db: Path) -> None:
    out = bootstrap_project(personal_data=False, data_class="L2", slug="pd4")
    assert _data_class("pd4") == "L2"
    assert not any("přepsáno" in w for w in out["warnings"])


def test_failed_gate_in_pr_risks_and_ship_head(shipped: dict[str, Any]) -> None:
    slug = shipped["slug"]
    with transaction() as conn:
        conn.execute("UPDATE quality_gates SET status = 'fail', details_md = 'a11y: x' "
                     "WHERE gate_type = 'a11y'")
    md = handoff_pr.render_ship_md(slug)
    assert "selhala: přístupnost" in md.split("## Skóre")[1].split("##")[0]
    assert len(md.splitlines()) <= 60
    body = handoff_pr.build_pr(slug)["body"]
    rizika = next(x for x in body.splitlines() if x.startswith("**Rizika:**"))
    assert "selhala: přístupnost" in rizika


def test_pr_lead_risks_contain_failed_gates() -> None:
    lead = handoff_pr._pr_lead(
        hook="h", winner="A", open_crit=0, open_remarks=0, open_conditions=0, failures=3,
        override=None, overridden=False, unverified=[], blocked_by=[], metric=None,
        failed_gates=[("a11y", 3)])
    rizika = next(x for x in lead if x.startswith("**Rizika:**"))
    assert "1 brána selhala: přístupnost (3 nálezy)" in rizika


def test_preview_personal_data_warning_text(tmp_db: Path) -> None:
    bootstrap_project(personal_data=True, slug="pd5")
    bootstrap_project(personal_data=False, slug="pd6")
    assert preview.has_personal_data("pd5") is True
    assert preview.has_personal_data("pd6") is False
    w = preview.PERSONAL_DATA_NET_WARNING
    assert "HTTP bez šifrování" in w and "testovací data" in w and "--tunnel cloudflared" in w


def test_docs_and_templates() -> None:
    tpl = (ROOT / "tool/templates/INTEGRATION_GUIDE.python.md.template").read_text("utf-8")
    assert "python-multipart" in tpl and "httpx" in tpl and "pythonpath = ." in tpl
    faq = (ROOT / "docs/faq.md").read_text("utf-8")
    assert "## API hubu" in faq and "/api/projects/<slug>/missing" in faq
    assert "/votes" in faq and "HTTP Basic" in faq
    assert "aspoň L3" in (ROOT / "docs/zacni.md").read_text("utf-8")
    from tool.cli import quick_session
    assert "L3" in quick_session.BOOTSTRAP_EPILOG and "přepíše" in quick_session.BOOTSTRAP_EPILOG


def test_checkpoint_critical_warning_names_variant(project: dict[str, Any],
                                                   vote: Callable[..., Any]) -> None:
    from tests.test_pilot18 import _add
    from tool.cli import session_2
    slug = project["slug"]
    vote(slug)
    _add(slug, "B", "critical", "Přehled je veřejný", dept="Bezpečnost & právo", by="Jana")
    res = checkpoint.sign(slug, "bezpecnost", by="Karel", note="ověřeno")
    txt = " ".join(res["warnings"])
    assert "Otevřené „Kritické“ od Jana na variantě B" in txt
    session_2.record_decision(slug=slug, decision="go", winner="A", rationale="A je rychlejší")
    res = checkpoint.sign(slug, "bezpecnost", by="Karel", note="znovu")
    txt = " ".join(res["warnings"])
    assert "na poražené variantě B — Ship vítěze neblokuje" in txt
