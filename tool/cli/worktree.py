"""Worktree setup pro Pflanzer in-room session — KRITICKÝ P0 FIX.

Před tímto fixem `pflanzer.md` doporučoval `git worktree add` z PflanzerMethod
meta-repu. Důsledek: Claude Code kódoval **uvnitř meta-toolu**, ne uvnitř
target zákazníkova repa. Reuse byl z definice 0 % (per autoresearch
perspektiva 05 brownfield-integration § P0).

Po fixu (Sprint 1):
1. Naclonujeme `projects.target_repo_url` do `~/.pflanzer/targets/<repo-slug>/`
   (cached, full clone — ne shallow, AI potřebuje history pro context).
2. Vytvoříme 3 worktree z target clonu:
   `git worktree add <target-clone>/../<slug>-A -b pflanzer/<slug>-A origin/main`
3. Per worktree spustíme package-manager install (pnpm/yarn/npm dle
   `packageManager` field v target `package.json`).
4. Pre-flight check: každý worktree má `git remote get-url origin == target_repo_url`.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tool.cli.db import audit, current_actor, transaction  # noqa: E402

TARGETS_CACHE = Path.home() / ".pflanzer" / "targets"


@dataclass
class WorktreeSetup:
    slug: str
    target_repo_url: str
    target_branch: str
    target_clone_path: Path
    worktrees: list[Path]
    package_manager: str | None
    install_results: list[dict[str, Any]]


def _slugify_repo(url: str) -> str:
    """Extract repo slug from git URL.
    https://github.com/foo/bar.git → foo-bar
    git@github.com:foo/bar.git → foo-bar
    """
    m = re.search(r"[:/]([\w.-]+)/([\w.-]+?)(?:\.git)?/?$", url)
    if not m:
        raise ValueError(f"Cannot extract repo slug from URL: {url}")
    return f"{m.group(1)}-{m.group(2)}".lower()


def _detect_package_manager(repo_path: Path) -> str | None:
    """Detect from package.json `packageManager` field, then lockfiles."""
    pkg = repo_path / "package.json"
    if pkg.exists():
        try:
            data = json.loads(pkg.read_text(encoding="utf-8"))
            pm = data.get("packageManager", "")
            if pm.startswith("pnpm@"):
                return "pnpm"
            if pm.startswith("yarn@"):
                return "yarn"
            if pm.startswith("npm@"):
                return "npm"
        except (json.JSONDecodeError, OSError):
            pass
    if (repo_path / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (repo_path / "yarn.lock").exists():
        return "yarn"
    if (repo_path / "package-lock.json").exists():
        return "npm"
    return None


def _run(cmd: list[str], cwd: Path | None = None, timeout: int = 300) -> tuple[int, str, str]:
    res = subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout,
    )
    return res.returncode, res.stdout, res.stderr


def _ensure_target_clone(target_repo_url: str, target_branch: str) -> Path:
    """Clone target repo (cached). Returns local path to clone."""
    repo_slug = _slugify_repo(target_repo_url)
    clone_path = TARGETS_CACHE / repo_slug

    if clone_path.exists() and (clone_path / ".git").exists():
        # Update existing clone
        rc, out, err = _run(["git", "fetch", "origin"], cwd=clone_path, timeout=60)
        if rc != 0:
            raise RuntimeError(f"git fetch failed in {clone_path}: {err}")
        return clone_path

    TARGETS_CACHE.mkdir(parents=True, exist_ok=True)
    # Full clone (not --depth=1) — AI needs history for context understanding
    rc, out, err = _run(
        ["git", "clone", target_repo_url, str(clone_path)], timeout=300,
    )
    if rc != 0:
        raise RuntimeError(f"git clone failed: {err.strip()}")

    # Checkout target branch
    rc, out, err = _run(["git", "checkout", target_branch], cwd=clone_path)
    if rc != 0:
        # Branch may not exist yet — fall back to default
        rc, out, _ = _run(["git", "branch", "--show-current"], cwd=clone_path)
        actual_branch = out.strip()
        if actual_branch != target_branch:
            print(f"[warn] target_branch='{target_branch}' not found, using '{actual_branch}'",
                  file=sys.stderr)
    return clone_path


def _create_worktrees(
    target_clone: Path, slug: str, base_branch: str,
    mode: str = "parallel",
) -> list[Path]:
    """Create worktrees per mode.

    - parallel (default): 3 worktrees A/B/C as siblings.
    - mob (per ADR-0011): 1 worktree '<slug>-mob', single shared branch.
    """
    worktrees: list[Path] = []
    variants = ("A", "B", "C") if mode == "parallel" else ("mob",)
    for variant in variants:
        wt_path = target_clone.parent / f"{slug}-{variant}"
        feat_branch = f"pflanzer/{slug}-{variant}"

        if wt_path.exists():
            # Idempotent: skip existing
            worktrees.append(wt_path)
            continue

        # Check if branch already exists; if yes, checkout, else create
        rc, _, _ = _run(
            ["git", "rev-parse", "--verify", feat_branch],
            cwd=target_clone,
        )
        if rc == 0:
            # Branch exists — add worktree from it
            rc, out, err = _run(
                ["git", "worktree", "add", str(wt_path), feat_branch],
                cwd=target_clone,
            )
        else:
            # Create new branch from base
            rc, out, err = _run(
                ["git", "worktree", "add", str(wt_path), "-b", feat_branch, base_branch],
                cwd=target_clone,
            )
        if rc != 0:
            raise RuntimeError(f"git worktree add failed for {variant}: {err.strip()}")
        worktrees.append(wt_path)
    return worktrees


def _install_deps(worktrees: list[Path], pm: str | None) -> list[dict[str, Any]]:
    """Run package-manager install per worktree (best-effort)."""
    if not pm:
        return [{"path": str(w), "status": "skipped", "reason": "no package manager detected"}
                for w in worktrees]
    install_cmd = {
        "pnpm": ["pnpm", "install", "--frozen-lockfile"],
        "yarn": ["yarn", "install", "--frozen-lockfile"],
        "npm":  ["npm", "ci", "--no-audit", "--no-fund"],
    }[pm]
    results = []
    for w in worktrees:
        if (w / "node_modules").exists():
            results.append({"path": str(w), "status": "cached"})
            continue
        rc, out, err = _run(install_cmd, cwd=w, timeout=600)
        results.append({
            "path": str(w),
            "status": "ok" if rc == 0 else "failed",
            "details": (out + err)[-300:] if rc != 0 else None,
        })
    return results


def setup(slug: str, *, install_deps: bool = True,
          mode: str = "parallel") -> WorktreeSetup:
    """Setup worktrees for in-room session pro `slug` projekt.

    Args:
        slug: project slug.
        install_deps: auto npm/pnpm/yarn install per worktree.
        mode: 'parallel' (3 worktrees A/B/C — default) | 'mob' (1 worktree).

    Reads `projects.target_repo_url` + `target_branch` z DB.
    Vrátí WorktreeSetup s konkrétními paths které facilitátor použije.
    """
    if mode not in ("parallel", "mob"):
        raise ValueError(f"mode must be 'parallel' or 'mob', got '{mode}'")
    with transaction() as conn:
        proj = conn.execute(
            "SELECT id, target_repo_url, target_branch, throwaway_or_evolve "
            "FROM projects WHERE slug = ?", (slug,),
        ).fetchone()
        if not proj:
            raise ValueError(f"Project '{slug}' not found.")
        project_id, target_url, target_branch, profile = (
            int(proj[0]), proj[1], proj[2] or "main", proj[3],
        )

    if not target_url:
        raise ValueError(
            f"Project '{slug}' has no target_repo_url set. "
            "Mandatory pro pilot/production profil. "
            "Spusť `python -c \"import sqlite3; sqlite3.connect('data/pflanzer.db')"
            f".execute('UPDATE projects SET target_repo_url=? WHERE slug=?', "
            f"('https://github.com/...', '{slug}'))\"` "
            "nebo re-run /pflanzer wizard."
        )

    print(f"[setup] target_repo_url = {target_url}", file=sys.stderr)
    print(f"[setup] target_branch = {target_branch}", file=sys.stderr)

    target_clone = _ensure_target_clone(target_url, target_branch)
    print(f"[setup] target clone at {target_clone}", file=sys.stderr)

    worktrees = _create_worktrees(target_clone, slug, target_branch, mode=mode)
    print(f"[setup] mode={mode} → created {len(worktrees)} worktree(s): "
          f"{[w.name for w in worktrees]}", file=sys.stderr)

    pm = _detect_package_manager(target_clone)
    print(f"[setup] detected package manager: {pm}", file=sys.stderr)

    install_results = []
    if install_deps:
        install_results = _install_deps(worktrees, pm)
        ok_count = sum(1 for r in install_results if r["status"] in ("ok", "cached"))
        print(f"[setup] install: {ok_count}/{len(install_results)} ok",
              file=sys.stderr)

    # Audit
    with transaction() as conn:
        audit(
            conn, action="worktree.setup",
            target_type="project", target_id=project_id,
            payload={
                "slug": slug, "target_repo_url": target_url,
                "target_branch": target_branch,
                "mode": mode,
                "worktrees": [str(w) for w in worktrees],
                "package_manager": pm,
                "install_ok": sum(1 for r in install_results
                                  if r["status"] in ("ok", "cached")),
            },
        )

    return WorktreeSetup(
        slug=slug, target_repo_url=target_url, target_branch=target_branch,
        target_clone_path=target_clone, worktrees=worktrees,
        package_manager=pm, install_results=install_results,
    )


def verify_cwd_in_target(slug: str, cwd: Path) -> tuple[bool, str]:
    """Pre-flight check: cwd's git remote must match target_repo_url."""
    with transaction() as conn:
        row = conn.execute(
            "SELECT target_repo_url FROM projects WHERE slug = ?", (slug,),
        ).fetchone()
        if not row or not row[0]:
            return False, "No target_repo_url for this project"
        expected = row[0]

    rc, out, _ = _run(["git", "remote", "get-url", "origin"], cwd=cwd)
    if rc != 0:
        return False, f"Not in a git repo: {cwd}"
    actual = out.strip()
    # Normalize for comparison: strip .git, https vs ssh
    def norm(u: str) -> str:
        return re.sub(r"\.git/?$", "", u).replace("git@github.com:", "https://github.com/")
    if norm(actual) != norm(expected):
        return False, (
            f"Wrong repo: cwd remote = {actual}, expected {expected}. "
            "Run `python tool/cli/worktree.py setup --slug X` first."
        )
    return True, "OK"


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    p_setup = sub.add_parser("setup", help="Clone target + create worktrees")
    p_setup.add_argument("--slug", required=True)
    p_setup.add_argument("--mode", choices=["parallel", "mob"], default="parallel",
                         help="parallel = 3 worktrees A/B/C (default); mob = 1 worktree (per ADR-0011)")
    p_setup.add_argument("--no-install", action="store_true",
                         help="Skip package-manager install (faster, ale gates skipnou)")

    p_verify = sub.add_parser("verify", help="Verify cwd is in target repo")
    p_verify.add_argument("--slug", required=True)
    p_verify.add_argument("--cwd", default=".")

    args = p.parse_args()

    if args.cmd == "setup":
        s = setup(args.slug, install_deps=not args.no_install, mode=args.mode)
        if args.mode == "mob":
            next_steps = [
                f"cd {s.worktrees[0]} && claude  # MOB session — všech 6 lidí "
                "u 1 monitoru (per ADR-0011)",
                "Driver/navigator rotation: 8 min cycle, 25 min hard break",
                "Iteration timing: 25 min iter1 + 25 min iter2 + 15 min "
                "review/decide (90 min cap)",
            ]
        else:
            next_steps = [
                f"cd {w} && claude  # variant {chr(ord('A')+i)}"
                for i, w in enumerate(s.worktrees)
            ]
        print(json.dumps({
            "slug": s.slug,
            "mode": args.mode,
            "target_repo_url": s.target_repo_url,
            "target_clone_path": str(s.target_clone_path),
            "worktrees": [str(w) for w in s.worktrees],
            "package_manager": s.package_manager,
            "install_results": s.install_results,
            "next_steps": next_steps,
        }, ensure_ascii=False, indent=2))
    else:
        ok, msg = verify_cwd_in_target(args.slug, Path(args.cwd).resolve())
        print(json.dumps({"ok": ok, "message": msg}))
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
