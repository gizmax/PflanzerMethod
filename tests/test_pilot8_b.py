"""Pilot 8 (Autoservis Píst, dvě repa web + api): Ship ověřuje KAŽDÉ repo vítěze, handoff
generuje push + PR per repo (provázané), be.md nehledá API v podsložce, a11y FAIL má důvody."""
from __future__ import annotations

import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from conftest import bootstrap_project, file_url, git, make_bare_repo, push_files, set_status

from tool.cli import a11y_html, handoff, handoff_pr, quality_gates, session_3, worktree
from tool.cli.extract import repo_blocks

WEB_ADAPTER = (
    "build: {cmd: \"true\"}\n"
    "tests: {cmd: \"true\"}\n"
    "lint: {cmd: \"true\"}\n"
    "types: {cmd: \"true\"}\n"
)


def api_adapter(*, tests_ok: bool = True) -> str:
    return (
        "build: {cmd: \"true\"}\n"
        f"tests: {{cmd: \"{'true' if tests_ok else 'false'}\"}}\n"
        "lint: {cmd: \"true\"}\n"
        "types: {cmd: \"true\"}\n"
    )


def _duo(tmp_path: Path, tmp_targets: Path, vote: Callable[..., Any], *,
         api_tests_ok: bool = True) -> dict[str, Any]:
    web = make_bare_repo(tmp_path / "repos", "autoservis-web")
    api = make_bare_repo(tmp_path / "repos", "autoservis-api",
                         {"requirements.txt": "flask\n", "src/app.py": "print('api')\n"})
    push_files(web, {"pflanzer.gates.yml": WEB_ADAPTER}, "ci: gates")
    push_files(api, {"pflanzer.gates.yml": api_adapter(tests_ok=api_tests_ok)}, "ci: gates")
    info = bootstrap_project(slug="duo", target_repos=[
        {"role": "web", "url": file_url(web)}, {"role": "api", "url": file_url(api)},
    ])
    worktree.setup("duo", install_deps=False, run_guard=False)
    wt_web, wt_api = tmp_targets / "duo-A", tmp_targets / "duo-A-api"
    assert wt_web.is_dir() and wt_api.is_dir()  # konvence názvů: <slug>-<X> a <slug>-<X>-<role>
    (wt_web / "node_modules").mkdir(exist_ok=True)
    (wt_web / "wizard.js").write_text("export const wizard = () => 3;\n", encoding="utf-8")
    git(wt_web, "add", "-A")
    git(wt_web, "commit", "-q", "-m", "feat: wizard")
    (wt_api / "src" / "orders.py").write_text("def orders():\n    return []\n", encoding="utf-8")
    git(wt_api, "add", "-A")
    git(wt_api, "commit", "-q", "-m", "feat: orders api")
    vote("duo", status="handoff")
    set_status("duo", "handoff")
    return {**info, "wt_web": wt_web, "wt_api": wt_api}


@pytest.fixture
def duo(tmp_db: Path, tmp_path: Path, tmp_targets: Path,
        vote: Callable[..., Any]) -> dict[str, Any]:
    return _duo(tmp_path, tmp_targets, vote)


@pytest.fixture
def duo_api_failing(tmp_db: Path, tmp_path: Path, tmp_targets: Path,
                    vote: Callable[..., Any]) -> dict[str, Any]:
    return _duo(tmp_path, tmp_targets, vote, api_tests_ok=False)


# --- 2. Ship ověřuje všechna repa ---------------------------------------------------------


def test_ship_runs_gates_in_every_repo(duo: dict[str, Any]) -> None:
    out = session_3.hardening_run(slug="duo")
    w = out["winner"]
    assert [r["role"] for r in w["repos"]] == ["web", "api"]
    assert all(r["gate_score"] == 100 for r in w["repos"])
    assert w["summary_line"].startswith("**Skóre 100 ze 100")
    assert "Po repech: web 100/100 · api 100/100." in w["summary_line"]
    assert w["gate_score"] == 100
    # větev i SHA jsou per repo, rozsah diffu taky
    api = w["repos"][1]
    assert api["branch"] == "pflanzer/duo-A" and api["head_sha"]
    assert api["diff"]["added"] == 2
    report = Path(out["report_path"]).read_text(encoding="utf-8")
    assert "Repo web" in report and "Repo api" in report
    assert "## Repa" in report
    # výsledky bran jsou uložené pro handoff
    saved = quality_gates.load_repo_gates("duo", "A")
    assert [r["role"] for r in saved] == ["web", "api"]


def test_fail_in_api_means_not_passed_even_with_good_average(
        duo_api_failing: dict[str, Any]) -> None:
    out = session_3.hardening_run(slug="duo")
    w = out["winner"]
    scores = {r["role"]: r["gate_score"] for r in w["repos"]}
    assert scores["web"] == 100 and scores["api"] < 80
    # vážený průměr (8 aplikovatelných bran) je nad prahem, ale FAIL tests v api to přebíjí
    assert w["gate_score"] >= 80
    assert w["gate_ready"] is False and out["production_ready"] is False
    assert "api" in w["verdict"] and "neprošlo" in w["verdict"]
    assert any("repo api" in line for line in session_3._failed_gate_lines(w["failures"]))
    assert w["failures"][0]["repo"] == "api"
    assert any("Repo api" in x for x in out["warnings"])  # průměr nesmí zakrýt slabé repo


def test_missing_second_worktree_fails_loud(duo: dict[str, Any]) -> None:
    shutil.rmtree(duo["wt_api"])
    git(duo["wt_web"], "worktree", "prune")
    out = session_3.hardening_run(slug="duo")
    err = next(e for e in out["errors"] if e["variant"] == "A")
    assert "pracovní kopie repa api" in err["error"] and "worktree setup" in err["error"]
    assert out["winner"]["variant"] != "A"  # varianta s neověřeným repem nevyhrává


def test_single_repo_project_is_unchanged(project: dict[str, Any]) -> None:
    assert repo_blocks(project["slug"], "A") == []


def test_aggregate_is_weighted_by_applicable_gates() -> None:
    agg = quality_gates.aggregate_repos([
        {"role": "web", "gate_score": 90, "applicable_gates": 9, "total_gates": 10,
         "sufficient": True},
        {"role": "api", "gate_score": 70, "applicable_gates": 3, "total_gates": 10,
         "sufficient": False, "sufficiency_blocker": "gates:insufficient (3/10 run)"},
    ])
    assert agg["gate_score"] == 85  # (90*9 + 70*3) / 12
    assert agg["sufficient"] is False and "api" in agg["blocker"]


# --- 4. Handoff: PR per repo --------------------------------------------------------------


def test_ship_md_has_push_and_pr_for_both_repos(duo: dict[str, Any]) -> None:
    session_3.hardening_run(slug="duo")
    md = handoff_pr.render_ship_md("duo")
    assert md.count("git push -u origin pflanzer/duo-A") == 2
    assert md.count("gh pr create") == 2
    assert "duo-A-api" in md and "--repo api" in md and "--repo web" in md
    assert '--related "web=$PR_WEB"' in md       # druhé PR odkazuje na první
    assert 'gh pr edit "$PR_WEB"' in md          # první PR se doplní o odkaz na druhé
    assert "Po repech: web 100/100 · api 100/100" in md
    assert "Rozsah: web:" in md and "api: +" in md
    # každý PR míří do base svého repa
    assert md.count("--base main") == 2


def test_pr_bodies_link_each_other(duo: dict[str, Any]) -> None:
    session_3.hardening_run(slug="duo")
    web_body = handoff_pr.build_pr("duo")["body"]
    assert "Související PR v api repu" in web_body
    api_body = handoff_pr.build_pr(
        "duo", repo="api", related={"web": "https://github.com/f/web/pull/7"})["body"]
    assert "Související PR v web repu: https://github.com/f/web/pull/7" in api_body
    assert "repu api" in api_body
    assert handoff_pr.build_pr("duo", repo="api")["title"].endswith("(api)")
    with pytest.raises(ValueError, match="není"):
        handoff_pr.build_pr("duo", repo="mobile")


def test_pr_body_cli_prints_second_repo(duo: dict[str, Any], monkeypatch: pytest.MonkeyPatch,
                                        capsys: pytest.CaptureFixture[str]) -> None:
    import sys

    session_3.hardening_run(slug="duo")
    monkeypatch.setattr(sys, "argv", ["handoff_pr.py", "--slug", "duo", "--pr-body",
                                      "--repo", "api", "--related", "web=https://x/pr/1"])
    handoff_pr.main()
    assert "https://x/pr/1" in capsys.readouterr().out


def test_be_md_does_not_send_you_to_subfolders(duo: dict[str, Any]) -> None:
    session_3.hardening_run(slug="duo")
    ctx = handoff._fetch_project_context("duo")
    be = handoff.render_be(ctx)
    assert "`server/` nebo `api/`" not in be
    assert "samostatném repu `api`" in be and "file://" not in be
    assert "**web**" in be and "**api**" in be and "+2 / -0 řádků v 1 souborech" in be
    fe = handoff.render_fe(ctx)
    assert "### Repa" in fe


# --- 7. a11y důvody -----------------------------------------------------------------------


def test_a11y_failure_names_concrete_reasons() -> None:
    findings = [("/", a11y_html.FAIL, msg) for _sev, msg in a11y_html.analyze(
        "<html><body><h1>Hi</h1></body></html>")]
    findings += [("/objednavka", a11y_html.FAIL, msg) for _sev, msg in a11y_html.analyze(
        "<html><body><p>x</p></body></html>")]
    details = a11y_html.summarize(findings, 2)
    assert details.splitlines()[0] == "a11y: 2 stránek zkontrolováno staticky"
    reasons = quality_gates.a11y_reasons(details)
    assert 1 <= len(reasons) <= 3
    assert any("lang" in r for r in reasons) and any("title" in r for r in reasons)

    fails = session_3._gate_failures([{"gate": "a11y", "status": "fail", "details": details}])
    line = session_3._failed_gate_lines(fails)[0]
    assert line.startswith("Selhala brána a11y: ")
    assert "lang" in line and "stránek zkontrolováno" not in line


def test_a11y_reasons_merge_same_message_across_pages() -> None:
    details = ("a11y: 3 stránek zkontrolováno staticky\n"
               "závažné · /: chybí <html lang>\nzávažné · /a: chybí <html lang>\n"
               "doporučení · /b: chybí meta viewport\n… a 4 dalších")
    assert quality_gates.a11y_reasons(details) == [
        "chybí <html lang> (2 stránky)", "/b: chybí meta viewport"]


def test_pr_failure_lines_use_a11y_reasons() -> None:
    details = "a11y: 2 stránek zkontrolováno staticky\nzávažné · /: chybí <title>"
    assert handoff_pr.failure_lines(details) == ["chybí <title>"]


def _api_repo(tmp_path: Path, routes: str) -> Path:
    repo = tmp_path / "api"
    (repo / "src").mkdir(parents=True)
    (repo / "src" / "__init__.py").write_text("", encoding="utf-8")
    (repo / "src" / "__main__.py").write_text(
        "import json, os\nfrom http.server import BaseHTTPRequestHandler, HTTPServer\n"
        "class H(BaseHTTPRequestHandler):\n"
        "    def do_GET(self):\n"
        f"        ok = self.path in {routes}\n"
        "        self.send_response(200 if ok else 404)\n"
        "        self.send_header('Content-Type', 'application/json')\n"
        "        self.end_headers()\n"
        "        self.wfile.write(json.dumps({'ok': ok}).encode())\n"
        "    def log_message(self, *a):\n        pass\n"
        "HTTPServer(('127.0.0.1', int(os.environ['PORT'])), H).serve_forever()\n",
        encoding="utf-8")
    (repo / "pyproject.toml").write_text('[project]\nname = "api"\n', encoding="utf-8")
    return repo


def test_api_repo_without_root_uses_health(tmp_path: Path) -> None:
    ctx, _, _ = quality_gates._make_ctx(_api_repo(tmp_path, "('/health', '/slots')"))
    res = quality_gates.gate_smoke(ctx)
    assert res.status == "pass" and "/health" in res.details


def test_api_repo_without_root_or_health_passes_with_hint(tmp_path: Path) -> None:
    ctx, _, _ = quality_gates._make_ctx(_api_repo(tmp_path, "('/slots',)"))
    res = quality_gates.gate_smoke(ctx)
    assert res.status == "pass" and "smoke_paths" in res.details
