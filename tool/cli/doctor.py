"""`pflanzer doctor [--target DIR] [--json]` — je repo připravené na Kickoff?

Checklist inspirovaný „vibe engineeringem“ (Willison): AI buildeři jsou
tak dobří, jak dobré je repo — testy, lint, build, CI, konvence a pravidla.
Ověřuje se, že je repo připravené na tři worktrees s AI:

  ✓ v pořádku   ⚠ upozornění (Kickoff jde, ale zhorší se Build)   ✗ blokuje

Exit code 0, pokud není žádné ✗. Nic nemění (jen `git fetch origin`
kvůli porovnání s originem).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PLUGIN_ROOT))

from tool.cli.ux import CzechArgumentParser, die, emit, tips_for  # noqa: E402

GUIDE_TEMPLATE = PLUGIN_ROOT / "tool" / "templates" / "INTEGRATION_GUIDE.md.template"
GUIDE_TEMPLATE_PYTHON = PLUGIN_ROOT / "tool" / "templates" / "INTEGRATION_GUIDE.python.md.template"
BRAND_LINE = "**Pflanzer Method | pflanzer.cz/method**"

OK, WARN, FAIL = "ok", "warn", "fail"
SYMBOL = {OK: "✓", WARN: "⚠", FAIL: "✗"}

INIT_FILES = ["docs/INTEGRATION_GUIDE.md", ".pflanzer/CONSTITUTION.md", ".pflanzer/project.toml"]
LOCKFILES = [
    "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock", "bun.lockb",
    "poetry.lock", "uv.lock", "Pipfile.lock", "pdm.lock", "Cargo.lock", "go.sum",
    "Gemfile.lock", "composer.lock", "pubspec.lock", "Package.resolved",
]
CI_FILES = [".gitlab-ci.yml", "azure-pipelines.yml", "bitbucket-pipelines.yml",
            ".circleci/config.yml", "Jenkinsfile", ".drone.yml", ".travis.yml"]
PREVIEW_FILES = ["vercel.json", ".vercel", "netlify.toml", "render.yaml", "fly.toml",
                 "wrangler.toml", "firebase.json", "amplify.yml", "app.json", "Procfile"]


def _git(cwd: Path, *args: str, timeout: int = 30) -> tuple[int, str]:
    try:
        r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True,
                           timeout=timeout)
        return r.returncode, (r.stdout + r.stderr).strip()
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return 124, str(e)


def _read_toml_project(repo: Path) -> dict[str, str]:
    path = repo / ".pflanzer" / "project.toml"
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if "=" in line and not line.startswith("["):
            k, v = (x.strip() for x in line.split("=", 1))
            out[k] = v.strip('"')
    return out


def _check(name: str, status: str, detail: str, advice: str = "",
           impact: str = "") -> dict[str, str]:
    """`impact` = co to znamená v praxi („pilot půjde, ale …“) — jen u ⚠."""
    return {"check": name, "status": status, "detail": detail, "advice": advice,
            "impact": impact}


def _is_node(repo: Path) -> bool:
    return (repo / "package.json").is_file()


# --------------------------------------------------------------------------
# Individual checks
# --------------------------------------------------------------------------


def check_git(repo: Path) -> tuple[list[dict[str, str]], str | None]:
    rc, _ = _git(repo, "rev-parse", "--is-inside-work-tree")
    if rc != 0:
        return [_check("Git repo + origin", FAIL, "není git repo",
                       "`git init`, přidej `git remote add origin <url>` a pushni.")], None
    rc, origin = _git(repo, "remote", "get-url", "origin")
    if rc != 0:
        return [_check("Git repo + origin", FAIL, "chybí remote `origin`",
                       "Worktrees se klonují z originu: `git remote add origin <url>`.")], None
    return [_check("Git repo + origin", OK, origin)], origin


PLACEHOLDER_RE = re.compile(r"<[^<>\n]*(?:\s\||\|\s|\s[^<>\n]*\s|doplň|vyplň)[^<>\n]*>")


def _guide_sections(text: str) -> list[str]:
    """Body of each `##` section (the intro before the first `##` is ignored)."""
    parts = re.split(r"(?m)^##\s+", text)
    return parts[1:]


def check_guide(repo: Path) -> dict[str, str]:
    name = "INTEGRATION_GUIDE.md"
    guide = repo / "docs" / "INTEGRATION_GUIDE.md"
    if not guide.is_file():
        guide = repo / "INTEGRATION_GUIDE.md"
    if not guide.is_file():
        return _check(name, FAIL, "chybí", "`pflanzer init`, pak ho vyplň podle reality repa.")
    text = guide.read_text(encoding="utf-8", errors="replace")
    if any(t.is_file() and text.strip() == t.read_text(encoding="utf-8").strip()
           for t in (GUIDE_TEMPLATE, GUIDE_TEMPLATE_PYTHON)):
        return _check(name, FAIL, "pořád jen nevyplněná šablona",
                      "Vyplň auth, API, state, logger, folder layout, test runner (cca 30 min).")
    sections = _guide_sections(text)
    open_sections = [sec for sec in sections if PLACEHOLDER_RE.search(sec)]
    placeholders = PLACEHOLDER_RE.findall(text)
    if sections and len(open_sections) * 2 > len(sections):
        return _check(name, FAIL,
                      f"nevyplněno: {len(open_sections)} z {len(sections)} sekcí má ještě placeholdery",
                      "Jeden doplněný řádek nestačí. Ve většině sekcí nahraď `<…>` realitou repa "
                      "(vývojář: „vyplň docs/INTEGRATION_GUIDE.md podle tohoto repa“, cca 30 min).")
    if placeholders:
        return _check(name, WARN, f"{len(placeholders)}× zbývá placeholder `<…>` "
                                  f"({len(open_sections)} z {len(sections)} sekcí)",
                      "Nahraď zbylé `<…>` skutečnými hodnotami, AI jinak hádá.",
                      "pilot půjde, ale AI bude u zbylých sekcí hádat konvence repa")
    return _check(name, OK, str(guide.relative_to(repo)))


def check_constitution(repo: Path) -> dict[str, str]:
    name = "CONSTITUTION.md"
    path = repo / ".pflanzer" / "CONSTITUTION.md"
    if not path.is_file():
        return _check(name, FAIL, "chybí", "`pflanzer init` ji vytvoří; pak doplň sekci pro svůj repo.")
    text = path.read_text(encoding="utf-8", errors="replace")
    n = text.count("<doplň>")
    if n:
        return _check(name, WARN, f"{n}× zbývá `<doplň>`",
                      "Doplň povolenou síť, zakázané adresáře a příkazy lint/test/build.",
                      "pilot půjde, ale AI nezná zakázané adresáře ani povolenou síť")
    return _check(name, OK, ".pflanzer/CONSTITUTION.md")


LOCKFILE_ADVICE = {
    "package.json": "Commitni lockfile (`npm install` vytvoří package-lock.json) — install ve "
                    "worktrees (`npm ci`) ho potřebuje.",
    "pyproject.toml": "Commitni lockfile (`uv lock` nebo `poetry lock`) — Python worktrees "
                      "pak mají stejné verze.",
    "requirements.txt": "Připni verze (`pip freeze > requirements.txt`) nebo přejdi na `uv lock`.",
    "Cargo.toml": "Commitni Cargo.lock (`cargo generate-lockfile`).",
    "go.mod": "Commitni go.sum (`go mod tidy`).",
    "Gemfile": "Commitni Gemfile.lock (`bundle install`).",
    "composer.json": "Commitni composer.lock (`composer install`).",
    "pubspec.yaml": "Commitni pubspec.lock (`flutter pub get`).",
    "Package.swift": "Commitni Package.resolved.",
}


def _manifest_has_deps(repo: Path, manifest: str) -> bool:
    """True, pokud manifest deklaruje závislosti (nečitelný/neznámý manifest = ano)."""
    path = repo / manifest
    try:
        if manifest == "package.json":
            data = json.loads(path.read_text(encoding="utf-8"))
            return any(bool(data.get(k)) for k in ("dependencies", "devDependencies",
                                                   "optionalDependencies", "peerDependencies"))
        if manifest == "pyproject.toml":
            import tomllib
            data = tomllib.loads(path.read_text(encoding="utf-8"))
            proj = data.get("project") or {}
            poetry = (data.get("tool") or {}).get("poetry") or {}
            poetry_deps = {k for k in (poetry.get("dependencies") or {}) if k.lower() != "python"}
            poetry_groups = any((g or {}).get("dependencies")
                                for g in (poetry.get("group") or {}).values())
            return bool(proj.get("dependencies") or proj.get("optional-dependencies")
                        or data.get("dependency-groups") or poetry_deps or poetry_groups
                        or poetry.get("dev-dependencies"))
        if manifest == "requirements.txt":
            return True
    except Exception:  # nečitelný manifest: raději upozorni na lockfile
        return True
    return True


def _requirements_files(repo: Path) -> list[Path]:
    return sorted(repo.glob("requirements*.txt"))


def _requirements_declare_deps(path: Path) -> bool:
    try:
        return any(ln.split("#", 1)[0].strip() for ln in path.read_text(
            encoding="utf-8", errors="replace").splitlines())
    except OSError:
        return True


def check_package_manager(repo: Path) -> dict[str, str]:
    name = "Package manager / lockfile"
    found = [f for f in LOCKFILES if (repo / f).exists()]
    if found:
        return _check(name, OK, ", ".join(found))
    manifests = [m for m in LOCKFILE_ADVICE if (repo / m).exists()]
    reqs = _requirements_files(repo)
    if manifests or reqs:
        declares = (any(_requirements_declare_deps(r) for r in reqs)
                    or any(_manifest_has_deps(repo, m) for m in manifests
                           if m != "requirements.txt"))
        if not declares:
            return _check(name, OK, "bez závislostí — lockfile netřeba")
        manifests = manifests or ["requirements.txt"]
        return _check(name, WARN, f"{', '.join(manifests)} bez lockfilu",
                      LOCKFILE_ADVICE[manifests[0]],
                      "pilot půjde, ale 3 worktrees nemusí mít stejné verze závislostí")
    return _check(name, WARN, "žádný manifest ani lockfile",
                  "Pokud je to statický web, ignoruj; jinak přidej manifest a lockfile.",
                  "pilot půjde, ale kontroly v Ship nebudou mít co instalovat")


def _scripts(repo: Path) -> tuple[dict[str, str], str]:
    """Return ({test, lint, build} -> how found, stack label)."""
    found: dict[str, str] = {}
    stack = "neznámý stack"

    pkg = repo / "package.json"
    if pkg.is_file():
        stack = "Node"
        try:
            scripts = json.loads(pkg.read_text(encoding="utf-8")).get("scripts", {}) or {}
        except (json.JSONDecodeError, OSError):
            scripts = {}
        for key, cands in {"test": ("test", "test:unit", "vitest", "jest"),
                           "lint": ("lint", "lint:check", "eslint", "check"),
                           "build": ("build",)}.items():
            hit = next((c for c in cands if c in scripts), None)
            if hit:
                found[key] = f"npm run {hit}"

    mk = repo / "Makefile"
    if mk.is_file():
        stack = "Makefile" if stack == "neznámý stack" else stack
        targets = set(re.findall(r"^([A-Za-z0-9_.-]+)\s*:", mk.read_text(errors="replace"), re.M))
        for key, cands in {"test": ("test", "check", "tests"),
                           "lint": ("lint", "check", "fmt-check"),
                           "build": ("build", "all")}.items():
            hit = next((c for c in cands if c in targets), None)
            if hit and key not in found:
                found[key] = f"make {hit}"

    pyp = repo / "pyproject.toml"
    if pyp.is_file():
        stack = "Python" if stack == "neznámý stack" else stack
        text = pyp.read_text(errors="replace")
        if "pytest" in text or (repo / "tests").is_dir() or (repo / "pytest.ini").exists():
            found.setdefault("test", "pytest")
        if re.search(r"ruff|flake8|pylint|mypy", text) or (repo / "ruff.toml").exists():
            found.setdefault("lint", "ruff/flake8/mypy")
        if "[build-system]" in text:
            found.setdefault("build", "python -m build")
    elif (repo / "requirements.txt").is_file() or (repo / "pytest.ini").exists():
        stack = "Python" if stack == "neznámý stack" else stack
        if (repo / "pytest.ini").exists() or (repo / "tests").is_dir():
            found.setdefault("test", "pytest")

    if (repo / "Cargo.toml").is_file():
        stack = "Rust"
        found.update({"test": "cargo test", "lint": "cargo clippy", "build": "cargo build"})
    if (repo / "go.mod").is_file():
        stack = "Go"
        found.update({"test": "go test ./...", "lint": "go vet ./...", "build": "go build ./..."})
    return found, stack


def check_scripts(repo: Path) -> list[dict[str, str]]:
    found, stack = _scripts(repo)
    rows = []
    for key, label, level in (("test", "Test skript", FAIL), ("lint", "Lint skript", WARN),
                              ("build", "Build skript", WARN)):
        if key in found:
            rows.append(_check(label, OK, f"{found[key]} ({stack})"))
        else:
            lvl = level if stack != "neznámý stack" or key != "test" else WARN
            rows.append(_check(
                label, lvl, f"nenalezen ({stack})",
                f"Builder musí po každém kroku pustit {key} a commitnout jen zelené — "
                f"přidej {key} skript (package.json / Makefile / pyproject).",
                "" if lvl == FAIL else
                f"pilot půjde, ale AI nebude mít čím po kroku ověřit {key} (kontroly až v Ship)"
            ))
    return rows


def check_ci(repo: Path) -> dict[str, str]:
    name = "CI konfigurace"
    wf = repo / ".github" / "workflows"
    if wf.is_dir() and any(wf.glob("*.y*ml")):
        return _check(name, OK, ".github/workflows")
    found = [f for f in CI_FILES if (repo / f).exists()]
    if found:
        return _check(name, OK, ", ".join(found))
    return _check(name, WARN, "žádná CI konfigurace",
                  "Přidej CI (lint + test + build) — stačí jedna GitHub Actions workflow.",
                  "pilot půjde, ale PR ze Ship bude bez automatických kontrol")


def check_preview(repo: Path) -> dict[str, str]:
    name = "Preview deploy"
    found = [f for f in PREVIEW_FILES if (repo / f).exists()]
    wf = repo / ".github" / "workflows"
    if wf.is_dir():
        for f in wf.glob("*.y*ml"):
            if "preview" in f.read_text(encoding="utf-8", errors="replace").lower() \
                    or "preview" in f.name.lower():
                found.append(f".github/workflows/{f.name}")
                break
    if found:
        return _check(name, OK, ", ".join(found))
    return _check(name, OK, "žádný preview deploy — stačí `pflanzer preview up`",
                  "Po Buildu `pflanzer preview up --slug <slug>` spustí 3 varianty za heslem "
                  "(lokálně, v síti `--host 0.0.0.0`, odkudkoli s cloudflared). Firemní preview "
                  "deploy je volitelný.")


def _git_add_command(repo: Path) -> str:
    """`git add` jen pro existující cesty (.gitignore nemusí v repu být)."""
    paths = ["docs", ".pflanzer", "tests"] + ([".gitignore"] if (repo / ".gitignore").exists() else [])
    return f"git add -A {' '.join(paths)}"


def check_pushed(repo: Path, has_origin: bool) -> list[dict[str, str]]:
    name = "Init soubory commitnuté a pushnuté"
    missing_init = [f for f in INIT_FILES if not (repo / f).exists()]
    if missing_init:
        return [_check(name, FAIL, f"chybí: {', '.join(missing_init)}", "Spusť `pflanzer init`.")]
    rows: list[dict[str, str]] = []

    untracked = []
    dirty = []
    for f in INIT_FILES:
        rc, _ = _git(repo, "ls-files", "--error-unmatch", f)
        if rc != 0:
            untracked.append(f)
            continue
        rc, out = _git(repo, "status", "--porcelain", "--", f)
        if out.strip():
            dirty.append(f)
    if untracked or dirty:
        bad = untracked + dirty
        return [_check(name, FAIL, f"necommitnuté: {', '.join(bad)}",
                       f"`{_git_add_command(repo)} && git commit -m 'chore(pflanzer): init' && git push -u origin HEAD`")]
    if not has_origin:
        return [_check(name, FAIL, "bez originu nelze ověřit push", "Přidej origin a pushni.")]

    cfg = _read_toml_project(repo)
    branch = cfg.get("target_branch") or "main"
    rc, out = _git(repo, "fetch", "origin", "--quiet", timeout=30)
    fetched = rc == 0
    ref = f"origin/{branch}"
    rc, _ = _git(repo, "rev-parse", "--verify", "--quiet", ref)
    if rc != 0:
        return [_check(name, FAIL, f"větev `{ref}` na originu neexistuje",
                       f"`git push -u origin {branch}` (worktrees se klonují z originu).")]
    not_pushed = []
    for f in INIT_FILES:
        rc, _ = _git(repo, "diff", "--quiet", ref, "--", f)
        rc2, _ = _git(repo, "cat-file", "-e", f"{ref}:{f}")
        if rc2 != 0 or rc != 0:
            not_pushed.append(f)
    note = "" if fetched else " (origin nedostupný — porovnáno s lokální kopií origin/*)"
    if not_pushed:
        return [_check(name, FAIL, f"na `{ref}` se liší/chybí: {', '.join(not_pushed)}{note}",
                       f"`git push origin HEAD:{branch}` — worktrees nepushnuté soubory neuvidí.")]
    rows.append(_check(name, OK if fetched else WARN, f"shodné s `{ref}`{note}",
                       "" if fetched else "Zkontroluj síť a spusť doctor znovu."))
    return rows


def check_project_toml(repo: Path) -> dict[str, str]:
    name = "project.toml (owner)"
    path = repo / ".pflanzer" / "project.toml"
    if not path.is_file():
        return _check(name, FAIL, "chybí", "`pflanzer init`.")
    text = path.read_text(encoding="utf-8", errors="replace")
    left = re.findall(r"=\s*\"<[^\"]*>\"", text)
    if left:
        return _check(name, WARN, f"{len(left)}× nevyplněný placeholder",
                      "Doplň `target_branch_owner` (GitHub handle) a `shadow_pm`.",
                      "pilot půjde, ale PR ze Ship nebude mít automaticky revieweře")
    return _check(name, OK, ".pflanzer/project.toml")


def check_gates_yaml(repo: Path) -> dict[str, str] | None:
    """⚠ když repo má pflanzer.gates.yml a PyYAML chybí (jinak se brány nenačtou)."""
    name = "Gate adaptér (YAML)"
    if not any((repo / f).is_file() for f in ("pflanzer.gates.yml", "pflanzer.gates.yaml")):
        return None
    try:
        import yaml  # noqa: F401
    except ImportError:
        return _check(name, WARN, "pflanzer.gates.yml je v repu, ale chybí PyYAML",
                      "Použijte pflanzer.gates.json, nebo `pip install pyyaml`.",
                      "pilot půjde, ale Ship brány z adaptéru nenačte")
    return None


def run_checks(repo: Path) -> list[dict[str, str]]:
    git_rows, origin = check_git(repo)
    rows = list(git_rows)
    if git_rows[0]["status"] == FAIL and "není git repo" in git_rows[0]["detail"]:
        return rows
    rows.append(check_guide(repo))
    rows.append(check_constitution(repo))
    rows.append(check_project_toml(repo))
    rows.append(check_package_manager(repo))
    gy = check_gates_yaml(repo)
    if gy:
        rows.append(gy)
    rows.extend(check_scripts(repo))
    rows.append(check_ci(repo))
    rows.append(check_preview(repo))
    rows.extend(check_pushed(repo, origin is not None))
    return rows


def render(repo: Path, rows: list[dict[str, str]]) -> str:
    """Human view as markdown (kept for scripts; `main` uses ux.emit)."""
    from tool.cli.ux import render as ux_render
    title, lines, nxt, warns, tips = _human(repo, rows)
    return ux_render(title, lines, nxt, tips, warns)


def _human(repo: Path, rows: list[dict[str, str]]):
    fails = [r for r in rows if r["status"] == FAIL]
    warns = [r for r in rows if r["status"] == WARN]
    oks = [r for r in rows if r["status"] == OK]
    lines: list[str] = []
    for r in fails:
        lines.append(f"✗ {r['check']} — {r['detail']}. {r['advice']}".strip())
    for r in warns:
        impact = (r["impact"][0].upper() + r["impact"][1:] + ". ") if r.get("impact") else ""
        lines.append(f"⚠ {r['check']} — {r['detail']}. {impact}{r['advice']}".strip())
    if oks:
        lines.append(f"✓ V pořádku ({len(oks)}): " + ", ".join(r["check"] for r in oks))
    ready = "ano" if not fails else "ne"
    title = f"Připraveno ke Kickoffu: {ready}" + (
        f" — {len(warns)}× s výhradou" if not fails and warns else "")
    if fails:
        nxt = f"oprav ✗ ({fails[0]['check']}): {fails[0]['advice']} — pak `pflanzer doctor` znovu"
    else:
        nxt = "restartuj Claude Code v tomto repu a spusť `/pm start`"
    return title, lines, nxt, [], tips_for("doctor", {})


def main() -> None:
    p = CzechArgumentParser(prog="pflanzer doctor", description=__doc__.split("\n")[0])
    p.add_argument("--target", default=".", help="Cesta k target repu (default: cwd)")
    p.add_argument("--json", action="store_true", help="Strojový výstup")
    args = p.parse_args()

    repo = Path(args.target).expanduser().resolve()
    if not repo.is_dir():
        die(f"{repo} není složka. Příklad: `pflanzer doctor --target ~/projekty/moje-appka`.")
        return
    rows = run_checks(repo)
    fails = sum(r["status"] == FAIL for r in rows)
    data = {"brand": "Pflanzer Method | pflanzer.cz/method", "target": str(repo),
            "ready": fails == 0, "checks": rows}
    title, lines, nxt, warns, tips = _human(repo, rows)
    emit(data, title=title, lines=lines, next_step=nxt, tips=tips, warnings=warns,
         as_json=args.json)
    sys.exit(0 if fails == 0 else 1)


if __name__ == "__main__":
    main()
