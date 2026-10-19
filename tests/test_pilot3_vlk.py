"""Nálezy z pilotu „Vlk & syn" (production): auto-migrace DB, akceptační testy v test runneru."""
from __future__ import annotations

import json
from pathlib import Path

from tool.cli import db, quality_gates


def _node_repo(tmp_path: Path, test_body: str) -> Path:
    repo = tmp_path / "app"
    (repo / "tests" / "acceptance").mkdir(parents=True)
    (repo / "package.json").write_text(json.dumps({"name": "x", "type": "module",
                                                   "scripts": {"test": "node --test"}}))
    (repo / "tests" / "acceptance" / "stav.test.js").write_text(
        'import { test } from "node:test";\nimport assert from "node:assert/strict";\n'
        f'test("hlavní tok", () => {{ {test_body} }});\n')
    return repo


def test_acceptance_runs_native_node_tests(tmp_path: Path) -> None:
    ctx, _, _ = quality_gates._make_ctx(_node_repo(tmp_path, "assert.equal(1, 1);"))
    res = quality_gates.gate_acceptance(ctx)
    assert res.status == "pass" and "1/1 akceptačních testů" in res.details


def test_acceptance_native_failure_fails(tmp_path: Path) -> None:
    ctx, _, _ = quality_gates._make_ctx(_node_repo(tmp_path, "assert.equal(1, 2);"))
    assert quality_gates.gate_acceptance(ctx).status == "fail"


def test_outdated_db_is_migrated_on_connect(tmp_db: Path, monkeypatch) -> None:
    from tool.db import migrate

    migrate.apply_schema()                      # aktuální schéma
    conn = db.get_connection()
    conn.execute("PRAGMA user_version = 1")     # jako po aktualizaci toolu
    conn.close()
    calls: list[int] = []
    monkeypatch.setattr(migrate, "apply_schema", lambda reset=False: calls.append(1))
    db._SCHEMA_CHECKED.discard(str(db.DB_PATH))
    conn = db.get_connection()
    conn.close()
    assert calls == [1]
