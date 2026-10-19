"""Quality gates (Ship, v0.5) — automatické brány místo lidí v místnosti.

Pro worktree / adresář vítězné varianty spustí až 9 gates:
- **build**         `npm run build` (jen pokud je build script)
- **types**         `tsc --noEmit` (jen s tsconfig.json) / mypy (jen s konfigurací)
- **lint**          `npm run lint` (jen pokud je lint script) / ruff
- **tests**         `npm test` / pytest; žádné nalezené testy = FAIL ("žádné testy")
- **coverage**      vitest --coverage (jen pokud je coverage nástroj)
- **acceptance**    Playwright scénáře z `tests/acceptance/` (jen pokud existují)
- **security**      secret scan + `npm audit` (vždy)
- **a11y**          heuristika nad HTML/JSX/TSX/Vue/Svelte (jen pokud UI soubory jsou)
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
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tool.cli.db import audit, current_actor, display_path, transaction  # noqa: E402
from tool.cli.extract import BRAND, DATA_ROOT  # noqa: E402

GATES_DIR = DATA_ROOT / "handoffs"
# Pořadí = fail-fast (levné → drahé).
GATE_TYPES = ("build", "types", "lint", "tests", "coverage", "acceptance",
              "security", "a11y", "observability")
GATE_WEIGHTS = {  # Production readiness weight
    "build": 1.5,        # bez buildu se nešipuje
    "types": 1.5,        # type errors = bugs
    "lint": 1.0,
    "tests": 2.0,        # primary safety net
    "coverage": 1.0,
    "acceptance": 2.5,   # Decider-written scénáře = ground truth
    "security": 2.0,     # blocker-class
    "a11y": 1.0,
    "observability": 0.5,
}
COVERAGE_TARGET = 60  # % branch coverage; pod tímto = warn, pod 30 = fail
LOW_CONFIDENCE_MIN_GATES = 3  # méně aplikovatelných bran = skóre má malou vypovídací hodnotu
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

    @property
    def label(self) -> str:
        parts = []
        if self.node:
            parts.append("node" + (f"/{self.package_manager}" if self.package_manager else ""))
            parts.append("ts" if self.has_tsconfig else "js")
        if self.python:
            parts.append("python")
        return "+".join(parts) or "neznámý"


def detect_stack(path: Path) -> Stack:
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
    st.has_tsconfig = (path / "tsconfig.json").exists()
    st.python = any((path / f).exists() for f in ("pyproject.toml", "setup.py", "requirements.txt"))
    return st


def _has(tool: str) -> bool:
    return shutil.which(tool) is not None


def _run(cmd: list[str], cwd: Path, timeout: int = 120) -> tuple[int, str, str]:
    env = {**os.environ, "CI": "1", "FORCE_COLOR": "0", "NO_COLOR": "1"}
    try:
        res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                             timeout=timeout, env=env)
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


def _skip(gate: str, reason: str) -> GateResult:
    return GateResult(gate, "skipped", f"SKIP: {reason}")


def _needs_deps(ctx: Ctx, gate: str) -> GateResult | None:
    """SKIP s důvodem, pokud node projekt potřebuje závislosti a ty nejsou."""
    if ctx.stack.node and ctx.stack.needs_install and not ctx.deps_ok:
        return _skip(gate, ctx.deps_reason or "chybí node_modules")
    return None


def _iter_files(root: Path, suffixes: tuple[str, ...]):
    for f in root.rglob("*"):
        rel_parts = f.relative_to(root).parts
        if any(p in SKIP_DIRS for p in rel_parts[:-1]):
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


def gate_build(ctx: Ctx) -> GateResult:
    st = ctx.stack
    if st.node:
        if "build" not in st.scripts:
            return _skip("build", "package.json nemá build script")
        if (s := _needs_deps(ctx, "build")):
            return s
        if not _has("npm"):
            return _skip("build", "npm není na PATH")
        rc, out, err = _run(["npm", "run", "build"], ctx.path, timeout=180)
        if rc == 0:
            size_kb = 0
            for d in ("dist", "build", "out"):
                dist = ctx.path / d
                if dist.exists():
                    size_kb = sum(f.stat().st_size for f in dist.rglob("*") if f.is_file()) // 1024
                    break
            return GateResult("build", "pass", f"Build OK, výstup {size_kb} KB", metric=size_kb)
        return GateResult("build", "fail", (out + err)[-500:])
    if st.python:
        return _skip("build", "Python build není v rozsahu bran")
    return _skip("build", "neznámý stack (bez package.json / pyproject.toml)")


def gate_types(ctx: Ctx) -> GateResult:
    st = ctx.stack
    if st.node:
        if not st.has_tsconfig:
            return _skip("types", "bez tsconfig.json - projekt není TypeScript")
        if (s := _needs_deps(ctx, "types")):
            return s
        tsc = ctx.path / "node_modules" / ".bin" / "tsc"
        if not tsc.exists() and not _has("tsc"):
            return _skip("types", "tsconfig.json je, ale typescript není nainstalovaný")
        cmd = [str(tsc)] if tsc.exists() else ["tsc"]
        rc, out, err = _run(cmd + ["--noEmit"], ctx.path, timeout=120)
        if rc == 0:
            return GateResult("types", "pass", "tsc --noEmit bez chyb", metric=0)
        errors = out.count("error TS")
        return GateResult("types", "fail", f"{errors} TS chyb\n{out[-500:]}", metric=errors)
    if st.python:
        configured = (ctx.path / "mypy.ini").exists() or any(
            "mypy" in (ctx.path / f).read_text(encoding="utf-8", errors="ignore")
            for f in ("pyproject.toml", "setup.cfg") if (ctx.path / f).exists())
        if not configured:
            return _skip("types", "mypy není v projektu nakonfigurovaný")
        if not _has("mypy"):
            return _skip("types", "mypy není na PATH")
        rc, out, _ = _run(["mypy", "."], ctx.path)
        return GateResult("types", "pass" if rc == 0 else "fail", out[-500:] or "OK")
    return _skip("types", "neznámý stack")


def gate_lint(ctx: Ctx) -> GateResult:
    st = ctx.stack
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
                          f"lint hlásí chybu ({problems} nálezů)\n{(out + err)[-500:]}",
                          metric=problems)
    if st.python:
        if not _has("ruff"):
            return _skip("lint", "ruff není na PATH")
        rc, out, err = _run(["ruff", "check", "."], ctx.path)
        return GateResult("lint", "pass" if rc == 0 else "fail", (out + err)[-500:] or "OK")
    return _skip("lint", "neznámý stack")


_PLACEHOLDER_TEST = re.compile(r"no test specified", re.IGNORECASE)


def _count_tests(output: str) -> int | None:
    """Počet testů z výstupu node:test / vitest / jest / pytest (None = nezjištěno)."""
    for pat in (r"^# pass (\d+)", r"^\W*pass (\d+)\s*$", r"Tests?:\s+(?:\d+ failed, )?(\d+) passed",
                r"\b(\d+) passed", r"(\d+)\s+pass(?:ed|ing)?\b"):
        m = re.search(pat, output, re.MULTILINE)
        if m:
            return int(m.group(1))
    m = re.search(r"^# tests (\d+)", output, re.MULTILINE)
    return int(m.group(1)) if m else None


def gate_tests(ctx: Ctx) -> GateResult:
    st = ctx.stack
    if st.node:
        script = st.scripts.get("test")
        if not script or _PLACEHOLDER_TEST.search(script):
            return GateResult("tests", "fail", "žádné testy - package.json nemá test script",
                              metric=0)
        if (s := _needs_deps(ctx, "tests")):
            return s
        rc, out, err = _run(["npm", "test"], ctx.path, timeout=180)
        if rc != 0:
            return GateResult("tests", "fail", (out + err)[-500:])
        count = _count_tests(out + err)
        if count == 0 or (count is None and not _has_test_files(ctx.path)):
            return GateResult("tests", "fail",
                              "žádné testy - test script proběhl, ale nenašel žádný test",
                              metric=0)
        note = f"{count} testů prošlo" if count is not None else "testy prošly (počet nezjištěn)"
        return GateResult("tests", "pass", note, metric=count)
    if st.python:
        if not _has("pytest"):
            return _skip("tests", "pytest není na PATH")
        rc, out, err = _run(["pytest", "-q"], ctx.path, timeout=180)
        if rc == 5:
            return GateResult("tests", "fail", "žádné testy - pytest žádný nenašel", metric=0)
        count = _count_tests(out)
        return GateResult("tests", "pass" if rc == 0 else "fail", (out + err)[-500:],
                          metric=count)
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
    for f in _iter_files(ctx.path, (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py",
                                    ".env", ".json", ".yml", ".yaml", ".toml", ".sh")):
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

    audit_note = "npm audit nespuštěn"
    audit_findings = 0
    st = ctx.stack
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
    return GateResult("security", "pass", f"Žádné secrets; {audit_note}", metric=0)


def gate_a11y(ctx: Ctx) -> GateResult:
    """Heuristika (ne náhrada axe-core): alt u img, type u button, lang u html."""
    files = list(_iter_files(ctx.path, (".html", ".jsx", ".tsx", ".vue", ".svelte")))
    if not files:
        return _skip("a11y", "projekt nemá žádné UI soubory (html/jsx/tsx/vue/svelte)")
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
                          "(heuristika; pro detail `npx axe`)", metric=issues)
    return GateResult("a11y", "pass",
                      f"{len(files)} UI souborů, {semantic} se sémantickými značkami, 0 zjevných "
                      "problémů (heuristika; pro produkci doporuč. axe)", metric=0)


def gate_coverage(ctx: Ctx) -> GateResult:
    st = ctx.stack
    has_tool = st.node and "vitest" in st.deps and any(
        k in st.deps for k in ("@vitest/coverage-v8", "@vitest/coverage-istanbul"))
    if not has_tool:
        return _skip("coverage", "není nakonfigurovaný coverage nástroj (vitest + coverage-v8)")
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


def gate_acceptance(ctx: Ctx) -> GateResult:
    """Playwright acceptance scénáře z `tests/acceptance/` (zadání Deciderem při Kickoffu)."""
    acc_dir = ctx.path / "tests" / "acceptance"
    if not acc_dir.exists():
        return _skip("acceptance", "tests/acceptance/ neexistuje (kritéria nejsou v kódu)")
    st = ctx.stack
    if not (st.node and "@playwright/test" in st.deps):
        return _skip("acceptance", "scénáře jsou, ale chybí @playwright/test")
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
            return _skip("acceptance", "žádné acceptance scénáře nenalezeny")
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
        return GateResult("acceptance", "fail", (out + err)[-500:])


def gate_observability(ctx: Ctx) -> GateResult:
    """Produkční kód by neměl mít `console.*` bez kontextu (jen JS/TS)."""
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


GATE_RUNNERS = {
    "build": gate_build,
    "types": gate_types,
    "lint": gate_lint,
    "tests": gate_tests,
    "coverage": gate_coverage,
    "acceptance": gate_acceptance,
    "security": gate_security,
    "a11y": gate_a11y,
    "observability": gate_observability,
}


# --------------------------------------------------------------------------
# Aggregate score
# --------------------------------------------------------------------------


STATUS_VALUES = {"pass": 1.0, "warn": 0.5, "fail": 0.0, "skipped": None, "unsupported": None}


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
    return {
        "gate_score": score,
        "counts": counts,
        "applicable_gates": applicable,
        "total_gates": len(results),
        "low_confidence": applicable < LOW_CONFIDENCE_MIN_GATES,
        "weight_applicable": round(total_weight, 2),
        "weight_earned": round(earned, 2),
    }


def run_gates_on_path(path: Path) -> tuple[Stack, list[GateResult], dict[str, Any], tuple[bool, str]]:
    """Čistá funkce bez DB: stack → gates → skóre (použitelné i v testech)."""
    st = detect_stack(path)
    deps = prepare_deps(st)
    ctx = Ctx(path=path, stack=st, deps_ok=deps[0], deps_reason=deps[1])
    results = [GATE_RUNNERS[g](ctx) for g in GATE_TYPES]
    return st, results, aggregate_score(results), deps


# --------------------------------------------------------------------------
# Persistence + render
# --------------------------------------------------------------------------


def run_all(extracted_id: int) -> dict[str, Any]:
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
            raise ValueError(f"extracted_code id={extracted_id} not found.")

    local_path = REPO_ROOT / ext[1] if not Path(ext[1]).is_absolute() else Path(ext[1])
    if not local_path.exists():
        raise ValueError(f"Složka s kódem varianty neexistuje: {display_path(local_path)}")

    project_id = int(ext[4])
    slug = ext[5]
    variant_name = ext[3]
    target = int(ext[6]) if ext[6] is not None else 80

    stack, results, score_info, deps = run_gates_on_path(local_path)
    if not deps[0]:
        print(f"[gates] pozor: {deps[1]}; gates závislé na instalaci jsou SKIP", file=sys.stderr)
    score = score_info["gate_score"]

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
            },
        )

    GATES_DIR.mkdir(parents=True, exist_ok=True)
    project_dir = GATES_DIR / slug
    project_dir.mkdir(parents=True, exist_ok=True)
    md_path = project_dir / f"quality-{variant_name}.md"
    md_path.write_text(_render_md(slug, variant_name, results, score_info, target, stack),
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
        "production_ready": score >= target and not score_info["low_confidence"],
        "applicable_gates": score_info["applicable_gates"],
        "total_gates": score_info["total_gates"],
        "low_confidence": score_info["low_confidence"],
        "counts": score_info["counts"],
        "summary_path": display_path(md_path),
        "results": [
            {"gate": r.gate_type, "status": r.status,
             "metric": r.metric, "details": r.details[:200]}
            for r in results
        ],
    }


def verdict_label(score: int, target: int, low_confidence: bool = False) -> str:
    if target <= 0:
        return f"informativně (práh 0, throwaway), skóre {score}/100"
    if low_confidence:
        return (f"nelze potvrdit práh - skóre {score}/100 je jen z malého počtu aplikovatelných "
                "bran (viz SKIP důvody)")
    if score >= target:
        return f"splňuje práh ({score}/100 ≥ {target})"
    return f"pod prahem ({score}/100 < {target})"


def _render_md(slug: str, variant: str, results: list[GateResult],
               score_info: dict[str, Any], target: int, stack: Stack) -> str:
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
               "malá vypovídací hodnota.\n")
    return f"""{BRAND}

# Quality gates — {slug} / varianta {variant}

> Skóre: **{score}/100** (práh {target}) · {verdict_label(score, target, score_info['low_confidence'])}
> Stack: `{stack.label}` · Aplikovatelné brány: {score_info['applicable_gates']} z {score_info['total_gates']} · {score_info['counts']}
{low}
| Gate | Stav | Metrika | Detail |
|------|------|---------|--------|
{rows}

## Jak číst

- PASS = v pořádku, WARN = do pilotu, opravit v dalším sprintu, FAIL = blokuje.
- SKIP = brána pro tento stack nedává smysl nebo nejde spustit (důvod v detailu);
  do skóre se nepočítá. Skóre = body z aplikovatelných bran / max aplikovatelných × 100.
- Váhy: acceptance 2,5 · testy 2,0 · security 2,0 · build 1,5 · typy 1,5 · ostatní 0,5–1,0.

Opakování: `pflanzer quality_gates --slug {slug} --variant {variant}`
"""


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--extracted-id", type=int, default=None)
    p.add_argument("--slug", default=None)
    p.add_argument("--variant", default=None)
    args = p.parse_args()

    if not args.extracted_id:
        if not (args.slug and args.variant):
            p.error("Either --extracted-id OR (--slug AND --variant) required")
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
                sys.exit(f"No extracted_code for {args.slug}/{args.variant}. "
                         f"Spusť nejdřív `pflanzer extract --slug {args.slug} --variant {args.variant}`.")
            args.extracted_id = int(row[0])

    print(json.dumps(run_all(args.extracted_id), ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
