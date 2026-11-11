"""`gh pr create` / `gh pr edit`: existující draft PR, reviewer, labely, preview, Makefile."""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import Any, Callable

import pytest
from conftest import git
from test_pilot8_b import duo  # noqa: F401  (fixture: dvourepový projekt)

from tool.cli import handoff_pr, init, quality_gates, session_3, worktree
from tool.cli.db import transaction

PR_URL = "https://github.com/firma/repo/pull/12"


@pytest.fixture
def shipped(worktree_project: dict[str, Any], vote: Callable[..., Any]) -> dict[str, Any]:
    slug = worktree_project["slug"]
    wt = worktree_project["worktrees"]["A"]
    (wt / "checkout.js").write_text("export const fastCheckout = () => true;\n", encoding="utf-8")
    git(wt, "add", "checkout.js")
    git(wt, "commit", "-q", "-m", "feat: fast checkout")
    vote(slug, status="handoff")
    session_3.hardening_run(slug=slug)
    return worktree_project


def _set_owner(slug: str, owner: str) -> None:
    with transaction() as conn:
        conn.execute("UPDATE projects SET target_branch_owner = ? WHERE slug = ?", (owner, slug))


def _block(md: str) -> str:
    return md.split("## Otevři PR", 1)[1]


# --- 1. create vs. edit ---------------------------------------------------------------


def test_single_repo_without_stored_pr_uses_create(shipped: dict[str, Any]) -> None:
    md = handoff_pr.render_ship_md(shipped["slug"])
    assert "gh pr create" in md and "gh pr edit" not in md and "gh pr ready" not in md


def test_single_repo_with_stored_draft_pr_uses_edit(
        shipped: dict[str, Any], tmp_path: Path) -> None:
    slug = shipped["slug"]
    assert worktree.set_prototype_url(slug, "A", PR_URL)
    md = handoff_pr.render_ship_md(slug)
    block = _block(md)
    assert "gh pr create" not in md
    assert "| gh pr edit 12 \\" in block
    assert "--add-label" in block and "--body-file -" in block
    assert "Draft PR #12" in block
    # fixture je blokovaná (draft) -> PR zůstává draft, žádné `ready`
    assert "gh pr ready" not in block
    ship = tmp_path / "SHIP.md"
    ship.write_text(md, encoding="utf-8")
    cmd = handoff_pr.pr_create_command(ship)
    assert cmd and "gh pr edit 12" in cmd and "--pr-body" in cmd and "\n" not in cmd


def test_non_pr_prototype_url_keeps_create(shipped: dict[str, Any]) -> None:
    worktree.set_prototype_url(shipped["slug"], "A", "https://preview.example.com/abc")
    md = handoff_pr.render_ship_md(shipped["slug"])
    assert "gh pr create" in md and "gh pr edit" not in md


def test_edit_form_ready_and_create_command_joins_ready(tmp_path: Path) -> None:
    cmd = handoff_pr._publish_cmd(
        pipe="pflanzer handoff_pr --slug s --pr-body", number=12, title="feat(s): x",
        base="main", labels=["pflanzer", "ai-generated"], reviewer="octocat", draft=False,
        indent="  ")
    assert cmd.splitlines()[-1] == "gh pr ready 12"
    assert "--add-reviewer octocat" in cmd and '--add-label "ai-generated"' in cmd
    ship = tmp_path / "SHIP.md"
    ship.write_text("## Otevři PR\n\n```bash\ngit push\n" + cmd + "\n```\n", encoding="utf-8")
    one = handoff_pr.pr_create_command(ship)
    assert one and one.endswith("&& gh pr ready 12") and "gh pr edit 12" in one
    draft = handoff_pr._publish_cmd(
        pipe="pflanzer handoff_pr --slug s --pr-body", number=None, title="t", base="main",
        labels=["pflanzer"], reviewer=None, draft=True, indent="  ")
    assert "gh pr create" in draft and "--draft" in draft and "--reviewer" not in draft


def test_next_step_texts_follow_form(shipped: dict[str, Any], tmp_path: Path) -> None:
    slug = shipped["slug"]
    assert "gh pr create" in handoff_pr._human_ship_md(slug, tmp_path / "SHIP.md")["next_step"]
    worktree.set_prototype_url(slug, "A", PR_URL)
    nxt = handoff_pr._human_ship_md(slug, tmp_path / "SHIP.md")["next_step"]
    assert "gh pr edit" in nxt and "gh pr ready" in nxt
    out = {"ship_path": "~/x/SHIP.md", "production_ready": True,
           "production_readiness_target": 80, "risk_profile": "pilot",
           "triage": {"human_blockers": []}, "winner": {"local_path": None},
           "pr_command": "pflanzer handoff_pr --slug s --pr-body | gh pr edit 12 && gh pr ready 12"}
    monkey = pytest.MonkeyPatch()
    try:
        monkey.setattr(shutil, "which", lambda name: "/usr/bin/gh")
        _lines, step = session_3._ship_md_lines(out, "s", "x")
    finally:
        monkey.undo()
    assert step.startswith("Povýš existující draft PR") and "gh pr edit 12" in step


def test_multi_repo_create_form_without_stored_pr(duo: dict[str, Any]) -> None:  # noqa: F811
    session_3.hardening_run(slug="duo")
    md = handoff_pr.render_ship_md("duo")
    assert md.count("gh pr create") == 2 and "PR_WEB=$(gh pr view" not in md


def test_multi_repo_primary_with_stored_pr_uses_edit(duo: dict[str, Any]) -> None:  # noqa: F811
    session_3.hardening_run(slug="duo")
    assert worktree.set_prototype_url("duo", "A", "https://github.com/f/web/pull/7")
    md = handoff_pr.render_ship_md("duo")
    assert md.count("gh pr create") == 1                    # jen druhé repo (api) se vytváří
    assert "gh pr edit 7 \\" in md
    assert "PR_WEB=$(gh pr view 7 --json url -q .url)" in md
    assert '--related "web=$PR_WEB"' in md                  # api PR stále odkazuje na web
    assert 'gh pr edit "$PR_WEB"' in md                     # provázání zůstává


# --- 2. reviewer ------------------------------------------------------------------------


def test_reviewer_from_branch_owner_handle(shipped: dict[str, Any]) -> None:
    slug = shipped["slug"]
    _set_owner(slug, "@octocat")
    block = _block(handoff_pr.render_ship_md(slug))
    assert "--reviewer octocat" in block and "ignoruje" in block
    worktree.set_prototype_url(slug, "A", PR_URL)
    block = _block(handoff_pr.render_ship_md(slug))
    assert "--add-reviewer octocat" in block and "--reviewer octocat" not in block.replace(
        "--add-reviewer", "")


def test_reviewer_manual_when_owner_is_a_name(shipped: dict[str, Any]) -> None:
    _set_owner(shipped["slug"], "Jan Novák")
    block = _block(handoff_pr.render_ship_md(shipped["slug"]))
    assert "--reviewer octocat" not in block
    assert "Reviewera přidejte ručně (`--reviewer <github-handle>`)" in block


@pytest.mark.parametrize("value,expected", [
    ("@octocat", "octocat"), ("octocat", "octocat"), ("org/team", "org/team"),
    ("Jan Novák", None), ("<@github-handle>", None), ("", None), (None, None)])
def test_github_handle(value: Any, expected: str | None) -> None:
    assert handoff_pr.github_handle(value) == expected


# --- 3. AI provenance heading -------------------------------------------------------------


def test_pr_body_has_plain_ai_provenance_heading(shipped: dict[str, Any]) -> None:
    body = handoff_pr.build_pr(shipped["slug"])["body"]
    assert "\n## AI provenance\n" in body
    assert "<summary>AI provenance</summary>" not in body and "Původ kódu a podíl AI" not in body
    detail = handoff_pr.render_ship_detail_md(shipped["slug"])
    assert "## AI provenance" in detail and "Původ kódu a podíl AI" not in detail


# --- 6. labels --------------------------------------------------------------------------


def test_label_commands_are_shared_and_do_not_force(shipped: dict[str, Any]) -> None:
    md = handoff_pr.render_ship_md(shipped["slug"])
    assert "--force" not in md
    assert 'gh label create "ai-generated" --color D93F0B --description' in md
    assert f'gh label create "pflanzer:{shipped["slug"]}" --color 5319E7 --description' in md
    assert worktree.label_create_args("pflanzer")[:3] == ["gh", "label", "create"]
    assert "--force" not in worktree.label_create_args("pflanzer")
    assert worktree.label_create_failed(1, "", "label already exists") is False
    assert worktree.label_create_failed(1, "", "HTTP 403") is True
    assert worktree.label_create_failed(0, "", "") is False


# --- 4, 5, 6, 10. preview PR ------------------------------------------------------------


def test_preview_body_uses_real_author_and_committed_decision_log(shipped: dict[str, Any]) -> None:
    res = worktree.preview_draft_pr(shipped["slug"], run=False)
    by_variant = {r["variant"]: r for r in res}
    body_a = (worktree.PREVIEWS_DIR / shipped["slug"] / "A"
              / f"pr-body-{by_variant['A']['repo']}.md").read_text(encoding="utf-8")
    assert "Test Dev (autor posledního commitu na větvi)" in body_a
    assert "(git author commitů)" not in body_a
    assert "`.pflanzer/decisions/" in body_a and "data/sessions" not in body_a
    body_b = (worktree.PREVIEWS_DIR / shipped["slug"] / "B"
              / f"pr-body-{by_variant['B']['repo']}.md").read_text(encoding="utf-8")
    assert "(vývojář z Kickoffu)" in body_b          # B nemá commity nad base
    assert any("gh label create" in c and "--force" not in c for c in by_variant["A"]["commands"])


def test_preview_run_creates_labels_without_force_and_reports_failures(
        shipped: dict[str, Any], monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []
    real_run = worktree._run

    def fake_run(cmd: list[str], cwd: Path | None = None, timeout: int = 300,
                 env: dict[str, str] | None = None) -> tuple[int, str, str]:
        if cmd[0] == "git" and "push" in cmd:
            calls.append(cmd)
            return 0, "", ""
        if cmd[0] != "gh":
            return real_run(cmd, cwd, timeout, env)
        calls.append(cmd)
        if cmd[:3] == ["gh", "label", "create"]:
            if cmd[3] == "pflanzer":
                return 1, "", "label already exists"
            if cmd[3] == "ai-generated":
                return 1, "", "HTTP 403: forbidden"
            return 0, "", ""
        if cmd[:3] == ["gh", "pr", "create"]:
            return 0, "https://github.com/firma/repo/pull/5\n", ""
        return 0, "", ""

    monkeypatch.setattr(worktree, "_run", fake_run)
    monkeypatch.setattr(shutil, "which", lambda name: "/usr/bin/gh")
    res = worktree.preview_draft_pr(shipped["slug"], run=True)
    created = next(r for r in res if r.get("status") == "created")
    assert created["pr_url"].endswith("/pull/5")
    assert any(c[0] == "git" and "push" in c for c in calls)
    labels = [c for c in calls if c[:3] == ["gh", "label", "create"]]
    assert labels and all("--force" not in c and "--description" in c for c in labels)
    # "already exists" není chyba, 403 ano
    assert len(created["warnings"]) == 1 and "ai-generated" in created["warnings"][0]


def test_preview_cli_prints_commands_without_run(
        shipped: dict[str, Any], monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(sys, "argv", ["worktree", "preview", "--slug", shipped["slug"]])
    worktree.main()
    out = capsys.readouterr().out
    assert "dry-run" in out and "$ git -C" in out and "gh pr create --draft" in out


# --- 9. clone failure ---------------------------------------------------------------------


def test_clone_failure_is_human_message(monkeypatch: pytest.MonkeyPatch,
                                        capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(worktree, "_run",
                        lambda *a, **k: (128, "", "fatal: could not read Username"))
    with pytest.raises(worktree.GitAccessError) as exc:
        worktree._ensure_target_clone("https://github.com/firma/repo.git", "main")
    assert "gh auth setup-git" in exc.value.human()

    def boom(*a: Any, **k: Any) -> None:
        raise exc.value

    monkeypatch.setattr(worktree, "setup", boom)
    monkeypatch.setattr(sys, "argv", ["worktree", "setup", "--slug", "x"])
    with pytest.raises(SystemExit) as se:
        worktree.main()
    assert se.value.code != 0
    err = capsys.readouterr().err
    assert "gh auth setup-git" in err and "Traceback" not in err and "CHYBA" in err


# --- 7. Makefile gates --------------------------------------------------------------------

MAKEFILE = "test:\n\t@true\n\nlint:\n\t@true\n\nbuild:\n\t@true\n"


def test_gates_template_recognises_makefile_targets(tmp_path: Path) -> None:
    (tmp_path / "Makefile").write_text(MAKEFILE, encoding="utf-8")
    data = json.loads(init.render_gates_json(tmp_path)[0])
    assert data["tests"] == {"cmd": "make test"}
    assert data["lint"] == {"cmd": "make lint"} and data["build"] == {"cmd": "make build"}
    yml = init.render_gates_template(tmp_path)[0]
    assert "cmd: 'make test'" in yml


def test_gates_template_makefile_does_not_override_node_scripts(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        json.dumps({"scripts": {"test": "node --test"}}), encoding="utf-8")
    (tmp_path / "Makefile").write_text(MAKEFILE, encoding="utf-8")
    data = json.loads(init.render_gates_json(tmp_path)[0])
    assert data["tests"] == {"cmd": "npm test"}                 # skript má přednost
    assert data["lint"] == {"cmd": "make lint"}                  # chybějící skript -> Makefile


def test_gates_template_python_prefers_makefile_target(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "Makefile").write_text(MAKEFILE, encoding="utf-8")
    data = json.loads(init.render_gates_json(tmp_path)[0])
    assert data["tests"] == {"cmd": "make test"} and data["build"] == {"cmd": "make build"}


@pytest.mark.skipif(shutil.which("make") is None, reason="make není na PATH")
def test_default_gate_detection_runs_make_targets(tmp_path: Path) -> None:
    (tmp_path / "Makefile").write_text(
        "test:\n\t@echo '3 passed'\n\nlint:\n\t@true\n\nbuild:\n\t@exit 3\n", encoding="utf-8")
    ctx = quality_gates._make_ctx(tmp_path)[0]
    tests = quality_gates.gate_tests(ctx)
    assert tests.status == "pass" and "make test" in tests.details and tests.metric == 3
    assert quality_gates.gate_lint(ctx).status == "pass"
    build = quality_gates.gate_build(ctx)
    assert build.status == "fail" and "make build" in build.details


def test_no_makefile_keeps_old_behaviour(tmp_path: Path) -> None:
    ctx = quality_gates._make_ctx(tmp_path)[0]
    assert quality_gates.gate_lint(ctx).status == "skipped"
    assert quality_gates.gate_tests(ctx).status == "fail"


# --- 8. provenance mismatch ----------------------------------------------------------------


def test_manual_builder_with_ai_trailer_warns(shipped: dict[str, Any]) -> None:
    wt = shipped["worktrees"]["A"]
    (wt / "x.txt").write_text("x\n", encoding="utf-8")
    git(wt, "add", "x.txt")
    git(wt, "commit", "-q", "-m", "feat: x", "-m", f"Pflanzer-Variant: {shipped['slug']}-A\n"
        "AI-Assisted: claude-code")
    prov = handoff_pr.check_provenance(slug=shipped["slug"], variant="A", builder="manual",
                                       target_branch="main", worktree=wt)
    assert prov["ai_trailer_commits"] >= 1
    assert any("builder je `manual`" in w for w in prov["warnings"])
