"""quality_gates: adapter-driven gates, external adapter override, run_all outside the repo."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from tool.cli import quality_gates as qg
from tool.cli.db import transaction

pytest.importorskip("yaml")  # pflanzer.gates.yml needs PyYAML (CI installs it)

ADAPTER = 'build: {cmd: "true"}\ntests: {cmd: "false"}\n'


def _by_gate(results: list[qg.GateResult]) -> dict[str, str]:
    return {r.gate_type: r.status for r in results}


def test_adapter_in_tree_drives_gates(tmp_path: Path) -> None:
    (tmp_path / "pflanzer.gates.yml").write_text(ADAPTER, encoding="utf-8")
    results = qg.run_gates_on_path(tmp_path)
    status = _by_gate(results)
    assert status["build"] == "pass"
    assert status["tests"] == "fail"
    others = {g: s for g, s in status.items() if g not in ("build", "tests")}
    assert set(others) == set(qg.GATE_TYPES) - {"build", "tests"}
    assert set(others.values()) == {"unsupported"}

    agg = qg.aggregate_score(results)
    assert agg["gates_run"] == 2
    assert agg["gates_unsupported"] == len(qg.GATE_TYPES) - 2
    # build (1.5) passes, tests (2.0) fails -> 1.5 / 3.5
    assert agg["gate_score"] == round(100 * 1.5 / 3.5)


def test_external_adapter_overrides_tree_adapter(tmp_path: Path) -> None:
    tree = tmp_path / "tree"
    tree.mkdir()
    (tree / "pflanzer.gates.yml").write_text(ADAPTER, encoding="utf-8")
    external = tmp_path / "base" / "pflanzer.gates.json"
    external.parent.mkdir()
    external.write_text(json.dumps({"lint": {"cmd": "true"}, "tests": {"cmd": "true"}}),
                        encoding="utf-8")

    status = _by_gate(qg.run_gates_on_path(tree, adapter_path=external))
    assert status["tests"] == "pass"      # external wins over the tree's failing tests
    assert status["lint"] == "pass"
    assert status["build"] == "unsupported"  # tree adapter ignored entirely
    assert "external adapter" in qg.describe_gate_source(tree, external)


def test_adapter_cwd_resolves_against_checked_path(tmp_path: Path) -> None:
    tree = tmp_path / "tree"
    (tree / "sub").mkdir(parents=True)
    (tree / "sub" / "marker").touch()
    external = tmp_path / "pflanzer.gates.json"
    external.write_text(json.dumps({"build": {"cmd": "test -f marker", "cwd": "sub"}}),
                        encoding="utf-8")
    status = _by_gate(qg.run_gates_on_path(tree, adapter_path=external))
    assert status["build"] == "pass"


def _insert_extracted(local_path: Path) -> int:
    with transaction() as conn:
        conn.execute("INSERT INTO projects (slug, name, production_readiness_target) "
                      "VALUES ('gates-demo', 'Gates demo', 70)")
        pid = conn.execute("SELECT id FROM projects WHERE slug='gates-demo'").fetchone()[0]
        sid = conn.execute("INSERT INTO sessions (project_id, type) VALUES (?, 1)",
                           (pid,)).lastrowid
        vid = conn.execute(
            "INSERT INTO variants (session_id, name, builder, prototype_url) "
            "VALUES (?, 'A', 'claude-code', 'local://a')", (sid,),
        ).lastrowid
        return int(conn.execute(
            "INSERT INTO extracted_code (variant_id, source_url, local_path, "
            "extraction_method, extracted_by) VALUES (?, 'local://a', ?, 'worktree', 't')",
            (vid, str(local_path)),
        ).lastrowid)


def test_run_all_outside_repo(tmp_db: Path, tmp_path: Path) -> None:
    wt = tmp_path / "outside" / "gates-demo-A"
    wt.mkdir(parents=True)
    (wt / "pflanzer.gates.yml").write_text(ADAPTER, encoding="utf-8")
    ext_id = _insert_extracted(wt)

    out: dict[str, Any] = qg.run_all(ext_id)
    assert out["local_path"] == str(wt.resolve())  # absolute, no relative_to crash
    assert out["gates_run"] == 2
    assert out["production_ready"] is False
    assert Path(out["summary_path"]).exists()
    with transaction() as conn:
        rows = dict(conn.execute(
            "SELECT gate_type, status FROM quality_gates WHERE extracted_id = ?", (ext_id,),
        ).fetchall())
        latest = conn.execute(
            "SELECT gate_score_latest FROM projects WHERE slug='gates-demo'"
        ).fetchone()[0]
    assert rows["build"] == "pass" and rows["tests"] == "fail"
    assert latest == out["gate_score"]
