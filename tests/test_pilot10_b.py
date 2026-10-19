"""Pilot 10 (Záložka, Go): acceptance pro Go, production bez acceptance = NEOVĚŘENO, Make cíle,
prompt s *_test.go, gates-template bez PyYAML, Go routy, make run, Date jednou."""
from __future__ import annotations

import base64
import http.client
import http.server
import json
import shutil
import subprocess
import threading
from pathlib import Path

import pytest

from tool.cli import apprun, init, preview, quick_session
from tool.cli import quality_gates as qg

needs_go = pytest.mark.skipif(shutil.which("go") is None, reason="go není v PATH")


@pytest.fixture(autouse=True)
def _go_env(tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path_factory.mktemp("goenv")
    monkeypatch.setenv("GOCACHE", str(root / "cache"))
    monkeypatch.setenv("GOPATH", str(root / "path"))
    monkeypatch.setenv("GOFLAGS", "-mod=mod")


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", *args], cwd=cwd,
                   check=True, capture_output=True)


def go_repo(root: Path, acceptance: str | None = None, *, name: str = "tests/acceptance") -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "go.mod").write_text("module example.com/zak\n\ngo 1.21\n", encoding="utf-8")
    (root / "main.go").write_text(
        'package main\n\nimport "net/http"\n\nfunc main() {\n'
        '\thttp.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {})\n'
        '\thttp.ListenAndServe(":8080", nil)\n}\n', encoding="utf-8")
    if acceptance is not None:
        d = (root / name).parent
        d.mkdir(parents=True, exist_ok=True)
        pkg = "acceptance" if name.startswith("tests/acceptance") else "main"
        (root / name).write_text(f"package {pkg}\n\n{acceptance}", encoding="utf-8")
    return root


PASS_T = 'import "testing"\n\nfunc TestAcceptanceOk(t *testing.T) {}\n'
FAIL_T = 'import "testing"\n\nfunc TestAcceptanceBad(t *testing.T) { t.Fatal("nejde") }\n'


@needs_go
def test_go_acceptance_pass(tmp_path: Path) -> None:
    repo = go_repo(tmp_path / "r", PASS_T, name="tests/acceptance/zak_test.go")
    res = qg._go_acceptance(repo)
    assert res.status == "pass", res.details
    assert qg._gate_other_stack("acceptance", repo, "go").status == "pass"


@needs_go
def test_go_acceptance_fail(tmp_path: Path) -> None:
    repo = go_repo(tmp_path / "r", FAIL_T, name="tests/acceptance/zak_test.go")
    res = qg._go_acceptance(repo)
    assert res.status == "fail", res.details


@needs_go
def test_go_acceptance_by_name_anywhere(tmp_path: Path) -> None:
    repo = go_repo(tmp_path / "r", PASS_T, name="zak_acceptance_test.go")
    assert qg._go_acceptance(repo).status == "pass"


@needs_go
def test_go_acceptance_missing_is_unverified_with_advice(tmp_path: Path) -> None:
    repo = go_repo(tmp_path / "r")
    res = qg._go_acceptance(repo)
    assert res.status == "skipped" and res.details.startswith(qg.UNVERIFIED_PREFIX)
    assert "tests/acceptance/*_test.go" in res.details
    assert qg.acceptance_unverified(qg.unverified_gates([res]))


def test_acceptance_never_unsupported_on_other_stacks(tmp_path: Path) -> None:
    (tmp_path / "pom.xml").write_text("<project/>", encoding="utf-8")
    res = qg._gate_other_stack("acceptance", tmp_path, "maven")
    assert res.status == "skipped" and res.details.startswith(qg.UNVERIFIED_PREFIX)
    # ostatní brány bez příkazu zůstávají unsupported
    assert qg._gate_other_stack("coverage", tmp_path, "maven").status == "unsupported"


def test_go_types_is_skip_not_doplň(tmp_path: Path) -> None:
    go_repo(tmp_path)
    res = qg._gate_other_stack("types", tmp_path, "go")
    assert res.status == "skipped" and "kompilátor" in res.details
    assert "doplň" not in res.details


def test_adapter_without_acceptance_is_unverified(tmp_path: Path) -> None:
    repo = go_repo(tmp_path / "r")
    (repo / "pflanzer.gates.json").write_text(json.dumps({"build": {"cmd": "true"}}),
                                              encoding="utf-8")
    _stack, results, _score, _deps = qg.evaluate_path(repo)
    by = {r.gate_type: r for r in results}
    assert by["acceptance"].details.startswith(qg.UNVERIFIED_PREFIX)
    assert by["types"].status == "skipped"
    assert qg.acceptance_unverified(qg.unverified_gates(results))


def test_human_lines_one_per_gate() -> None:
    rows = [{"gate": "build", "status": "pass", "details": "Go: `go build` OK"},
            {"gate": "acceptance", "status": "skipped",
             "details": "NEOVĚŘENO: chybí akceptační testy — napište je"},
            {"gate": "types", "status": "skipped", "details": "SKIP: typy kontroluje kompilátor"}]
    lines = qg.human_gate_lines("summary", rows, per_gate=True)
    assert lines[0] == "summary" and len(lines) == 4
    assert lines[1].startswith("build: PASS")
    assert lines[2].startswith("acceptance: NEOVĚŘENO")
    assert lines[3].startswith("types: SKIP")


# ---- check_commands / prompt -------------------------------------------------------------


def test_check_commands_make_targets(tmp_path: Path) -> None:
    repo = go_repo(tmp_path)
    (repo / "Makefile").write_text("test:\n\tgo test ./...\nlint:\n\tgo vet ./...\n"
                                   "build:\n\tgo build ./...\nrun:\n\tgo run .\n", encoding="utf-8")
    prof = quick_session.stack_profile(repo)
    assert prof.commands == ["make test", "make lint", "make build"]
    assert prof.run_cmd == "make run"


def test_check_commands_go_without_makefile(tmp_path: Path) -> None:
    prof = quick_session.stack_profile(go_repo(tmp_path))
    assert prof.commands == ["go build ./... && go vet ./... && go test ./..."]
    assert prof.run_cmd == "go run ."


def test_prompt_go_acceptance_glob(tmp_path: Path) -> None:
    prof = quick_session.stack_profile(go_repo(tmp_path))
    text = quick_session._builder_rules("zak", "hook", "A", True, stack=prof)
    assert "tests/acceptance/*_test.go" in text and "*.test.js" not in text
    plain = quick_session.StackProfile()
    node = quick_session._builder_rules("zak", "hook", "A", True, stack=plain)
    assert "*.test.js" in node


# ---- gates-template bez PyYAML -----------------------------------------------------------


def test_gates_template_json_without_pyyaml(tmp_path: Path,
                                            monkeypatch: pytest.MonkeyPatch) -> None:
    repo = go_repo(tmp_path)
    monkeypatch.setattr(init, "_yaml_available", lambda: False)
    out = init.write_gates_template(repo)
    assert out["ok"] and out["format"] == "json" and "PyYAML" in out["note"]
    path = repo / "pflanzer.gates.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["build"]["cmd"] == "go build ./..."
    # quality_gates JSON načte i bez PyYAML
    assert qg.load_gates_adapter(path)["tests"]["cmd"] == "go test ./..."
    again = init.write_gates_template(repo)
    assert not again["ok"] and "už existuje" in again["reason"]


def test_gates_template_yaml_when_available(tmp_path: Path,
                                            monkeypatch: pytest.MonkeyPatch) -> None:
    repo = go_repo(tmp_path)
    monkeypatch.setattr(init, "_yaml_available", lambda: True)
    out = init.write_gates_template(repo)
    assert out["ok"] and out["format"] == "yaml" and (repo / "pflanzer.gates.yml").exists()


def test_integration_guide_per_stack(tmp_path: Path) -> None:
    go = go_repo(tmp_path / "go")
    assert init.guide_template_for(go) == init.GO_TEMPLATE_PATH
    assert "React" not in init.GO_TEMPLATE_PATH.read_text(encoding="utf-8")
    empty = tmp_path / "empty"
    empty.mkdir()
    assert init.guide_template_for(empty) == init.GENERIC_TEMPLATE_PATH
    node = tmp_path / "node"
    node.mkdir()
    (node / "package.json").write_text("{}", encoding="utf-8")
    assert init.guide_template_for(node) == init.TEMPLATE_PATH


# ---- Go routy, make run, Date ------------------------------------------------------------


def test_go_routes_in_added_routes(tmp_path: Path) -> None:
    repo = go_repo(tmp_path / "r")
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "base")
    _git(repo, "checkout", "-qb", "feat")
    (repo / "routes.go").write_text(
        'package main\n\nfunc routes(mux *http.ServeMux) {\n'
        '\thttp.HandleFunc("/zalozky", h)\n'
        '\tmux.HandleFunc("GET /oblibene", h)\n'
        '\tmux.Handle("/stitky/", h)\n'
        '\tmux.HandleFunc("POST /zalozky/{id}/smazat", h)\n'
        '\tmux.Handle("/static/", h)\n}\n', encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "feat")
    routes = preview._added_routes(repo)
    assert "/oblibene" in routes and "/stitky" in routes and "/zalozky" in routes
    assert not any(r.startswith("/static") for r in routes)


def test_make_run_autodetected_for_go(tmp_path: Path) -> None:
    repo = go_repo(tmp_path)
    (repo / "Makefile").write_text("run:\n\tgo run .\n", encoding="utf-8")
    spec = apprun.detect_run(repo, 8123)
    assert spec is not None and spec.command == "make run" and spec.env["PORT"] == "8123"


@needs_go
def test_go_run_fallback_without_makefile(tmp_path: Path) -> None:
    spec = apprun.detect_run(go_repo(tmp_path), 8124)
    assert spec is not None and spec.command == "go run ." and spec.env["PORT"] == "8124"


def test_proxy_forwards_date_once() -> None:
    class Backend(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a: object) -> None:
            pass

        def do_GET(self) -> None:  # noqa: N802 — send_response přidá Server i Date
            body = b"ok"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    backend = http.server.HTTPServer(("127.0.0.1", 0), Backend)
    proxy = preview._Server(("127.0.0.1", 0), preview._make_handler(backend.server_port, "pw", "A"))
    threads = [threading.Thread(target=s.serve_forever, daemon=True) for s in (backend, proxy)]
    for t in threads:
        t.start()
    try:
        conn = http.client.HTTPConnection("127.0.0.1", proxy.server_port, timeout=10)
        auth = base64.b64encode(b"pflanzer:pw").decode()
        conn.request("GET", "/", headers={"Authorization": f"Basic {auth}"})
        resp = conn.getresponse()
        resp.read()
        names = [k.lower() for k, _ in resp.getheaders()]
        conn.close()
        assert resp.status == 200
        assert names.count("date") == 1 and names.count("server") == 1
    finally:
        for s in (proxy, backend):
            s.shutdown()
            s.server_close()
