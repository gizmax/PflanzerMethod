"""`pflanzer doctor [--target DIR] [--json]` — je repo připravené na Kickoff?

Checklist inspirovaný „vibe engineeringem“ (Willison): AI buildeři jsou
tak dobří, jak dobré je repo — testy, lint, build, CI, konvence a pravidla.
Ověřuje se, že je repo připravené na tři worktrees s AI:

  ✓ v pořádku   ⚠ upozornění (Kickoff jde, ale zhorší se Build)   ✗ blokuje

Exit code 0, pokud není žádné ✗. Nic nemění (jen `git fetch origin`
kvůli porovnání s originem).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
GUIDE_TEMPLATE = PLUGIN_ROOT / "tool" / "templates" / "INTEGRATION_GUIDE.md.template"
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


def _check(name: str, status: str, detail: str, advice: str = "") -> dict[str, str]:
    return {"check": name, "status": status, "detail": detail, "advice": advice}


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


def check_guide(repo: Path) -> dict[str, str]:
    name = "INTEGRATION_GUIDE.md"
    guide = repo / "docs" / "INTEGRATION_GUIDE.md"
    if not guide.is_file():
        guide = repo / "INTEGRATION_GUIDE.md"
    if not guide.is_file():
        return _check(name, FAIL, "chybí", "`pflanzer init`, pak ho vyplň podle reality repa.")
    text = guide.read_text(encoding="utf-8", errors="replace")
    if GUIDE_TEMPLATE.is_file() and text.strip() == GUIDE_TEMPLATE.read_text(encoding="utf-8").strip():
        return _check(name, FAIL, "pořád jen nevyplněná šablona",
                      "Vyplň auth, API, state, logger, folder layout, test runner (cca 30 min).")
    placeholders = re.findall(r"<[^<>\n]*(?:\s\||\|\s|\s[^<>\n]*\s|doplň|vyplň)[^<>\n]*>", text)
    if placeholders:
        return _check(name, WARN, f"{len(placeholders)}× zbývá placeholder `<…>`",
                      "Nahraď zbylé `<…>` skutečnými hodnotami, AI jinak hádá.")
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
                      "Doplň povolenou síť, zakázané adresáře a příkazy lint/test/build.")
    return _check(name, OK, ".pflanzer/CONSTITUTION.md")


def check_package_manager(repo: Path) -> dict[str, str]:
    name = "Package manager / lockfile"
    found = [f for f in LOCKFILES if (repo / f).exists()]
    if found:
        return _check(name, OK, ", ".join(found))
    manifests = [m for m in ("package.json", "pyproject.toml", "requirements.txt", "Cargo.toml",
                             "go.mod", "Gemfile", "composer.json", "pubspec.yaml", "Package.swift")
                 if (repo / m).exists()]
    if manifests:
        return _check(name, WARN, f"{', '.join(manifests)} bez lockfilu",
                      "Commitni lockfile — install ve worktrees (`npm ci`/`--frozen-lockfile`) ho potřebuje.")
    return _check(name, WARN, "žádný manifest ani lockfile",
                  "Pokud je to statický web, ignoruj; jinak přidej manifest a lockfile.")


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
                f"přidej {key} skript (package.json / Makefile / pyproject)."
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
                  "PR ze Ship bude bez automatických kontrol — přidej CI (lint + test + build).")


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
    return _check(name, WARN, "žádná indikace preview deploye",
                  "Bez preview URL zástupci v Asyncu varianty neuvidí; "
                  "počítej s `npm run dev` + port-forward (nebo přidej Vercel/Netlify preview).")


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
                       "`git add docs/INTEGRATION_GUIDE.md .pflanzer/ && git commit -m 'chore(pflanzer): init' && git push`")]
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
                      "Doplň `target_branch_owner` (GitHub handle) a `shadow_pm`.")
    return _check(name, OK, ".pflanzer/project.toml")


def run_checks(repo: Path) -> list[dict[str, str]]:
    git_rows, origin = check_git(repo)
    rows = list(git_rows)
    if git_rows[0]["status"] == FAIL and "není git repo" in git_rows[0]["detail"]:
        return rows
    rows.append(check_guide(repo))
    rows.append(check_constitution(repo))
    rows.append(check_project_toml(repo))
    rows.append(check_package_manager(repo))
    rows.extend(check_scripts(repo))
    rows.append(check_ci(repo))
    rows.append(check_preview(repo))
    rows.extend(check_pushed(repo, origin is not None))
    return rows


def render(repo: Path, rows: list[dict[str, str]]) -> str:
    fails = sum(r["status"] == FAIL for r in rows)
    warns = sum(r["status"] == WARN for r in rows)
    out = [BRAND_LINE, "", f"# Připravenost repa — `{repo}`", "",
           "| | Kontrola | Nález | Rada |", "|---|----------|-------|------|"]
    for r in rows:
        out.append(f"| {SYMBOL[r['status']]} | {r['check']} | {r['detail']} | {r['advice']} |")
    ready = "ano" if fails == 0 else "ne"
    out += ["", f"**Připraveno ke Kickoffu: {ready}**  "
            f"(✗ {fails}, ⚠ {warns}, ✓ {len(rows) - fails - warns})"]
    if fails:
        out.append("Oprav ✗ a spusť `pflanzer doctor` znovu.")
    else:
        out.append("Pokračuj: restartuj Claude Code v tomto repu a spusť `/pm start`."
                   + (" ⚠ nejsou blokující, ale zhorší Build." if warns else ""))
    return "\n".join(out)


def main() -> None:
    p = argparse.ArgumentParser(prog="pflanzer doctor", description=__doc__.split("\n")[0])
    p.add_argument("--target", default=".", help="Cesta k target repu (default: cwd)")
    p.add_argument("--json", action="store_true", help="Strojový výstup")
    args = p.parse_args()

    repo = Path(args.target).expanduser().resolve()
    if not repo.is_dir():
        print(f"CHYBA: {repo} není složka.", file=sys.stderr)
        sys.exit(2)
    rows = run_checks(repo)
    fails = sum(r["status"] == FAIL for r in rows)
    if args.json:
        print(json.dumps({"brand": "Pflanzer Method | pflanzer.cz/method", "target": str(repo),
                          "ready": fails == 0, "checks": rows}, ensure_ascii=False, indent=2))
    else:
        print(render(repo, rows))
    sys.exit(0 if fails == 0 else 1)


if __name__ == "__main__":
    main()
