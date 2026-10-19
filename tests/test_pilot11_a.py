"""Pilot 11 (Kvítek, Next.js) — trasy z app/**/page.tsx, build .next, acceptance přes node,
preview down --variants, port hubu z hub.json."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from tool.cli import apprun, preview, quality_gates, quick_session


def _git(cwd: Path, *a: str) -> None:
    subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True)


def _next_repo(tmp_path: Path, new_files: list[str]) -> Path:
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "config", "user.email", "t@t.cz")
    _git(tmp_path, "config", "user.name", "T")
    (tmp_path / "package.json").write_text(json.dumps({
        "name": "kvitek", "dependencies": {"next": "15.5.9", "react": "19"},
        "scripts": {"dev": "next dev", "build": "next build"}}), encoding="utf-8")
    (tmp_path / "src" / "app").mkdir(parents=True)
    (tmp_path / "src" / "app" / "page.tsx").write_text("export default () => null\n")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-qm", "base")
    _git(tmp_path, "checkout", "-qb", "feat")
    for f in new_files:
        p = tmp_path / f
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("export default () => null\n")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-qm", "feat")
    return tmp_path


def test_is_nextjs(tmp_path: Path) -> None:
    assert not apprun.is_nextjs(tmp_path)
    (tmp_path / "next.config.mjs").write_text("export default {}")
    assert apprun.is_nextjs(tmp_path)


def test_next_added_routes_only_from_page_files(tmp_path: Path) -> None:
    wt = _next_repo(tmp_path, [
        "src/features/kvitek/Banner.tsx",
        "src/components/Hero.tsx",
        "src/app/(shop)/kvetiny/page.tsx",
        "src/app/kvetiny/[id]/page.tsx",
        "src/app/api/ping/route.ts",
        "src/app/layout.tsx",
    ])
    routes = preview._added_routes(wt)
    assert routes == ["/kvetiny", "/kvetiny/[id]"]
    assert "/banner" not in routes


def test_next_pages_router_routes() -> None:
    assert preview.next_route_for("pages/o-nas.tsx") == "/o-nas"
    assert preview.next_route_for("src/pages/blog/index.tsx") == "/blog"
    assert preview.next_route_for("pages/_app.tsx") is None
    assert preview.next_route_for("pages/api/x.ts") is None
    assert preview.next_route_for("src/modules/x/Panel.tsx") is None


def test_dynamic_route_counts_as_linked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    wt = _next_repo(tmp_path, ["src/app/kvetiny/[id]/page.tsx"])
    monkeypatch.setattr(apprun, "http_fetch", lambda *a, **k: (
        200, "<a href='/kvetiny/ruze'>Růže</a>", "text/html"))
    assert preview.check_reachable("A", wt, 1) is None


class _Ctx:
    def __init__(self, path: Path, **stack: Any) -> None:
        self.path = path
        base = {"node": True, "python": False, "other": None, "deps": {}, "scripts": {},
                "workspaces": []}
        self.stack = type("S", (), {**base, **stack})()


def test_next_build_reports_next_dir_size_without_cache(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "package.json").write_text('{"dependencies": {"next": "15"}}')
    nxt = tmp_path / ".next"
    (nxt / "cache").mkdir(parents=True)
    (nxt / "server").mkdir()
    (nxt / "server" / "a.js").write_bytes(b"x" * 4096)
    (nxt / "cache" / "big").write_bytes(b"x" * 100_000)
    monkeypatch.setattr(quality_gates, "_run", lambda *a, **k: (0, "", ""))
    monkeypatch.setattr(quality_gates, "_needs_deps", lambda *a, **k: None)
    monkeypatch.setattr(quality_gates, "_has", lambda *a, **k: True)
    monkeypatch.setattr(preview, "restart_for_worktree",
                        lambda p: "preview varianty A restartováno")
    res = quality_gates.gate_build(_Ctx(tmp_path, scripts={"build": "next build"}))  # type: ignore[arg-type]
    assert res.status == "pass"
    assert res.metric == 4 and "4 KB" in res.details and "restartováno" in res.details


def test_acceptance_uses_npm_test_when_it_covers_acceptance(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    acc = tmp_path / "tests" / "acceptance"
    acc.mkdir(parents=True)
    (acc / "a.test.ts").write_text("// x")
    calls: list[list[str]] = []

    def fake_run(cmd: list[str], *a: Any, **k: Any) -> tuple[int, str, str]:
        calls.append(cmd)
        return 0, "ℹ tests 3\nℹ pass 3\nℹ fail 0\n", ""
    monkeypatch.setattr(quality_gates, "_run", fake_run)
    monkeypatch.setattr(quality_gates, "_has", lambda *a, **k: True)
    ctx = _Ctx(tmp_path, scripts={
        "test": "node --test --experimental-strip-types tests/acceptance/*.test.ts"})
    res = quality_gates._native_acceptance(ctx, acc)  # type: ignore[arg-type]
    assert calls[0][:2] == ["npm", "test"]
    assert res is not None and res.status == "pass" and "3/3" in res.details


def test_acceptance_ts_runs_node_with_strip_types(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    acc = tmp_path / "tests" / "acceptance"
    acc.mkdir(parents=True)
    (acc / "a.test.ts").write_text(
        "import test from 'node:test';\nimport assert from 'node:assert';\n"
        "test('ok', () => { const x: number = 1; assert.equal(x, 1); });\n")
    monkeypatch.setattr(quality_gates, "_node_strip_flag",
                        lambda node: "--experimental-strip-types")
    ctx = _Ctx(tmp_path, scripts={"test": "node --test test/*.test.ts"})
    res = quality_gates._native_acceptance(ctx, acc)  # type: ignore[arg-type]
    assert res is not None and res.status == "pass", res


def test_acceptance_ts_old_node_is_unverified(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    acc = tmp_path / "tests" / "acceptance"
    acc.mkdir(parents=True)
    (acc / "a.test.ts").write_text("// x")
    monkeypatch.setattr(quality_gates, "_node_strip_flag", lambda node: None)
    res = quality_gates._native_acceptance(_Ctx(tmp_path), acc)  # type: ignore[arg-type]
    assert res is not None and res.details.startswith("NEOVĚŘENO")


def test_prompt_next_stack_label_and_rules(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(json.dumps({
        "dependencies": {"next": "15", "react": "19"}, "devDependencies": {"typescript": "5"},
        "scripts": {"dev": "next dev", "build": "next build",
                    "test": "node --test test/*.test.ts"}}))
    (tmp_path / "tsconfig.json").write_text("{}")
    (tmp_path / "src" / "app").mkdir(parents=True)
    prof = quick_session.stack_profile(tmp_path)
    assert prof.label == "Next.js (App Router, TS)"
    assert prof.acceptance_glob == "tests/acceptance/*.test.ts"
    rules = quick_session._builder_rules("kv", "hook", "A", True, stack=prof)
    assert "Next.js (App Router, TS)" in rules
    assert "pflanzer preview restart --slug kv --variants A" in rules
    assert "devIndicators: false" in rules
    assert "*.test.ts" in rules


def _state(slug: str, running: bool = False) -> dict[str, Any]:
    return {"slug": slug, "password": "p", "user": "pflanzer", "host": "127.0.0.1",
            "variants": {n: {"worktree": "/x", "app_port": 1, "proxy_port": 2}
                         for n in ("A", "B", "C")}}


def test_preview_down_variants_keeps_the_rest(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from tool.cli import db
    monkeypatch.setattr(db, "DATA_ROOT", tmp_path)
    preview.save_state("s", _state("s"))
    res = preview.down("s", variants=["C"])
    assert res["slug"] == "s"
    left = preview.load_state("s")
    assert left and set(left["variants"]) == {"A", "B"}
    with pytest.raises(ValueError):
        preview.down("s", variants=["Z"])
    preview.down("s")
    assert preview.load_state("s") is None


def test_restart_defaults_to_variants_in_play_and_hints_dropped(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from tool.cli import db
    monkeypatch.setattr(db, "DATA_ROOT", tmp_path)
    monkeypatch.setattr(preview, "in_play", lambda slug: ["A", "B"])
    monkeypatch.setattr(preview, "_variant_running", lambda v: {"app": True})
    monkeypatch.setattr(preview, "_alive", lambda pid, started: True)
    monkeypatch.setattr(preview, "_wait_port_free", lambda port: True)
    monkeypatch.setattr(apprun, "kill_group", lambda *a, **k: None)
    monkeypatch.setattr(apprun, "proc_started", lambda pid: "t")
    monkeypatch.setattr(apprun, "wait_http", lambda *a, **k: (True, 200))
    started: list[int] = []

    def fake_detect(wt: Path, port: int, *a: Any, **k: Any) -> apprun.RunSpec:
        started.append(port)
        return apprun.RunSpec("x", ["x"], {}, wt, "t")

    class _P:
        pid = 4242

    monkeypatch.setattr(apprun, "detect_run", fake_detect)
    monkeypatch.setattr(apprun, "start_app", lambda *a, **k: _P())
    st = _state("s")
    for i, v in enumerate(st["variants"].values()):
        v.update(app_port=1000 + i, proxy_port=2000 + i, worktree=str(tmp_path),
                 log=str(tmp_path / f"l{i}.log"), proxy_pid=1, proxy_started="t")
    preview.save_state("s", st)
    res = preview.restart("s")
    assert started == [1000, 1001]  # A, B; C vypadla ze hry
    assert res["restarted"] == ["A", "B"]
    assert any("preview down --slug s --variants C" in w for w in res["warnings"])
    started.clear()
    assert preview.restart("s", variants=["C"])["restarted"] == ["C"]  # explicitní vyhrává


def test_hub_urls_read_port_from_hub_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from tool.cli import db
    monkeypatch.setattr(db, "DATA_ROOT", tmp_path)
    assert preview.hub_urls() == (preview.HUB_HEALTH_URL, preview.HUB_URL)
    (tmp_path / "hub.json").write_text(json.dumps({"port": 8123, "url": "http://localhost:8123"}))
    health, url = preview.hub_urls()
    assert health == "http://localhost:8123/api/health"
    assert url == "http://localhost:8123/method/"
    (tmp_path / "hub.json").write_text("not json")
    assert preview.hub_urls() == (preview.HUB_HEALTH_URL, preview.HUB_URL)
