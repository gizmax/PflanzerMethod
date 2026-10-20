"""`pflanzer init` — příprava target repa na Kickoff a Build.

Spuštěno **uvnitř target repa** (ne uvnitř plugin dir).
Co dělá:
1. Ověří, že cwd je git repo + git remote get-url origin existuje.
2. Zkopíruje INTEGRATION_GUIDE.md.template do `docs/INTEGRATION_GUIDE.md`
   (pokud chybí). Tým ji vyplní podle reality svého repa.
3. Vytvoří `.pflanzer/CONSTITUTION.md` (krátká nepřekročitelná pravidla pro
   AI buildery) ze šablony.
4. Vytvoří `tests/acceptance/.gitkeep` (Kickoff tam píše `.feature` per slug).
5. Vytvoří `.pflanzer/project.toml` (target_repo_url z git origin).
6. Vypíše další kroky: vyplnit → `pflanzer doctor` → commit + push → `/pm start`.

Subcommand `gates-template --path <repo> [--force]` (audit N7) autodetects the
stack (package.json / pyproject / pom.xml / build.gradle / *.sln / go.mod) and
writes a prefilled `pflanzer.gates.yml` from
`tool/templates/pflanzer.gates.yml.template`. See `tool/templates/README-gates.md`.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_PATH = PLUGIN_ROOT / "tool" / "templates" / "INTEGRATION_GUIDE.md.template"
PYTHON_TEMPLATE_PATH = PLUGIN_ROOT / "tool" / "templates" / "INTEGRATION_GUIDE.python.md.template"
GO_TEMPLATE_PATH = PLUGIN_ROOT / "tool" / "templates" / "INTEGRATION_GUIDE.go.md.template"
GENERIC_TEMPLATE_PATH = PLUGIN_ROOT / "tool" / "templates" / "INTEGRATION_GUIDE.generic.md.template"
CONSTITUTION_TEMPLATE_PATH = PLUGIN_ROOT / "tool" / "templates" / "CONSTITUTION.md.template"
GATES_TEMPLATE_PATH = PLUGIN_ROOT / "tool" / "templates" / "pflanzer.gates.yml.template"
GATES_FILENAME = "pflanzer.gates.yml"

sys.path.insert(0, str(PLUGIN_ROOT))
from tool.cli.apprun import workspace_packages  # noqa: E402
from tool.cli.quality_gates import GATE_TYPES, STACK_LABELS, detect_stack  # noqa: E402
from tool.cli.ux import CzechArgumentParser, die, emit, tips_for  # noqa: E402


def guide_template_for(path: Path) -> Path:
    """INTEGRATION_GUIDE šablona podle stacku: Python / Go; Node (React/TS) a repo bez rozpoznaného
    stacku (bez package.json) dostane generic variantu, jen neznámé s package.json zůstává Node."""
    try:
        stack = detect_stack(path)
    except OSError:
        stack = None
    if stack == "python" and PYTHON_TEMPLATE_PATH.is_file():
        return PYTHON_TEMPLATE_PATH
    if stack == "go" and GO_TEMPLATE_PATH.is_file():
        return GO_TEMPLATE_PATH
    if stack in ("maven", "gradle", "dotnet") and GENERIC_TEMPLATE_PATH.is_file():
        return GENERIC_TEMPLATE_PATH
    if stack is None and not (path / "package.json").is_file() and GENERIC_TEMPLATE_PATH.is_file():
        return GENERIC_TEMPLATE_PATH
    return TEMPLATE_PATH


# Python artefakty, které `pip install -e .` / pytest / build vyrábí a které nepatří do PR.
PYTHON_IGNORES = ("*.egg-info/", "__pycache__/", ".pytest_cache/", ".ruff_cache/",
                  ".coverage", "htmlcov/", "dist/", "build/")


def git_add_command(target_repo: Path | None = None) -> str:
    """Jediný zdroj pravdy pro init commit: `git add` jen pro cesty, které existují.

    Bez `target_repo` vrací kanonický tvar pro dokumentaci (všechny cesty včetně `.claude`).
    """
    paths = ["docs", ".pflanzer", "tests"]
    if target_repo is None:
        return f"git add -A {' '.join(paths + CANONICAL_EXTRA)}"
    if (target_repo / ".gitignore").exists():
        paths.append(".gitignore")
    if (target_repo / ".claude" / "settings.json").exists():
        paths.append(".claude/settings.json")
    return f"git add -A {' '.join(paths)}"


CANONICAL_EXTRA = [".gitignore", ".claude/settings.json"]


def _git_origin(cwd: Path) -> str | None:
    try:
        res = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=cwd, capture_output=True, text=True, check=True,
        )
        return res.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def _normalize_origin(url: str, base: Path | None = None) -> str:
    """git@github.com:foo/bar.git → https://github.com/foo/bar.

    Relativní lokální cesta (`../origin.git`) se převede na absolutní vůči `base` (target repo),
    jinak by ji `quick_session bootstrap` z jiného cwd nenašel ani neprošla validací.
    """
    if url.startswith(("./", "../", "~")) or (base and not url.startswith(("/", "file:"))
                                              and "://" not in url and "@" not in url):
        from tool.cli.db import resolve_local_repo_url
        return resolve_local_repo_url(url, base) or url
    if url.startswith(("/", "file:")):
        return url
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
    "smoke": {"builtin": True},  # needs `[preview] command` in .pflanzer/project.toml
    "acceptance": {"cmd": "<acceptance test command over tests/acceptance/>"},
    "security": {"cmd": "<dependency / SCA scan command>"},
    "a11y": {"cmd": "npx @axe-core/cli http://localhost:8080 --exit"},
    "observability": {"cmd": "<command that fails on stray console/print logging>"},
}
JVM_PRINT_SCAN = r"! grep -rnE 'System\.(out|err)\.print|printStackTrace\(' src/main"


def _read_json(p: Path) -> dict[str, Any]:
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _pkg_deps(pkg: dict[str, Any]) -> set[str]:
    return set((pkg.get("dependencies") or {})) | set((pkg.get("devDependencies") or {}))


def _node_presets(target: Path) -> dict[str, dict[str, Any]]:
    """Node / monorepo (npm workspaces) presets. Nástroj se do šablony dostane jen tehdy, když
    je deklarovaný v package.json (`npx --no-install`, nikdy stahování ze sítě); jinak je řádek
    zakomentovaný s vysvětlením. Cíl: šablona nikdy nedá horší skóre než autodetekce."""
    pkg = _read_json(target / "package.json")
    scripts = pkg.get("scripts") or {}
    ws_dirs = workspace_packages(target)
    pkgs = [(target, pkg)] + [(w, _read_json(w / "package.json")) for w in ws_dirs]
    all_deps = set().union(*(_pkg_deps(p) for _d, p in pkgs))

    def rel(d: Path) -> str:
        return str(d.relative_to(target)) or "."

    out: dict[str, dict[str, Any]] = {}

    def script_gate(gate: str, script: str, cmd: str) -> None:
        if script in scripts:
            out[gate] = {"cmd": cmd}
        else:
            out[f"#{gate}"] = {"_note": f"package.json nemá script `{script}` — doplňte ho "
                                        "a odkomentujte.", "cmd": cmd}

    script_gate("build", "build", "npm run build")
    # types: tsc per balíček s tsconfig.json, jen kde je typescript deklarovaný
    ts_dirs = [d for d, p in pkgs if (d / "tsconfig.json").exists()]
    ts_ok = [d for d, p in pkgs if (d / "tsconfig.json").exists()
             and ("typescript" in _pkg_deps(p) or "typescript" in _pkg_deps(pkg))]
    if ts_dirs and len(ts_ok) == len(ts_dirs):
        cmds = ["npx --no-install tsc --noEmit" if d == target
                else f"(cd {rel(d)} && npx --no-install tsc --noEmit)" for d in ts_dirs]
        out["types"] = {"cmd": " && ".join(cmds)}
    elif ts_dirs:
        out["#types"] = {"_note": "tsconfig.json je, ale `typescript` není v devDependencies — "
                                  "přidejte ho (bez toho by `npx tsc` stahoval ze sítě).",
                         "cmd": "npx --no-install tsc --noEmit"}
    else:
        out["#types"] = {"_note": "žádný tsconfig.json — projekt není TypeScript.",
                         "cmd": "npx --no-install tsc --noEmit"}
    script_gate("lint", "lint", "npm run lint")
    script_gate("tests", "test", "npm test")
    if "vitest" in all_deps and ({"@vitest/coverage-v8", "@vitest/coverage-istanbul"} & all_deps):
        out["coverage"] = {"cmd": "npx --no-install vitest run --coverage",
                           "parse": r"regex:All files\s*\|\s*[\d.]+\s*\|\s*(?P<metric>[\d.]+)",
                           **COVERAGE_THRESHOLDS}
    else:
        out["#coverage"] = {
            "_note": "vitest + @vitest/coverage-v8 nejsou v závislostech — bez nich by "
                     "`npx vitest` stahoval ze sítě. U node:test: "
                     "`node --test --experimental-test-coverage`.",
            "cmd": "npx --no-install vitest run --coverage",
            "parse": r"regex:All files\s*\|\s*[\d.]+\s*\|\s*(?P<metric>[\d.]+)",
            **COVERAGE_THRESHOLDS}
    out["smoke"] = {"builtin": True}
    # acceptance: node:test (`*.test.js`) před Playwrightem; kořen i workspace balíčky
    node_cmds: list[str] = []
    pw_dir = False
    for d, _p in pkgs:
        acc = d / "tests" / "acceptance"
        if not acc.is_dir():
            continue
        if next(acc.glob("*.test.*"), None) is not None and next(acc.glob("*.spec.*"), None) is None:
            glob = "tests/acceptance/*.test.*"
            runner = ("npx --no-install tsx --test" if "tsx" in _pkg_deps(_p)
                      or "tsx" in all_deps else "node --test")
            node_cmds.append(f"{runner} {glob}" if d == target
                             else f"(cd {rel(d)} && {runner} {glob})")
        elif next(acc.glob("*.spec.*"), None) is not None:
            pw_dir = True
    if node_cmds:
        out["acceptance"] = {"cmd": " && ".join(node_cmds)}
    elif pw_dir and "@playwright/test" in all_deps:
        out["acceptance"] = {"cmd": "npx --no-install playwright test tests/acceptance"}
    else:
        out["#acceptance"] = {
            "_note": "tests/acceptance/ s testy nenalezeno (nebo chybí @playwright/test) — "
                     "node:test: `node --test tests/acceptance/*.test.js`.",
            "cmd": "npx --no-install playwright test tests/acceptance"}
    out["security"] = {"builtin": True}
    out["#security"] = {"cmd": "npm audit --audit-level=high"}
    out["a11y"] = {"builtin": True}
    out["observability"] = {"builtin": True}
    return out


def _gate_presets(stack: str | None, target: Path) -> dict[str, dict[str, Any]]:
    """Per-stack gate specs. `gate` = active entry, `#gate` = commented example."""
    security = {"security": {"builtin": True}}
    if stack == "node":
        return _node_presets(target)
    if stack == "python":
        return {
            "#build": {"cmd": "python -m build"},
            "types": {"cmd": "mypy ."},
            "lint": {"cmd": "ruff check ."},
            "tests": {"cmd": "python3 -m pytest -q"},
            "#smoke": {"builtin": True},  # po doplnění [preview] command v .pflanzer/project.toml
            "#coverage": {"cmd": "python3 -m pytest -q --cov --cov-branch --cov-report=term",
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
            ("acceptance" if next((target / "tests" / "acceptance").glob("*_test.go"), None)
             else "#acceptance"): {
                "_note": "Go akceptační testy: tests/acceptance/*_test.go (package acceptance).",
                "cmd": "go test ./tests/acceptance/..."},
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
    note = spec.get("_note")
    lines = [f"{gate}:"] + [f"  {k}: {_yaml_scalar(v)}" for k, v in spec.items()
                            if not k.startswith("_")]
    lines = [f"# {line}" for line in lines] if commented else lines
    return ([f"# {note}"] if note else []) + lines


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


def _yaml_available() -> bool:
    try:
        import yaml  # noqa: F401
    except ImportError:
        return False
    return True


def render_gates_json(target: Path) -> tuple[str, str | None]:
    """JSON varianta adaptéru (bez PyYAML): jen aktivní brány, komentované příklady jdou do `_poznamka`."""
    stack = detect_stack(target)
    presets = _gate_presets(stack, target)
    data: dict[str, Any] = {}
    for gate in GATE_TYPES:
        spec = presets.get(gate)
        if spec is not None:
            data[gate] = {k: v for k, v in spec.items() if not k.startswith("_")}
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n", stack


def write_gates_template(target: Path, force: bool = False, fmt: str = "auto") -> dict[str, Any]:
    """`fmt`: auto (YAML, bez PyYAML JSON) | yaml | json. Nikdy nekončí bez rady."""
    target = target.resolve()
    if not target.is_dir():
        return {"ok": False, "reason": f"{target} není adresář"}
    if not GATES_TEMPLATE_PATH.exists():
        return {"ok": False, "reason": f"Template missing: {GATES_TEMPLATE_PATH}"}
    note = ""
    if fmt == "auto":
        fmt = "yaml" if _yaml_available() else "json"
        if fmt == "json":
            note = ("PyYAML není nainstalovaný, proto vznikl `pflanzer.gates.json` "
                    "(stejný obsah; YAML by quality_gates nenačetl).")
    elif fmt == "yaml" and not _yaml_available():
        note = ("pozor: PyYAML chybí — `pflanzer.gates.yml` se nenačte, dokud nespustíš "
                "`pip install pyyaml` (nebo `--format json`).")
    filename = GATES_FILENAME if fmt == "yaml" else "pflanzer.gates.json"
    out_path = target / filename
    others = [n for n in ("pflanzer.gates.yml", "pflanzer.gates.yaml", "pflanzer.gates.json")
              if (target / n).exists()]
    if others and not force:
        return {"ok": False, "path": str(target / others[0]),
                "reason": f"{others[0]} už existuje (--force pro overwrite)"}
    text, stack = render_gates_json(target) if fmt == "json" else render_gates_template(target)
    out_path.write_text(text, encoding="utf-8")
    if fmt == "json":
        active = [g for g in GATE_TYPES if g in json.loads(text)]
    else:
        active = [g for g in GATE_TYPES
                  if any(line.startswith(f"{g}:") for line in text.splitlines())]
    steps = [
        f"1. Projdi `{filename}` — doplň příkazy pro brány, které tým umí měřit "
        "(lint, coverage, acceptance).",
        "2. Ověř lokálně: `pflanzer quality_gates --path <repo>` (bez DB).",
        f"3. Commitni `{filename}` do main — reviewuj jeho změny jako CI config.",
    ]
    if note:
        steps.insert(0, note)
    return {
        "ok": True,
        "path": str(out_path),
        "format": fmt,
        "stack": stack or "unknown",
        "active_gates": active,
        "unsupported_gates": [g for g in GATE_TYPES if g not in active],
        "note": note,
        "next_steps": steps,
    }


def init(target_repo: Path, force: bool = False) -> dict[str, Any]:
    target_repo = target_repo.resolve()

    if not _is_git_repo(target_repo):
        return {"ok": False, "reason": f"{target_repo} není git repo. Spusť `git init` a `git remote add origin ...`"}

    origin = _git_origin(target_repo)
    origin_normalized = _normalize_origin(origin, target_repo) if origin else None

    actions: list[str] = []

    # 1. INTEGRATION_GUIDE.md
    docs_dir = target_repo / "docs"
    docs_dir.mkdir(exist_ok=True)
    guide = docs_dir / "INTEGRATION_GUIDE.md"
    if guide.exists() and not force:
        actions.append("docs/INTEGRATION_GUIDE.md už existuje (skip; --force pro overwrite)")
    else:
        template = guide_template_for(target_repo)
        if not template.exists():
            return {"ok": False, "reason": f"Template missing: {template}"}
        guide.write_text(template.read_text(encoding="utf-8"), encoding="utf-8")
        actions.append("napsáno: docs/INTEGRATION_GUIDE.md (vyplň ručně podle realit svého repa)")

    # 1b. .pflanzer/CONSTITUTION.md
    pflanzer_dir = target_repo / ".pflanzer"
    pflanzer_dir.mkdir(exist_ok=True)
    constitution = pflanzer_dir / "CONSTITUTION.md"
    if constitution.exists() and not force:
        actions.append(".pflanzer/CONSTITUTION.md už existuje (skip; --force pro overwrite)")
    else:
        if not CONSTITUTION_TEMPLATE_PATH.exists():
            return {"ok": False, "reason": f"Template missing: {CONSTITUTION_TEMPLATE_PATH}"}
        constitution.write_text(CONSTITUTION_TEMPLATE_PATH.read_text(encoding="utf-8"),
                                encoding="utf-8")
        actions.append("napsáno: .pflanzer/CONSTITUTION.md (doplň sekci „Doplň pro svůj repo“)")

    # 2. tests/acceptance/.gitkeep
    acc_dir = target_repo / "tests" / "acceptance"
    acc_dir.mkdir(parents=True, exist_ok=True)
    gitkeep = acc_dir / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.write_text("", encoding="utf-8")
        actions.append("vytvořeno: tests/acceptance/.gitkeep")

    # 3. .pflanzer/project.toml
    project_toml = pflanzer_dir / "project.toml"
    if not project_toml.exists() or force:
        slug_default = re.sub(r"[^a-z0-9]+", "-",
                              (target_repo.name or "myproject").lower()).strip("-")
        project_toml.write_text(f"""# Pflanzer per-project config
# Tento soubor čte Kickoff (quick_session bootstrap) a `pflanzer charter` jako defaults.

[project]
slug_default = "{slug_default}"  # kód v URL a větvích, není to název projektu
target_repo_url = "{origin_normalized or '<vyplň ručně>'}"
target_branch = "main"

# Default risk profile per nový projekt v tomto repu
default_risk_profile = "pilot"  # throwaway | pilot | production

# Owner GitHub handles (pre-populated do SHIP.md gh pr create --reviewer)
target_branch_owner = "<@github-handle>"
shadow_pm = "<jméno PdM>"

# Spuštění aplikace pro `pflanzer preview up` a bránu `smoke` ({{port}} dosadí tool).
# Bez tohoto bloku se zkusí autodetekce (npm run dev / start, make run, python -m …).
# [preview]
# command = "npm run dev -- --port {{port}}"
# smoke_paths = ["/", "/rezervace"]
# Monorepo (npm workspaces: web + api): `{{api_port}}` = port API části (port + 1001), každá
# varianta má vlastní, takže varianty nesdílí API port. PORT i API_PORT jdou i do env.
# command = "npx concurrently \\"PORT={{api_port}} npm run dev -w apps/api\\" \\"npm run dev -w apps/web -- --port {{port}} --strictPort\\""

# Vygenerováno: {date.today().isoformat()}
""", encoding="utf-8")
        actions.append("napsáno: .pflanzer/project.toml")

    # 3b. Claude Code: AI není spoluautor commitu — původ nesou trailery Pflanzer-* (N11).
    #     Výchozí `Co-Authored-By` by byl v rozporu s CONSTITUTION, proto ho vypneme v repu.
    cc_settings = target_repo / ".claude" / "settings.json"
    try:
        cfg = json.loads(cc_settings.read_text(encoding="utf-8")) if cc_settings.exists() else {}
    except (ValueError, OSError):
        cfg = None  # nevalidní JSON: nesahej, jen upozorni
    if cfg is None:
        actions.append("pozor: .claude/settings.json není validní JSON — "
                       "nastav ručně \"includeCoAuthoredBy\": false")
    elif cfg.get("includeCoAuthoredBy") is not False:
        cfg["includeCoAuthoredBy"] = False
        cc_settings.parent.mkdir(parents=True, exist_ok=True)
        cc_settings.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        actions.append("napsáno: .claude/settings.json (AI není spoluautor commitů — původ nesou trailery)")

    # 4. .gitignore — pridej extracted/ pokud chybí
    gitignore = target_repo / ".gitignore"
    if True:  # create when missing: specs for /pm must never be committed
        text = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
        additions = []
        if "extracted/" not in text:
            additions.append("\n# Pflanzer Method runtime (clones from vibe-coding sessions)\nextracted/\n")
        if ".pflanzer/local/" not in text:
            additions.append(".pflanzer/local/\n")
        if ".pflanzer/specs/" not in text:
            additions.append(".pflanzer/specs/\n")
        lines_present = {ln.strip() for ln in text.splitlines()}

        def _missing(*entries: str) -> list[str]:
            return [e for e in entries if e not in lines_present
                    and e.rstrip("/") not in lines_present]

        stack_now = detect_stack(target_repo)
        if stack_now == "node" or (target_repo / "package.json").is_file():
            extra = _missing("node_modules/")
            try:
                pkg = json.loads((target_repo / "package.json").read_text(encoding="utf-8"))
                has_build = isinstance((pkg.get("scripts") or {}).get("build"), str)
            except (OSError, ValueError, AttributeError):
                has_build = False
            if has_build:
                extra += _missing("dist/")
            if extra:
                additions.append("\n# Node (nikdy do commitu)\n" + "".join(f"{e}\n" for e in extra))
        if stack_now == "python":
            extra = _missing(".venv/", *PYTHON_IGNORES)
            if extra:
                additions.append("\n# Python (nikdy do commitu)\n" + "".join(f"{e}\n" for e in extra))
        if additions and text and not text.endswith("\n"):
            text += "\n"
        if additions:
            gitignore.write_text(text + "".join(additions), encoding="utf-8")
            actions.append(f"updated: .gitignore (+{len(additions)} entries)")

    # 5. Non-Node/Python stacks need a gate adapter (audit N7); only hint,
    # never write it implicitly (it switches quality_gates to adapter mode).
    stack = detect_stack(target_repo)
    gates_hint: list[str] = []
    if stack not in (None, "node", "python") and not any(
            (target_repo / n).exists()
            for n in ("pflanzer.gates.yml", "pflanzer.gates.yaml", "pflanzer.gates.json")):
        gates_hint.append(
            f"6. Stack {STACK_LABELS[stack]}: vygeneruj gate adaptér "
            "`pflanzer init gates-template --path .` (jinak část quality "
            "gates skončí jako neověřené).")

    return {
        "ok": True,
        "brand": "Pflanzer Method | pflanzer.cz/method",
        "target_repo": str(target_repo),
        "origin": origin_normalized,
        "actions": actions,
        "next_steps": [
            "1. Vyplň `docs/INTEGRATION_GUIDE.md` (auth, API, state, logger, "
            "feature flags, folder layout, test runner) a `.pflanzer/CONSTITUTION.md` "
            "(sekce „Doplň pro svůj repo“). Přes Claude Code cca 5 minut (AI vyplní podle repa, ty zkontroluješ), ručně cca 30 minut.",
            "2. Zkontroluj `.pflanzer/project.toml` (target_branch_owner = GitHub handle).",
            "3. Ověř připravenost: `pflanzer doctor`",
            "4. Commit + PUSH (worktrees se klonují z originu, nepushnuté soubory v nich nebudou): "
            f"`{git_add_command(target_repo)} "
            "&& git commit -m \"chore(pflanzer): init\" && git push -u origin HEAD`",
            "5. Restartuj Claude Code v tomto repu a spusť: `/pm start`",
        ] + gates_hint,
    }


def _short_action(action: str) -> str:
    """One short human line per action ("napsáno: docs/X (vyplň…)" → "napsáno: docs/X")."""
    return re.sub(r"\s*\(.*$", "", action).strip()


def main() -> None:
    p = CzechArgumentParser(prog="pflanzer init", description=__doc__.split("\n")[0])
    p.add_argument("--target", default=".", help="Target repo path (default: cwd)")
    p.add_argument("--force", action="store_true", help="Přepíše existující soubory")
    p.add_argument("--json", action="store_true", help="Strojový výstup")
    sub = p.add_subparsers(dest="command")
    gt = sub.add_parser(
        "gates-template",
        help="Write a prefilled pflanzer.gates.yml (stack autodetect) into the target repo",
    )
    gt.add_argument("--path", default=".", help="Target repo path (default: cwd)")
    gt.add_argument("--force", action="store_true", help="Overwrite existing pflanzer.gates.*")
    gt.add_argument("--format", choices=("auto", "yaml", "json"), default="auto",
                    help="auto = YAML, bez PyYAML JSON (default)")
    gt.add_argument("--json", action="store_true", help="Strojový výstup")
    args = p.parse_args()

    if args.command == "gates-template":
        out = write_gates_template(Path(args.path), force=args.force, fmt=args.format)
        if not out.get("ok"):
            if args.json:
                print(json.dumps(out, ensure_ascii=False, indent=2))
                sys.exit(1)
            die(out["reason"])
        emit(out, title="Gate adaptér vytvořen",
             lines=[f"Soubor `{out['path']}` (stack: {out['stack']}).",
                    f"Aktivní kontroly: {', '.join(out['active_gates']) or '—'}.",
                    "Bez příkazu (doplň ručně): " + (", ".join(out["unsupported_gates"]) or "žádné")]
             + ([out["note"]] if out.get("note") else []),
             next_step="projdi soubor, odkomentuj, co tým umí měřit, a commitni ho do main",
             tips=[], as_json=args.json)
        return

    out = init(Path(args.target), force=args.force)
    if not out.get("ok"):
        if args.json:
            print(json.dumps(out, ensure_ascii=False, indent=2))
            sys.exit(2)
        die(out["reason"])
    emit(out, title="Repo je připravené na Pflanzer Method",
         lines=[_short_action(a) for a in out["actions"][:6]],
         next_step="vyplň `docs/INTEGRATION_GUIDE.md` a `.pflanzer/CONSTITUTION.md` "
                   "(přes Claude Code cca 5 minut, ručně cca 30), pak `pflanzer doctor` — a commit + push",
         tips=tips_for("init"),
         warnings=[n for n in out["next_steps"] if "gates-template" in n],
         as_json=args.json)


if __name__ == "__main__":
    main()
