"""Python repo jen s requirements*.txt: sjednocená detekce, gates-template, doctor varování."""
from __future__ import annotations

from pathlib import Path

import pytest

from tool.cli import doctor, init, quality_gates


def _flask_repo(tmp_path: Path, reqs: str = "flask\n", tests: bool = True) -> Path:
    (tmp_path / "requirements.txt").write_text(reqs)
    (tmp_path / "app.py").write_text("print('x')\n")
    if tests:
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "test_a.py").write_text("def test_a():\n    assert True\n")
    return tmp_path


@pytest.mark.parametrize("fname", [
    "requirements.txt", "requirements-dev.txt", "setup.cfg", "Pipfile"])
def test_detect_python_from_manifests(tmp_path, fname):
    (tmp_path / fname).write_text("flask\n")
    assert quality_gates.detect_stack(tmp_path) == "python"
    assert quality_gates.detect_stack(tmp_path) is not None


def test_empty_dir_not_python(tmp_path):
    assert quality_gates.detect_stack(tmp_path) is None


def test_guide_template_python_for_requirements_only(tmp_path):
    _flask_repo(tmp_path)
    assert init.guide_template_for(tmp_path) == init.PYTHON_TEMPLATE_PATH


def test_gates_template_activates_tests_not_lint(tmp_path):
    _flask_repo(tmp_path)
    presets = init._gate_presets("python", tmp_path)
    assert presets["tests"]["cmd"].endswith("pytest -q")
    assert "lint" not in presets and "#lint" in presets


def test_gates_template_lint_when_declared(tmp_path):
    _flask_repo(tmp_path, "flask\nruff\n")
    assert init._gate_presets("python", tmp_path)["lint"]["cmd"] == "ruff check ."


def test_gates_template_no_tests_commented(tmp_path):
    _flask_repo(tmp_path, tests=False)
    presets = init._gate_presets("python", tmp_path)
    assert "tests" not in presets and "#tests" in presets


def test_stack_python_flag_for_requirements(tmp_path):
    _flask_repo(tmp_path)
    assert quality_gates._is_python_project(tmp_path)


def test_doctor_warns_missing_pytest(tmp_path):
    _flask_repo(tmp_path)
    row = doctor.check_python_test_deps(tmp_path)
    assert row and row["status"] == doctor.WARN
    assert "pytest" in row["detail"] and "requirements-dev.txt" in row["advice"]


def test_doctor_ok_when_pytest_declared(tmp_path):
    _flask_repo(tmp_path)
    (tmp_path / "requirements-dev.txt").write_text("pytest\n")
    assert doctor.check_python_test_deps(tmp_path) is None


def test_doctor_warns_ruff_used_in_makefile(tmp_path):
    _flask_repo(tmp_path, "flask\npytest\n")
    (tmp_path / "Makefile").write_text("lint:\n\truff check .\n")
    row = doctor.check_python_test_deps(tmp_path)
    assert row and "ruff" in row["detail"] and "pytest" not in row["detail"]


def test_doctor_silent_without_tests(tmp_path):
    _flask_repo(tmp_path, tests=False)
    assert doctor.check_python_test_deps(tmp_path) is None
