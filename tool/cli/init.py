"""`pflanzer init` — bootstrap target repo pro Pflanzer sessions.

Spuštěno **uvnitř target zákazníkova repa** (ne uvnitř plugin dir).
Co dělá:
1. Ověří, že cwd je git repo + git remote get-url origin existuje.
2. Zkopíruje INTEGRATION_GUIDE.md.template do `docs/INTEGRATION_GUIDE.md`
   (pokud chybí). Tým ji ručně vyplní podle reality svého repa.
3. Vytvoří `tests/acceptance/.gitkeep` aby složka existovala (Charter wizard
   tam pak píše `.feature` soubory per slug).
4. Vytvoří `.pflanzer/` config dir s `project.toml` (slug, target_repo_url
   pre-populated z git origin).
5. Print onboarding steps pro tým.

Subcommand `gates-template --path <repo> [--force]` (audit N7) autodetects the
stack (package.json / pyproject / pom.xml / build.gradle / *.sln / go.mod) and
writes a prefilled `pflanzer.gates.yml` from
`tool/templates/pflanzer.gates.yml.template`. See `tool/templates/README-gates.md`.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_PATH = PLUGIN_ROOT / "tool" / "templates" / "INTEGRATION_GUIDE.md.template"
GATES_TEMPLATE_PATH = PLUGIN_ROOT / "tool" / "templates" / "pflanzer.gates.yml.template"
GATES_FILENAME = "pflanzer.gates.yml"

sys.path.insert(0, str(PLUGIN_ROOT))
from tool.cli.quality_gates import GATE_TYPES, STACK_LABELS, detect_stack  # noqa: E402


def _git_origin(cwd: Path) -> str | None:
    try:
        res = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=cwd, capture_output=True, text=True, check=True,
        )
        return res.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def _normalize_origin(url: str) -> str:
    """git@github.com:foo/bar.git → https://github.com/foo/bar"""
    url = re.sub(r"\.git/?$", "", url)
    return url.replace("git@github.com:", "https://github.com/")


def _is_git_repo(cwd: Path) -> bool:
    return (cwd / ".git").exists() or _git_origin(cwd) is not None


# --------------------------------------------------------------------------
# gates-template (audit N7)
# --------------------------------------------------------------------------

COVERAGE_THRESHOLDS = {"warn_below": 60, "fail_below": 30}
# Commented-out fallbacks for gates a stack has no preset/example for.
GENERIC_GATE_EXAMPLES: dict[str, dict[str, Any]] = {
    "build": {"cmd": "<build command>"},
    "types": {"cmd": "<type checker command>"},
    "lint": {"cmd": "<lint command>"},
    "tests": {"cmd": "<test command>"},
    "coverage": {"cmd": "<command printing e.g. 'Branch coverage: 72.4%'>",
                 "parse": r"regex:Branch coverage: (?P<metric>[\d.]+)%",
                 **COVERAGE_THRESHOLDS},
    "acceptance": {"cmd": "<acceptance test command over tests/acceptance/>"},
    "security": {"cmd": "<dependency / SCA scan command>"},
    "a11y": {"cmd": "npx @axe-core/cli http://localhost:8080 --exit"},
    "observability": {"cmd": "<command that fails on stray console/print logging>"},
}
JVM_PRINT_SCAN = r"! grep -rnE 'System\.(out|err)\.print|printStackTrace\(' src/main"


def _gate_presets(stack: str | None, target: Path) -> dict[str, dict[str, Any]]:
    """Per-stack gate specs. `gate` = active entry, `#gate` = commented example."""
    security = {"security": {"builtin": True}}
    if stack == "node":
        # Mirrors the legacy Node autodetection in quality_gates.py.
        return {
            "build": {"cmd": "npm run build"},
            "types": {"cmd": "npx tsc --noEmit"},
            "lint": {"cmd": "npm run lint"},
            "tests": {"cmd": "npm test"},
            "coverage": {"cmd": "npx vitest run --coverage",
                         "parse": r"regex:All files\s*\|\s*[\d.]+\s*\|\s*(?P<metric>[\d.]+)",
                         **COVERAGE_THRESHOLDS},
            "acceptance": {"cmd": "npx playwright test tests/acceptance"},
            **security,
            "#security": {"cmd": "npm audit --audit-level=high"},
            "a11y": {"builtin": True},
            "observability": {"builtin": True},
        }
    if stack == "python":
        return {
            "#build": {"cmd": "python -m build"},
            "types": {"cmd": "mypy ."},
            "lint": {"cmd": "ruff check ."},
            "tests": {"cmd": "pytest -q"},
            "#coverage": {"cmd": "pytest -q --cov --cov-branch --cov-report=term",
                          "parse": r"regex:^TOTAL\s.*?(?P<metric>\d+(?:\.\d+)?)%\s*$",
                          **COVERAGE_THRESHOLDS},
            **security,
            "#security": {"cmd": "pip-audit"},
        }
    if stack == "maven":
        return {
            "build": {"cmd": "mvn -q -DskipTests compile"},
            "tests": {"cmd": "mvn -q test"},
            "#lint": {"cmd": "mvn -q checkstyle:check"},
            **security,
            "#security": {"cmd": "mvn -q org.owasp:dependency-check-maven:check -DfailBuildOnCVSS=7"},
            "#observability": {"cmd": JVM_PRINT_SCAN},
        }
    if stack == "gradle":
        gradle = "./gradlew" if (target / "gradlew").exists() else "gradle"
        return {
            "build": {"cmd": f"{gradle} build -x test"},
            "tests": {"cmd": f"{gradle} test"},
            "#lint": {"cmd": f"{gradle} check -x test"},
            **security,
            "#security": {"cmd": f"{gradle} dependencyCheckAnalyze"},
            "#observability": {"cmd": JVM_PRINT_SCAN},
        }
    if stack == "dotnet":
        return {
            "build": {"cmd": "dotnet build --nologo"},
            "tests": {"cmd": "dotnet test --nologo"},
            "lint": {"cmd": "dotnet format --verify-no-changes"},
            **security,
            "#observability": {"cmd": "! grep -rn --include='*.cs' 'Console.Write' ."},
        }
    if stack == "go":
        return {
            "build": {"cmd": "go build ./..."},
            "lint": {"cmd": "go vet ./..."},
            "tests": {"cmd": "go test ./..."},
            "#coverage": {"cmd": "go test -coverprofile=cover.out ./... && go tool cover -func=cover.out",
                          "parse": r"regex:^total:\s+\(statements\)\s+(?P<metric>[\d.]+)%",
                          **COVERAGE_THRESHOLDS},
            **security,
            "#security": {"cmd": "govulncheck ./..."},
        }
    return dict(security)


def _yaml_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    # Single quotes: backslashes in regexes stay literal; only ' is escaped.
    return "'" + str(value).replace("'", "''") + "'"


def _gate_block(gate: str, spec: dict[str, Any], commented: bool) -> list[str]:
    lines = [f"{gate}:"] + [f"  {k}: {_yaml_scalar(v)}" for k, v in spec.items()]
    return [f"# {line}" for line in lines] if commented else lines


def render_gates_template(target: Path) -> tuple[str, str | None]:
    """Render the adapter for `target`. Returns (yaml_text, stack_id)."""
    stack = detect_stack(target)
    presets = _gate_presets(stack, target)
    text = GATES_TEMPLATE_PATH.read_text(encoding="utf-8")
    text = text.replace("{{date}}", date.today().isoformat())
    text = text.replace("{{stack}}", STACK_LABELS.get(stack, stack) if stack
                        else "unknown (fill in the commented examples)")
    for gate in GATE_TYPES:
        active, example = presets.get(gate), presets.get(f"#{gate}")
        if active is not None:
            lines = _gate_block(gate, active, commented=False)
            if example is not None:
                lines += ["# alternative:"] + _gate_block(gate, example, commented=True)
        else:
            lines = _gate_block(gate, example or GENERIC_GATE_EXAMPLES[gate], commented=True)
        text = text.replace(f"{{{{gate:{gate}}}}}", "\n".join(lines))
    return text, stack


def write_gates_template(target: Path, force: bool = False) -> dict[str, Any]:
    target = target.resolve()
    if not target.is_dir():
        return {"ok": False, "reason": f"{target} není adresář"}
    if not GATES_TEMPLATE_PATH.exists():
        return {"ok": False, "reason": f"Template missing: {GATES_TEMPLATE_PATH}"}
    out_path = target / GATES_FILENAME
    if out_path.exists() and not force:
        return {"ok": False, "path": str(out_path),
                "reason": f"{GATES_FILENAME} už existuje (--force pro overwrite)"}
    text, stack = render_gates_template(target)
    out_path.write_text(text, encoding="utf-8")
    active = [g for g in GATE_TYPES
              if any(line.startswith(f"{g}:") for line in text.splitlines())]
    return {
        "ok": True,
        "path": str(out_path),
        "stack": stack or "unknown",
        "active_gates": active,
        "unsupported_gates": [g for g in GATE_TYPES if g not in active],
        "next_steps": [
            f"1. Projdi `{GATES_FILENAME}` — odkomentuj příklady pro gates, které "
            "tým umí měřit (lint, coverage, acceptance).",
            "2. Ověř lokálně: `python3 tool/cli/quality_gates.py --path <repo>` "
            "(bez DB, jen JSON výstup).",
            f"3. Commitni `{GATES_FILENAME}` do main — reviewuj jeho změny jako CI config.",
        ],
    }


def init(target_repo: Path, force: bool = False) -> dict[str, Any]:
    target_repo = target_repo.resolve()

    if not _is_git_repo(target_repo):
        return {"ok": False, "reason": f"{target_repo} není git repo. Spusť `git init` a `git remote add origin ...`"}

    origin = _git_origin(target_repo)
    origin_normalized = _normalize_origin(origin) if origin else None

    actions: list[str] = []

    # 1. INTEGRATION_GUIDE.md
    docs_dir = target_repo / "docs"
    docs_dir.mkdir(exist_ok=True)
    guide = docs_dir / "INTEGRATION_GUIDE.md"
    if guide.exists() and not force:
        actions.append(f"docs/INTEGRATION_GUIDE.md už existuje (skip; --force pro overwrite)")
    else:
        if not TEMPLATE_PATH.exists():
            return {"ok": False, "reason": f"Template missing: {TEMPLATE_PATH}"}
        guide.write_text(TEMPLATE_PATH.read_text(encoding="utf-8"), encoding="utf-8")
        actions.append(f"napsáno: docs/INTEGRATION_GUIDE.md (vyplň ručně podle realit svého repa)")

    # 2. tests/acceptance/.gitkeep
    acc_dir = target_repo / "tests" / "acceptance"
    acc_dir.mkdir(parents=True, exist_ok=True)
    gitkeep = acc_dir / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.write_text("", encoding="utf-8")
        actions.append("vytvořeno: tests/acceptance/.gitkeep")

    # 3. .pflanzer/project.toml
    pflanzer_dir = target_repo / ".pflanzer"
    pflanzer_dir.mkdir(exist_ok=True)
    project_toml = pflanzer_dir / "project.toml"
    if not project_toml.exists() or force:
        slug_default = re.sub(r"[^a-z0-9]+", "-",
                              (target_repo.name or "myproject").lower()).strip("-")
        project_toml.write_text(f"""# Pflanzer per-project config
# Tento soubor přečte `tool/cli/quick_session.py bootstrap()` jako defaults.

[project]
slug_default = "{slug_default}"
target_repo_url = "{origin_normalized or '<vyplň ručně>'}"
target_branch = "main"

# Default risk profile per nový projekt v tomto repu
default_risk_profile = "pilot"  # throwaway | pilot | production

# Owner GitHub handles (pre-populated do SHIP.md gh pr create --reviewer)
target_branch_owner = "<@github-handle>"
shadow_pm = "<jméno PM>"

# Vygenerováno: {date.today().isoformat()}
""", encoding="utf-8")
        actions.append("napsáno: .pflanzer/project.toml")

    # 4. .gitignore — pridej extracted/ pokud chybí
    gitignore = target_repo / ".gitignore"
    if gitignore.exists():
        text = gitignore.read_text(encoding="utf-8")
        additions = []
        if "extracted/" not in text:
            additions.append("\n# Pflanzer Method runtime (clones from vibe-coding sessions)\nextracted/\n")
        if ".pflanzer/local/" not in text:
            additions.append(".pflanzer/local/\n")
        if additions:
            gitignore.write_text(text + "".join(additions), encoding="utf-8")
            actions.append(f"updated: .gitignore (+{len(additions)} entries)")

    # 5. Non-Node/Python stacks need a gate adapter (audit N7); only hint,
    # never write it implicitly (it switches quality_gates to adapter mode).
    stack = detect_stack(target_repo)
    gates_hint: list[str] = []
    if stack not in (None, "node", "python") and not (target_repo / GATES_FILENAME).exists():
        gates_hint.append(
            f"5. Stack {STACK_LABELS[stack]}: vygeneruj gate adaptér "
            "`pflanzer init gates-template --path .` (jinak část quality "
            "gates skončí jako unsupported).")

    return {
        "ok": True,
        "target_repo": str(target_repo),
        "origin": origin_normalized,
        "actions": actions,
        "next_steps": [
            "1. Vyplň `docs/INTEGRATION_GUIDE.md` (auth, API, state, logger, "
            "feature flags, folder layout, test runner). 30 minut.",
            "2. Pre-populated `.pflanzer/project.toml` review — settni "
            "target_branch_owner GitHub handle.",
            "3. Commit oba soubory: `git add docs/INTEGRATION_GUIDE.md .pflanzer/ "
            "&& git commit -m 'chore(pflanzer): init project'`",
            "4. V Claude Code spusť: `/pflanzer \"co dnes řešíme\"`",
        ] + gates_hint,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--target", default=".", help="Target repo path (default: cwd)")
    p.add_argument("--force", action="store_true", help="Overwrite existing files")
    sub = p.add_subparsers(dest="command")
    gt = sub.add_parser(
        "gates-template",
        help="Write a prefilled pflanzer.gates.yml (stack autodetect) into the target repo",
    )
    gt.add_argument("--path", default=".", help="Target repo path (default: cwd)")
    gt.add_argument("--force", action="store_true", help="Overwrite existing pflanzer.gates.yml")
    args = p.parse_args()

    if args.command == "gates-template":
        out = write_gates_template(Path(args.path), force=args.force)
        print(json.dumps(out, ensure_ascii=False, indent=2))
        sys.exit(0 if out.get("ok") else 1)

    out = init(Path(args.target), force=args.force)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(0 if out.get("ok") else 1)


if __name__ == "__main__":
    main()
