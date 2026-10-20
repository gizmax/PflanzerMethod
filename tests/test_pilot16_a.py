"""Pilot 16 (Úsměv, TS + Express) — brány pro tsx, adaptér z base, zpráva pro kolegy, hub tunel."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

from tests.conftest import git
from tool.cli import (
    doctor,
    extract,
    hub,
    init,
    preview,
    worktree,
)
from tool.cli import quality_gates as qg


def _ts_project(tmp_path: Path, script: str, dev: dict[str, str] | None = None,
                ext: str = "ts") -> Path:
    (tmp_path / "tests" / "acceptance").mkdir(parents=True)
    (tmp_path / "tests" / "acceptance" / f"a.test.{ext}").write_text("// t\n")
    (tmp_path / "package.json").write_text(json.dumps(
        {"name": "x", "scripts": {"test": script}, "devDependencies": dev or {}}))
    return tmp_path


def _ctx(path: Path) -> qg.Ctx:
    return qg.Ctx(path=path, stack=qg.detect_stack_info(path), deps_ok=True, deps_reason="")


@pytest.mark.parametrize("script,expected", [
    ("tsx --test tests/**/*.test.ts", ["npx", "--no-install", "tsx"]),
    ("npx tsx --test tests/*.test.ts", ["npx", "--no-install", "tsx"]),
    ("node --import tsx --test tests/*.test.ts", ["NODE", "--import", "tsx"]),
    ("node --loader ts-node/esm --test x.ts", ["NODE", "--loader", "ts-node/esm"]),
    ("node --test tests/*.test.js", None),
    ("vitest run", None),
])
def test_ts_runner_detection(script: str, expected: list[str] | None) -> None:
    got = qg._ts_test_runner(script, "NODE")
    assert got == expected


def test_acceptance_uses_tsx_runner_not_bare_node(tmp_path: Path,
                                                  monkeypatch: pytest.MonkeyPatch) -> None:
    proj = _ts_project(tmp_path, "tsx --test tests/**/*.test.ts", {"tsx": "^4"})
    seen: list[Any] = []

    def fake_run(cmd: Any, cwd: Path, timeout: int = 120) -> tuple[int, str, str]:
        seen.append(cmd)
        return 0, "# pass 3\n# fail 0\n", ""

    monkeypatch.setattr(qg, "_run", fake_run)
    res = qg.gate_acceptance(_ctx(proj))
    assert res.status == "pass"
    assert seen[0][:4] == ["npx", "--no-install", "tsx", "--test"]
    assert seen[0][4] == "tests/acceptance/a.test.ts"


def test_module_not_found_is_unverified_with_adapter_advice(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    proj = _ts_project(tmp_path, "node --test tests/*.test.js", ext="js")
    monkeypatch.setattr(qg, "_run", lambda *a, **k: (
        1, "", "Error [ERR_MODULE_NOT_FOUND]: Cannot find module './x.js'"))
    res = qg.gate_acceptance(_ctx(proj))
    assert res.status == "skipped" and res.details.startswith(qg.UNVERIFIED_PREFIX)
    assert "pflanzer.gates.json" in res.details and "tsx --test" in res.details


def test_real_failure_is_still_fail(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    proj = _ts_project(tmp_path, "node --test tests/*.test.js", ext="js")
    monkeypatch.setattr(qg, "_run", lambda *a, **k: (1, "# pass 0\n# fail 4\n", "assertion"))
    assert qg.gate_acceptance(_ctx(proj)).status == "fail"


def test_gates_template_uses_tsx_when_declared(tmp_path: Path) -> None:
    _ts_project(tmp_path, "tsx --test tests/**/*.test.ts", {"tsx": "^4"})
    text, _stack = init.render_gates_json(tmp_path)
    assert json.loads(text)["acceptance"]["cmd"] == \
        "npx --no-install tsx --test tests/acceptance/*.test.*"
    (tmp_path / "package.json").write_text(json.dumps({"scripts": {"test": "node --test"}}))
    text, _ = init.render_gates_json(tmp_path)
    assert json.loads(text)["acceptance"]["cmd"].startswith("node --test")


def test_adapter_created_in_base_after_branch_is_info(tmp_path: Path) -> None:
    repo = tmp_path / "r"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    (repo / "a.txt").write_text("1")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "init")
    git(repo, "checkout", "-q", "-b", "variant")
    git(repo, "checkout", "-q", "main")
    (repo / "pflanzer.gates.json").write_text("{}")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "adapter")
    git(repo, "checkout", "-q", "variant")
    out = extract.base_gates_adapter(repo, "main")
    try:
        assert out["adapter_path"] is not None and out["warnings"] == []
        assert any("merge main" in i for i in out["infos"])
    finally:
        import shutil
        shutil.rmtree(out["tmp_dir"], ignore_errors=True)


def test_adapter_deleted_by_branch_still_warns(tmp_path: Path) -> None:
    repo = tmp_path / "r"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    (repo / "pflanzer.gates.json").write_text("{}")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "init")
    git(repo, "checkout", "-q", "-b", "variant")
    git(repo, "rm", "-q", "pflanzer.gates.json")
    git(repo, "commit", "-qm", "rm")
    git(repo, "branch", "base", "HEAD~1")  # base = stav s adaptérem, větev ho smazala
    out = extract.base_gates_adapter(repo, "base")
    try:
        assert any("smazán" in w for w in out["warnings"]) and not out["infos"]
    finally:
        import shutil
        shutil.rmtree(out["tmp_dir"], ignore_errors=True)


def _res(host: str = "127.0.0.1", tunnel: bool = False) -> dict[str, Any]:
    v: dict[str, Any] = {"url": "https://t.trycloudflare.com/" if tunnel else "http://x/"}
    if tunnel:
        v["tunnel_url"] = v["url"]
    return {"variants": {"A": v}, "password": "p", "user": "pflanzer", "host": host}


def test_share_message_has_no_cli_commands() -> None:
    for hub_url in (None, "https://h.trycloudflare.com/method/"):
        msg = preview.share_message(_res(), hub_url, "Jana Nováková")
        assert "pflanzer " not in msg and "`" not in msg
        assert "Jana Nováková" in msg
    assert "https://h.trycloudflare.com/method/" in msg
    assert "hub" not in preview.share_message(_res(), None, "Jana").lower().replace("hubu", "")


def test_shareable_hub_url_matches_reach(monkeypatch: pytest.MonkeyPatch) -> None:
    data = {"port": 8000, "url": "http://127.0.0.1:8000/method/",
            "lan_url": "http://10.0.0.5:8000/method/",
            "public_url": "https://h.trycloudflare.com/method/"}
    monkeypatch.setattr(preview, "hub_data", lambda: data)
    assert preview.shareable_hub_url(_res(tunnel=True)) == data["public_url"]
    assert preview.shareable_hub_url(_res(host="0.0.0.0")) == data["lan_url"]
    assert preview.shareable_hub_url(_res()) is None
    monkeypatch.setattr(preview, "hub_data", lambda: {"port": 8000})
    assert preview.shareable_hub_url(_res(tunnel=True)) is None


def test_hub_json_and_tunnel_arg(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                 capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(hub, "DATA_ROOT", tmp_path)
    hub.write_hub_json(8123, "0.0.0.0", "https://h.trycloudflare.com", lan="10.0.0.5")
    data = json.loads((tmp_path / "hub.json").read_text())
    assert data["public_url"] == "https://h.trycloudflare.com/method/"
    assert data["lan_url"] == "http://10.0.0.5:8123/method/"
    assert data["url"] == "http://127.0.0.1:8123/method/" and "password" not in json.dumps(data)
    # tunel vynutí heslo i na localhostu
    env, notes = hub.plan_auth("127.0.0.1", None, {}, shared=True)
    assert env.get("PFLANZER_HUB_PASSWORD") and any("eslo" in n for n in notes)
    assert "PFLANZER_HUB_PASSWORD" not in hub.plan_auth("127.0.0.1", None, {})[0]
    # auto bez cloudflared = bez tunelu; cloudflared bez binárky = chyba
    monkeypatch.setattr(hub.shutil, "which", lambda _n: None)
    assert hub.resolve_tunnel("auto") is False and hub.resolve_tunnel("none") is False
    monkeypatch.setattr(sys, "argv", ["pflanzer hub", "--tunnel", "cloudflared"])
    with pytest.raises(SystemExit) as e:
        hub.main()
    assert e.value.code == 2 and "cloudflared" in capsys.readouterr().err
    monkeypatch.setattr(hub.shutil, "which", lambda _n: "/bin/cloudflared")
    assert hub.resolve_tunnel("auto") is True


def test_vote_hint_says_catalog_number() -> None:
    assert "pořadí role z Kickoffu" not in worktree.VOTE_HINT
    assert "katalog" in worktree.VOTE_HINT


def test_doctor_after_kickoff_reports_next_step(tmp_path: Path, tmp_db: Path) -> None:
    from tool.cli.db import transaction
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "remote", "add", "origin", "https://github.com/acme/web.git")
    assert doctor.existing_project(repo) is None
    with transaction() as conn:
        conn.execute("INSERT INTO projects (slug, name, status, target_repo_url) "
                     "VALUES ('web', 'Web', 'session_1', 'git@github.com:acme/web.git')")
    proj = doctor.existing_project(repo)
    assert proj is not None and proj["slug"] == "web"
    title, _lines, nxt, _w, _t = doctor._human(repo, [])
    assert title.startswith("Kickoff hotový") and "další krok" in title and nxt
