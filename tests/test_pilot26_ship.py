"""Pilot 26 (Go, production): adaptér s acceptance, nativní fallback, git add, text blokace."""
from __future__ import annotations

import json
from pathlib import Path

from tool.cli import init, session_3
from tool.cli import quality_gates as qg


def _go_repo(tmp_path: Path) -> Path:
    (tmp_path / "go.mod").write_text("module x\n\ngo 1.22\n")
    (tmp_path / "tests" / "acceptance").mkdir(parents=True)
    return tmp_path


def test_go_template_has_active_acceptance_even_without_tests(tmp_path: Path) -> None:
    repo = _go_repo(tmp_path)
    res = init.write_gates_template(repo, force=True, fmt="json")
    assert res["ok"]
    data = json.loads((repo / "pflanzer.gates.json").read_text())
    assert data["acceptance"]["cmd"] == "go test -v ./tests/acceptance/..."
    text, _ = init.render_gates_template(repo)
    assert any(line.startswith("acceptance:") for line in text.splitlines())


def test_adapter_without_acceptance_uses_native_go(tmp_path: Path, monkeypatch) -> None:
    repo = _go_repo(tmp_path)
    (repo / "pflanzer.gates.json").write_text(json.dumps({"build": {"cmd": "true"}}))
    called: list[Path] = []

    def fake(path: Path) -> qg.GateResult:
        called.append(path)
        return qg.GateResult("acceptance", "pass", "native")

    monkeypatch.setattr(qg, "_go_acceptance", fake)
    results = {r.gate_type: r for r in qg.run_gates_on_path(repo)}
    assert called and results["acceptance"].details == "native"


def test_adapter_can_still_disable_acceptance_explicitly(tmp_path: Path, monkeypatch) -> None:
    repo = _go_repo(tmp_path)
    (repo / "pflanzer.gates.json").write_text(json.dumps({"build": {"cmd": "true"},
                                                          "acceptance": False}))
    monkeypatch.setattr(qg, "_go_acceptance", lambda p: qg.GateResult("acceptance", "pass", "x"))
    results = {r.gate_type: r for r in qg.run_gates_on_path(repo)}
    assert results["acceptance"].details != "x"


def test_git_add_includes_adapter_and_github(tmp_path: Path) -> None:
    (tmp_path / "pflanzer.gates.json").write_text("{}")
    (tmp_path / ".github").mkdir()
    cmd = init.git_add_command(tmp_path)
    assert "pflanzer.gates.json" in cmd and ".github" in cmd
    assert "pflanzer.gates" not in init.git_add_command()
    assert "egg-info" not in cmd


def test_block_reasons_text() -> None:
    assert session_3._block_reasons(["gates:acceptance-neověřeno"]) == \
        "akceptační testy neověřené (production vyžaduje)"
