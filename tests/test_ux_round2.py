"""Kolo 2 cvičných projektů: status po Go, podpisy a AI náhrada, tipy bez opakování,
quick_session (tier, slug, vote validace), skloňování."""
from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from conftest import bootstrap_project, file_url

from tool.cli import checkpoint, init, quick_session, session_2, status, ux
from tool.cli.db import transaction

OWNERS = {"byznys": "Dana", "produkt": "Petr", "design": "Eva", "vyvoj": "Tomáš",
          "bezpecnost": "Lucie", "provoz": "Karel"}


def _owners(**over: str) -> dict[str, str]:
    return {**OWNERS, **over}


def _add_critical(slug: str, variant: str, who: str = "Jana") -> None:
    with transaction() as conn:
        vid = conn.execute(
            "SELECT v.id FROM variants v JOIN sessions s ON s.id = v.session_id "
            "JOIN projects p ON p.id = s.project_id WHERE p.slug = ? AND v.name = ?",
            (slug, variant)).fetchone()[0]
        conn.execute(
            "INSERT INTO feedback (variant_id, severity, department, category, score, "
            "rationale, submitted_by) VALUES (?, 'critical', 'legal', 'privacy', 0.1, "
            "'osobní údaje', ?)", (vid, who))


# ------------------------------------------------------------------ status


def test_status_after_go_critical_on_loser_is_info_and_next_is_ship(
        tmp_db: Path, bare_repo: Path, vote: Callable[..., Any]) -> None:
    bootstrap_project(slug="go2", target_repo_url=file_url(bare_repo), path_owners=_owners())
    vote("go2")
    _add_critical("go2", "B")
    session_2.record_decision(slug="go2", decision="go", winner="A", rationale="A vyhrává")
    checkpoint.sign("go2", "bezpecnost", by="Lucie", note="ok")
    checkpoint.sign("go2", "provoz", by="Karel", note="ok")
    d = status.project_detail("go2")
    assert d["next_step"] == "/pm ship go2"
    assert d["feedback"]["critical"] == 0 and d["feedback"]["critical_total"] == 1
    assert not [b for b in d["blockers"] if b["kind"] == "critical"]
    assert any("poražené variantě B" in i for i in d["info"])


def test_status_after_go_missing_signatures_names_person(
        tmp_db: Path, bare_repo: Path, vote: Callable[..., Any]) -> None:
    bootstrap_project(slug="go3", target_repo_url=file_url(bare_repo), path_owners=_owners())
    vote("go3")
    session_2.record_decision(slug="go3", decision="go", winner="A", rationale="A")
    assert status.project_detail("go3")["next_step"].startswith(
        'pflanzer checkpoint --slug go3 bezpecnost --by "Lucie"')


def test_status_build_running_after_worktree_setup(tmp_db: Path, bare_repo: Path) -> None:
    bootstrap_project(slug="bld", target_repo_url=file_url(bare_repo), path_owners=_owners())
    assert status.project_detail("bld")["phase"] == "Kickoff hotový"
    with transaction() as conn:
        pid = conn.execute("SELECT id FROM projects WHERE slug='bld'").fetchone()[0]
        from tool.cli.db import audit
        audit(conn, action="worktree.setup", target_type="project", target_id=pid, payload={})
    assert status.project_detail("bld")["phase"] == "Build běží"


def test_checkpoint_never_recommends_retro_early(tmp_db: Path, bare_repo: Path) -> None:
    """Skóre bran se plní už v Buildu — samo o sobě neznamená „Ship hotový“."""
    bootstrap_project(slug="early", target_repo_url=file_url(bare_repo), path_owners=_owners())
    with transaction() as conn:
        conn.execute("UPDATE projects SET status='handoff', gate_score_latest=90 "
                     "WHERE slug='early'")
    res = checkpoint.sign("early", "provoz", by="Karel", note="rollback")
    assert "retro" not in res["next_step"]


def test_blocked_checkpoint_shows_reason(tmp_db: Path, bare_repo: Path) -> None:
    bootstrap_project(slug="why", target_repo_url=file_url(bare_repo), path_owners=_owners())
    checkpoint.sign("why", "bezpecnost", by="Lucie", note="chybí DPA", blocked=True)
    d = status.project_detail("why")
    text = next(b["text"] for b in d["blockers"] if b["kind"] == "blocked")
    assert "BLOKOVÁNO (Lucie): chybí DPA" in text


def test_project_list_shows_same_next_step_as_detail(tmp_db: Path, bare_repo: Path) -> None:
    bootstrap_project(slug="lst", target_repo_url=file_url(bare_repo), path_owners=_owners())
    assert status.list_projects()[0]["next_step"] == status.project_detail("lst")["next_step"]


# ------------------------------------------------------------------ podpisy


def test_code_author_signing_security_is_flagged(tmp_db: Path, bare_repo: Path) -> None:
    bootstrap_project(slug="autor", target_repo_url=file_url(bare_repo),
                      path_owners=_owners(bezpecnost="AI"))
    res = checkpoint.sign("autor", "bezpecnost", by="Tomáš", note="prošel jsem to")
    assert res["status"] == "ok" and res["signed_by_role"] == "autor kódu"
    assert any("autor kódu" in w and "u pilotu dovoleno" in w and "GDPR" in w
               for w in res["warnings"])
    summary = {r["window"]: r for r in checkpoint.checkpoint_summary("autor")}
    assert summary["bezpecnost"]["signer_kind"] == "autor kódu"
    assert summary["bezpecnost"]["signed_by"] == "Tomáš"


def test_signer_kinds_representative_substitute_and_ai(tmp_db: Path, bare_repo: Path) -> None:
    bootstrap_project(slug="kinds", target_repo_url=file_url(bare_repo), path_owners=_owners())
    checkpoint.sign("kinds", "bezpecnost", by="Lucie", note="ok")
    checkpoint.sign("kinds", "provoz", by="Tomáš", note="vývojář z jádra (pilot)")
    s = {r["window"]: r for r in checkpoint.checkpoint_summary("kinds")}
    assert s["bezpecnost"]["signer_kind"] == "zástupce"
    assert s["provoz"]["signer_kind"] == "zástup"
    assert s["zadani"]["state"] != "ok" or s["zadani"]["signer_kind"]


def test_ai_draft_then_human_keeps_agent_in_summary(tmp_db: Path, bare_repo: Path) -> None:
    bootstrap_project(slug="draft", target_repo_url=file_url(bare_repo),
                      path_owners=_owners(bezpecnost="AI"))
    checkpoint.sign("draft", "bezpecnost", ai=True, agent="security-expert", note="pre-check")
    s = {r["window"]: r for r in checkpoint.checkpoint_summary("draft")}
    assert s["bezpecnost"]["signer_kind"] == "AI draft" and s["bezpecnost"]["state"] == "pending"
    checkpoint.sign("draft", "bezpecnost", by="Dana", note="přečteno")
    s = {r["window"]: r for r in checkpoint.checkpoint_summary("draft")}
    assert s["bezpecnost"]["state"] == "ok"
    assert s["bezpecnost"]["ai_agent"] == "security-expert"
    assert s["bezpecnost"]["note"] == "přečteno"


def test_decision_log_ai_draft_wording(tmp_db: Path, bare_repo: Path,
                                       monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    repo = tmp_path / "target"
    (repo / ".pflanzer").mkdir(parents=True)
    monkeypatch.chdir(repo)
    bootstrap_project(slug="log", target_repo_url=file_url(bare_repo),
                      path_owners=_owners(bezpecnost="AI"))
    checkpoint.sign("log", "bezpecnost", ai=True, agent="security-expert", note="pre-check")
    text = (repo / ".pflanzer" / "decisions" / "log.md").read_text(encoding="utf-8")
    assert "AI draft (security-expert) — čeká na podpis: „určete kdo“" in text
    assert "PENDING" not in text and "Podepsal: AI" not in text


def test_bootstrap_with_ai_security_tells_who_may_sign(tmp_db: Path, bare_repo: Path) -> None:
    out = bootstrap_project(slug="whosigns", target_repo_url=file_url(bare_repo),
                            path_owners=_owners(bezpecnost="AI"))
    msg = next(w for w in out["warnings"] if "nikdo zatím není určen" in w)
    assert "Decider (Dana)" in msg and "PdM (Petr)" in msg and "ne autor kódu (Tomáš)" in msg


def test_design_window_for_ai_design(tmp_db: Path, bare_repo: Path) -> None:
    bootstrap_project(slug="dsg", target_repo_url=file_url(bare_repo),
                      path_owners=_owners(design="AI:ux-expert"))
    rows = {c["window"]: c for c in checkpoint.list_checkpoints("dsg")}
    assert rows["design"]["state"] == "pending"
    gate = checkpoint.design_gate("dsg")
    assert gate["applies"] and not gate["blocks_ship"]              # pilot neblokuje
    d = status.project_detail("dsg")
    assert any(i.startswith("Design: AI (ux-expert) — potvrdí Petr") for i in d["info"])
    res = checkpoint.sign("dsg", "design", by="Petr", note="hlavní tok i kontrasty")
    assert res["status"] == "ok" and res["signed_by_role"] == "zástup"
    assert checkpoint.design_gate("dsg")["state"] == "ok"
    with transaction() as conn:       # žádný nový triage track
        n = conn.execute("SELECT COUNT(*) FROM triage").fetchone()[0]
    assert n == 4


def test_design_window_blocks_production_only(tmp_db: Path, bare_repo: Path) -> None:
    bootstrap_project(slug="dsgp", risk_profile="production", target_repo_url=file_url(bare_repo),
                      path_owners=_owners(design="AI"))
    assert checkpoint.design_gate("dsgp")["blocks_ship"] is True


def test_design_window_rejected_for_human_design_and_ai_flag(tmp_db: Path,
                                                             bare_repo: Path) -> None:
    bootstrap_project(slug="dh", target_repo_url=file_url(bare_repo), path_owners=_owners())
    with pytest.raises(ValueError, match="jen pro AI náhradu"):
        checkpoint.sign("dh", "design", by="Eva", note="x")
    bootstrap_project(slug="da", target_repo_url=file_url(bare_repo),
                      path_owners=_owners(design="AI"))
    with pytest.raises(ValueError, match="potvrzuje člověk"):
        checkpoint.sign("da", "design", ai=True, note="x")


# ------------------------------------------------------------------ tipy


def test_tips_for_seen_dedupes() -> None:
    seen: set[str] = set()
    first = ux.tips_for("after_go", seen=seen)
    assert first and ux.tips_for("after_go", seen=seen) == []
    assert ux.tips_for("after_go") == first          # bez seen se nic nepamatuje


def test_tips_for_project_never_repeats(tmp_db: Path, bare_repo: Path) -> None:
    bootstrap_project(slug="tips", target_repo_url=file_url(bare_repo), path_owners=_owners())
    first = ux.tips_for_project("tips", "after_vote")
    assert first
    assert ux.tips_for_project("tips", "after_vote") == []
    assert ux.tips_for_project("neexistuje", "after_vote") == ux.tips_for("after_vote")


def test_no_duplicate_or_generic_tips() -> None:
    texts = [t for items in ux.TIPS.values() for _, t in items]
    assert len(texts) == len(set(texts))
    assert sum("Max 5 lidí" in t for t in texts) == 1
    assert not any("zkontrolujte vždy před schůzkou" in t for t in texts)
    assert [p for p, items in ux.TIPS.items()
            if any("Poraženým" in t for _, t in items)] == ["after_go"]
    for phase in ("after_go", "after_critical", "after_resolve", "after_vote", "after_setup",
                  "after_ship"):
        assert ux.tips_for(phase)


# ------------------------------------------------------------------ plural


@pytest.mark.parametrize("n,expected", [(0, "0 dnů"), (1, "1 den"), (2, "2 dny"), (4, "4 dny"),
                                        (5, "5 dnů"), (11, "11 dnů"), (22, "22 dnů")])
def test_plural(n: int, expected: str) -> None:
    assert ux.plural(n, "den", "dny", "dnů") == expected


def test_plural_words() -> None:
    assert ux.plural(3, "připomínka", "připomínky", "připomínek") == "3 připomínky"
    assert ux.plural(1, "hlas", "hlasy", "hlasů") == "1 hlas"


# ------------------------------------------------------------------ quick_session


def test_tier_default_by_risk_and_explicit(tmp_db: Path, bare_repo: Path) -> None:
    url = file_url(bare_repo)
    assert bootstrap_project(slug="t-pilot", target_repo_url=url)["tier"] == "lean"
    assert bootstrap_project(slug="t-thr", risk_profile="throwaway")["tier"] == "quick"
    assert bootstrap_project(slug="t-prod", risk_profile="production",
                             target_repo_url=url)["tier"] == "lean"
    assert bootstrap_project(slug="t-live", target_repo_url=url, tier="quick")["tier"] == "quick"
    with pytest.raises(ValueError, match="tier"):
        bootstrap_project(slug="t-bad", target_repo_url=url, tier="huge")


def test_slug_max_five_words_and_name_cut() -> None:
    hook = "Rychlejší schvalování žádostí tak aby šéf viděl co je nové každý den"
    assert quick_session.slugify(hook).count("-") == 4
    long_hook = ("Chceme zrychlit schvalování žádostí o dovolenou v celé firmě. "
                 "Druhá věta už se do názvu nevejde vůbec nikdy ani omylem, protože je dlouhá.")
    name = quick_session.short_name(long_hook)
    assert name == "Chceme zrychlit schvalování žádostí o dovolenou v celé firmě"
    words = quick_session.short_name("slovo " * 40)
    assert words.endswith("…") and len(words) <= 80 and "slov…" not in words.replace("slovo…", "")


def test_name_not_cut_mid_word() -> None:
    name = quick_session.short_name("Zkrátit dobu cyklu schvalování objednávek " * 4)
    assert name.endswith("…") and len(name) <= 80
    assert name[:-1].rstrip().split()[-1] in {"Zkrátit", "dobu", "cyklu", "schvalování",
                                              "objednávek"}


def _vote_spec(**over: Any) -> dict[str, Any]:
    spec: dict[str, Any] = {
        "slug": "checkout", "facilitator": "Fanda",
        "votes": [{"name": "A", "role_preferences": [
            {"role_idx": 1, "user_value": 0.8, "rationale": "rychlé"}]}],
        "decider_call": {"shortlist": ["A"], "rationale": "A"}}
    spec.update(over)
    return spec


def test_vote_validation_messages(project: dict[str, Any]) -> None:
    bad = _vote_spec()
    bad["votes"][0]["role_preferences"][0]["user_value"] = 8
    with pytest.raises(ValueError, match="od 0 do 1"):
        quick_session.record_voting(**bad)
    no_call = _vote_spec()
    del no_call["decider_call"]
    msg = "Ve specu chybí „decider_call“ \\(shortlist, rationale\\)"
    with pytest.raises(ValueError, match=msg):
        quick_session.record_voting(**no_call)
    with pytest.raises(ValueError, match="neexistuje.*pflanzer status"):
        quick_session.record_voting(**_vote_spec(slug="nejaky-neznamy"))


def test_vote_without_url_stores_empty_string(project: dict[str, Any]) -> None:
    out = quick_session.record_voting(**_vote_spec())
    assert out["variants"][0]["prototype_url"] is None
    assert any("nemá preview URL" in w for w in out["warnings"])
    with transaction() as conn:
        assert conn.execute("SELECT prototype_url FROM variants").fetchone()[0] == ""


def test_bootstrap_reminds_to_commit_acceptance_feature(
        tmp_db: Path, bare_repo: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    repo = tmp_path / "target"
    (repo / ".pflanzer").mkdir(parents=True)
    monkeypatch.chdir(repo)
    out = bootstrap_project(slug="feat", target_repo_url=file_url(bare_repo),
                            metric="10 z 15 lidí otevře přehled do 30 dnů")
    assert "tests/acceptance/feat.feature" in out["acceptance_commit_hint"]


def test_keyboard_owner_is_dev_not_git_user(project: dict[str, Any]) -> None:
    assert quick_session.keyboard_owner(project["slug"]) is None   # fixture bez path_owners


def test_keyboard_owner_from_path_owners(tmp_db: Path, bare_repo: Path) -> None:
    bootstrap_project(slug="kbd", target_repo_url=file_url(bare_repo), path_owners=_owners())
    assert quick_session.keyboard_owner("kbd") == "Tomáš"


# ------------------------------------------------------------------ init / doctor / worktree


def test_init_python_repo_gets_python_guide_and_conditional_gitignore(tmp_path: Path) -> None:
    repo = tmp_path / "pyrepo"
    repo.mkdir()
    (repo / "pyproject.toml").write_text('[project]\nname = "x"\n', encoding="utf-8")
    from conftest import git
    git(repo, "init", "-q", "-b", "main")
    git(repo, "remote", "add", "origin", "https://github.com/acme/pyrepo.git")
    out = init.init(repo)
    assert out["ok"]
    guide = (repo / "docs" / "INTEGRATION_GUIDE.md").read_text(encoding="utf-8")
    assert "pytest" in guide and "ruff" in guide and ".venv" in guide
    # init založí .gitignore i v repu bez něj — specy pro /pm se nesmí commitnout
    assert ".pflanzer/specs/" in (repo / ".gitignore").read_text(encoding="utf-8")
    assert ".gitignore" in init.git_add_command(repo)


def test_init_node_repo_keeps_node_guide(tmp_path: Path) -> None:
    repo = tmp_path / "noderepo"
    repo.mkdir()
    (repo / "package.json").write_text(json.dumps({"name": "x", "scripts": {"test": "x"}}),
                                       encoding="utf-8")
    assert init.guide_template_for(repo) == init.TEMPLATE_PATH


def test_env_gitignore_fix_is_not_a_warning(worktree_project: dict[str, Any]) -> None:
    from tool.cli import worktree
    wt = worktree_project["worktrees"]["A"]
    rows = worktree.check_env_files(wt, fix_gitignore=True)
    env = next(r for r in rows if r["check"] == ".env* v .gitignore")
    assert env["status"] == "OK" and "přidáno" in env["detail"]
    rows = worktree.check_env_files(wt, fix_gitignore=True)
    assert next(r for r in rows if r["check"] == ".env* v .gitignore")["status"] == "OK"
