"""Production-ready quality gate runner.

Pro každý extracted/<slug>/<variant>/ projektu spustí 7 gates:
- **lint**         npm run lint / ruff check
- **types**        tsc --noEmit / mypy
- **tests**        npm test / pytest
- **security**     npm audit / pip-audit + secret scan (gitleaks pokud k dispozici)
- **a11y**         axe-core (volitelně, only pokud npm install proběhl)
- **build**        npm run build / python -m build
- **observability**  scan na console.log → warn (production code by neměl mít)

Gate report: per gate { status: pass|warn|fail|skipped|unsupported, details, metric }.
Aggregate: gate_score 0..100 (passing weight = 1, warn = 0.5, fail/skip = 0).

Vstup: extracted_id z `extracted_code` table (or --slug + --variant lookup).
Output: persisted do `quality_gates` table + summary MD do
`data/handoffs/<slug>/quality-<variant>.md` + návratové `gate_score`.

Závislosti: žádné Python deps (jen subprocess). Předpokládá `npm`/`node` na PATH.
Pokud chybí, gates se označí 'unsupported' (ne fail).
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tool.cli.db import audit, current_actor, transaction  # noqa: E402

GATES_DIR = REPO_ROOT / "data" / "handoffs"
# Sprint 2 (per autoresearch ADR-0012):
# - Order = fail-fast (cheap → expensive). build first kills broken stack quickly.
# - acceptance = primary signal pro reuse (Decider written .feature scénáře).
# - coverage = real test signal, ne placebo (current gate_tests = "1 trivial test pass").
GATE_TYPES = ("build", "types", "lint", "tests", "coverage", "acceptance",
              "security", "a11y", "observability")
GATE_WEIGHTS = {  # Production readiness weight
    "build": 1.5,        # bez buildu se nešipuje
    "types": 1.5,        # type errors = bugs
    "lint": 1.0,
    "tests": 2.0,        # primary safety net
    "coverage": 1.0,     # real coverage, ne 1 trivial test
    "acceptance": 2.5,   # Decider-written scénáře = ground truth pro reuse
    "security": 2.0,     # blocker-class
    "a11y": 1.0,
    "observability": 0.5,
}
COVERAGE_TARGET = 60  # % branch coverage; pod tímto = warn, pod 30 = fail


@dataclass
class GateResult:
    gate_type: str
    status: str  # pass | warn | fail | skipped | unsupported
    details: str = ""
    metric: float | None = None
    duration_s: float = 0.0


# --------------------------------------------------------------------------
# Tool detection
# --------------------------------------------------------------------------


def _has(tool: str) -> bool:
    return shutil.which(tool) is not None


def _is_node_project(path: Path) -> bool:
    return (path / "package.json").exists()


def _ensure_node_deps(path: Path) -> bool:
    """Auto `npm ci` (or pnpm/yarn) jednou per gate run pokud node_modules chybí.

    Per autoresearch perspektiva 03 (devex): bez tohoto majority gates skipne
    s "node_modules missing" → false-low gate_score. Lepší zaplatit ~30s
    install než reportovat falsely-low score.
    """
    if (path / "node_modules").exists():
        return True
    if not _is_node_project(path):
        return False
    # Detect package manager + lockfile
    has_lock_pnpm = (path / "pnpm-lock.yaml").exists()
    has_lock_yarn = (path / "yarn.lock").exists()
    has_lock_npm = (path / "package-lock.json").exists()

    if has_lock_pnpm and shutil.which("pnpm"):
        cmd = ["pnpm", "install", "--frozen-lockfile", "--reporter=silent"]
    elif has_lock_yarn and shutil.which("yarn"):
        cmd = ["yarn", "install", "--frozen-lockfile", "--silent"]
    elif has_lock_npm and shutil.which("npm"):
        cmd = ["npm", "ci", "--no-audit", "--no-fund", "--silent"]
    elif shutil.which("npm"):
        # No lockfile — fallback to install (creates lockfile + resolves deps)
        cmd = ["npm", "install", "--no-audit", "--no-fund", "--silent"]
    else:
        return False
    try:
        rc = subprocess.run(cmd, cwd=path, capture_output=True, timeout=300).returncode
        return rc == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def _is_python_project(path: Path) -> bool:
    return (path / "pyproject.toml").exists() or (path / "setup.py").exists()


# --------------------------------------------------------------------------
# Per-gate runners
# --------------------------------------------------------------------------


def _run(cmd: list[str], cwd: Path, timeout: int = 120) -> tuple[int, str, str]:
    try:
        res = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout,
        )
        return res.returncode, res.stdout, res.stderr
    except subprocess.TimeoutExpired:
        return 124, "", f"Timeout po {timeout}s"
    except FileNotFoundError as e:
        return 127, "", str(e)


def gate_lint(path: Path) -> GateResult:
    if _is_node_project(path):
        if not _has("npm"):
            return GateResult("lint", "unsupported", "npm not on PATH")
        # Skip lint if node_modules missing (user run npm install)
        if not (path / "node_modules").exists():
            return GateResult("lint", "skipped",
                              "node_modules missing — spusť `npm install` v extracted/")
        rc, out, err = _run(["npm", "run", "lint"], path, timeout=60)
        if rc == 0:
            return GateResult("lint", "pass", "ESLint zero warnings", metric=0)
        # Parse warnings/errors
        problems = len(re.findall(r"^\s+\d+:\d+", out, re.MULTILINE))
        return GateResult(
            "lint", "fail" if rc != 0 and problems > 0 else "warn",
            f"ESLint reported {problems} issue(s)\n{(out + err)[-500:]}",
            metric=problems,
        )
    if _is_python_project(path):
        if not _has("ruff"):
            return GateResult("lint", "unsupported", "ruff not on PATH")
        rc, out, err = _run(["ruff", "check", "."], path)
        return GateResult("lint", "pass" if rc == 0 else "fail",
                          (out + err)[-500:] or "OK")
    return GateResult("lint", "unsupported", "Unknown project type (no package.json or pyproject.toml)")


def gate_types(path: Path) -> GateResult:
    if _is_node_project(path):
        if not _has("npx"):
            return GateResult("types", "unsupported", "npx not on PATH")
        if not (path / "node_modules").exists():
            return GateResult("types", "skipped", "node_modules missing")
        rc, out, err = _run(["npx", "tsc", "--noEmit"], path, timeout=120)
        if rc == 0:
            return GateResult("types", "pass", "TypeScript strict mode passes")
        errors = out.count("error TS")
        return GateResult("types", "fail",
                          f"{errors} TS errors\n{out[-500:]}", metric=errors)
    if _is_python_project(path):
        if not _has("mypy"):
            return GateResult("types", "unsupported", "mypy not on PATH")
        rc, out, _ = _run(["mypy", "."], path)
        return GateResult("types", "pass" if rc == 0 else "fail", out[-500:])
    return GateResult("types", "unsupported", "Unknown project type")


def gate_tests(path: Path) -> GateResult:
    if _is_node_project(path):
        if not (path / "node_modules").exists():
            return GateResult("tests", "skipped", "node_modules missing")
        rc, out, err = _run(["npm", "test"], path, timeout=180)
        if rc == 0:
            # Extract pass count
            m = re.search(r"(\d+)\s+pass", out)
            count = int(m.group(1)) if m else 0
            return GateResult("tests", "pass",
                              f"All tests pass ({count} cases)", metric=count)
        return GateResult("tests", "fail", (out + err)[-500:])
    if _is_python_project(path):
        if not _has("pytest"):
            return GateResult("tests", "unsupported", "pytest not on PATH")
        rc, out, _ = _run(["pytest", "-q"], path, timeout=180)
        return GateResult("tests", "pass" if rc == 0 else "fail", out[-500:])
    return GateResult("tests", "unsupported", "Unknown project type")


def gate_security(path: Path) -> GateResult:
    findings: list[str] = []
    secrets_count = 0

    # Naive secret scan (žádný gitleaks dependency v MVP)
    secret_patterns = [
        (r"(?i)api[_-]?key\s*[:=]\s*['\"][^'\"]{16,}", "API key"),
        (r"(?i)secret\s*[:=]\s*['\"][^'\"]{16,}", "secret"),
        (r"(?i)password\s*[:=]\s*['\"][^'\"]{8,}", "password"),
        (r"-----BEGIN (RSA |OPENSSH |EC |)PRIVATE KEY-----", "private key"),
        (r"sk-[a-zA-Z0-9]{32,}", "OpenAI-style key"),
        (r"sk-ant-[a-zA-Z0-9_-]{32,}", "Anthropic key"),
    ]
    skip_dirs = {"node_modules", "dist", ".git", "coverage"}
    for f in path.rglob("*"):
        if any(p in skip_dirs for p in f.parts):
            continue
        if not f.is_file() or f.suffix.lower() not in (".ts", ".tsx", ".js", ".jsx",
                                                       ".py", ".env", ".json", ".yml", ".yaml"):
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pat, label in secret_patterns:
            if re.search(pat, text):
                secrets_count += 1
                findings.append(f"{label} v {f.relative_to(path)}")

    # npm audit (Node only)
    audit_findings = 0
    if _is_node_project(path) and _has("npm") and (path / "node_modules").exists():
        rc, out, _ = _run(["npm", "audit", "--json"], path, timeout=60)
        try:
            audit_json = json.loads(out)
            audit_findings = audit_json.get("metadata", {}).get("vulnerabilities", {}).get("total", 0)
            if audit_findings:
                findings.append(f"npm audit: {audit_findings} vulnerability(s)")
        except (json.JSONDecodeError, KeyError):
            pass

    if secrets_count > 0:
        return GateResult("security", "fail",
                          f"⚠ Secret scan: {secrets_count} potential leak(s)\n"
                          + "\n".join(findings[:10]),
                          metric=secrets_count)
    if audit_findings > 5:
        return GateResult("security", "warn",
                          f"npm audit: {audit_findings} vulnerabilities (> 5 = review)",
                          metric=audit_findings)
    if audit_findings > 0:
        return GateResult("security", "warn",
                          f"npm audit: {audit_findings} vulnerabilities (acceptable)",
                          metric=audit_findings)
    return GateResult("security", "pass",
                      f"Žádné secrets detected, {audit_findings} npm vulnerabilities",
                      metric=0)


def gate_a11y(path: Path) -> GateResult:
    """A11y check via axe-core (pokud installed). MVP: jen smoke."""
    if not _is_node_project(path):
        return GateResult("a11y", "unsupported", "Pouze Node projekty zatím")
    if not (path / "node_modules").exists():
        return GateResult("a11y", "skipped", "node_modules missing")
    # Basic semantic check: hledá nějaké role/aria/alt v src/
    src = path / "src"
    if not src.exists():
        return GateResult("a11y", "skipped", "src/ missing")
    semantic_count = 0
    issue_count = 0
    for f in src.rglob("*.tsx"):
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        # Naive checks
        if re.search(r"<button(?:\s|>)", text) and "type=" not in text:
            issue_count += 1  # button bez type → submit default = bug
        if re.search(r"<img\b", text) and "alt=" not in text:
            issue_count += 1
        if re.search(r'role=|aria-|alt=|<main|<nav|<header|<footer|<section', text):
            semantic_count += 1
    if issue_count > 0:
        return GateResult("a11y", "warn",
                          f"{issue_count} potential a11y issue(s) — run `npx axe-core` "
                          f"pro detail. Found {semantic_count} semantic markers.",
                          metric=issue_count)
    return GateResult("a11y", "pass",
                      f"Found {semantic_count} semantic markers, 0 obvious issues. "
                      "Pro produkci doporučeno: `npm i -D @axe-core/cli && npx axe http://localhost:5173`.",
                      metric=0)


def gate_build(path: Path) -> GateResult:
    if _is_node_project(path):
        if not _has("npm"):
            return GateResult("build", "unsupported", "npm not on PATH")
        if not (path / "node_modules").exists():
            return GateResult("build", "skipped", "node_modules missing")
        rc, out, err = _run(["npm", "run", "build"], path, timeout=180)
        if rc == 0:
            dist = path / "dist"
            size_kb = sum(f.stat().st_size for f in dist.rglob("*") if f.is_file()) // 1024 if dist.exists() else 0
            return GateResult("build", "pass",
                              f"Build OK, dist size = {size_kb} KB",
                              metric=size_kb)
        return GateResult("build", "fail", (out + err)[-500:])
    if _is_python_project(path):
        # python -m build is heavy; skip in MVP
        return GateResult("build", "skipped", "Python build not in MVP")
    return GateResult("build", "unsupported", "Unknown project type")


def gate_coverage(path: Path) -> GateResult:
    """Branch coverage % via Vitest --coverage. Sprint 2 ADR-0012."""
    if not _is_node_project(path):
        return GateResult("coverage", "unsupported", "Pouze Node projekty zatím")
    if not (path / "node_modules").exists():
        return GateResult("coverage", "skipped", "node_modules missing")
    rc, out, err = _run(["npx", "vitest", "run", "--coverage", "--reporter=verbose"],
                        path, timeout=180)
    # Parse "All files | xx.xx" line z istanbul/v8 reporter
    m = re.search(r"All files\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)", out)
    if not m:
        # Coverage report not generated — treat as warn (test ran but no coverage tool)
        return GateResult("coverage", "warn",
                          "No coverage report parsed (chybí @vitest/coverage-v8?)",
                          metric=None)
    branch_pct = float(m.group(2))
    if branch_pct >= COVERAGE_TARGET:
        return GateResult("coverage", "pass",
                          f"Branch coverage {branch_pct:.1f} % (target {COVERAGE_TARGET})",
                          metric=branch_pct)
    if branch_pct >= 30:
        return GateResult("coverage", "warn",
                          f"Branch coverage {branch_pct:.1f} % < target {COVERAGE_TARGET} %",
                          metric=branch_pct)
    return GateResult("coverage", "fail",
                      f"Branch coverage {branch_pct:.1f} % je critically low (< 30 %)",
                      metric=branch_pct)


def gate_acceptance(path: Path) -> GateResult:
    """Run Playwright acceptance scénáře (z tests/acceptance/).

    Per autoresearch ADR-0010: Decider-written .feature scénáře jsou ground
    truth pro reusability. Pass rate ≥ 80 % = variant je apples-to-apples
    s ostatními a může jít do shortlistu.
    """
    if not _is_node_project(path):
        return GateResult("acceptance", "unsupported", "Pouze Node projekty zatím")
    acc_dir = path / "tests" / "acceptance"
    if not acc_dir.exists():
        return GateResult("acceptance", "skipped",
                          "tests/acceptance/ chybí — Decider zapomněl Charter "
                          "acceptance criteria. Per ADR-0010 mandatory pro "
                          "pilot/production.")
    if not (path / "node_modules").exists():
        return GateResult("acceptance", "skipped", "node_modules missing")
    rc, out, err = _run(["npx", "playwright", "test", "tests/acceptance",
                         "--reporter=json"], path, timeout=300)
    # Playwright JSON reporter writes to stdout — try parse
    try:
        # JSON může být wrapped — najdi first { a parse
        json_start = out.find("{")
        if json_start < 0:
            raise ValueError("no JSON in output")
        report = json.loads(out[json_start:])
        stats = report.get("stats", {})
        passed = stats.get("expected", 0)
        failed = stats.get("unexpected", 0)
        total = passed + failed
        if total == 0:
            return GateResult("acceptance", "skipped",
                              "Žádné acceptance scenarios nenalezeny")
        pass_rate = round(100 * passed / total)
        if pass_rate >= 80:
            return GateResult("acceptance", "pass",
                              f"{passed}/{total} scénářů ({pass_rate} %)",
                              metric=pass_rate)
        if pass_rate >= 50:
            return GateResult("acceptance", "warn",
                              f"{passed}/{total} scénářů ({pass_rate} %) "
                              "< target 80 %", metric=pass_rate)
        return GateResult("acceptance", "fail",
                          f"{passed}/{total} scénářů ({pass_rate} %) — varianta "
                          "neimplementuje Decider's spec", metric=pass_rate)
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        if rc == 0:
            return GateResult("acceptance", "warn",
                              f"Playwright passed ale JSON parse failed: {e}")
        return GateResult("acceptance", "fail", (out + err)[-500:])


def gate_observability(path: Path) -> GateResult:
    """Production code by nemělo mít console.log / print bez context."""
    if not (path / "src").exists() and not _is_python_project(path):
        return GateResult("observability", "skipped", "No src/")
    leaks = 0
    targets = list((path / "src").rglob("*.tsx")) + list((path / "src").rglob("*.ts")) \
        if (path / "src").exists() else []
    for f in targets:
        if "test" in f.name.lower() or "spec" in f.name.lower():
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        leaks += len(re.findall(r"console\.(log|debug|info|warn|error)\(", text))
    if leaks == 0:
        return GateResult("observability", "pass", "Žádný console.log v src/", metric=0)
    if leaks <= 10:
        return GateResult("observability", "warn",
                          f"{leaks} console.log statements — replace with structured logger pre-prod",
                          metric=leaks)
    # Per K4 conflict resolution: fail jen pokud opravdu zaplaveno (>10),
    # jinak je to lint-time concern (Biome no-console rule), ne gate concern.
    return GateResult("observability", "warn",
                      f"{leaks} console.log statements — high noise. "
                      "Long-term: enforce přes lint rule (no-console).",
                      metric=leaks)


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


STATUS_VALUES = {"pass": 1.0, "warn": 0.5, "fail": 0.0, "skipped": 0.0, "unsupported": None}


def aggregate_score(results: list[GateResult]) -> dict[str, Any]:
    total_weight = 0.0
    earned = 0.0
    counts = {"pass": 0, "warn": 0, "fail": 0, "skipped": 0, "unsupported": 0}
    for r in results:
        counts[r.status] += 1
        val = STATUS_VALUES.get(r.status)
        if val is None:  # unsupported = exclude from denominator
            continue
        weight = GATE_WEIGHTS.get(r.gate_type, 1.0)
        total_weight += weight
        earned += val * weight

    score = round(100 * earned / total_weight) if total_weight > 0 else 0
    return {
        "gate_score": score,
        "counts": counts,
        "weighted_max": round(total_weight, 2),
        "weighted_earned": round(earned, 2),
    }


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
        raise ValueError(f"Extracted dir missing: {local_path}")

    project_id = int(ext[4])
    slug = ext[5]
    variant_name = ext[3]
    target = int(ext[6] or 80)

    # Auto-install node deps so gates don't false-skip (Sprint 2)
    installed = _ensure_node_deps(local_path)
    if not installed and _is_node_project(local_path):
        print(f"[gates] warning: could not install deps in {local_path}; "
              "gates may report 'skipped'", file=sys.stderr)

    results: list[GateResult] = []
    for gate in GATE_TYPES:
        runner = GATE_RUNNERS[gate]
        results.append(runner(local_path))

    score_info = aggregate_score(results)
    score = score_info["gate_score"]

    # Persist
    with transaction() as conn:
        # Clear old runs for this extracted_id (idempotent re-run)
        conn.execute("DELETE FROM quality_gates WHERE extracted_id = ?", (extracted_id,))
        for r in results:
            conn.execute(
                """
                INSERT INTO quality_gates (
                    extracted_id, gate_type, status, details_md, metric_value, ran_by
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (extracted_id, r.gate_type, r.status, r.details, r.metric, current_actor()),
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
            },
        )

    # Write summary MD
    GATES_DIR.mkdir(parents=True, exist_ok=True)
    project_dir = GATES_DIR / slug
    project_dir.mkdir(parents=True, exist_ok=True)
    md_path = project_dir / f"quality-{variant_name}.md"
    md_path.write_text(_render_md(slug, variant_name, results, score_info, target),
                       encoding="utf-8")

    return {
        "extracted_id": extracted_id,
        "slug": slug,
        "variant": variant_name,
        "local_path": str(local_path.relative_to(REPO_ROOT)),
        "gate_score": score,
        "target": target,
        "production_ready": score >= target,
        "counts": score_info["counts"],
        "summary_path": str(md_path.relative_to(REPO_ROOT)),
        "results": [
            {"gate": r.gate_type, "status": r.status,
             "metric": r.metric, "details": r.details[:200]}
            for r in results
        ],
    }


def _render_md(slug: str, variant: str, results: list[GateResult],
               score_info: dict[str, Any], target: int) -> str:
    badges = {"pass": "✅", "warn": "⚠️", "fail": "❌",
              "skipped": "⏭️", "unsupported": "—"}
    rows = "\n".join(
        f"| {badges[r.status]} {r.gate_type} | `{r.status}` | "
        f"{r.metric if r.metric is not None else '—'} | "
        f"{r.details[:120].replace(chr(10), ' ')} |"
        for r in results
    )
    score = score_info["gate_score"]
    verdict = "**🚀 Production-ready**" if score >= target else (
        "**⚠ Pilot-only**" if score >= target * 0.7 else "**❌ Discovery sprint needed**"
    )

    return f"""# Quality gates — {slug} / variant {variant}

> Score: **{score}/100** (target: {target}) · Verdict: {verdict}
> Counts: {score_info['counts']}

| Gate | Status | Metric | Details |
|------|--------|--------|---------|
{rows}

## Co dál

- ✅ pass = ready for production
- ⚠ warn = ship to pilot, fix mid-sprint
- ❌ fail = block před promote-to-prod
- ⏭ skipped = run `npm install` v extracted/{slug}/{variant}/ a re-run gates
- — unsupported = nástroj chybí na PATH (info, ne blocker)

Pro re-run: `python3 tool/cli/quality_gates.py --extracted-id <id>`
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
                         f"Run extract.py first.")
            args.extracted_id = int(row[0])

    print(json.dumps(run_all(args.extracted_id), ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
