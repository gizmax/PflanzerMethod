"""Pilot 12 (Paprika, FastAPI + Jinja) — egg-info mimo PR, trasy s prefixem routeru, jeden
`git add` pro init, doctor Makefile bez build, popisky resolved / next step, text hypotézy."""
from __future__ import annotations

import subprocess
from pathlib import Path

from tool.cli import doctor, handoff_pr, init, preview, quick_session, session_2, status

REPO = Path(__file__).resolve().parents[1]


def _git(cwd: Path, *a: str) -> str:
    return subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True, text=True).stdout


def _py_repo(tmp_path: Path) -> Path:
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "config", "user.email", "t@t.cz")
    _git(tmp_path, "config", "user.name", "T")
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "p"\n', encoding="utf-8")
    (tmp_path / "app" / "templates").mkdir(parents=True)
    (tmp_path / "app" / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()\n")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-qm", "base")
    _git(tmp_path, "checkout", "-qb", "feat")
    return tmp_path


def _commit(repo: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "feat")


# --- 1. egg-info -------------------------------------------------------------------------------

def test_init_gitignore_python_artifacts(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\n', encoding="utf-8")
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "remote", "add", "origin", "https://github.com/acme/x.git")
    assert init.init(tmp_path)["ok"]
    gi = (tmp_path / ".gitignore").read_text(encoding="utf-8").splitlines()
    for entry in init.PYTHON_IGNORES:
        assert entry in gi


def test_init_gitignore_not_python_artifacts_for_node(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text('{"name": "x"}', encoding="utf-8")
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "remote", "add", "origin", "https://github.com/acme/x.git")
    init.init(tmp_path)
    assert "*.egg-info/" not in (tmp_path / ".gitignore").read_text(encoding="utf-8")


def test_ship_add_command_skips_egg_info(tmp_path: Path) -> None:
    src = (REPO / "tool" / "cli" / "handoff_pr.py").read_text(encoding="utf-8")
    assert "git add -A -- . ':(exclude)*.egg-info/*'" in src
    assert "\ngit add -A\n" not in src
    repo = _py_repo(tmp_path)
    (repo / "paprika.egg-info").mkdir()
    (repo / "paprika.egg-info" / "PKG-INFO").write_text("x")
    (repo / "app" / "new.py").write_text("x = 1\n")
    _git(repo, "add", "-A", "--", ".", ":(exclude)*.egg-info/*")
    staged = _git(repo, "diff", "--cached", "--name-only").split()
    assert staged == ["app/new.py"]


def test_install_python_excludes_egg_info_locally() -> None:
    src = (REPO / "tool" / "cli" / "worktree.py").read_text(encoding="utf-8")
    assert '"*.egg-info/"' in src and "_exclude_locally(wt, pat)" in src


# --- 2. trasy ----------------------------------------------------------------------------------

def test_fastapi_router_prefix_and_templates(tmp_path: Path) -> None:
    repo = _py_repo(tmp_path)
    _commit(repo, {
        "app/features/objednavka/router.py":
            'from fastapi import APIRouter\n'
            'router = APIRouter(prefix="/objednavka")\n'
            '@router.get("")\ndef a(): ...\n'
            '@router.get("/{order_id}")\ndef b(): ...\n',
        "app/templates/objednavka/_banner.html": "<p>x</p>",
        "app/templates/objednavka/form.html": "<form></form>",
    })
    routes = preview._added_routes(repo, spa=False)
    assert routes == ["/objednavka", "/objednavka/{order_id}"]
    assert "/_banner" not in routes and "/form" not in routes


def test_include_router_prefix_and_flask_blueprint(tmp_path: Path) -> None:
    repo = _py_repo(tmp_path)
    _commit(repo, {
        "app/orders.py": 'router = APIRouter()\n@router.get("/seznam")\ndef a(): ...\n',
        "app/main.py": 'app.include_router(orders.router, prefix="/obedy")\n',
        "app/bp.py": 'bp = Blueprint("x", __name__, url_prefix="/menu")\n'
                     '@bp.route("/<int:item_id>")\ndef c(): ...\n',
    })
    routes = preview._added_routes(repo, spa=False)
    assert "/obedy/seznam" in routes
    assert "/menu/{item_id}" in routes


def test_root_param_route_ignored(tmp_path: Path) -> None:
    repo = _py_repo(tmp_path)
    _commit(repo, {"app/r.py": 'router = APIRouter()\n@router.get("/{x}")\ndef a(): ...\n'})
    assert preview._added_routes(repo, spa=False) == []


# --- 3. git add --------------------------------------------------------------------------------

def test_git_add_single_source_of_truth() -> None:
    cmd = init.git_add_command()
    assert cmd == "git add -A docs .pflanzer tests .gitignore .claude/settings.json"
    for rel in ("README.md", "docs/dev.md", "docs/zacni.md", "install.sh",
                ".claude/commands/pm.md", ".claude/commands/pflanzer-charter.md"):
        text = (REPO / rel).read_text(encoding="utf-8")
        assert cmd in text, rel
        assert "tests .gitignore &&" not in text and "tests .gitignore .claude &&" not in text


# --- 4. doctor ---------------------------------------------------------------------------------

def test_doctor_makefile_without_build(tmp_path: Path) -> None:
    (tmp_path / "Makefile").write_text("test:\n\tpytest\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\n', encoding="utf-8")
    row = next(r for r in doctor.check_scripts(tmp_path) if r["check"].startswith("Build"))
    blob = str(row)
    assert "Makefile bez cíle `build`" in blob and "compileall" in blob
    assert "nenalezen" not in blob
    (tmp_path / "pyproject.toml").unlink()
    (tmp_path / "go.mod").unlink() if (tmp_path / "go.mod").exists() else None
    row = next(r for r in doctor.check_scripts(tmp_path) if r["check"].startswith("Build"))
    assert "Makefile bez cíle `build`" in str(row) and "nenalezen" not in str(row)


# --- kosmetika ---------------------------------------------------------------------------------

def test_prep_view_resolved_critical_label() -> None:
    out = {"slug": "s", "open_critical": [], "focus_variants": [], "variants": [],
           "feedback_summary": {"count": 2, "by_severity": {"critical": 1, "low": 1},
                                "open_critical": 0, "resolved_critical": 1},
           "conflicts": [], "ready_for_decision": True, "winner": None,
           "critical_on_all_variants": False}
    try:
        _t, lines, *_ = session_2._prep_view(out)
    except Exception:  # noqa: BLE001 — jen formát řádku Feedback
        lines = []
    fb = next((x for x in lines if x.startswith("Feedback:")), "")
    assert "Kritické: 1 (vyřešeno)" in fb


def test_build_running_next_step_is_not_build() -> None:
    phase, nxt = status._phase("triage", "none", 0, 0, build_running=True)
    assert phase == "Build běží" and "/pm build" not in nxt and "session --spec" in nxt
    assert status._phase("triage", "none", 0, 0)[1] == "/pm build"
    assert status._phase("handoff", "none", 2, 0)[1] == "/pm ship"


def test_charter_command_arguments_not_contradictory() -> None:
    text = (REPO / ".claude" / "commands" / "pflanzer-charter.md").read_text(encoding="utf-8")
    assert "první slovo" not in text
    assert "problém v 1 větě" in text


def test_integration_guide_templates_use_slug_placeholder() -> None:
    for f in (REPO / "tool" / "templates").glob("INTEGRATION_GUIDE*.template"):
        text = f.read_text(encoding="utf-8")
        assert "objednavka" not in text, f.name
        assert "<slug>" in text, f.name


def test_hypothesis_has_no_invented_pilot_claim() -> None:
    src = (REPO / "tool" / "cli" / "quick_session.py").read_text(encoding="utf-8")
    assert "{profile['label']}.\"" not in src
    pr = handoff_pr._what_changes(
        (0, 0, 0, 0, "Problém: **x**. Ověříme ho na třech variantách. Pilot s 5-20 reálnými "
         "uživateli."), None, "n", "metrika")
    assert all("5-20" not in ln for ln in pr)
    assert quick_session.RISK_PROFILES["pilot"]["label"]  # label zůstává v metadatech
