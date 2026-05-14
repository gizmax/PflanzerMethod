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
        ],
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--target", default=".", help="Target repo path (default: cwd)")
    p.add_argument("--force", action="store_true", help="Overwrite existing files")
    args = p.parse_args()

    out = init(Path(args.target), force=args.force)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(0 if out.get("ok") else 1)


if __name__ == "__main__":
    main()
