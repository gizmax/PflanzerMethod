"""Quality gates (Ship, v0.5) — automatické brány místo lidí v místnosti.

Pro worktree / adresář vítězné varianty spustí až 10 gates:
- **build**         `npm run build` (jen pokud je build script)
- **types**         `tsc --noEmit` (jen s tsconfig.json) / mypy (jen s konfigurací)
- **lint**          `npm run lint` (jen pokud je lint script) / ruff
- **tests**         `npm test` / pytest; žádné nalezené testy = FAIL ("žádné testy")
- **coverage**      vitest --coverage (jen pokud je coverage nástroj)
- **smoke**         spustí aplikaci vítěze (`[preview] command` / autodetekce) a ověří GET `/`
                    (+ `[preview] smoke_paths`) < 400; bez příkazu = NEOVĚŘENO
- **acceptance**    Playwright scénáře z `tests/acceptance/` (jen pokud existují)
- **security**      secret scan + `npm audit` (vždy)
- **a11y**          statická kontrola stránek běžící aplikace (jako smoke); jinak heuristika nad
                    HTML/JSX/TSX/Vue/Svelte; bez UI souborů i bez příkazu = NEOVĚŘENO
- **observability** `console.*` ve zdrojácích (jen pro JS/TS)

**Stack-aware:** gate, který pro stack nedává smysl (např. `types` bez
tsconfig.json), je `skipped` s důvodem a **nepočítá se do jmenovatele**.
Skóre = body z aplikovatelných gates / max aplikovatelných × 100, vždy 0–100.
Výstup: "X/100 (práh Y)".

Gate report: per gate { status: pass|warn|fail|skipped, details, metric }.
pass = 1, warn = 0.5, fail = 0; skipped / unsupported se vynechávají.

Vstup: extracted_id z `extracted_code` (nebo --slug + --variant).
Výstup: řádky v `quality_gates`, `<DATA_ROOT>/handoffs/<slug>/quality-<variant>.md`
a návratové `gate_score`.

Závislosti: žádné Python deps (jen subprocess). Chybí-li `node_modules`, zkusí
se instalace přes detekovaný package manager (timeout `PFLANZER_INSTALL_TIMEOUT`,
default 300 s); nejde-li to, gates závislé na instalaci jsou SKIP s důvodem.

Gate adapter (audit N7): pokud existuje `pflanzer.gates.yml` (nebo `.yaml` / `.json`)
v kontrolované cestě či jejím rodiči až po git root, jeho příkazy per gate NAHRADÍ
autodetekci úplně:

    build: {cmd: "mvn -q -DskipTests compile", cwd: ".", parse: exit_code}
    coverage: {cmd: "...", parse: 'regex:(?P<metric>[\\d.]+)%', warn_below: 60, fail_below: 30}
    security: {builtin: true}   # použije vestavěný runner (secret scan)

Gate chybějící v adaptéru je 'unsupported' ("define in pflanzer.gates.yml"), nikdy
'fail', a stejně jako SKIP nejde do jmenovatele skóre. YAML vyžaduje PyYAML
(volitelný import); bez něj použij `pflanzer.gates.json`. Šablona + dokumentace:
`tool/templates/pflanzer.gates.yml.template`, `tool/templates/README-gates.md`;
generátor: `pflanzer init gates-template --path <repo>`.

Bez adaptéru se autodetekuje Node a Python; jiné stacky jen jako fallback (adresář není
Node ani Python): Maven (`pom.xml`), Gradle, .NET (`*.sln`/`*.csproj`), Go (`go.mod`)
-> build/tests (+ lint pro .NET a Go, acceptance pro Go: tests/acceptance/*_test.go nebo
testy *Acceptance*), zbytek 'unsupported'; acceptance bez příkazu je vždy NEOVĚŘENO.

Bez DB: `run_gates_on_path(path)` / CLI `--path <dir>`. `adapter_path=` / CLI
`--adapter <file>` vloží adaptér zvenku worktree (Ship ho čte z base branche přes
`git show`, takže agent ve worktree si brány nepřepíše); jeho `cwd` se vztahuje ke
kontrolované cestě. `aggregate_score()` hlásí i `gates_run` (pass/warn/fail) a
`gates_unsupported`; verdikt vyžaduje minimum reálně spuštěných bran (`sufficiency`).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tool.cli import a11y_html, apprun, render  # noqa: E402
from tool.cli.db import audit, current_actor, display_path, transaction  # noqa: E402
from tool.cli.extract import BRAND, DATA_ROOT  # noqa: E402
from tool.cli.ux import CzechArgumentParser, die, emit, tips_for  # noqa: E402

GATES_DIR = DATA_ROOT / "handoffs"
RESULT_DETAIL_LIMIT = 700  # a11y důvody a názvy selhaných testů se vejdou celé
# Pořadí = fail-fast (levné → drahé).
GATE_TYPES = ("build", "types", "lint", "tests", "coverage", "smoke", "acceptance",
              "security", "a11y", "observability")
GATE_WEIGHTS = {  # Production readiness weight
    "build": 1.5,        # bez buildu se nešipuje
    "types": 1.5,        # type errors = bugs
    "lint": 1.0,
    "tests": 2.0,        # primary safety net
    "coverage": 1.0,
    "smoke": 1.5,        # aplikace vítěze vůbec naběhne a odpoví
    "acceptance": 2.5,   # Decider-written scénáře = ground truth
    "security": 2.0,     # blocker-class
    "a11y": 1.0,
    "observability": 0.5,
}
COVERAGE_TARGET = 60  # % branch coverage; pod tímto = warn, pod 30 = fail
# Minimum důkazů pro verdikt "splňuje práh": aspoň MIN_GATES_RUN reálně spuštěných bran
# (pass/warn/fail; SKIP / unsupported se nepočítají) a mezi nimi build i tests.
MIN_SOLID_GATES = 5
MIN_GATES_RUN = 4
REQUIRED_GATES = ("build", "tests")
RAN_STATUSES = ("pass", "warn", "fail")
SKIP_DIRS = {"node_modules", "dist", "build", "out", ".git", "coverage", ".venv", "venv",
             "__pycache__", ".next", ".turbo", ".cache"}


@dataclass
class GateResult:
    gate_type: str
    status: str  # pass | warn | fail | skipped | unsupported
    details: str = ""
    metric: float | None = None
    duration_s: float = 0.0


# --------------------------------------------------------------------------
# Stack detection
# --------------------------------------------------------------------------


@dataclass
class Stack:
    path: Path
    node: bool = False
    python: bool = False
    package_manager: str | None = None
    scripts: dict[str, str] | None = None
    deps: dict[str, str] | None = None
    has_tsconfig: bool = False
    needs_install: bool = False
    workspaces: list[Path] = field(default_factory=list)  # npm/yarn workspace balíčky
    other: str | None = None  # maven | gradle | dotnet | go (jen když není Node ani Python)

    @property
    def label(self) -> str:
        parts = []
        if self.node:
            parts.append("node" + (f"/{self.package_manager}" if self.package_manager else ""))
            parts.append("ts" if self.has_tsconfig else "js")
        if self.python:
            parts.append("python")
        if self.other:
            parts.append(STACK_LABELS[self.other])
        return "+".join(parts) or "neznámý"


def _is_node_project(path: Path) -> bool:
    return (path / "package.json").exists()


def _is_python_project(path: Path) -> bool:
    # Jedna definice pro init, gates i doctor: pyproject/setup.py/setup.cfg/Pipfile/requirements*.txt.
    if any((path / f).exists() for f in ("pyproject.toml", "setup.py", "setup.cfg", "Pipfile")):
        return True
    return next(path.glob("requirements*.txt"), None) is not None


# Non-Node/Python stacks (audit N7). They are only consulted when the dir is
# neither a Node nor a Python project, so legacy behaviour stays identical.
OTHER_STACKS = ("maven", "gradle", "dotnet", "go")
STACK_LABELS = {"node": "Node", "python": "Python", "maven": "Maven",
                "gradle": "Gradle", "dotnet": ".NET", "go": "Go"}
STACK_TIMEOUT = 600  # first Maven/Gradle/NuGet run downloads the dependency tree
# Autodetected commands per stack. Gradle entries are arguments appended to
# the wrapper/binary resolved by `_gradle_cmd()`.
STACK_COMMANDS: dict[str, dict[str, list[str]]] = {
    "maven": {
        "build": ["mvn", "-q", "-DskipTests", "compile"],
        "tests": ["mvn", "-q", "test"],
    },
    "gradle": {
        "build": ["build", "-x", "test"],
        "tests": ["test"],
    },
    "dotnet": {
        "build": ["dotnet", "build", "--nologo"],
        "tests": ["dotnet", "test", "--nologo"],
        "lint": ["dotnet", "format", "--verify-no-changes"],
    },
    "go": {
        "build": ["go", "build", "./..."],
        "lint": ["go", "vet", "./..."],
        "tests": ["go", "test", "./..."],
    },
}
# Extra files/dirs for the secret scan on non-Node/Python stacks.
STACK_SCAN_SUFFIXES = (".java", ".kt", ".kts", ".gradle", ".properties", ".xml",
                       ".cs", ".config", ".go", ".toml")
STACK_SKIP_DIRS = {"target", "build", "bin", "obj", "vendor", ".gradle", ".idea"}


def _is_maven_project(path: Path) -> bool:
    return (path / "pom.xml").exists()


def _is_gradle_project(path: Path) -> bool:
    return any((path / name).exists() for name in (
        "build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts"))


def _is_dotnet_project(path: Path) -> bool:
    return any(next(path.glob(pattern), None) is not None
               for pattern in ("*.sln", "*.slnx", "*.csproj", "*.fsproj"))


def _is_go_project(path: Path) -> bool:
    return (path / "go.mod").exists()


def detect_stack(path: Path) -> str | None:
    """Return the stack id (node, python, maven, gradle, dotnet, go) or None.

    Order matters: Node and Python win (legacy behaviour), so e.g. a Maven
    project with a frontend `package.json` at its root is still treated as Node.
    """
    if _is_node_project(path):
        return "node"
    if _is_python_project(path):
        return "python"
    if _is_maven_project(path):
        return "maven"
    if _is_gradle_project(path):
        return "gradle"
    if _is_dotnet_project(path):
        return "dotnet"
    if _is_go_project(path):
        return "go"
    return None


def _other_stack(path: Path) -> str | None:
    """Stack id for the N7 fallback runners; None for Node/Python/unknown."""
    stack = detect_stack(path)
    return stack if stack in OTHER_STACKS else None


def _gradle_cmd(path: Path) -> list[str] | None:
    wrapper = path / "gradlew"
    if wrapper.is_file():
        if os.access(wrapper, os.X_OK):
            return ["./gradlew"]
        return ["sh", "./gradlew"] if _has("sh") else None
    return ["gradle"] if _has("gradle") else None


def detect_stack_info(path: Path) -> Stack:
    st = Stack(path=path, scripts={}, deps={})
    pkg = path / "package.json"
    if pkg.exists():
        st.node = True
        try:
            data = json.loads(pkg.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}
        st.scripts = {k: str(v) for k, v in (data.get("scripts") or {}).items()}
        st.deps = {**(data.get("dependencies") or {}), **(data.get("devDependencies") or {})}
        pm = str(data.get("packageManager", ""))
        if pm.startswith(("pnpm@", "yarn@", "npm@")):
            st.package_manager = pm.split("@")[0]
        elif (path / "pnpm-lock.yaml").exists():
            st.package_manager = "pnpm"
        elif (path / "yarn.lock").exists():
            st.package_manager = "yarn"
        else:
            st.package_manager = "npm"
        st.needs_install = bool(st.deps)
    if st.node:
        st.workspaces = apprun.workspace_packages(path)
    st.has_tsconfig = (path / "tsconfig.json").exists() or any(
        (w / "tsconfig.json").exists() for w in st.workspaces)
    st.python = _is_python_project(path)
    if not st.node and not st.python:
        found = detect_stack(path)
        st.other = found if found in OTHER_STACKS else None
    return st


def _has(tool: str) -> bool:
    return shutil.which(tool) is not None


def _run(cmd: list[str] | str, cwd: Path, timeout: int = 120) -> tuple[int, str, str]:
    # Řetězec (adapter `cmd`) jde přes shell (`&&`, env proměnné, wrappery); seznam zůstává exec-style.
    env = {**os.environ, **apprun.venv_env(cwd), "CI": "1", "FORCE_COLOR": "0", "NO_COLOR": "1"}
    try:
        res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                             timeout=timeout, env=env, shell=isinstance(cmd, str))
        return res.returncode, res.stdout, res.stderr
    except subprocess.TimeoutExpired:
        return 124, "", f"Timeout po {timeout}s"
    except FileNotFoundError as e:
        return 127, "", str(e)


def prepare_deps(st: Stack) -> tuple[bool, str]:
    """Zajisti node_modules (jen když je potřeba). Vrací (ok, důvod při selhání)."""
    if not st.node or not st.needs_install:
        return True, ""
    if (st.path / "node_modules").exists():
        return True, ""
    pm = st.package_manager or "npm"
    lock_npm = (st.path / "package-lock.json").exists()
    if pm == "pnpm" and _has("pnpm"):
        cmd = ["pnpm", "install", "--frozen-lockfile", "--reporter=silent"]
    elif pm == "yarn" and _has("yarn"):
        cmd = ["yarn", "install", "--frozen-lockfile", "--silent"]
    elif _has("npm"):
        cmd = ["npm", "ci" if lock_npm else "install", "--no-audit", "--no-fund", "--silent"]
    else:
        return False, f"{pm} není na PATH, závislosti nelze nainstalovat"
    timeout = int(os.environ.get("PFLANZER_INSTALL_TIMEOUT", "300"))
    rc, out, err = _run(cmd, st.path, timeout=timeout)
    err = (err + out)
    if rc == 0:
        return True, ""
    if rc == 124:
        return False, f"instalace závislostí vypršela po {timeout}s ({' '.join(cmd[:2])})"
    return False, f"instalace závislostí selhala ({' '.join(cmd[:2])}, rc={rc}): {err.strip()[-160:]}"


@dataclass
class Ctx:
    path: Path
    stack: Stack
    deps_ok: bool
    deps_reason: str
    app_run: "AppRun | None" = None  # cache: aplikace se pro smoke + a11y spouští jen jednou


def _skip(gate: str, reason: str) -> GateResult:
    """Brána pro tento stack nedává smysl (typy bez TS, a11y bez UI) - nepočítá se a nevadí."""
    return GateResult(gate, "skipped", f"SKIP: {reason}")


UNVERIFIED_PREFIX = "NEOVĚŘENO:"
PRODUCTION_TARGET = 85  # práh production; pilot 80


def _unverified(gate: str, short: str, long: str = "") -> GateResult:
    """Brána by dávala smysl, ale chybí nástroj / konfigurace - výsledek je NEOVĚŘENO.

    `short` jde do souhrnu skóre („chybí @playwright/test“), `long` jen do reportu.
    """
    return GateResult(gate, "skipped", f"{UNVERIFIED_PREFIX} {short}" + (f" — {long}" if long else ""))


def _needs_deps(ctx: Ctx, gate: str) -> GateResult | None:
    """SKIP s důvodem, pokud node projekt potřebuje závislosti a ty nejsou."""
    if ctx.stack.node and ctx.stack.needs_install and not ctx.deps_ok:
        return _unverified(gate, "chybí nainstalované závislosti",
                           ctx.deps_reason or "chybí node_modules")
    return None


def _iter_files(root: Path, suffixes: tuple[str, ...], skip: set[str] | None = None):
    skip_dirs = SKIP_DIRS if skip is None else skip
    for f in root.rglob("*"):
        rel_parts = f.relative_to(root).parts
        if any(p in skip_dirs for p in rel_parts[:-1]):
            continue
        if f.is_file() and f.suffix.lower() in suffixes:
            yield f


_TEST_FILE_RE = re.compile(r"(\.|_)(test|spec)\.[a-z]+$|^test_.*\.py$|_test\.py$")


def _has_test_files(root: Path) -> bool:
    for f in _iter_files(root, (".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".py")):
        rel = f.relative_to(root).parts
        if _TEST_FILE_RE.search(f.name) or any(p in ("test", "tests", "__tests__") for p in rel[:-1]):
            return True
    return False


# --------------------------------------------------------------------------
# Per-gate runners
# --------------------------------------------------------------------------


def _unavailable(gate: str, text: str, advice: str = "") -> GateResult:
    """Brána nemá z čeho běžet. Acceptance je vždy NEOVĚŘENO (nikdy tichý průchod u production),
    ostatní brány zůstávají „unsupported“ (mimo jmenovatel skóre)."""
    if gate == "acceptance":
        return _unverified("acceptance", text, advice)
    return GateResult(gate, "unsupported", text + (f" — {advice}" if advice else ""))


GO_ACCEPTANCE_HINT = (
    "napište akceptační testy do tests/acceptance/*_test.go (package acceptance; "
    "spustí se `go test ./tests/acceptance/...`), nebo pojmenujte testy TestAcceptance* "
    "(`go test -run Acceptance ./...`)")


def _go_acceptance(path: Path) -> GateResult:
    """Go: `tests/acceptance/*_test.go`, jinak testy s `Acceptance` v názvu funkce / `*_acceptance_test.go`."""
    if not _has("go"):
        return _unverified("acceptance", "go není na PATH", "nainstalujte Go (https://go.dev/dl)")
    acc_dir = path / "tests" / "acceptance"
    if acc_dir.is_dir() and any(acc_dir.rglob("*_test.go")):
        cmd = ["go", "test", "-v", "./tests/acceptance/..."]
        where = "tests/acceptance"
    else:
        named = [f for f in _iter_files(path, (".go",), SKIP_DIRS | STACK_SKIP_DIRS)
                 if f.name.endswith("_test.go")
                 and (f.name.endswith("_acceptance_test.go")
                      or re.search(r"^func Test\w*Acceptance\w*\(", f.read_text(
                          encoding="utf-8", errors="ignore"), re.M))]
        if not named:
            return _unverified("acceptance", "chybí akceptační testy", GO_ACCEPTANCE_HINT)
        cmd = ["go", "test", "-v", "-run", "Acceptance", "./..."]
        where = "testy *Acceptance*"
    started = time.monotonic()
    rc, out, err = _run(cmd, path, timeout=STACK_TIMEOUT)
    duration = round(time.monotonic() - started, 2)
    passed = len(re.findall(r"^--- PASS", out, re.M))
    failed = len(re.findall(r"^--- FAIL", out, re.M))
    total = passed + failed
    if total == 0:
        if rc == 0:
            return _unverified("acceptance", "žádné akceptační testy neběžely", GO_ACCEPTANCE_HINT)
        return GateResult("acceptance", "fail",
                          f"Go: `{' '.join(cmd)}` exit {rc} (nezkompilovalo se?)\n"
                          + _tail(out + err, 400), metric=0, duration_s=duration)
    rate = round(100 * passed / total)
    label = f"Go: {passed}/{total} akceptačních testů ({rate} %, {where})"
    if rate >= 80 and rc == 0:
        return GateResult("acceptance", "pass", label, metric=rate, duration_s=duration)
    status = "warn" if rate >= 50 else "fail"
    tail = _tail(out + err, 400)
    suffix = " < cíl 80 %" if rate < 80 else f" — {_tests_fail_phrase(failed or 1)}"
    return GateResult("acceptance", status, label + suffix + "\n" + tail,
                      metric=rate, duration_s=duration)


def _gate_other_stack(gate: str, path: Path, stack: str) -> GateResult:
    """Run the autodetected command for a Maven/Gradle/.NET/Go gate."""
    label = STACK_LABELS[stack]
    if gate == "acceptance" and stack == "go":
        return _go_acceptance(path)
    args = STACK_COMMANDS[stack].get(gate)
    if args is None:
        if gate == "types":
            return _skip("types", "typy kontroluje kompilátor (brána build)")
        return _unavailable(gate, f"{label}: žádný autodetekovaný příkaz",
                            "definuj ho v pflanzer.gates.json (`pflanzer init gates-template`)")
    if stack == "gradle":
        base = _gradle_cmd(path)
        if base is None:
            return _unavailable(gate, "gradlew / gradle není na PATH")
        cmd = base + args
    else:
        cmd = args
        if not _has(cmd[0]):
            return _unavailable(gate, f"{cmd[0]} není na PATH")
    started = time.monotonic()
    rc, out, err = _run(cmd, path, timeout=STACK_TIMEOUT)
    duration = round(time.monotonic() - started, 2)
    shown = " ".join(cmd)
    if rc == 0:
        return GateResult(gate, "pass", f"{label}: `{shown}` OK", duration_s=duration)
    return GateResult(gate, "fail",
                      f"{label}: `{shown}` exit {rc}\n{_tail(out + err, 500)}",
                      duration_s=duration)

def _python_cmd(path: Path | None = None) -> str:
    """Interpreter pro Python brány.

    Pořadí: `PFLANZER_PYTHON` > `.venv/bin/python` / `venv/bin/python` v projektu > `python3`.
    """
    env = os.environ.get("PFLANZER_PYTHON")
    if env:
        return env
    if path is not None:
        for d in (".venv", "venv"):
            cand = path / d / "bin" / "python"
            if cand.is_file():
                return str(cand)
    return "python3"


GATES_JSON_HINT = (
    "doplňte do `pflanzer.gates.json` v base branchi např.:\n"
    '{"tests": {"cmd": ".venv/bin/python -m pytest -q"},\n'
    ' "lint": {"cmd": ".venv/bin/python -m ruff check ."},\n'
    ' "build": {"cmd": "make build"}}'
)


def _no_python(py: str) -> str:
    """Lidská věta pro chybějící interpret (bez anglického `python: No such file`)."""
    return ("Python v projektu nenašel — vytvořte .venv v repu nebo nastavte PFLANZER_PYTHON "
            f"(hledal jsem `{py}`); nebo {GATES_JSON_HINT}")


def _has_make_target(path: Path, target: str) -> bool:
    pat = re.compile(rf"^{re.escape(target)}\s*:(?!=)", re.MULTILINE)
    for name in ("Makefile", "makefile", "GNUmakefile"):
        f = path / name
        if f.is_file():
            try:
                return bool(pat.search(f.read_text(encoding="utf-8", errors="ignore")))
            except OSError:
                return False
    return False


def _has_make_build(path: Path) -> bool:
    return _has_make_target(path, "build")


def _python_build(ctx: Ctx) -> GateResult:
    """`make build`, když Makefile má cíl build; jinak `compileall` jako ekvivalent."""
    started = time.monotonic()
    if _has_make_build(ctx.path) and _has("make"):
        rc, out, err = _run(["make", "build"], ctx.path, timeout=300)
        dur = round(time.monotonic() - started, 2)
        if rc == 0:
            return GateResult("build", "pass", "`make build` OK", duration_s=dur)
        return GateResult("build", "fail", f"`make build` exit {rc}\n{_tail(out + err, 500)}",
                          duration_s=dur)
    py = _python_cmd(ctx.path)
    if not _has(py):
        return _skip("build", _no_python(py))
    rc, out, err = _run([py, "-m", "compileall", "-q", "."], ctx.path, timeout=120)
    dur = round(time.monotonic() - started, 2)
    if rc == 0:
        return GateResult("build", "pass",
                          "Python bez Makefile cíle build: `compileall` (syntaxe) OK",
                          duration_s=dur)
    return GateResult("build", "fail", f"`compileall` exit {rc}\n{_tail(out + err, 500)}",
                      duration_s=dur)


def _dir_kb(root: Path, skip: tuple[str, ...] = ()) -> int:
    """Velikost adresáře v KB; podadresáře z `skip` (první úroveň) se nepočítají."""
    total = 0
    for f in root.rglob("*"):
        try:
            rel = f.relative_to(root).parts
            if f.is_file() and not (rel and rel[0] in skip):
                total += f.stat().st_size
        except OSError:
            continue
    return total // 1024


def gate_build(ctx: Ctx) -> GateResult:
    st = ctx.stack
    if st.other:
        return _gate_other_stack("build", ctx.path, st.other)
    if st.node:
        if "build" not in st.scripts:
            return _skip("build", "package.json nemá build script")
        if (s := _needs_deps(ctx, "build")):
            return s
        if not _has("npm"):
            return _skip("build", "npm není na PATH")
        rc, out, err = _run(["npm", "run", "build"], ctx.path, timeout=180)
        nextjs = apprun.is_nextjs(ctx.path)
        note = ""
        if nextjs:
            # `next build` přepsal .next pod případným běžícím `next dev` (preview by dávalo 500)
            try:
                from tool.cli import preview as _preview
                msg = _preview.restart_for_worktree(ctx.path)
                note = f"; {msg}" if msg else ""
            except Exception:  # noqa: BLE001 — advisory only
                pass
        if rc == 0:
            if nextjs and (ctx.path / ".next").is_dir():
                size_kb = _dir_kb(ctx.path / ".next", skip=("cache",))
                return GateResult("build", "pass",
                                  f"Build OK (Next.js), .next {size_kb} KB bez cache{note}",
                                  metric=size_kb)
            size_kb = 0
            for base in [ctx.path, *st.workspaces]:  # monorepo: výstup leží v balíčcích
                for d in ("dist", "build", "out"):
                    dist = base / d
                    if dist.is_dir():
                        size_kb += sum(f.stat().st_size for f in dist.rglob("*")
                                       if f.is_file()) // 1024
                        break
            return GateResult("build", "pass", f"Build OK, výstup {size_kb} KB", metric=size_kb)
        return GateResult("build", "fail", _tail(out + err, 500))
    if st.python:
        return _python_build(ctx)
    return _skip("build", "neznámý stack (bez package.json / pyproject.toml)")


def _node_types(ctx: Ctx) -> GateResult:
    """`tsc --noEmit` v kořeni i v každém workspace balíčku s tsconfig.json (`-p <balíček>`)."""
    st = ctx.stack
    dirs = [d for d in [ctx.path, *st.workspaces] if (d / "tsconfig.json").exists()]
    local = [ctx.path / "node_modules" / ".bin" / "tsc",
             *(d / "node_modules" / ".bin" / "tsc" for d in st.workspaces)]
    tsc = next((t for t in local if t.exists()), None)
    if tsc is None and not _has("tsc"):
        where = ", ".join(str(d.relative_to(ctx.path)) or "." for d in dirs)
        return _unverified("types", "chybí typescript",
                           f"tsconfig.json je ({where}), ale typescript není nainstalovaný — "
                           "spusťte `npm install` (nic se nestahuje automaticky)")
    errors = 0
    fails: list[str] = []
    for d in dirs:
        rel = str(d.relative_to(ctx.path)) or "."
        cand = [d / "node_modules" / ".bin" / "tsc", ctx.path / "node_modules" / ".bin" / "tsc"]
        exe = next((str(c) for c in cand if c.exists()), str(tsc) if tsc else "tsc")
        cmd = [exe, "--noEmit"] + ([] if d == ctx.path else ["-p", rel])
        rc, out, err = _run(cmd, ctx.path, timeout=120)
        if rc != 0:
            n = (out + err).count("error TS")
            errors += n
            fails.append(f"{rel}: {n} TS chyb\n{_tail(out + err, 500)}")
    scope = f" ({len(dirs)} balíčků)" if len(dirs) > 1 else ""
    if not fails:
        return GateResult("types", "pass", f"tsc --noEmit bez chyb{scope}", metric=0)
    return GateResult("types", "fail", f"{errors} TS chyb\n" + "\n".join(fails)[:700],
                      metric=errors)


def gate_types(ctx: Ctx) -> GateResult:
    st = ctx.stack
    if st.other:
        return _gate_other_stack("types", ctx.path, st.other)
    if st.node:
        if not st.has_tsconfig:
            return _skip("types", "bez tsconfig.json - projekt není TypeScript")
        if (s := _needs_deps(ctx, "types")):
            return s
        return _node_types(ctx)
    if st.python:
        configured = (ctx.path / "mypy.ini").exists() or any(
            "mypy" in (ctx.path / f).read_text(encoding="utf-8", errors="ignore")
            for f in ("pyproject.toml", "setup.cfg") if (ctx.path / f).exists())
        if not configured:
            return _skip("types", "mypy není v projektu nakonfigurovaný")
        if not _has("mypy"):
            return _unverified("types", "chybí mypy", "mypy je nakonfigurované, ale není na PATH")
        rc, out, _ = _run(["mypy", "."], ctx.path)
        return GateResult("types", "pass" if rc == 0 else "fail", _tail(out, 500) or "OK")
    return _skip("types", "neznámý stack")


def gate_lint(ctx: Ctx) -> GateResult:
    st = ctx.stack
    if st.other:
        return _gate_other_stack("lint", ctx.path, st.other)
    if st.node:
        if "lint" not in st.scripts:
            return _skip("lint", "package.json nemá lint script")
        if (s := _needs_deps(ctx, "lint")):
            return s
        rc, out, err = _run(["npm", "run", "lint"], ctx.path, timeout=120)
        if rc == 0:
            return GateResult("lint", "pass", "lint bez nálezů", metric=0)
        problems = len(re.findall(r"^\s+\d+:\d+", out, re.MULTILINE))
        return GateResult("lint", "fail",
                          f"lint hlásí chybu ({problems} nálezů)\n{_tail(out + err, 500)}",
                          metric=problems)
    if st.python:
        started = time.monotonic()
        if _has_make_target(ctx.path, "lint") and _has("make"):
            rc, out, err = _run(["make", "lint"], ctx.path, timeout=180)
            dur = round(time.monotonic() - started, 2)
            if rc == 0:
                return GateResult("lint", "pass", "`make lint` OK", duration_s=dur)
            return GateResult("lint", "fail", f"`make lint` exit {rc}\n{_tail(out + err, 500)}",
                              duration_s=dur)
        py = _python_cmd(ctx.path)
        if Path(py).is_absolute() and _has(py):  # venv projektu / PFLANZER_PYTHON: jeho ruff
            cmd = [py, "-m", "ruff", "check", "."]
        elif _has("ruff"):
            cmd = ["ruff", "check", "."]
        elif _has(py):
            cmd = [py, "-m", "ruff", "check", "."]
        else:
            return _skip("lint", _no_python(py))
        rc, out, err = _run(cmd, ctx.path)
        text = out + err
        if rc != 0 and _NO_MODULE_RE.search(text):
            return _skip("lint", "ruff není nainstalovaný (`pip install ruff` do .venv projektu); "
                                 "nástroj chybí, kód se nehodnotil")
        return GateResult("lint", "pass" if rc == 0 else "fail", _tail(text, 500) or "OK")
    return _skip("lint", "neznámý stack")


_NO_MODULE_RE = re.compile(r"No module named ['\"]?([\w.\-]+)")
_PLACEHOLDER_TEST = re.compile(r"no test specified", re.IGNORECASE)


def _count_tests(output: str) -> int | None:
    """Počet testů z výstupu node:test / vitest / jest / pytest (None = nezjištěno)."""
    for pat in (r"^\s*Tests\s+(?:\d+ failed \| )?(\d+) passed",  # vitest: Tests  8 passed (8)
                r"^# pass (\d+)", r"^\W*pass (\d+)\s*$", r"Tests?:\s+(?:\d+ failed, )?(\d+) passed",
                r"\b(\d+) passed", r"(\d+)\s+pass(?:ed|ing)?\b"):
        m = re.search(pat, output, re.MULTILINE)
        if m:
            return int(m.group(1))
    m = re.search(r"^# tests (\d+)", output, re.MULTILINE)
    return int(m.group(1)) if m else None


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _unquote(v: str) -> str:
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"":
        v = v[1:-1]
    return v


def _tap_failures(lines: list[str]) -> list[tuple[str, str]]:
    """Node `--test` v TAP: `not ok N - název` + YAML blok (`error:`, `expected:`, `actual:`)."""
    out: list[tuple[str, str]] = []
    for i, ln in enumerate(lines):
        m = re.match(r"^(\s*)not ok \d+ - (.*?)(?:\s+# .*)?$", ln)
        if not m:
            continue
        base = len(m.group(1))
        block: list[str] = []
        for nxt in lines[i + 1:]:
            if nxt.strip() and _indent(nxt) <= base:
                break
            block.append(nxt)
        text = "\n".join(block)
        if "subtestsFailed" in text:  # rodičovský suite; selhání nesou jeho podtesty
            continue
        fields: dict[str, str] = {}
        for j, b in enumerate(block):
            fm = re.match(r"^\s*(error|expected|actual):\s*(.*)$", b)
            if not fm:
                continue
            val = fm.group(2).strip()
            if val in ("|-", "|", ">-", ">") and j + 1 < len(block):
                val = block[j + 1].strip()
            fields.setdefault(fm.group(1), _unquote(val))
        detail = fields.get("error", "")
        if "expected" in fields or "actual" in fields:
            detail = (detail + " " if detail else "") + (
                f"(očekáváno {fields.get('expected', '?')}, bylo {fields.get('actual', '?')})")
        out.append((m.group(2).strip(), detail))
    return out


def _jest_failures(lines: list[str]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for i, ln in enumerate(lines):
        m = re.match(r"^\s*● (?!Console)(.+)$", ln)
        if not m:
            continue
        exp = rec = ""
        first = ""
        for nxt in lines[i + 1:i + 40]:
            if re.match(r"^\s*● ", nxt):
                break
            t = nxt.strip()
            if t.startswith("Expected") and not exp:
                exp = t.split(":", 1)[-1].strip() if ":" in t else t
            elif t.startswith("Received") and not rec:
                rec = t.split(":", 1)[-1].strip() if ":" in t else t
            elif not first and re.match(r"(expect\(|Error|TypeError|ReferenceError)", t):
                first = t
        detail = f"očekáváno {exp}, bylo {rec}" if exp or rec else first
        out.append((m.group(1).strip(), detail))
    return out


def _vitest_failures(lines: list[str]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for i, ln in enumerate(lines):
        m = re.match(r"^\s*FAIL\s+(\S.*? > .+)$", ln)
        if not m:
            continue
        detail = ""
        for nxt in lines[i + 1:i + 8]:
            t = nxt.strip()
            if re.match(r"(AssertionError|\w*Error)\b", t):
                detail = t
                break
        out.append((m.group(1).strip(), detail))
    return out


def _pytest_failures(lines: list[str]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for ln in lines:
        m = re.match(r"^FAILED (\S+?)(?: - (.*))?$", ln.strip())
        if m:
            out.append((m.group(1), (m.group(2) or "").strip()))
    return out


def _node_spec_failures(lines: list[str]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for i, ln in enumerate(lines):
        m = re.match(r"^\s*✖ (.+?) \(\d+(?:\.\d+)?ms\)\s*$", ln)
        if not m or m.group(1) in seen:
            continue
        seen.add(m.group(1))
        detail = ""
        for nxt in lines[i + 1:i + 6]:
            t = nxt.strip()
            if re.match(r"(AssertionError|\w*Error)\b", t):
                detail = t
                break
        out.append((m.group(1).strip(), detail))
    return out


def _summary_failures(lines: list[str]) -> list[tuple[str, str]]:
    """Naše vlastní shrnutí (`summarize_test_failures`): `✗ název — detail`."""
    out: list[tuple[str, str]] = []
    for ln in lines:
        m = re.match(r"^✗ (.+?)(?: — (.*))?$", ln.strip())
        if m:
            out.append((m.group(1), (m.group(2) or "").strip()))
    return out


def parse_test_failures(output: str) -> list[tuple[str, str]]:
    """Selhané testy jako (název, detail) z výstupu Node TAP / jest / vitest / pytest / node spec."""
    lines = (output or "").splitlines()
    for parser in (_summary_failures, _tap_failures, _jest_failures, _vitest_failures, _pytest_failures,
                   _node_spec_failures):
        found = parser(lines)
        if found:
            return found
    return []


def summarize_test_failures(output: str, root: Path | None = None) -> str:
    """Lidské shrnutí selhání: `✗ název: detail` na řádek, pak (stručně) konec výstupu.

    Cesty jsou relativní k repu (`root`), ne absolutní.
    """
    if root is not None:
        for r in {str(root), str(root.resolve())}:
            output = output.replace(r + os.sep, "")
    found = parse_test_failures(output)
    if not found:
        return _tail(output, 500)
    rows = [f"✗ {name}" + (f" — {detail}" if detail else "") for name, detail in found[:6]]
    if len(found) > 6:
        rows.append(f"…a dalších {len(found) - 6} testů")
    return "\n".join(rows)


def _pysummarize_test_failures(output: str) -> str:
    """Užitečný konec pytest výstupu: řádky `E   …` (assertion) a shrnutí FAILED, ne useknutý stack."""
    lines = output.splitlines()
    picked = [ln.strip() for ln in lines if ln.lstrip().startswith("E ")][:4]
    picked += [ln.strip() for ln in lines if ln.startswith("FAILED ")][:3]
    summary = next((ln.strip() for ln in reversed(lines) if re.search(r"\d+ (failed|passed|error)", ln)), "")
    text = "\n".join([*picked, summary] if picked else [output[-500:]])
    return text[-600:]


def gate_tests(ctx: Ctx) -> GateResult:
    st = ctx.stack
    if st.other:
        return _gate_other_stack("tests", ctx.path, st.other)
    if st.node:
        script = st.scripts.get("test")
        if not script or _PLACEHOLDER_TEST.search(script):
            return GateResult("tests", "fail", "žádné testy - package.json nemá test script",
                              metric=0)
        if (s := _needs_deps(ctx, "tests")):
            return s
        rc, out, err = _run(["npm", "test"], ctx.path, timeout=180)
        if rc != 0:
            return GateResult("tests", "fail", summarize_test_failures(out + err, ctx.path))
        count = _count_tests(out + err)
        if count == 0 or (count is None and not _has_test_files(ctx.path)):
            return GateResult("tests", "fail",
                              "žádné testy - test script proběhl, ale nenašel žádný test",
                              metric=0)
        note = f"{count} testů prošlo" if count is not None else "testy prošly (počet nezjištěn)"
        return GateResult("tests", "pass", note, metric=count)
    if st.python:
        py = _python_cmd(ctx.path)
        if not _has(py):
            return _skip("tests", _no_python(py))
        rc, out, err = _run([py, "-m", "pytest", "-q"], ctx.path, timeout=180)
        if rc != 0 and (m := _NO_MODULE_RE.search(out + err)) and m.group(1).split(".")[0] == "pytest":
            return _skip("tests", f"pytest není nainstalovaný pro {py} (`{py} -m pip install pytest`); "
                                  f"nebo {GATES_JSON_HINT}")
        if rc == 5:
            return GateResult("tests", "fail", "žádné testy - pytest žádný nenašel", metric=0)
        count = _count_tests(out)
        if rc == 0:
            note = f"{count} testů prošlo" if count is not None else "testy prošly"
            return GateResult("tests", "pass", note, metric=count)
        found = summarize_test_failures(out + err, ctx.path) if parse_test_failures(out + err) else ""
        return GateResult("tests", "fail",
                          found or _pysummarize_test_failures(out + err), metric=count)
    return GateResult("tests", "fail", "žádné testy - neznámý stack, nic ke spuštění", metric=0)


def gate_security(ctx: Ctx) -> GateResult:
    findings: list[str] = []
    secrets_count = 0
    secret_patterns = [
        (r"(?i)api[_-]?key\s*[:=]\s*['\"][^'\"]{16,}", "API key"),
        (r"(?i)secret\s*[:=]\s*['\"][^'\"]{16,}", "secret"),
        (r"(?i)password\s*[:=]\s*['\"][^'\"]{8,}", "password"),
        (r"-----BEGIN (RSA |OPENSSH |EC |)PRIVATE KEY-----", "private key"),
        (r"sk-[a-zA-Z0-9]{32,}", "OpenAI-style key"),
        (r"sk-ant-[a-zA-Z0-9_-]{32,}", "Anthropic key"),
    ]
    scan_suffixes: tuple[str, ...] = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py",
                                      ".env", ".json", ".yml", ".yaml", ".toml", ".sh")
    skip_dirs = SKIP_DIRS
    if ctx.stack.other:
        scan_suffixes += STACK_SCAN_SUFFIXES
        skip_dirs = SKIP_DIRS | STACK_SKIP_DIRS
    for f in _iter_files(ctx.path, scan_suffixes, skip_dirs):
        try:
            if f.stat().st_size > 1_000_000:
                continue
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pat, label in secret_patterns:
            if re.search(pat, text):
                secrets_count += 1
                findings.append(f"{label} v {f.relative_to(ctx.path)}")

    st = ctx.stack
    audit_note = "npm audit nespuštěn" if st.node else ""
    audit_findings = 0
    if st.node and _has("npm") and ((ctx.path / "node_modules").exists()
                                    or (ctx.path / "package-lock.json").exists()):
        rc, out, _ = _run(["npm", "audit", "--json"], ctx.path, timeout=60)
        try:
            audit_json = json.loads(out)
            audit_findings = audit_json.get("metadata", {}).get("vulnerabilities", {}).get("total", 0)
            audit_note = f"npm audit: {audit_findings} zranitelností"
            if audit_findings:
                findings.append(audit_note)
        except (json.JSONDecodeError, KeyError, AttributeError):
            audit_note = "npm audit nedostupný (offline / bez lockfile)"

    if secrets_count > 0:
        return GateResult("security", "fail",
                          f"Secret scan: {secrets_count} možný únik(y)\n" + "\n".join(findings[:10]),
                          metric=secrets_count)
    if audit_findings > 0:
        return GateResult("security", "warn",
                          f"{audit_note}" + (" (> 5 = review)" if audit_findings > 5 else ""),
                          metric=audit_findings)
    return GateResult("security", "pass",
                      "Žádné secrets" + (f"; {audit_note}" if audit_note else ""), metric=0)


def _a11y_heuristic(ctx: Ctx, files: list[Path]) -> GateResult:
    """Heuristika nad zdrojáky (ne náhrada axe-core): alt u img, type u button, lang u html."""
    semantic = issues = 0
    for f in files:
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if re.search(r"<button(?![^>]*\btype=)", text):
            issues += 1
        if re.search(r"<img(?![^>]*\balt=)", text):
            issues += 1
        if f.suffix == ".html" and re.search(r"<html(?![^>]*\blang=)", text):
            issues += 1
        if re.search(r'role=|aria-|alt=|<main|<nav|<header|<footer|<section', text):
            semantic += 1
    if issues:
        return GateResult("a11y", "warn",
                          f"{issues} možných a11y problémů v {len(files)} UI souborech "
                          "(heuristika" + ("; pro detail `npx axe`)" if ctx.stack.node else ")"),
                          metric=issues)
    return GateResult("a11y", "pass",
                      f"{len(files)} UI souborů, {semantic} se sémantickými značkami, 0 zjevných "
                      "problémů (heuristika" + ("; pro produkci doporuč. axe)" if ctx.stack.node else ")"),
                      metric=0)


def _is_html_ctype(ctype: str) -> bool:
    """Prázdný content-type = neznámý (necháme projít); jinak jen text/html a xhtml."""
    c = (ctype or "").lower()
    return not c or "html" in c


def _a11y_spa(run: AppRun) -> GateResult:
    """SPA: statická kontrola jen nad vyrenderovaným DOM; bez prohlížeče NEOVĚŘENO."""
    if run.render is None:
        return _unverified("a11y", "SPA — bez headless prohlížeče nelze ověřit",
                           f"{render.INSTALL_HINT} (a11y nad prázdnou kostrou by nic neověřila)"
                           + (f"; {run.render_why}" if run.render_why else ""))
    ctypes = {pg[0]: (pg[3] or "") for pg in run.pages}
    # JSON / textové endpointy (např. /api/bikes) nejsou stránky; Chromium je obalí do <html>.
    pages = [(p.path, p.status, p.html, "text/html") for p in run.render.pages
             if not p.broken and _is_html_ctype(ctypes.get(p.path, ""))]
    res = _a11y_from_pages(replace(run, pages=pages)) if pages else None
    if res is None:
        return GateResult("a11y", "fail", "a11y: SPA se nevyrenderovala, nebylo co zkontrolovat",
                          duration_s=run.duration_s)
    return replace(res, details="SPA, vyrenderovaný DOM — " + res.details)


def _a11y_from_pages(run: AppRun) -> GateResult | None:
    """Statická kontrola HTML stránek běžící aplikace; None = žádná HTML stránka."""
    findings: list[tuple[str, str, str]] = []
    checked = 0
    for path, st, body, ctype in run.pages:
        if st is None or st >= 400 or not body.strip():
            continue
        if ctype and not _is_html_ctype(ctype):
            continue
        if not ctype and not body.lstrip().startswith(("<!", "<h", "<H")):
            continue
        checked += 1
        findings += [(path, sev, msg) for sev, msg in a11y_html.analyze(body)]
        if checked >= A11Y_MAX_PAGES:
            break
    if not checked:
        return None
    fails = sum(1 for f in findings if f[1] == a11y_html.FAIL)
    if not findings:
        return GateResult("a11y", "pass", f"a11y: {checked} stránek zkontrolováno staticky, "
                          "0 nálezů (lehká kontrola, ne axe-core)", metric=0,
                          duration_s=run.duration_s)
    return GateResult("a11y", "fail" if fails else "warn", a11y_html.summarize(findings, checked),
                      metric=len(findings), duration_s=run.duration_s)


def gate_a11y(ctx: Ctx) -> GateResult:
    """Statická kontrola stránek běžící aplikace; jinak heuristika nad UI soubory."""
    if ctx.stack.other and not apprun.read_preview_config(ctx.path).get("command"):
        return _gate_other_stack("a11y", ctx.path, ctx.stack.other)
    files = list(_iter_files(ctx.path, (".html", ".jsx", ".tsx", ".vue", ".svelte")))
    run = _app_run(ctx)
    if run.state == "ok" and run.spa:
        return _a11y_spa(run)
    if run.state == "ok":
        res = _a11y_from_pages(run)
        if res is not None:
            return res
        if not files:
            return _skip("a11y", "aplikace nevrací žádné HTML stránky (jen API?)")
    elif not files:
        if run.state == "deps":
            return replace(run.block, gate_type="a11y")  # type: ignore[arg-type]
        if run.state == "down":
            return _unverified("a11y", "aplikace nenaběhla", f"{run.why} (`{run.command}`)")
        return _unverified("a11y", "chybí příkaz pro spuštění",
                           "doplňte `[preview] command = \"… {port}\"` do .pflanzer/project.toml "
                           "v target repu; bez UI souborů nejde a11y ověřit")
    return _a11y_heuristic(ctx, files)


def gate_coverage(ctx: Ctx) -> GateResult:
    if ctx.stack.other:
        return _gate_other_stack("coverage", ctx.path, ctx.stack.other)
    st = ctx.stack
    has_tool = st.node and "vitest" in st.deps and any(
        k in st.deps for k in ("@vitest/coverage-v8", "@vitest/coverage-istanbul"))
    if not has_tool:
        if st.python and not st.node:
            return _unverified("coverage", "chybí příkaz pro coverage",
                               "coverage se pro Python nespouští automaticky — doporučeno "
                               "`pytest --cov` (pytest-cov); příkaz definuj v pflanzer.gates.json")
        if st.node and "vitest" in st.deps:
            return _unverified("coverage", "chybí coverage nástroj",
                               "k vitestu chybí `@vitest/coverage-v8`")
        return _unverified("coverage", "chybí coverage nástroj",
                           "doporučeno `node --test --experimental-test-coverage` nebo `c8` "
                           "(příkaz definuj v pflanzer.gates.json)")
    if (s := _needs_deps(ctx, "coverage")):
        return s
    rc, out, err = _run(["npx", "--no-install", "vitest", "run", "--coverage", "--reporter=verbose"],
                        ctx.path, timeout=180)
    m = re.search(r"All files\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)", out)
    if not m:
        return GateResult("coverage", "warn", "coverage report se nepodařilo přečíst", metric=None)
    branch_pct = float(m.group(2))
    if branch_pct >= COVERAGE_TARGET:
        return GateResult("coverage", "pass",
                          f"Branch coverage {branch_pct:.1f} % (cíl {COVERAGE_TARGET})", metric=branch_pct)
    if branch_pct >= 30:
        return GateResult("coverage", "warn",
                          f"Branch coverage {branch_pct:.1f} % < cíl {COVERAGE_TARGET} %", metric=branch_pct)
    return GateResult("coverage", "fail",
                      f"Branch coverage {branch_pct:.1f} % je kriticky nízká (< 30 %)", metric=branch_pct)


def _tail(text: str, n: int) -> str:
    """Posledních ~n znaků výstupu, začíná na celém řádku (ne uprostřed slova)."""
    text = text.strip()
    if len(text) <= n:
        return text
    cut = text[-n:]
    nl = cut.find("\n")
    return cut[nl + 1:].strip() if 0 <= nl < len(cut) - 1 else cut.lstrip()


def _tests_fail_phrase(n: int) -> str:
    return f"{n} test padá" if n == 1 else f"{n} testy padají" if 2 <= n <= 4 else f"{n} testů padá"


def _runner_counts(output: str) -> tuple[Any, Any]:
    """(match passed, match failed) z řádku Tests vitestu / jestu (jinak None, None)."""
    m = re.search(r"^\s*Tests:?\s+(.*)$", output, re.M)
    line = m.group(1) if m else ""
    return (re.search(r"(\d+) passed", line), re.search(r"(\d+) failed", line))


def _node_strip_flag(node: str) -> str | None:
    """Příznak pro spuštění .ts testů v `node --test`: "" nic netřeba (Node >= 22.18 / 23.6),
    `--experimental-strip-types` (22.6+), None = Node to neumí / není zjistitelný."""
    try:
        r = subprocess.run([node, "--version"], capture_output=True, text=True, timeout=10)
        m = re.match(r"v(\d+)\.(\d+)", r.stdout.strip())
    except (OSError, subprocess.SubprocessError):
        return None
    if not m:
        return None
    ver = (int(m.group(1)), int(m.group(2)))
    if ver >= (24, 0) or (23, 6) <= ver < (24, 0) or (22, 18) <= ver < (23, 0):
        return ""
    if ver >= (22, 6):
        return "--experimental-strip-types"
    return None


_TS_RUNNER_RE = re.compile(r"\b(?:tsx|ts-node|ts-node-esm|esbuild-register)\b|--(?:import|loader|experimental-loader|require)\b")
_MODULE_ERR_RE = re.compile(
    r"ERR_MODULE_NOT_FOUND|Cannot find module|Unknown file extension [\"']?\.[cm]?ts|ERR_UNKNOWN_FILE_EXTENSION")


def _ts_test_runner(script: str, node: str) -> list[str] | None:
    """Prefix příkazu (bez `--test` a souborů) z `scripts.test`, který spouští .ts testy přes
    tsx / ts-node / `--import tsx` / `--loader`: `tsx --test …`, `npx tsx --test …`,
    `node --import tsx --test …`. None = script takový runner nepoužívá."""
    import shlex
    for seg in re.split(r"&&|\|\||;", script or ""):
        if "--test" not in seg or not _TS_RUNNER_RE.search(seg):
            continue
        try:
            toks = shlex.split(seg)
        except ValueError:
            continue
        if "--test" not in toks:
            continue
        prefix = [t for t in toks[:toks.index("--test")] if not re.match(r"^\w+=", t)]
        if not prefix:
            continue
        head = prefix[0]
        if head == "node":
            prefix[0] = node
        elif head in ("tsx", "ts-node", "ts-node-esm"):
            prefix = ["npx", "--no-install", *prefix]
        elif head == "npx" and "--no-install" not in prefix and "--no" not in prefix:
            prefix.insert(1, "--no-install")
        elif head not in ("npx",):
            continue
        return prefix
    return None


def _native_acceptance(ctx: Ctx, acc_dir: Path) -> GateResult | None:
    """Akceptační testy v běžném test runneru projektu (node --test / pytest) — tak je
    buildeři píší nejčastěji. None = žádné takové testy (zkusí se Playwright)."""
    st = ctx.stack
    if st.node:
        files = sorted(str(f.relative_to(ctx.path)) for f in acc_dir.rglob("*")
                       if f.is_file() and re.search(r"\.test\.[cm]?[jt]sx?$", f.name))
        if not files:
            return None
        deps = st.deps or {}
        if "vitest" in deps or "jest" in deps:
            runner = "vitest" if "vitest" in deps else "jest"
            if (missing := _needs_deps(ctx, "acceptance")):
                return missing
            cmd = ["npx", "--no-install", runner] + (["run"] if runner == "vitest" else []) \
                + ["tests/acceptance"]
            rc, out, err = _run(cmd, ctx.path, timeout=300)
            m_pass, m_fail = _runner_counts(out + "\n" + err)
        else:
            node = os.environ.get("PFLANZER_NODE", "node")
            script = (getattr(st, "scripts", None) or {}).get("test", "")
            runnable = [f for f in files if re.search(r"\.test\.(?:[cm]?js|[cm]?ts)$", f)]
            ts_prefix = _ts_test_runner(script, node)
            if ts_prefix is not None and runnable:
                if (missing := _needs_deps(ctx, "acceptance")):
                    return missing
                files = runnable
                rc, out, err = _run([*ts_prefix, "--test", *files], ctx.path, timeout=300)
            elif re.search(r"\bnode\b[^&|;]*--test", script) and re.search(
                    r"acceptance|tests?/\*\*", script) and _has("npm"):
                # `npm test` projektu je node --test a pokrývá tests/acceptance -> spustit jím
                files = runnable or files
                rc, out, err = _run(["npm", "test", "--silent"], ctx.path, timeout=300)
            else:
                if not runnable:
                    return _unverified("acceptance", "testy .tsx bez vitest/jest",
                                       "v tests/acceptance/ jsou jen .tsx testy, které node "
                                       "neumí spustit — přidejte `npm i -D vitest`")
                flag = _node_strip_flag(node)
                if any(re.search(r"\.[cm]?ts$", f) for f in runnable) and flag is None:
                    return _unverified("acceptance", "testy .ts bez vitest/jest a Node < 22.6",
                                       "v tests/acceptance/ jsou TypeScript testy; potřebují "
                                       "Node >= 22.6 (`--experimental-strip-types`) nebo "
                                       "`npm i -D vitest`")
                files = runnable
                rc, out, err = _run([node, "--test", *([flag] if flag else []), *files],
                                    ctx.path, timeout=300)
            m_pass = re.search(r"^(?:#|ℹ) pass (\d+)", out, re.M)
            m_fail = re.search(r"^(?:#|ℹ) fail (\d+)", out, re.M)
            if rc != 0 and _MODULE_ERR_RE.search(out + "\n" + err):
                # selhal samotný runner (modul / přípona .ts), ne akceptační scénář -> ne FAIL
                return _unverified(
                    "acceptance", "test runner neumí načíst .ts moduly (ERR_MODULE_NOT_FOUND)",
                    "akceptační testy nešly spustit stejným runnerem jako `npm test`; do "
                    "pflanzer.gates.json přidejte adaptér acceptance.cmd, např. "
                    "`npx --no-install tsx --test tests/acceptance/*.test.ts` "
                    "(`pflanzer init gates-template`)\n" + _tail(out + err, 300))
    elif st.python:
        files = sorted(str(f.relative_to(ctx.path)) for f in acc_dir.rglob("test_*.py"))
        if not files:
            return None
        rc, out, err = _run([_python_cmd(ctx.path), "-m", "pytest", "-q", *files],
                            ctx.path, timeout=300)
        m_pass = re.search(r"(\d+) passed", out)
        m_fail = re.search(r"(\d+) failed", out)
    else:
        return None
    passed = int(m_pass.group(1)) if m_pass else 0
    failed = int(m_fail.group(1)) if m_fail else (0 if rc == 0 else 1)
    total = passed + failed
    if total == 0:
        return _unverified("acceptance", "v tests/acceptance/ nejsou žádné spustitelné testy")
    rate = round(100 * passed / total)
    label = f"{passed}/{total} akceptačních testů ({rate} %, {len(files)} soubor/ů)"
    if rate >= 80 and rc == 0:
        return GateResult("acceptance", "pass", label, metric=rate)
    if rate >= 80:  # poměr stačí, ale běh skončil chybou: nelhat o „< cíl 80 %“
        n_bad = failed if failed else 1
        return GateResult("acceptance", "warn",
                          f"{label} — {_tests_fail_phrase(n_bad)}\n" + _tail(out + err, 400),
                          metric=rate)
    if rate >= 50:
        return GateResult("acceptance", "warn", f"{label} < cíl 80 %", metric=rate)
    return GateResult("acceptance", "fail", f"{label} — varianta neplní zadání\n"
                      + _tail(out + err, 400), metric=rate)


def gate_acceptance(ctx: Ctx) -> GateResult:
    if ctx.stack.other:
        return _gate_other_stack("acceptance", ctx.path, ctx.stack.other)
    """Playwright acceptance scénáře z `tests/acceptance/` (zadání Deciderem při Kickoffu)."""
    acc_dir = ctx.path / "tests" / "acceptance"
    if not acc_dir.exists():
        return _unverified("acceptance", "tests/acceptance/ neexistuje",
                           "kritéria nejsou v kódu jako spustitelné testy")
    st = ctx.stack
    native = _native_acceptance(ctx, acc_dir)
    runner_deps = bool(st.node and {"vitest", "jest"} & set(st.deps or {}))
    if native is not None and (runner_deps or not (st.node and "@playwright/test" in st.deps)):
        return native
    if not (st.node and "@playwright/test" in st.deps):
        if st.python and not st.node:
            return _unverified("acceptance", "chybí akceptační testy",
                               "scénáře v tests/acceptance/*.feature jsou, ale chybí k nim "
                               "spustitelné testy — napište je do tests/acceptance/test_*.py")
        return _unverified("acceptance", "chybí akceptační testy",
                           "scénáře v tests/acceptance/*.feature jsou, ale chybí k nim "
                           "spustitelné testy — napište je do tests/acceptance/*.test.{js,ts,tsx} "
                           "(node --test / vitest / jest), nebo použijte @playwright/test")
    if (s := _needs_deps(ctx, "acceptance")):
        return s
    rc, out, err = _run(["npx", "--no-install", "playwright", "test", "tests/acceptance",
                         "--reporter=json"], ctx.path, timeout=300)
    try:
        json_start = out.find("{")
        if json_start < 0:
            raise ValueError("no JSON in output")
        report = json.loads(out[json_start:])
        stats = report.get("stats", {})
        passed = stats.get("expected", 0)
        failed = stats.get("unexpected", 0)
        total = passed + failed
        if total == 0:
            return _unverified("acceptance", "žádné acceptance scénáře nenalezeny")
        pass_rate = round(100 * passed / total)
        if pass_rate >= 80:
            return GateResult("acceptance", "pass", f"{passed}/{total} scénářů ({pass_rate} %)",
                              metric=pass_rate)
        if pass_rate >= 50:
            return GateResult("acceptance", "warn",
                              f"{passed}/{total} scénářů ({pass_rate} %) < cíl 80 %", metric=pass_rate)
        return GateResult("acceptance", "fail",
                          f"{passed}/{total} scénářů ({pass_rate} %) - varianta neplní zadání",
                          metric=pass_rate)
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        if rc == 0:
            return GateResult("acceptance", "warn", f"Playwright prošel, ale výstup nešel přečíst: {e}")
        return GateResult("acceptance", "fail", _tail(out + err, 500))


def gate_observability(ctx: Ctx) -> GateResult:
    """Produkční kód by neměl mít `console.*` bez kontextu (jen JS/TS)."""
    if ctx.stack.other:
        return _gate_other_stack("observability", ctx.path, ctx.stack.other)
    src = ctx.path / "src"
    root = src if src.exists() else ctx.path
    exts = (".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx")
    files = []
    for f in _iter_files(root, exts):
        rel = f.relative_to(root).parts
        if (_TEST_FILE_RE.search(f.name) or ".config." in f.name
                or any(p in ("test", "tests", "__tests__", "scripts") for p in rel[:-1])):
            continue
        files.append(f)
    if not files:
        if ctx.stack.python and not ctx.stack.node:
            return _skip("observability", "kontrola `console.*` je jen pro JS/TS; "
                                          "pro Python se nevyhodnocuje")
        return _skip("observability", "žádné JS/TS zdrojové soubory")
    leaks = 0
    for f in files:
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        leaks += len(re.findall(r"console\.(log|debug|info|warn|error)\(", text))
    if leaks == 0:
        return GateResult("observability", "pass", f"Žádný console.* v {len(files)} souborech", metric=0)
    return GateResult("observability", "warn",
                      f"{leaks} console.* volání - před produkcí nahradit strukturovaným loggerem"
                      + (" (vysoký šum)" if leaks > 10 else ""), metric=leaks)


@dataclass
class AppRun:
    """Výsledek jednoho spuštění aplikace: stažené stránky (sdílí smoke a a11y)."""
    state: str                      # ok | nospec | deps | down
    command: str = ""
    why: str = ""
    log_tail: str = ""
    block: GateResult | None = None  # state == deps
    pages: list[tuple[str, int | None, str, str]] = field(default_factory=list)
    smoke_paths: list[str] = field(default_factory=list)
    duration_s: float = 0.0
    spa: bool = False                # `/` je prázdná kostra SPA (obsah staví až JS)
    bundles: list[tuple[str, int | None]] = field(default_factory=list)  # (url skriptu, status)
    render: "render.RenderResult | None" = None  # None = nerenderováno (bez Playwrightu)
    render_why: str = ""             # proč se renderovat nepovedlo / nešlo
    api_root_404: bool = False       # JSON API bez `/` a bez health: server odpověděl, smoke_paths chybí


A11Y_MAX_PAGES = 5


API_HEALTH_PATHS = ("/health", "/healthz", "/api/health", "/status", "/api")


def _app_run(ctx: Ctx) -> AppRun:
    """Spustí aplikaci (jednou na Ctx), stáhne `smoke_paths` a odkazy z první stránky."""
    if ctx.app_run is not None:
        return ctx.app_run
    ctx.app_run = _do_app_run(ctx)
    return ctx.app_run


def _do_app_run(ctx: Ctx) -> AppRun:
    cfg = apprun.read_preview_config(ctx.path)
    if ctx.stack.other and not cfg.get("command"):
        return AppRun("nospec")
    paths = cfg.get("smoke_paths")
    paths = [str(p) for p in paths if str(p).strip()] if isinstance(paths, list) else []
    paths = [p if p.startswith("/") else "/" + p for p in paths] or ["/"]
    port = apprun.free_port()
    spec = apprun.detect_run(ctx.path, port, api_port=apprun.free_port())
    if spec is None:
        return AppRun("nospec")
    if (missing := _needs_deps(ctx, "smoke")) is not None:
        return AppRun("deps", block=missing)
    started = time.monotonic()
    timeout = float(os.environ.get("PFLANZER_SMOKE_TIMEOUT", "60"))
    with tempfile.TemporaryDirectory(prefix="pflanzer-smoke-") as tmp:
        log = Path(tmp) / "app.log"
        proc = apprun.start_app(spec, log)
        try:
            base = f"http://127.0.0.1:{port}"
            up, _ = apprun.wait_http(base + paths[0], timeout=timeout, proc=proc,
                                     ok=lambda _s: True)
            if not up:
                why = ("aplikace skončila" if proc.poll() is not None
                       else f"aplikace do {int(timeout)} s neodpověděla")
                return AppRun("down", spec.command, why, apprun.tail(log, 8), smoke_paths=paths,
                              duration_s=round(time.monotonic() - started, 2))
            pages = [(p, *apprun.http_fetch(base + p)) for p in paths]
            if not cfg.get("smoke_paths") and pages[0][1] == 404:
                # API repo without a `/` route: a health endpoint proves the app is up.
                for hp in API_HEALTH_PATHS:
                    hit = (hp, *apprun.http_fetch(base + hp))
                    if hit[1] is not None and hit[1] < 400:
                        paths, pages = [hp], [hit]
                        break
            api_root_404 = (not cfg.get("smoke_paths") and pages[0][1] == 404
                            and "json" in (pages[0][3] or "").lower())
            first = next((pg for pg in pages if pg[1] is not None and pg[1] < 400 and pg[2]), None)
            spa = first is not None and render.is_spa(first[2])
            bundles: list[tuple[str, int | None]] = []
            rendered = None
            render_why = ""
            if spa and first is not None:
                bundles = [(u, apprun.http_get(u)) for u in
                           render.script_urls(first[2], base + first[0])]
                pw = render.find_playwright(ctx.path)
                if pw is None:
                    render_why = "Playwright není nainstalovaný"
                else:
                    rr = render.render_pages(base, paths[:A11Y_MAX_PAGES], pw)
                    rendered, render_why = (rr, "") if rr.ok else (None, rr.why)
            elif first is not None and len(pages) < A11Y_MAX_PAGES:
                for extra in a11y_html.same_host_links(first[2], base + first[0]):
                    if len(pages) >= A11Y_MAX_PAGES:
                        break
                    if extra not in [pg[0] for pg in pages]:
                        pages.append((extra, *apprun.http_fetch(base + extra)))
        finally:
            apprun.kill_group(proc.pid)
    return AppRun("ok", spec.command, smoke_paths=paths, pages=pages,
                  duration_s=round(time.monotonic() - started, 2), spa=spa, bundles=bundles,
                  render=rendered, render_why=render_why, api_root_404=api_root_404)


def gate_smoke(ctx: Ctx) -> GateResult:
    """Aplikace vítěze naběhne a `/` (a `smoke_paths`) odpoví < 400; potom se ukončí."""
    run = _app_run(ctx)
    if run.state == "nospec":
        return _unverified("smoke", "chybí příkaz pro spuštění",
                           "doplňte `[preview] command = \"… {port}\"` do .pflanzer/project.toml "
                           "v target repu")
    if run.state == "deps":
        return run.block  # type: ignore[return-value]
    if run.state == "down":
        return GateResult("smoke", "fail", f"smoke: {run.why} (`{run.command}`)\n{run.log_tail}",
                          duration_s=run.duration_s)
    seen = [(p, st) for p, st, _b, _c in run.pages if p in run.smoke_paths]
    bad = [(p, st) for p, st in seen if st is None or st >= 400]
    text = ", ".join(f"{p} odpovídá {st if st is not None else 'nic'}" for p, st in seen)
    if bad and run.api_root_404:
        return GateResult("smoke", "pass", "smoke: API běží (`/` vrací JSON 404) — pro "
                          "přesnou kontrolu doplňte `smoke_paths = [\"/vas-endpoint\"]` do "
                          "[preview] v .pflanzer/project.toml", metric=0, duration_s=run.duration_s)
    if bad:
        return GateResult("smoke", "fail", f"smoke: {text}", metric=len(bad),
                          duration_s=run.duration_s)
    if run.spa:
        return _smoke_spa(run)
    return GateResult("smoke", "pass", f"smoke: {text}", metric=0, duration_s=run.duration_s)


def _smoke_spa(run: AppRun) -> GateResult:
    """SPA: surové HTML je jen kostra; plný pass jen s renderem, jinak pass s poznámkou."""
    bad_b = [(u, st) for u, st in run.bundles if st is None or st >= 400]
    if bad_b:
        u, st = bad_b[0]
        return GateResult("smoke", "fail", f"smoke: SPA — JS bundle {u} odpovídá "
                          f"{st if st is not None else 'nic'}", metric=len(bad_b),
                          duration_s=run.duration_s)
    if run.render is not None:
        pgs = run.render.pages
        bad = [p for p in pgs if p.broken]
        if bad:
            p = bad[0]
            why = (f"uncaught chyba: {p.errors[0]}" if p.errors else
                   "prázdný root (SPA se nevykreslila)" if p.root_empty else f"status {p.status}")
            return GateResult("smoke", "fail", f"smoke: SPA se nevyrenderovala — {p.path}: {why}",
                              metric=len(bad), duration_s=run.duration_s)
        n_con = sum(len(p.console_errors) for p in pgs)
        extra = f", {n_con}× console.error" if n_con else ""
        return GateResult("smoke", "pass", f"smoke: SPA vyrenderována v prohlížeči ({len(pgs)} "
                          f"stránek, root neprázdný, 0 uncaught chyb{extra})", metric=0,
                          duration_s=run.duration_s)
    ok_b = f" + JS bundle 200 ({len(run.bundles)})" if run.bundles else ""
    why = f" ({run.render_why})" if run.render_why else ""
    return GateResult("smoke", "pass", f"smoke: SPA — HTML kostra 200{ok_b}, render neověřen"
                      f"{why}", metric=0, duration_s=run.duration_s)


GATE_RUNNERS = {
    "build": gate_build,
    "types": gate_types,
    "lint": gate_lint,
    "tests": gate_tests,
    "coverage": gate_coverage,
    "smoke": gate_smoke,
    "acceptance": gate_acceptance,
    "security": gate_security,
    "a11y": gate_a11y,
    "observability": gate_observability,
}


# --------------------------------------------------------------------------
# Gate adapter (pflanzer.gates.yml) — audit N7
# --------------------------------------------------------------------------


class AdapterError(ValueError):
    """Adaptér bran nejde přečíst. Zpráva je lidská věta; Ship ji ukáže, brány se potichu nevypnou."""


ADAPTER_FILENAMES = ("pflanzer.gates.yml", "pflanzer.gates.yaml", "pflanzer.gates.json")
ADAPTER_DEFAULT_TIMEOUT = 600
ADAPTER_RESERVED_KEYS = {"version"}
THRESHOLD_KEYS = ("fail_below", "warn_below", "fail_above", "warn_above")


def find_gates_adapter(path: Path) -> Path | None:
    """Nearest adapter file in `path` or its parents, up to the git root.

    Without any git root above `path`, only `path` itself is checked, so a
    stray file somewhere up the filesystem is never picked up.
    """
    path = Path(path).resolve()
    chain = [path, *path.parents]
    git_idx = next((i for i, d in enumerate(chain) if (d / ".git").exists()), None)
    for directory in (chain[: git_idx + 1] if git_idx is not None else [path]):
        for name in ADAPTER_FILENAMES:
            candidate = directory / name
            if candidate.is_file():
                return candidate
    return None


def load_gates_adapter(adapter: Path) -> dict[str, Any]:
    """Parse the adapter into {gate: spec}. Raises ValueError on bad input."""
    text = adapter.read_text(encoding="utf-8")
    if adapter.suffix == ".json":
        data = json.loads(text)  # JSONDecodeError is a ValueError
    else:
        try:
            import yaml  # optional: PyYAML is not a hard dependency
        except ImportError as e:
            raise ValueError(
                f"{adapter.name} je YAML a PyYAML není nainstalovaný. Nejjednodušší: převeď "
                "adaptér na JSON (pflanzer.gates.json; vzor: `pflanzer init gates-template "
                "--format json`, pak smaž pflanzer.gates.yml). Nebo doinstaluj PyYAML do "
                "prostředí, kde běží pflanzer (`python3 -m venv ~/.pflanzer/venv && "
                "~/.pflanzer/venv/bin/pip install pyyaml`, případně `pipx inject`)") from e
        try:
            data = yaml.safe_load(text)
        except yaml.YAMLError as e:
            raise ValueError(f"{adapter.name}: neplatné YAML ({e})") from e
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"{adapter.name}: nejvyšší úroveň musí být objekt {{název_brány: nastavení}}")
    return data


def _run_adapter_gate(gate: str, spec: Any, adapter: Path, path: Path,
                      cwd_base: Path | None = None) -> GateResult:
    """Run one gate as declared in the adapter file.

    `cwd` resolves against `cwd_base` (default: the adapter's directory).
    """
    name = adapter.name
    if spec is None or spec is False:
        return _unavailable(gate, f"vypnuto v {name}")
    if isinstance(spec, str):
        spec = {"cmd": spec}
    if not isinstance(spec, dict):
        return GateResult(gate, "skipped", f"{name}: `{gate}` musí být objekt nebo příkaz jako text")
    if spec.get("builtin"):
        return GATE_RUNNERS[gate](_make_ctx(path)[0])

    cmd = spec.get("cmd")
    if not isinstance(cmd, str) or not cmd.strip():
        return GateResult(gate, "skipped", f"{name}: u `{gate}` chybí `cmd` (příkaz)")
    cwd = ((cwd_base or adapter.parent) / str(spec.get("cwd") or ".")).resolve()
    if not cwd.is_dir():
        return GateResult(gate, "skipped", f"{name}: složka `{gate}.cwd` neexistuje: {cwd}")

    parse = str(spec.get("parse") or "exit_code")
    pattern: re.Pattern[str] | None = None
    if parse.startswith("regex:"):
        try:
            pattern = re.compile(parse[len("regex:"):], re.MULTILINE)
        except re.error as e:
            return GateResult(gate, "skipped", f"{name}: `{gate}.parse` má neplatný regulární výraz: {e}")
        if "metric" not in pattern.groupindex:
            return GateResult(gate, "skipped",
                              f"{name}: regex v `{gate}.parse` potřebuje pojmenovanou skupinu (?P<metric>...)")
    elif parse != "exit_code":
        return GateResult(gate, "skipped",
                          f"{name}: `{gate}.parse` musí být exit_code nebo regex:<vzor>")

    thresholds: dict[str, float] = {}
    for key in THRESHOLD_KEYS:
        if spec.get(key) is None:
            continue
        try:
            thresholds[key] = float(spec[key])
        except (TypeError, ValueError):
            return GateResult(gate, "skipped", f"{name}: `{gate}.{key}` musí být číslo")
    try:
        timeout = int(spec.get("timeout") or ADAPTER_DEFAULT_TIMEOUT)
    except (TypeError, ValueError):
        return GateResult(gate, "skipped", f"{name}: `{gate}.timeout` musí být celé číslo")

    started = time.monotonic()
    rc, out, err = _run(cmd, cwd, timeout=timeout)
    duration = round(time.monotonic() - started, 2)
    tail = _tail(out + err, 500)
    shown = f"`{cmd}`"
    if rc == 127:  # shell: command not found -> same rule as a missing binary
        res = _unavailable(gate, f"{shown}: příkaz nenalezen", tail)
        res.duration_s = duration
        return res

    metric: float | None = None
    if pattern is not None:
        match = pattern.search(out + "\n" + err)
        if match and match.group("metric") is not None:
            try:
                metric = float(match.group("metric").replace(",", "."))
            except ValueError:
                metric = None

    if rc != 0:
        return GateResult(gate, "fail", f"{shown} skončil s kódem {rc}\n{tail}",
                          metric=metric, duration_s=duration)
    if pattern is None:
        return GateResult(gate, "pass", f"{shown} OK (kód 0)", duration_s=duration)
    if metric is None:
        return GateResult(gate, "warn", f"{shown} OK, ale regex nenašel žádnou metriku\n{tail}",
                          duration_s=duration)

    status = "pass"
    if (("fail_below" in thresholds and metric < thresholds["fail_below"])
            or ("fail_above" in thresholds and metric > thresholds["fail_above"])):
        status = "fail"
    elif (("warn_below" in thresholds and metric < thresholds["warn_below"])
            or ("warn_above" in thresholds and metric > thresholds["warn_above"])):
        status = "warn"
    limits = ", ".join(f"{k}={v:g}" for k, v in thresholds.items()) or "bez prahů"
    return GateResult(gate, status, f"{shown}: metrika {metric:g} ({limits})",
                      metric=metric, duration_s=duration)


def _run_adapter(adapter: Path, path: Path, cwd_base: Path | None = None) -> list[GateResult]:
    try:
        specs = load_gates_adapter(adapter)
    except (OSError, ValueError) as e:
        raise AdapterError(f"Adaptér bran {adapter.name} nejde přečíst: {e}.") from e
    unknown = sorted(set(specs) - set(GATE_TYPES) - ADAPTER_RESERVED_KEYS)
    if unknown:
        print(f"[gates] warning: {adapter} has unknown gate(s) {unknown}; "
              f"known: {list(GATE_TYPES)}", file=sys.stderr)
    return [
        _run_adapter_gate(g, specs[g], adapter, path, cwd_base) if g in specs
        else (_skip("types", "typy kontroluje kompilátor (brána build)")
              if g == "types" and _other_stack(path) else
              _unavailable(g, "není definovaná", f"doplň ji do {adapter.name}"))
        for g in GATE_TYPES
    ]


def describe_gate_source(path: Path, adapter_path: Path | None = None) -> str:
    """Čitelný původ příkazů bran (soubor adaptéru, nebo autodetekce)."""
    if adapter_path is not None:
        adapter = Path(adapter_path)
        if not adapter.is_file():
            return f"external adapter {adapter.name} (MISSING — all gates skipped)"
        digest = hashlib.sha256(adapter.read_bytes()).hexdigest()[:12]
        return (f"external adapter {adapter.name} (sha256 {digest}; "
                "supplied by caller, not read from the worktree)")
    adapter = find_gates_adapter(path)
    if adapter is None:
        st = detect_stack_info(Path(path))
        return f"autodetect (stack: {st.label})"
    digest = hashlib.sha256(adapter.read_bytes()).hexdigest()[:12]
    return f"adapter {adapter.name} (sha256 {digest}; read from the checked tree)"


def _make_ctx(path: Path) -> tuple[Ctx, Stack, tuple[bool, str]]:
    st = detect_stack_info(path)
    deps = prepare_deps(st)
    return Ctx(path=path, stack=st, deps_ok=deps[0], deps_reason=deps[1]), st, deps


def evaluate_path(path: Path, adapter_path: Path | None = None,
                  ) -> tuple[Stack, list[GateResult], dict[str, Any], tuple[bool, str]]:
    """Bez DB: stack -> brány (adaptér, nebo autodetekce) -> skóre."""
    path = Path(path).resolve()
    ctx, st, deps = _make_ctx(path)
    if adapter_path is not None:
        results = _run_adapter(Path(adapter_path).resolve(), path, cwd_base=path)
    else:
        adapter = find_gates_adapter(path)
        if adapter is not None:
            results = _run_adapter(adapter, path)
        else:
            results = [GATE_RUNNERS[g](ctx) for g in GATE_TYPES]
    return st, results, aggregate_score(results), deps


def run_gates_on_path(path: Path, adapter_path: Path | None = None) -> list[GateResult]:
    """Pusť všechny brány nad adresářem bez DB.

    `adapter_path` zadán -> ten adaptér, `cwd` relativně k `path` (adaptér z base branche).
    Jinak nejbližší adaptér ve stromu (`cwd` relativně k němu), jinak autodetekce.
    Počty reálně spuštěných bran dává `aggregate_score()` (`gates_run`, `gates_unsupported`).
    """
    return evaluate_path(path, adapter_path)[1]


# --------------------------------------------------------------------------
# Aggregate score
# --------------------------------------------------------------------------


STATUS_VALUES = {"pass": 1.0, "warn": 0.5, "fail": 0.0, "skipped": None, "unsupported": None}


def gates_sufficiency(results: list[Any]) -> dict[str, Any]:
    """Minimum důkazů pro verdikt: >= MIN_GATES_RUN spuštěných bran včetně build a tests.

    Brány SKIP / unsupported se nepočítají. Přijímá `GateResult` i dicty `{gate, status}`.
    """
    ran = []
    for r in results:
        gate = r.gate_type if hasattr(r, "gate_type") else r.get("gate")
        status = r.status if hasattr(r, "status") else r.get("status")
        if status in RAN_STATUSES:
            ran.append(gate)
    missing = [g for g in REQUIRED_GATES if g not in ran]
    sufficient = len(ran) >= MIN_GATES_RUN and not missing
    detail = f"{len(ran)}/{len(GATE_TYPES)} run"
    if missing:
        detail += f", missing: {', '.join(missing)}"
    elif len(ran) < MIN_GATES_RUN:
        detail += f", min {MIN_GATES_RUN}"
    return {
        "gates_run": len(ran), "missing": missing, "sufficient": sufficient,
        "blocker": None if sufficient else f"gates:insufficient ({detail})",
    }


def aggregate_score(results: list[GateResult]) -> dict[str, Any]:
    """Skóre 0–100 z aplikovatelných bran (skipped / unsupported mimo jmenovatel)."""
    total_weight = 0.0
    earned = 0.0
    applicable = 0
    counts = {"pass": 0, "warn": 0, "fail": 0, "skipped": 0, "unsupported": 0}
    for r in results:
        counts[r.status] += 1
        val = STATUS_VALUES.get(r.status)
        if val is None:
            continue
        weight = GATE_WEIGHTS.get(r.gate_type, 1.0)
        applicable += 1
        total_weight += weight
        earned += val * weight

    score = round(100 * earned / total_weight) if total_weight > 0 else 0
    score = max(0, min(100, score))
    suff = gates_sufficiency(results)
    return {
        "gate_score": score,
        "counts": counts,
        "applicable_gates": applicable,
        "total_gates": len(results),
        # reálně spuštěné brány (pass/warn/fail); unsupported / SKIP vypadávají ze jmenovatele
        "gates_run": counts["pass"] + counts["warn"] + counts["fail"],
        "gates_unsupported": counts["unsupported"],
        "gates_total": len(results),
        "sufficient": suff["sufficient"],
        "sufficiency_blocker": suff["blocker"],
        "low_confidence": not suff["sufficient"],
        "weight_applicable": round(total_weight, 2),
        "weight_earned": round(earned, 2),
    }


# --------------------------------------------------------------------------
# Persistence + render
# --------------------------------------------------------------------------


def run_all(extracted_id: int, adapter_path: Path | None = None) -> dict[str, Any]:
    with transaction() as conn:
        ext = conn.execute(
            """
            SELECT e.id, e.local_path, e.variant_id, v.name, s.project_id, p.slug,
                   p.production_readiness_target
            FROM extracted_code e
            JOIN variants v ON v.id = e.variant_id
            JOIN sessions s ON s.id = v.session_id
            JOIN projects p ON p.id = s.project_id
            WHERE e.id = ?
            """,
            (extracted_id,),
        ).fetchone()
        if not ext:
            raise ValueError(f"Načtený kód č. {extracted_id} neexistuje. "
                         "Nejdřív `pflanzer extract --slug … --variant …`.")

    local_path = REPO_ROOT / ext[1] if not Path(ext[1]).is_absolute() else Path(ext[1])
    if not local_path.exists():
        raise ValueError(f"Složka s kódem varianty neexistuje: {display_path(local_path)}")

    project_id = int(ext[4])
    slug = ext[5]
    variant_name = ext[3]
    target = int(ext[6]) if ext[6] is not None else 80

    gate_source = describe_gate_source(local_path, adapter_path)
    stack, results, score_info, deps = evaluate_path(local_path, adapter_path)
    if not deps[0]:
        print(f"[gates] pozor: {deps[1]}; gates závislé na instalaci jsou SKIP", file=sys.stderr)
    score = score_info["gate_score"]
    unv = unverified_gates(results)

    with transaction() as conn:
        conn.execute("DELETE FROM quality_gates WHERE extracted_id = ?", (extracted_id,))
        for r in results:
            conn.execute(
                """
                INSERT INTO quality_gates (
                    extracted_id, gate_type, status, details_md, metric_value, ran_by
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (extracted_id, r.gate_type, r.status, r.details[:2000], r.metric, current_actor()),
            )
        conn.execute(
            "UPDATE projects SET gate_score_latest = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (score, project_id),
        )
        audit(
            conn, action="quality_gates.run",
            target_type="extracted_code", target_id=extracted_id,
            payload={
                "slug": slug, "variant": variant_name, "score": score,
                "target": target, "ready": score >= target,
                "stack": stack.label,
                "applicable_gates": score_info["applicable_gates"],
                "gates_run": score_info["gates_run"], "gate_source": gate_source,
            },
        )

    GATES_DIR.mkdir(parents=True, exist_ok=True)
    project_dir = GATES_DIR / slug
    project_dir.mkdir(parents=True, exist_ok=True)
    md_path = project_dir / f"quality-{variant_name}.md"
    md_path.write_text(_render_md(slug, variant_name, results, score_info, target, stack,
                                  gate_source),
                       encoding="utf-8")

    return {
        "extracted_id": extracted_id,
        "slug": slug,
        "variant": variant_name,
        "local_path": display_path(local_path),
        "stack": stack.label,
        "gate_score": score,
        "target": target,
        "score_display": f"{score}/100 (práh {target})",
        "production_ready": (score >= target and score_info["sufficient"]
                             and not (target >= PRODUCTION_TARGET and acceptance_unverified(unv))),
        "unverified": unv,
        "applicable_gates": score_info["applicable_gates"],
        "total_gates": score_info["total_gates"],
        "gates_run": score_info["gates_run"],
        "gates_unsupported": score_info["gates_unsupported"],
        "gate_source": gate_source,
        "sufficient": score_info["sufficient"],
        "sufficiency_blocker": score_info["sufficiency_blocker"],
        "low_confidence": score_info["low_confidence"],
        "counts": score_info["counts"],
        "summary_path": display_path(md_path),
        "summary_line": gates_summary_line(score, results),
        "results": [
            {"gate": r.gate_type, "status": r.status,
             "metric": r.metric, "details": r.details[:RESULT_DETAIL_LIMIT]}
            for r in results
        ],
    }


def skip_reason(result: Any) -> str:
    """Důvod, proč brána neběžela (z `details`), celý a bez zalomení."""
    details = result.details if hasattr(result, "details") else result.get("details", "")
    text = " ".join((details or "").split())
    if text.upper().startswith("SKIP:"):
        text = text[5:].strip()
    elif text.startswith(UNVERIFIED_PREFIX):
        text = text[len(UNVERIFIED_PREFIX):].strip()
    return text


def unverified_gates(results: list[Any]) -> list[dict[str, str]]:
    """Brány, které by dávaly smysl, ale neběžely (chybí nástroj / konfigurace).

    Vrací `[{"gate": "acceptance", "reason": "chybí @playwright/test", "detail": "…"}]`;
    přijímá `GateResult` i dicty `{gate, status, details}`.
    """
    out: list[dict[str, str]] = []
    for r in results:
        status = r.status if hasattr(r, "status") else r.get("status")
        if status in RAN_STATUSES:
            continue
        details = (r.details if hasattr(r, "details") else r.get("details", "")) or ""
        text = " ".join(details.split())
        if not text.startswith(UNVERIFIED_PREFIX):
            continue
        gate = r.gate_type if hasattr(r, "gate_type") else r["gate"]
        body = text[len(UNVERIFIED_PREFIX):].strip()
        short, _, long = body.partition(" — ")
        out.append({"gate": gate, "reason": short.strip(), "detail": long.strip()})
    return out


def acceptance_unverified(unverified: list[dict[str, str]] | None) -> bool:
    return any(u["gate"] == "acceptance" for u in unverified or [])


def _brany(n: int) -> str:
    """„z 1 brány“ / „ze 4 bran“ / „z 5 bran“ — předložka podle čísla."""
    prep = "ze" if n in (2, 3, 4, 6, 7) else "z"
    return f"{prep} {n} {'brány' if n == 1 else 'bran'}"


def gates_summary_line(score: int, results: list[Any], reasons: bool = False) -> str:
    """Jedna krátká věta o skóre.

    „76/100 · 3 brány neběžely (coverage, acceptance, a11y)“; když běžely < 5 bran:
    „100/100 jen ze 4 bran — orientační“. Brány, které by dávaly smysl, ale chybí nástroj,
    jsou zvlášť: „100/100 ze 5 spuštěných · NEOVĚŘENO: acceptance (chybí @playwright/test)“.
    Důvody SKIP jsou jen s `reasons=True` (jinak je najdete v `skip_reasons`).
    """
    def g(r: Any) -> str:
        return r.gate_type if hasattr(r, "gate_type") else r["gate"]

    def st(r: Any) -> str:
        return r.status if hasattr(r, "status") else r["status"]

    unv = unverified_gates(results)
    unv_names = {u["gate"] for u in unv}
    ran = [r for r in results if st(r) in RAN_STATUSES]
    missing = [r for r in results if st(r) not in RAN_STATUSES and g(r) not in unv_names]
    unv_txt = ("NEOVĚŘENO: " + ", ".join(f"{u['gate']} ({u['reason']})" for u in unv)) if unv else ""
    if len(ran) < MIN_SOLID_GATES:
        line = f"{score}/100 jen {_brany(len(ran))} — orientační"
        return f"{line} · {unv_txt}" if unv_txt else line
    line = f"{score}/100"
    if unv:
        prep = "ze" if 2 <= len(ran) <= 7 else "z"
        line += f" {prep} {len(ran)} spuštěných"
    if missing:
        n = len(missing)
        names = ", ".join(
            f"{g(r)}: {skip_reason(r)}" if reasons and skip_reason(r) else g(r) for r in missing)
        line += (f" · {n} {'brána neběžela' if n == 1 else 'brány neběžely' if n < 5 else 'bran neběželo'}"
                 f" ({names})")
    if unv_txt:
        line += f" · {unv_txt}"
    return line


def spa_line(results: list[Any]) -> str:
    """Řádek do souhrnu Shipu u SPA: co ověřil render a co ne (prázdný řetězec = ne-SPA)."""
    def details(r: Any) -> str:
        return (r.details if hasattr(r, "details") else r.get("details", "")) or ""

    def gate(r: Any) -> str:
        return r.gate_type if hasattr(r, "gate_type") else r.get("gate", "")

    smoke = next((r for r in results if gate(r) == "smoke"), None)
    if smoke is None or "SPA" not in details(smoke):
        return ""
    if "vyrenderována" in details(smoke):
        return ("SPA: ověřeno renderem v prohlížeči — smoke (stránka se vykreslila, bez uncaught "
                "chyb) a a11y (statická kontrola nad DOM)")
    if "render neověřen" not in details(smoke):
        return ""
    return ("SPA: render neověřen — smoke je jen HTML kostra + JS bundle, a11y NEOVĚŘENO "
            f"({render.INSTALL_HINT})")


def skip_reasons(results: list[Any]) -> list[str]:
    """Řádky „coverage — důvod celý“ pro brány, které neběžely (do reportu)."""
    out: list[str] = []
    for r in results:
        status = r.status if hasattr(r, "status") else r["status"]
        if status in RAN_STATUSES:
            continue
        gate = r.gate_type if hasattr(r, "gate_type") else r["gate"]
        details = r.details if hasattr(r, "details") else r.get("details", "")
        text = " ".join((details or "").split())
        if text.upper().startswith("SKIP:"):
            text = text[5:].strip()
        elif text.startswith(UNVERIFIED_PREFIX):
            text = "NEOVĚŘENO — " + text[len(UNVERIFIED_PREFIX):].strip()
        out.append(f"{gate} — {text or 'neběžela'}")
    return out


def a11y_reasons(details: str, limit: int = 3) -> list[str]:
    """První konkrétní důvody z a11y detailu („chybí <html lang>“, „chybí <title>“ …).

    Detail má tvar `a11y: N stránek zkontrolováno staticky\nzávažné · /cesta: důvod…`.
    Důvody se slučují (stejný text na víc stránkách = „(2 stránky)“), závažné jdou první.
    """
    seen: dict[str, int] = {}
    first_path: dict[str, str] = {}
    for line in (details or "").splitlines()[1:]:
        text = line.strip()
        if text.startswith("…"):
            continue
        m = re.match(r"^(?:závažné|doporučení)\s*·\s*(\S+?):\s*(.+)$", text)
        msg = (m.group(2) if m else text).strip()
        if msg:
            seen[msg] = seen.get(msg, 0) + 1
            first_path.setdefault(msg, m.group(1) if m else "/")
    out = []
    for msg, n in list(seen.items())[:limit]:
        if n >= 2:
            out.append(f"{msg} ({n} {'stránky' if n < 5 else 'stránek'})")
        else:  # jediná stránka: uveď cestu, ať jde nález dohledat (kromě kořene)
            p = first_path[msg]
            out.append(msg if p == "/" else f"{p}: {msg}")
    return out


# --------------------------------------------------------------------------
# Multi-repo Ship (target_repos web + api …): brány v KAŽDÉM repu vítěze
# --------------------------------------------------------------------------


def repo_key(role: str | None, gate: str) -> str:
    """„lint“ v jednorepu, „api:lint“ ve vícerepu (role repa před bránou)."""
    return f"{role}:{gate}" if role else gate


def run_repo_gates(path: Path, role: str, base_branch: str) -> dict[str, Any]:
    """Pusť brány v jednom (ne primárním) repu vítěze; adaptér z base branche toho repa.

    Vrací záznam repa (stejný tvar, jaký Ship ukládá pro primární repo).
    """
    from tool.cli.extract import base_gates_adapter, diff_stats, git_info

    path = Path(path).resolve()
    adapter = base_gates_adapter(path, base_branch)
    try:
        stack, results, info, deps = evaluate_path(path, adapter.get("adapter_path"))
    finally:
        if adapter.get("tmp_dir"):
            shutil.rmtree(adapter["tmp_dir"], ignore_errors=True)
    if not deps[0]:
        print(f"[gates] {role}: {deps[1]}; gates závislé na instalaci jsou SKIP", file=sys.stderr)
    gi = git_info(path)
    d = diff_stats(path, base_branch)
    suff = gates_sufficiency(results)
    return {
        "role": role, "path": str(path), "base": base_branch,
        "branch": gi["branch"], "head_sha": gi["head_sha"],
        "stack": stack.label, "gate_score": info["gate_score"],
        "applicable_gates": info["applicable_gates"], "total_gates": info["total_gates"],
        "gates_run": info["gates_run"], "sufficient": suff["sufficient"],
        "sufficiency_blocker": suff["blocker"],
        "adapter_warnings": list(adapter.get("warnings") or []),
        "diff": {"added": d["added"], "removed": d["removed"], "files": d["files"]},
        "results": [{"gate": r.gate_type, "status": r.status, "metric": r.metric,
                     "details": r.details[:RESULT_DETAIL_LIMIT]} for r in results],
    }


def aggregate_repos(repos: list[dict[str, Any]]) -> dict[str, Any]:
    """Agregované skóre přes repa: průměr vážený počtem aplikovatelných bran.

    Proč vážený průměr a ne minimum: repo s 9 aplikovatelnými branami nese víc důkazů než
    malé API se 4; minimum by trestalo i drobnou warn v jinak zdravém repu. Slabé místo
    váženého průměru (dobré repo „zachrání“ špatné) pokrývají tvrdá pravidla Shipu:
    FAIL build / tests / smoke v KTERÉMKOLI repu = neprošlo bez ohledu na skóre,
    nedostatek bran se posuzuje per repo a repo pod prahem dostane varování.
    """
    weight = sum(int(r.get("applicable_gates") or 0) for r in repos)
    if weight:
        score = round(sum(int(r["gate_score"]) * int(r.get("applicable_gates") or 0)
                          for r in repos) / weight)
    else:
        score = min((int(r["gate_score"]) for r in repos), default=0)
    insufficient = [r for r in repos if not r.get("sufficient", True)]
    return {
        "gate_score": max(0, min(100, score)),
        "applicable_gates": sum(int(r.get("applicable_gates") or 0) for r in repos),
        "total_gates": sum(int(r.get("total_gates") or 0) for r in repos),
        "sufficient": not insufficient,
        "blocker": (f"gates:insufficient ({insufficient[0]['role']}: "
                    + str(insufficient[0].get("sufficiency_blocker") or "").split("(", 1)[-1].rstrip(")")
                    + ")") if insufficient else None,
    }


def repos_summary_line(repos: list[dict[str, Any]], total: int | None = None) -> str:
    """„web: 89/100 · api: 100/100 (celkem 94/100)“; detaily (SKIP, neověřeno) jsou v reportu."""
    parts = [f"{r['role']}: {int(r['gate_score'])}/100" for r in repos]
    line = " · ".join(parts)
    return f"{line} (celkem {total}/100)" if total is not None else line


def _repos_file(slug: str, variant: str) -> Path:
    return GATES_DIR / slug / f"repos-{variant}.json"


def save_repo_gates(slug: str, variant: str, repos: list[dict[str, Any]]) -> Path:
    """Ulož výsledky bran per repo (handoff_pr z nich skládá skóre a PR per repo)."""
    path = _repos_file(slug, variant)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"variant": variant, "repos": repos}, ensure_ascii=False,
                               indent=2), encoding="utf-8")
    return path


def load_repo_gates(slug: str, variant: str) -> list[dict[str, Any]]:
    """Záznamy repo z posledního Shipu varianty; [] když neexistují (jednorepo / starý Ship)."""
    path = _repos_file(slug, variant)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    repos = data.get("repos") if isinstance(data, dict) else None
    return repos if isinstance(repos, list) and len(repos) > 1 else []


def verdict_label(score: int, target: int, low_confidence: bool = False,
                  unverified: list[dict[str, str]] | None = None) -> str:
    unv = unverified or []
    names = ", ".join(u["gate"] for u in unv)
    if target <= 0:
        return f"informativně (práh 0, throwaway), skóre {score}/100"
    if low_confidence:
        return (f"nelze potvrdit práh - skóre {score}/100 je jen z malého počtu aplikovatelných "
                "bran (viz SKIP důvody)")
    if score >= target:
        if target >= PRODUCTION_TARGET and acceptance_unverified(unv):
            return (f"nesplňuje práh: acceptance je neověřená "
                    f"({next(u['reason'] for u in unv if u['gate'] == 'acceptance')}); "
                    f"skóre {score}/100 ≥ {target} ji nezahrnuje")
        base = f"splňuje práh ({score}/100 ≥ {target})"
        return f"{base} ⚠ ale neověřeno: {names}" if unv else base
    return f"pod prahem ({score}/100 < {target})"


def _render_md(slug: str, variant: str, results: list[GateResult],
               score_info: dict[str, Any], target: int, stack: Stack,
               gate_source: str = "") -> str:
    badges = {"pass": "PASS", "warn": "WARN", "fail": "FAIL", "skipped": "SKIP", "unsupported": "—"}
    rows = "\n".join(
        f"| {r.gate_type} | `{badges[r.status]}` | "
        f"{r.metric if r.metric is not None else '—'} | "
        f"{r.details[:140].replace(chr(10), ' ').replace('|', '/')} |"
        for r in results
    )
    score = score_info["gate_score"]
    low = ""
    if score_info["low_confidence"]:
        low = (f"\n> Pozor: skóre je jen z {score_info['applicable_gates']} aplikovatelných bran - "
               f"malá vypovídací hodnota (`{score_info['sufficiency_blocker']}`; verdikt vyžaduje "
               f"aspoň {MIN_GATES_RUN} spuštěné brány včetně build a tests).\n")
    skipped = skip_reasons(results)
    skip_block = ("\n## Brány, které neběžely\n\n" + "\n".join(f"- {x}" for x in skipped) + "\n"
                  if skipped else "")
    return f"""{BRAND}

# Quality gates — {slug} / varianta {variant}

> Skóre: {gates_summary_line(score, results)} (práh {target}) · {verdict_label(score, target, score_info['low_confidence'], unverified_gates(results))}
> Stack: `{stack.label}` · Aplikovatelné brány: {score_info['applicable_gates']} z {score_info['total_gates']} · {score_info['counts']}
> Zdroj příkazů: {gate_source or 'autodetekce'}
{low}
| Gate | Stav | Metrika | Detail |
|------|------|---------|--------|
{rows}
{skip_block}
## Jak číst

- PASS = v pořádku, WARN = do pilotu, opravit v dalším sprintu, FAIL = blokuje.
- SKIP = brána pro tento stack nedává smysl (důvod v detailu); do skóre se nepočítá.
- NEOVĚŘENO = brána by dávala smysl, ale chybí nástroj nebo konfigurace; do skóre se
  nepočítá, ale skóre o ní nic neříká. Skóre = body z aplikovatelných bran / max aplikovatelných × 100.
- Váhy: acceptance 2,5 · testy 2,0 · security 2,0 · build 1,5 · typy 1,5 · ostatní 0,5–1,0.

Opakování: `pflanzer quality_gates --slug {slug} --variant {variant}`
"""


_STATUS_CS = {"pass": "OK", "warn": "varování", "fail": "SELHALA", "skipped": "neběžela",
              "unsupported": "neběžela"}


def _first_line(text: str, limit: int = 110) -> str:
    for ln in (text or "").splitlines():
        if ln.strip():
            return ln.strip()[:limit]
    return ""


_GATE_LABEL = {"pass": "PASS", "warn": "WARN", "fail": "FAIL", "skipped": "SKIP", "unsupported": "—"}


def human_gate_lines(summary_line: str, results: list[dict[str, Any]], limit: int = 5,
                     per_gate: bool = False) -> list[str]:
    """Řádky pro lidský výstup: souhrn + nejdřív selhané, pak varování (max `limit`).

    `per_gate=True` vypíše řádek pro každou bránu (stav + první řádek detailu).
    """
    lines = [summary_line]
    if per_gate:
        for r in results:
            text = skip_reason(r) if r["status"] in ("skipped", "unsupported") \
                else _first_line(r.get("details", ""))
            label = _GATE_LABEL[r["status"]]
            if r["status"] == "skipped" and (r.get("details") or "").startswith(UNVERIFIED_PREFIX):
                label = "NEOVĚŘENO"
            lines.append(f"{r['gate']}: {label}" + (f" — {text[:110]}" if text else ""))
        return lines
    for r in results:
        if r["gate"] == "smoke" and r["status"] == "pass":
            lines.append(_first_line(r.get("details", "")))  # „smoke: / odpovídá 200“
    problems = [r for r in results if r["status"] == "fail"] + \
               [r for r in results if r["status"] == "warn"]
    for r in problems[: limit - 1]:
        why = ""
        if r["gate"] == "a11y":
            why = "; ".join(a11y_reasons(r.get("details", "")))
        lines.append(f"{_STATUS_CS[r['status']]}: {r['gate']} — "
                     f"{why or _first_line(r.get('details', ''))}")
    return lines


def main() -> None:
    p = CzechArgumentParser(prog="pflanzer quality_gates", description=__doc__.split("\n")[0])
    p.add_argument("--extracted-id", type=int, default=None)
    p.add_argument("--slug", default=None)
    p.add_argument("--variant", default=None)
    p.add_argument("--path", default=None,
                   help="Pusť brány nad adresářem bez DB (nic neukládá)")
    p.add_argument("--adapter", default=None,
                   help="Použij tento pflanzer.gates.json/.yml místo hledání ve stromu "
                        "(cwd se vztahuje ke kontrolované cestě)")
    p.add_argument("--json", action="store_true", help="Výstup jako JSON (pro skripty)")
    args = p.parse_args()
    adapter_path = Path(args.adapter).resolve() if args.adapter else None

    if args.path:
        target_dir = Path(args.path).resolve()
        if not target_dir.is_dir():
            die(f"Cesta {target_dir} není adresář.",
                "pflanzer quality_gates --path ./moje-aplikace")
        source = describe_gate_source(target_dir, adapter_path)
        try:
            _st, results, score_info, _deps = evaluate_path(target_dir, adapter_path)
        except AdapterError as e:
            die(str(e), "pflanzer quality_gates --path . --adapter pflanzer.gates.json")
        rows = [
            {"gate": r.gate_type, "status": r.status, "metric": r.metric,
             "duration_s": r.duration_s, "details": r.details[:300]}
            for r in results
        ]
        out = {
            "path": str(target_dir),
            "gate_source": source,
            "gate_score": score_info["gate_score"],
            "summary_line": gates_summary_line(score_info["gate_score"], results),
            "counts": score_info["counts"],
            "gates_run": score_info["gates_run"],
            "gates_unsupported": score_info["gates_unsupported"],
            "results": rows,
        }
        failing = [r["gate"] for r in rows if r["status"] == "fail"]
        emit(out, title=f"Kontrola bran: {target_dir.name}",
             lines=human_gate_lines(out["summary_line"], rows, per_gate=True),
             next_step=(f"oprav {', '.join(failing)} a spusť znovu: "
                        f"`pflanzer quality_gates --path {args.path}`" if failing
                        else "bez blokace; pro Ship vítěze: `pflanzer session_3 --slug <slug>`"),
             tips=tips_for("ship", {}) [:1], as_json=args.json)
        return

    if not args.extracted_id:
        if not (args.slug and args.variant):
            die("Chybí, co mám zkontrolovat: zadej --path <složka>, nebo --slug a --variant.",
                "pflanzer quality_gates --slug moje-appka --variant A")
        with transaction() as conn:
            row = conn.execute(
                """
                SELECT e.id FROM extracted_code e
                JOIN variants v ON v.id = e.variant_id
                JOIN sessions s ON s.id = v.session_id
                JOIN projects p ON p.id = s.project_id
                WHERE p.slug = ? AND v.name = ?
                ORDER BY e.id DESC LIMIT 1
                """, (args.slug, args.variant),
            ).fetchone()
            if not row:
                die(f"Varianta {args.variant} projektu {args.slug} ještě nemá načtený kód.",
                    f"pflanzer extract --slug {args.slug} --variant {args.variant}")
            args.extracted_id = int(row[0])

    try:
        out = run_all(args.extracted_id, adapter_path)
    except ValueError as e:  # vč. AdapterError
        die(str(e))
    failing = [r["gate"] for r in out["results"] if r["status"] == "fail"]
    emit(out, title=f"Kontrola bran: {out['slug']} / varianta {out['variant']}",
         lines=human_gate_lines(out["summary_line"], out["results"]) +
               [f"Práh projektu: {out['target']}/100 — "
                f"{'splněn' if out['production_ready'] else 'nesplněn nebo málo důkazů'}"],
         next_step=(f"oprav {', '.join(failing)} a spusť znovu: "
                    f"`pflanzer quality_gates --slug {out['slug']} --variant {out['variant']}`"
                    if failing else f"`pflanzer session_3 --slug {out['slug']}`"),
         as_json=args.json)


if __name__ == "__main__":
    main()
