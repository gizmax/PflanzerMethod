"""Worktree setup pro Pflanzer in-room session — KRITICKÝ P0 FIX.

Před tímto fixem `pflanzer.md` doporučoval `git worktree add` z PflanzerMethod
meta-repu. Důsledek: Claude Code kódoval **uvnitř meta-toolu**, ne uvnitř
target zákazníkova repa. Reuse byl z definice 0 % (per autoresearch
perspektiva 05 brownfield-integration § P0).

Po fixu (Sprint 1, ADR-0009) + audit 2026-09 (N8, N9, N11, N13, N14):
1. Pro každý repo z `projects.target_repos` (FE / BE / monorepo workspace;
   fallback = jediný `target_repo_url`) cached full clone
   v `~/.pflanzer/targets/<repo-slug>/` (override: `PFLANZER_TARGETS_DIR`).
2. Worktrees A/B/C (nebo 1× mob) per repo, branch `pflanzer/<slug>-<X>` ve
   všech repech. Primární repo: `<targets>/<slug>-<X>`, další repa:
   `<targets>/<slug>-<X>-<role>`.
3. Per worktree git config (`pflanzer.variant/session/builder`) +
   `prepare-commit-msg` hook, který doplní trailery per
   `07-handoff-do-vyvoje.md` § AI code provenance.
4. Data leakage guard (secrets, `.env*`, prod dumpy) + `CLAUDE.md` se sekcí
   „Pflanzer session rules".
5. Package-manager install (JS repa); non-JS repa se instalují lazily v gates.
6. Pre-flight check: `git remote get-url origin` ∈ target repos.

Další příkazy: `guard`, `init-pr` (první PR pilotu = INTEGRATION_GUIDE +
CLAUDE.md), `preview` (draft PR / Playwright záznam per varianta),
`set-session`, `set-url`, `verify`.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tool.cli.db import audit, current_actor, transaction  # noqa: E402,F401

TARGETS_CACHE = Path(
    os.environ.get("PFLANZER_TARGETS_DIR") or (Path.home() / ".pflanzer" / "targets")
).expanduser()
TEMPLATES_DIR = REPO_ROOT / "tool" / "templates"
CLAUDE_MD_TEMPLATE = TEMPLATES_DIR / "CLAUDE.md.pflanzer.template"
INTEGRATION_GUIDE_TEMPLATE = TEMPLATES_DIR / "INTEGRATION_GUIDE.md.template"
PREVIEWS_DIR = REPO_ROOT / "data" / "previews"
INIT_PR_DIR = REPO_ROOT / "data" / "init-pr"

BRAND_LINE = "Pflanzer Method | pflanzer.cz/method"
PFLANZER_START = "<!-- pflanzer:start -->"
PFLANZER_END = "<!-- pflanzer:end -->"
HOOK_MARKER = "pflanzer-trailers-hook"
HOOK_NAME = "prepare-commit-msg"
HOOK_STANDALONE = "pflanzer-prepare-commit-msg"

PARALLEL_VARIANTS = ("A", "B", "C")
MOB_VARIANTS = ("mob",)
DEFAULT_BUILDER = "claude-code"
SESSION_VALUES = ("1", "2", "ship")
BE_ROLES = {"be", "backend", "api"}
# Role preference for the "primary" repo (its worktrees keep the historic
# `<slug>-<X>` path that extract.py / handoff_pr.py rely on).
PRIMARY_ROLE_ORDER = ("app", "fe", "web", "ui", "mono", "monorepo", "frontend")


# --------------------------------------------------------------------------
# Target repos (N8): model, parsing, validation
# --------------------------------------------------------------------------


@dataclass
class TargetRepo:
    role: str
    url: str
    branch: str = "main"
    workspace: str | None = None

    @property
    def is_backend(self) -> bool:
        return self.role in BE_ROLES

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"role": self.role, "url": self.url, "branch": self.branch}
        if self.workspace:
            d["workspace"] = self.workspace
        return d


@dataclass
class WorktreeSetup:
    slug: str
    target_repo_url: str
    target_branch: str
    target_clone_path: Path
    worktrees: list[Path]
    package_manager: str | None
    install_results: list[dict[str, Any]]
    mode: str = "parallel"
    repos: list[dict[str, Any]] = field(default_factory=list)
    guard: list[dict[str, Any]] = field(default_factory=list)
    init_missing: list[dict[str, Any]] = field(default_factory=list)


_REPO_URL_RE = re.compile(
    r"^(?:"
    r"(?:https?|ssh|git)://[^\s/]+/(?:[\w.~%-]+/)+[\w.~%-]+?(?:\.git)?/?"  # scheme URLs
    r"|[\w.-]+@[\w.-]+:(?:[\w.~-]+/)+[\w.-]+?(?:\.git)?/?"                 # scp-like ssh
    r"|file://(?:/[^\s/]+){2,}/?"                                           # local (tests)
    r")$"
)


def validate_repo_url(url: str | None) -> bool:
    """Accept https/ssh/scp-like/file git URLs with at least `<owner>/<repo>`."""
    return bool(url) and bool(_REPO_URL_RE.match(url.strip()))


def _slugify_repo(url: str) -> str:
    """Extract repo slug from git URL.
    https://github.com/foo/bar.git → foo-bar
    git@github.com:foo/bar.git → foo-bar
    """
    m = re.search(r"[:/]([\w.-]+)/([\w.-]+?)(?:\.git)?/?$", url)
    if not m:
        raise ValueError(f"Cannot extract repo slug from URL: {url}")
    return f"{m.group(1)}-{m.group(2)}".lower()


def _norm_url(u: str) -> str:
    """Normalize a git URL for equality checks (strip .git, ssh → https)."""
    u = u.strip().rstrip("/")
    u = re.sub(r"\.git$", "", u)
    m = re.match(r"^[\w.-]+@([\w.-]+):(.+)$", u)
    if m:
        u = f"https://{m.group(1)}/{m.group(2)}"
    return u.lower()


def _clean_workspace(ws: str | None) -> str | None:
    if not ws:
        return None
    ws = ws.strip().strip("/")
    if ws.startswith("./"):
        ws = ws[2:]
    if not ws:
        return None
    if ".." in Path(ws).parts or Path(ws).is_absolute():
        raise ValueError(f"workspace '{ws}' musí být relativní cesta uvnitř repa (bez '..').")
    return ws


def parse_target_repos_text(text: str) -> list[dict[str, Any]]:
    """Parse the wizard text input `role=url[#branch][:workspace], ...`.

    Examples:
        https://github.com/org/app                       → 1 repo, role app
        fe=https://github.com/org/web#main:apps/web, be=git@github.com:org/api.git#develop
    """
    entries: list[dict[str, Any]] = []
    for chunk in re.split(r"[,\n;]", text or ""):
        chunk = chunk.strip()
        if not chunk:
            continue
        role = None
        m = re.match(r"^([A-Za-z][\w-]{0,15})\s*=\s*(.+)$", chunk)
        if m:
            role, chunk = m.group(1).lower(), m.group(2).strip()
        branch, workspace = "main", None
        if "#" in chunk:
            url, rest = chunk.split("#", 1)
            b, _, workspace = rest.partition(":")
            branch = b.strip() or "main"
        else:
            url = chunk
            idx = chunk.rfind(":")
            if idx > 0:
                head, tail = chunk[:idx], chunk[idx + 1:]
                if (tail and not tail.startswith("/") and not re.match(r"^\d+(/|$)", tail)
                        and validate_repo_url(head)):
                    url, workspace = head, tail
        entries.append({"role": role, "url": url.strip(), "branch": branch,
                        "workspace": (workspace or "").strip() or None})
    return entries


def normalize_target_repos(
    raw: Any, *, fallback_url: str | None = None, fallback_branch: str | None = None,
) -> list[TargetRepo]:
    """Turn `target_repos` (JSON string / list / wizard text / None) into TargetRepo list.

    Backward compatible: None/empty → `[{"role": "app", "url": fallback_url,
    "branch": fallback_branch}]` (or [] when there is no fallback URL either).
    Raises ValueError with a Czech, actionable message on invalid input.
    """
    items: list[dict[str, Any]]
    if raw is None or (isinstance(raw, str) and not raw.strip()) or raw == []:
        if not fallback_url:
            return []
        items = [{"role": "app", "url": fallback_url, "branch": fallback_branch or "main"}]
    elif isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = parse_target_repos_text(raw)
        items = parsed if isinstance(parsed, list) else [parsed]
    elif isinstance(raw, dict):
        items = [raw]
    elif isinstance(raw, list):
        items = [({"url": x} if isinstance(x, str) else x) for x in raw]
    else:
        raise ValueError(f"target_repos: nepodporovaný formát {type(raw).__name__}")

    repos: list[TargetRepo] = []
    seen_roles: set[str] = set()
    for i, it in enumerate(items):
        if not isinstance(it, dict) or not it.get("url"):
            raise ValueError(f"target_repos[{i}]: chybí 'url' ({it!r}).")
        url = str(it["url"]).strip()
        if not validate_repo_url(url):
            raise ValueError(
                f"target_repos[{i}]: '{url}' není platná git URL "
                "(očekávám https://<host>/<org>/<repo>, git@<host>:<org>/<repo>.git "
                "nebo file:///<cesta>/<repo>)."
            )
        role = str(it.get("role") or ("app" if len(items) == 1 else f"repo{i + 1}")).lower()
        if not re.match(r"^[a-z][\w-]{0,15}$", role):
            raise ValueError(f"target_repos[{i}]: role '{role}' — použij krátký identifikátor (fe, be, api, app).")
        if role in seen_roles:
            role = f"{role}{i + 1}"
        seen_roles.add(role)
        branch = str(it.get("branch") or fallback_branch or "main").strip()
        repos.append(TargetRepo(role=role, url=url, branch=branch,
                                workspace=_clean_workspace(it.get("workspace"))))
    return repos


def pick_primary(repos: list[TargetRepo], target_repo_url: str | None = None) -> int:
    """Index of the primary repo: the one matching target_repo_url, else by role."""
    if target_repo_url:
        for i, r in enumerate(repos):
            if _norm_url(r.url) == _norm_url(target_repo_url):
                return i
    for role in PRIMARY_ROLE_ORDER:
        for i, r in enumerate(repos):
            if r.role == role:
                return i
    for i, r in enumerate(repos):
        if not r.is_backend:
            return i
    return 0


def load_project(slug: str) -> dict[str, Any]:
    with transaction() as conn:
        row = conn.execute("SELECT * FROM projects WHERE slug = ?", (slug,)).fetchone()
    if not row:
        raise ValueError(f"Project '{slug}' not found.")
    return dict(row)


def load_target_repos(slug: str, project: dict[str, Any] | None = None) -> list[TargetRepo]:
    """Target repos of a project, primary first (see `pick_primary`)."""
    proj = project or load_project(slug)
    repos = normalize_target_repos(
        proj.get("target_repos"),
        fallback_url=proj.get("target_repo_url"),
        fallback_branch=proj.get("target_branch") or "main",
    )
    if not repos:
        return []
    idx = pick_primary(repos, proj.get("target_repo_url"))
    return [repos[idx]] + [r for i, r in enumerate(repos) if i != idx]


def worktree_dir(slug: str, variant: str, repo: TargetRepo, primary: bool) -> Path:
    """Primary repo keeps `<slug>-<X>` (extract.py contract); others get `-<role>`."""
    name = f"{slug}-{variant}" if primary else f"{slug}-{variant}-{repo.role}"
    return TARGETS_CACHE / name


def variant_worktrees(slug: str, repos: list[TargetRepo], variant: str) -> list[tuple[TargetRepo, Path]]:
    """All (repo, worktree path) pairs for one variant — pure path computation."""
    return [(r, worktree_dir(slug, variant, r, i == 0)) for i, r in enumerate(repos)]


def variant_label(slug: str, variant: str) -> str:
    return f"{slug}-{variant}"


# --------------------------------------------------------------------------
# Git / process helpers
# --------------------------------------------------------------------------


def _run(cmd: list[str], cwd: Path | None = None, timeout: int = 300,
         env: dict[str, str] | None = None) -> tuple[int, str, str]:
    try:
        res = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout,
            env={**os.environ, **env} if env else None,
        )
    except FileNotFoundError as exc:
        return 127, "", str(exc)
    except subprocess.TimeoutExpired:
        return 124, "", f"timeout after {timeout}s: {' '.join(cmd)}"
    return res.returncode, res.stdout, res.stderr


def _git(cwd: Path, *args: str, timeout: int = 120) -> tuple[int, str, str]:
    return _run(["git", *args], cwd=cwd, timeout=timeout)


def _git_common_dir(repo: Path) -> Path:
    rc, out, err = _git(repo, "rev-parse", "--git-common-dir")
    if rc != 0:
        raise RuntimeError(f"git rev-parse --git-common-dir failed in {repo}: {err.strip()}")
    p = Path(out.strip())
    return p if p.is_absolute() else (repo / p).resolve()


def _ensure_target_clone(target_repo_url: str, target_branch: str) -> Path:
    """Clone target repo (cached). Returns local path to clone."""
    repo_slug = _slugify_repo(target_repo_url)
    clone_path = TARGETS_CACHE / repo_slug

    if clone_path.exists() and (clone_path / ".git").exists():
        rc, out, err = _run(["git", "fetch", "origin", "--prune"], cwd=clone_path, timeout=120)
        if rc != 0:
            raise RuntimeError(f"git fetch failed in {clone_path}: {err}")
        return clone_path

    TARGETS_CACHE.mkdir(parents=True, exist_ok=True)
    # Full clone (not --depth=1) — AI needs history for context understanding
    rc, out, err = _run(["git", "clone", target_repo_url, str(clone_path)], timeout=600)
    if rc != 0:
        raise RuntimeError(f"git clone failed: {err.strip()}")

    rc, out, err = _run(["git", "checkout", target_branch], cwd=clone_path)
    if rc != 0:
        rc, out, _ = _run(["git", "branch", "--show-current"], cwd=clone_path)
        actual_branch = out.strip()
        if actual_branch != target_branch:
            print(f"[warn] target_branch='{target_branch}' not found, using '{actual_branch}'",
                  file=sys.stderr)
    return clone_path


def _resolve_base_ref(clone: Path, branch: str) -> str:
    """Prefer the freshly fetched `origin/<branch>`, then local branch, then HEAD."""
    for candidate in (f"origin/{branch}", branch):
        rc, _, _ = _git(clone, "rev-parse", "--verify", "--quiet", f"{candidate}^{{commit}}")
        if rc == 0:
            return candidate
    print(f"[warn] base '{branch}' nenalezena v {clone}, používám HEAD", file=sys.stderr)
    return "HEAD"


def _add_worktree(clone: Path, wt_path: Path, branch: str, base_ref: str) -> None:
    if wt_path.exists():
        return  # idempotent: reuse existing worktree
    rc, _, _ = _git(clone, "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}")
    if rc == 0:
        rc, out, err = _git(clone, "worktree", "add", str(wt_path), branch)
    else:
        rc, out, err = _git(clone, "worktree", "add", str(wt_path), "-b", branch, base_ref)
    if rc != 0:
        raise RuntimeError(f"git worktree add failed for {wt_path.name}: {err.strip()}")


def _create_worktrees(
    target_clone: Path, slug: str, base_branch: str,
    mode: str = "parallel", *, repo: TargetRepo | None = None, primary: bool = True,
) -> list[Path]:
    """Create worktrees per mode.

    - parallel (default): 3 worktrees A/B/C as siblings.
    - mob (per ADR-0011): 1 worktree '<slug>-mob', single shared branch.
    """
    repo = repo or TargetRepo(role="app", url="", branch=base_branch)
    _git(target_clone, "worktree", "prune")
    base_ref = _resolve_base_ref(target_clone, base_branch)
    worktrees: list[Path] = []
    for variant in (PARALLEL_VARIANTS if mode == "parallel" else MOB_VARIANTS):
        wt_path = worktree_dir(slug, variant, repo, primary)
        _add_worktree(target_clone, wt_path, f"pflanzer/{slug}-{variant}", base_ref)
        worktrees.append(wt_path)
    return worktrees


# --------------------------------------------------------------------------
# Package manager install (JS only; non-JS installs lazily in gates)
# --------------------------------------------------------------------------


def _detect_package_manager(repo_path: Path) -> str | None:
    """Detect from package.json `packageManager` field, then lockfiles."""
    pkg = repo_path / "package.json"
    if not pkg.exists():
        return None
    try:
        data = json.loads(pkg.read_text(encoding="utf-8"))
        pm = str(data.get("packageManager", ""))
        for name in ("pnpm", "yarn", "npm"):
            if pm.startswith(f"{name}@"):
                return name
    except (json.JSONDecodeError, OSError):
        pass
    if (repo_path / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (repo_path / "yarn.lock").exists():
        return "yarn"
    return "npm"


def _install_cmd(wt: Path, pm: str) -> list[str]:
    has_lock = {
        "pnpm": (wt / "pnpm-lock.yaml").exists(),
        "yarn": (wt / "yarn.lock").exists(),
        "npm": (wt / "package-lock.json").exists() or (wt / "npm-shrinkwrap.json").exists(),
    }[pm]
    if pm == "pnpm":
        return ["pnpm", "install", "--frozen-lockfile"] if has_lock else ["pnpm", "install"]
    if pm == "yarn":
        return ["yarn", "install", "--frozen-lockfile"] if has_lock else ["yarn", "install"]
    return (["npm", "ci", "--no-audit", "--no-fund"] if has_lock
            else ["npm", "install", "--no-audit", "--no-fund"])


def _install_deps(worktrees: list[Path], pm: str | None) -> list[dict[str, Any]]:
    """Run package-manager install per worktree (best-effort)."""
    results = []
    for w in worktrees:
        if not (w / "package.json").exists():
            results.append({"path": str(w), "status": "skipped",
                            "reason": "non-JS repo (bez package.json) — Maven/Gradle/.NET/Go "
                                      "závislosti se nainstalují lazily v quality gates"})
            continue
        pm_w = pm or _detect_package_manager(w)
        if not pm_w:
            results.append({"path": str(w), "status": "skipped", "reason": "no package manager detected"})
            continue
        if (w / "node_modules").exists():
            results.append({"path": str(w), "status": "cached"})
            continue
        cmd = _install_cmd(w, pm_w)
        rc, out, err = _run(cmd, cwd=w, timeout=600)
        results.append({
            "path": str(w), "status": "ok" if rc == 0 else "failed", "cmd": " ".join(cmd),
            "details": (out + err)[-300:] if rc != 0 else None,
        })
    return results


# --------------------------------------------------------------------------
# Trailers (N11): per-worktree config + prepare-commit-msg hook
# --------------------------------------------------------------------------

HOOK_SCRIPT = f"""#!/bin/sh
# {HOOK_MARKER} v1 — managed by Pflanzer Method (tool/cli/worktree.py).
# Adds commit trailers per docs/methodology/07-handoff-do-vyvoje.md
# (AI code provenance): Pflanzer-Variant, Pflanzer-Session, AI-Assisted.
# Values come from `git config --worktree pflanzer.*`; worktrees without
# them (e.g. the cached clone itself) are left untouched.
# Never adds Co-Authored-By — AI is never an author.
msg_file="$1"
case "$2" in merge|squash) exit 0 ;; esac
[ -n "$msg_file" ] && [ -f "$msg_file" ] || exit 0
variant=$(git config --get pflanzer.variant 2>/dev/null) || exit 0
[ -n "$variant" ] || exit 0
session=$(git config --get pflanzer.session 2>/dev/null) || session=1
builder=$(git config --get pflanzer.builder 2>/dev/null) || builder=claude-code
set -- --in-place --if-exists doNothing \\
  --trailer "Pflanzer-Variant: $variant" --trailer "Pflanzer-Session: $session"
if [ "$builder" != "manual" ]; then
  set -- "$@" --trailer "AI-Assisted: $builder"
fi
git interpret-trailers "$@" "$msg_file" || exit 0
if grep -qiE '^co-authored-by:.*(claude|anthropic|copilot|openai|codex|cursor|gpt|gemini)' "$msg_file"; then
  echo "[pflanzer] WARNING: Co-Authored-By trailer za AI — AI není autor; odstraň ho (07-handoff § AI code provenance)." >&2
fi
exit 0
"""

CHAIN_LINE = 'sh "$(git rev-parse --git-common-dir)/hooks/' + HOOK_STANDALONE + '" "$@"'


def _chain_help(hooks_path: str | None, existing: Path | None = None) -> str:
    if hooks_path:
        return (
            f"Repo má core.hooksPath='{hooks_path}' (husky/lefthook) — Pflanzer hook "
            "NEpřepisuji. Zřetězení: husky → do `.husky/prepare-commit-msg` přidej řádek "
            f"`{CHAIN_LINE}`; lefthook → v lefthook.yml `prepare-commit-msg: commands: "
            f"pflanzer-trailers: run: sh \"$(git rev-parse --git-common-dir)/hooks/{HOOK_STANDALONE}\" "
            "{1} {2} {3}`."
        )
    return (
        f"Existující hook {existing} není od Pflanzeru — NEpřepisuji. Zřetězení: na jeho "
        f"konec přidej řádek `{CHAIN_LINE}`."
    )


def _install_trailer_hook(clone: Path) -> dict[str, Any]:
    """Install the trailer hook into the clone's common hooks dir (shared by worktrees)."""
    hooks_dir = _git_common_dir(clone) / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    standalone = hooks_dir / HOOK_STANDALONE
    if not standalone.exists() or standalone.read_text(encoding="utf-8") != HOOK_SCRIPT:
        standalone.write_text(HOOK_SCRIPT, encoding="utf-8")
    standalone.chmod(0o755)

    rc, out, _ = _git(clone, "config", "--get", "core.hooksPath")
    hooks_path = out.strip() if rc == 0 else ""
    if hooks_path:
        return {"status": "chain-needed", "hook": str(standalone), "message": _chain_help(hooks_path)}

    target = hooks_dir / HOOK_NAME
    if target.exists():
        content = target.read_text(encoding="utf-8", errors="replace")
        if HOOK_MARKER not in content:
            return {"status": "chain-needed", "hook": str(standalone),
                    "message": _chain_help(None, target)}
        if content == HOOK_SCRIPT:
            target.chmod(0o755)
            return {"status": "unchanged", "hook": str(target)}
        status = "updated"
    else:
        status = "installed"
    target.write_text(HOOK_SCRIPT, encoding="utf-8")
    target.chmod(0o755)
    return {"status": status, "hook": str(target)}


def _configure_worktree(clone: Path, wt: Path, *, variant: str, builder: str,
                        session: str | None = None) -> None:
    """Per-worktree trailer values (`git config --worktree pflanzer.*`).

    Session is only initialised (to 1) when unset, so re-running setup never
    moves a worktree back from session 2 / ship.
    """
    rc, _, err = _git(clone, "config", "extensions.worktreeConfig", "true")
    if rc != 0:
        raise RuntimeError(f"git config extensions.worktreeConfig failed: {err.strip()}")
    _git(wt, "config", "--worktree", "pflanzer.variant", variant)
    _git(wt, "config", "--worktree", "pflanzer.builder", builder)
    if session:
        _git(wt, "config", "--worktree", "pflanzer.session", session)
    else:
        rc, out, _ = _git(wt, "config", "--worktree", "--get", "pflanzer.session")
        if rc != 0 or not out.strip():
            _git(wt, "config", "--worktree", "pflanzer.session", "1")


def _variant_builders(project_id: int) -> dict[str, str]:
    """name → builder from the latest Session 1 variants (if voting already ran)."""
    with transaction() as conn:
        rows = conn.execute(
            "SELECT v.name, v.builder FROM variants v JOIN sessions s ON s.id = v.session_id "
            "WHERE s.project_id = ? AND s.type = 1 ORDER BY v.id",
            (project_id,),
        ).fetchall()
    return {r[0]: r[1] for r in rows}


# --------------------------------------------------------------------------
# CLAUDE.md (N13) — Pflanzer session rules, idempotent marker block
# --------------------------------------------------------------------------


def render_claude_md(*, slug: str | None, variant: str | None = None,
                     branch: str | None = None, workspace: str | None = None) -> str:
    """Render the full CLAUDE.md template. slug=None → generic (for init-pr)."""
    tpl = CLAUDE_MD_TEMPLATE.read_text(encoding="utf-8")
    if slug and variant:
        line = f"Tento worktree: varianta **`{variant}`**, branch `{branch}`."
    else:
        line = ("Aktuální variantu worktree zjistíš přes "
                "`git config --worktree pflanzer.variant` (zapisuje `worktree.py setup`).")
    if workspace:
        line += (f" Monorepo workspace: **`{workspace}`** — pracuj v `{workspace}/`, "
                 "mimo něj jen po domluvě s týmem.")
    return tpl.replace("{{session_line}}", line).replace("{{slug}}", slug or "<slug>")


def _pflanzer_block(full: str) -> str:
    start = full.index(PFLANZER_START)
    end = full.index(PFLANZER_END) + len(PFLANZER_END)
    return full[start:end]


def upsert_claude_md(path: Path, rendered_full: str) -> str:
    """Create CLAUDE.md or insert/replace the marker block. Returns created|appended|updated|unchanged."""
    block = _pflanzer_block(rendered_full)
    if not path.exists():
        path.write_text(rendered_full, encoding="utf-8")
        return "created"
    current = path.read_text(encoding="utf-8")
    if PFLANZER_START in current and PFLANZER_END in current:
        s = current.index(PFLANZER_START)
        e = current.index(PFLANZER_END) + len(PFLANZER_END)
        new = current[:s] + block + current[e:]
        if new == current:
            return "unchanged"
        path.write_text(new, encoding="utf-8")
        return "updated"
    sep = "" if current.endswith("\n\n") else ("\n" if current.endswith("\n") else "\n\n")
    path.write_text(current + sep + f"> {BRAND_LINE}\n\n" + block + "\n", encoding="utf-8")
    return "appended"


def _exclude_locally(clone: Path, pattern: str) -> None:
    """Add a pattern to the shared `info/exclude` (never committed)."""
    excl = _git_common_dir(clone) / "info" / "exclude"
    excl.parent.mkdir(parents=True, exist_ok=True)
    raw = excl.read_text(encoding="utf-8") if excl.exists() else ""
    if pattern not in raw.splitlines():
        prefix = "\n" if raw and not raw.endswith("\n") else ""
        with excl.open("a", encoding="utf-8") as fh:
            fh.write(f"{prefix}{pattern}\n")


def _write_worktree_claude_md(clone: Path, wt: Path, *, slug: str, variant: str,
                              workspace: str | None) -> str:
    """Write CLAUDE.md into a variant worktree without polluting the variant diff.

    New file → excluded via info/exclude; tracked file → `skip-worktree` so the
    appended section never shows in `git status`. The durable version goes to
    the target repo through `init-pr` (N14).
    """
    path = wt / "CLAUDE.md"
    tracked = _git(wt, "ls-files", "--error-unmatch", "CLAUDE.md")[0] == 0
    status = upsert_claude_md(path, render_claude_md(
        slug=slug, variant=variant_label(slug, variant),
        branch=f"pflanzer/{slug}-{variant}", workspace=workspace))
    if tracked:
        _git(wt, "update-index", "--skip-worktree", "CLAUDE.md")
    else:
        _exclude_locally(clone, "/CLAUDE.md")
    return status


# --------------------------------------------------------------------------
# Data leakage guard (N13)
# --------------------------------------------------------------------------

SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("aws-access-key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("private-key", re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP |ENCRYPTED )?PRIVATE KEY")),
    ("api-key-sk", re.compile(r"\bsk-(?:ant-|proj-)?[A-Za-z0-9_-]{20,}|\bsk_(?:live|test)_[A-Za-z0-9]{16,}")),
    ("github-token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36}\b|\bgithub_pat_[A-Za-z0-9_]{40,}")),
    ("password-assignment", re.compile(
        r"(?i)\bpass(?:word|wd)\s*=\s*['\"]?(?!process\.env|os\.environ|getenv|\$\{|<|\*{3})[^\s'\"<>{}();,]{4,}")),
]
SCAN_SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build",
                  ".next", "target", "vendor", "coverage", "playwright-report", "test-results",
                  ".gradle", ".idea", ".vscode"}
BINARY_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip", ".gz", ".tgz",
              ".jar", ".war", ".class", ".so", ".dll", ".exe", ".woff", ".woff2", ".ttf", ".otf",
              ".mp4", ".mov", ".webm", ".lock", ".bin", ".pyc"}
DUMP_LIMITS = {".sql": 1 * 1024 * 1024, ".csv": 5 * 1024 * 1024}
ENV_ALLOWED_SUFFIXES = (".example", ".sample", ".template", ".dist", ".defaults")
GITIGNORE_BLOCK = (
    "\n# Pflanzer session guard: env files never go to git or to AI prompts\n"
    ".env\n.env.*\n!.env.example\n"
)
MAX_SCAN_BYTES = 1024 * 1024


def _is_fixture_path(rel: str) -> bool:
    return any(seg in f"/{rel}" for seg in ("/test/fixtures/", "/tests/fixtures/", "/__fixtures__/"))


def _gitleaks_scan(wt: Path) -> dict[str, Any] | None:
    if not shutil.which("gitleaks"):
        return None
    with tempfile.TemporaryDirectory() as td:
        report = Path(td) / "gitleaks.json"
        rc, out, err = _run(
            ["gitleaks", "detect", "--no-git", "-s", str(wt), "--no-banner", "--exit-code", "0",
             "--report-format", "json", "--report-path", str(report)], timeout=600,
        )
        if rc != 0 or not report.exists():
            return None
        try:
            leaks = json.loads(report.read_text(encoding="utf-8") or "[]") or []
        except json.JSONDecodeError:
            return None
    hits = []
    for lk in leaks:
        f = str(lk.get("File", ""))
        try:
            f = str(Path(f).resolve().relative_to(wt.resolve()))
        except ValueError:
            pass
        if f.split("/")[0] in SCAN_SKIP_DIRS:
            continue
        hits.append(f"{f}:{lk.get('StartLine', '?')} {lk.get('RuleID', '')}")
    return {"engine": "gitleaks", "hits": hits}


def _walk_files(wt: Path):
    for root, dirs, files in os.walk(wt):
        dirs[:] = [d for d in dirs if d not in SCAN_SKIP_DIRS]
        for name in files:
            p = Path(root) / name
            yield p, p.relative_to(wt).as_posix()


def _regex_scan(wt: Path) -> dict[str, Any]:
    hits: list[str] = []
    for p, rel in _walk_files(wt):
        if p.suffix.lower() in BINARY_EXT or p.is_symlink():
            continue
        try:
            if p.stat().st_size > MAX_SCAN_BYTES:
                continue
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for name, rx in SECRET_PATTERNS:
                if rx.search(line):
                    hits.append(f"{rel}:{lineno} {name}")
    return {"engine": "regex", "hits": hits}


def check_env_files(wt: Path, *, fix_gitignore: bool = True) -> list[dict[str, str]]:
    """`.env*` must not be tracked and must be ignored; optionally fix .gitignore."""
    rows: list[dict[str, str]] = []
    rc, out, _ = _git(wt, "ls-files", "--", ".env*", "*/.env*")
    tracked = [f for f in out.splitlines() if f and not f.endswith(ENV_ALLOWED_SUFFIXES)]
    rows.append({
        "check": ".env* trackované",
        "status": "FAIL" if tracked else "OK",
        "detail": (f"trackované: {', '.join(tracked[:5])} — `git rm --cached` + rotace secrets"
                   if tracked else "žádný .env* soubor v gitu"),
    })
    not_ignored = [n for n in (".env", ".env.local")
                   if _git(wt, "check-ignore", "-q", "--no-index", n)[0] != 0]
    if not not_ignored:
        rows.append({"check": ".env* v .gitignore", "status": "OK", "detail": ".env i .env.local ignorované"})
        return rows
    detail = f"{', '.join(not_ignored)} nejsou v .gitignore"
    if fix_gitignore:
        gi = wt / ".gitignore"
        existing = gi.read_text(encoding="utf-8") if gi.exists() else ""
        if "Pflanzer session guard" not in existing:
            new = (existing.rstrip("\n") + "\n" + GITIGNORE_BLOCK) if existing.strip() else GITIGNORE_BLOCK.lstrip("\n")
            gi.write_text(new, encoding="utf-8")
        detail += " → přidáno do .gitignore (commitni, ideálně v `init-pr`)"
    rows.append({"check": ".env* v .gitignore", "status": "WARN", "detail": detail})
    return rows


def guard_worktree(wt: Path, *, fix_gitignore: bool = True) -> list[dict[str, str]]:
    """Pre-session data leakage checks for one worktree. Returns finding rows."""
    rows: list[dict[str, str]] = []

    # (a) secrets
    scan = _gitleaks_scan(wt) or _regex_scan(wt)
    hits = scan["hits"]
    rows.append({
        "check": f"secrets ({scan['engine']})",
        "status": "FAIL" if hits else "OK",
        "detail": (f"{len(hits)} nález(ů): " + "; ".join(hits[:5]) + (" …" if len(hits) > 5 else ""))
                  if hits else "žádné secret patterny",
    })

    # (b) .env* tracked + ignored
    rows += check_env_files(wt, fix_gitignore=fix_gitignore)

    # (c) prod-looking data dumps
    dumps: list[str] = []
    for p, rel in _walk_files(wt):
        limit = DUMP_LIMITS.get(p.suffix.lower())
        if limit is None or _is_fixture_path(rel):
            continue
        try:
            size = p.stat().st_size
        except OSError:
            continue
        if size > limit:
            dumps.append(f"{rel} ({size / 1024 / 1024:.1f} MB)")
    rows.append({
        "check": "data dumpy (*.sql > 1 MB, *.csv > 5 MB)",
        "status": "WARN" if dumps else "OK",
        "detail": ("vypadá jako prod data: " + "; ".join(dumps[:5]) + " — ověř, že jsou syntetická"
                   if dumps else "žádné velké dumpy mimo test/fixtures"),
    })
    return rows


def _existing_worktrees(slug: str, repos: list[TargetRepo]) -> list[tuple[TargetRepo, str, Path]]:
    out = []
    for variant in PARALLEL_VARIANTS + MOB_VARIANTS:
        for repo, path in variant_worktrees(slug, repos, variant):
            if path.is_dir():
                out.append((repo, variant, path))
    return out


def guard(slug: str, *, fix_gitignore: bool = True) -> list[dict[str, str]]:
    repos = load_target_repos(slug)
    rows: list[dict[str, str]] = []
    wts = _existing_worktrees(slug, repos)
    if not wts:
        raise ValueError(f"Žádné worktrees pro '{slug}' — spusť `python tool/cli/worktree.py setup --slug {slug}`.")
    for repo, variant, path in wts:
        for r in guard_worktree(path, fix_gitignore=fix_gitignore):
            rows.append({"repo": repo.role, "variant": variant, **r})
    return rows


# --------------------------------------------------------------------------
# init-pr (N14) helpers — autodetected INTEGRATION_GUIDE hints
# --------------------------------------------------------------------------

LIB_HINTS: dict[str, str] = {
    # JS/TS
    "react": "UI", "next": "UI", "vue": "UI", "nuxt": "UI", "@angular/core": "UI",
    "svelte": "UI", "@sveltejs/kit": "UI", "vite": "Build",
    "@tanstack/react-query": "Server state", "react-query": "Server state", "swr": "Server state",
    "@reduxjs/toolkit": "Global state", "redux": "Global state", "zustand": "Global state",
    "jotai": "Global state", "mobx": "Global state",
    "react-hook-form": "Formuláře", "formik": "Formuláře", "zod": "Validace", "yup": "Validace",
    "axios": "HTTP / API client", "@trpc/client": "HTTP / API client", "ky": "HTTP / API client",
    "openapi-typescript": "Generated SDK", "@openapitools/openapi-generator-cli": "Generated SDK",
    "orval": "Generated SDK",
    "next-auth": "Auth", "@auth0/auth0-react": "Auth", "@auth0/nextjs-auth0": "Auth",
    "aws-amplify": "Auth", "keycloak-js": "Auth", "@azure/msal-browser": "Auth",
    "tailwindcss": "Styling", "styled-components": "Styling", "@emotion/react": "Styling",
    "@mui/material": "Design system", "@chakra-ui/react": "Design system", "antd": "Design system",
    "launchdarkly-react-client-sdk": "Feature flags", "@unleash/proxy-client-react": "Feature flags",
    "vitest": "Test runner", "jest": "Test runner", "@testing-library/react": "Testy UI",
    "msw": "API mocking", "@playwright/test": "E2E", "cypress": "E2E",
    "pino": "Logger", "winston": "Logger", "@sentry/react": "Observability",
    "@opentelemetry/api": "Observability",
    "prisma": "ORM", "@prisma/client": "ORM", "drizzle-orm": "ORM", "typeorm": "ORM",
    "express": "BE framework", "@nestjs/core": "BE framework", "fastify": "BE framework",
    # Python
    "fastapi": "BE framework", "django": "BE framework", "flask": "BE framework",
    "sqlalchemy": "ORM", "sqlmodel": "ORM", "alembic": "Migrace", "pydantic": "Validace",
    "pytest": "Test runner", "structlog": "Logger",
    # JVM
    "spring-boot-starter-web": "BE framework", "spring-boot-starter-security": "Auth",
    "spring-boot-starter-data-jpa": "ORM", "hibernate-core": "ORM", "flyway-core": "Migrace",
    "liquibase-core": "Migrace", "junit-jupiter": "Test runner", "mockito-core": "Test mocking",
    "springdoc-openapi-starter-webmvc-ui": "OpenAPI",
}


def _read_text(repo: Path, rel: str) -> str | None:
    p = repo / rel
    try:
        return p.read_text(encoding="utf-8", errors="ignore") if p.is_file() else None
    except OSError:
        return None


def detect_stack(repo: Path, workspace: str | None = None) -> dict[str, Any]:
    """Cheap lib-name autodetection from package.json / pyproject / pom / gradle / go.mod / csproj."""
    found: dict[str, list[str]] = {}
    manifests: list[str] = []

    def add(name: str, dep: str) -> None:
        cat = LIB_HINTS.get(dep)
        if cat and dep not in found.setdefault(cat, []):
            found[cat].append(dep)

    roots = [""] + ([workspace] if workspace else [])
    for base in roots:
        pre = f"{base}/" if base else ""
        pkg = _read_text(repo, f"{pre}package.json")
        if pkg:
            manifests.append(f"{pre}package.json")
            try:
                data = json.loads(pkg)
                for key in ("dependencies", "devDependencies", "peerDependencies"):
                    for dep in (data.get(key) or {}):
                        add("js", dep)
                if data.get("workspaces"):
                    found.setdefault("Monorepo", []).append("npm/yarn workspaces")
            except json.JSONDecodeError:
                pass
        for pyfile in (f"{pre}pyproject.toml", f"{pre}requirements.txt"):
            txt = _read_text(repo, pyfile)
            if txt:
                manifests.append(pyfile)
                for dep in re.findall(r"(?im)^[\s\"']*([A-Za-z][\w.-]*)\s*(?:[<>=~!\[;\"',]|$)", txt):
                    add("py", dep.lower())
        for jvm in (f"{pre}pom.xml", f"{pre}build.gradle", f"{pre}build.gradle.kts"):
            txt = _read_text(repo, jvm)
            if txt:
                manifests.append(jvm)
                for dep in set(re.findall(r"<artifactId>([^<]+)</artifactId>", txt)
                               + re.findall(r"[\"'][\w.-]+:([\w.-]+)(?::[^\"']*)?[\"']", txt)):
                    add("jvm", dep)
        gomod = _read_text(repo, f"{pre}go.mod")
        if gomod:
            manifests.append(f"{pre}go.mod")
            mod = re.search(r"(?m)^module\s+(\S+)", gomod)
            found.setdefault("Go module", []).append(mod.group(1) if mod else "?")
    for marker, label in (("pnpm-workspace.yaml", "pnpm workspaces"), ("nx.json", "Nx"),
                          ("turbo.json", "Turborepo"), ("lerna.json", "Lerna")):
        if (repo / marker).exists():
            found.setdefault("Monorepo", []).append(label)
    csproj = [p for p in repo.glob("**/*.csproj") if "node_modules" not in p.parts][:3]
    for p in csproj:
        manifests.append(p.relative_to(repo).as_posix())
        pkgs = re.findall(r'PackageReference\s+Include="([^"]+)"',
                          p.read_text(encoding="utf-8", errors="ignore"))
        if pkgs:
            found.setdefault(".NET packages", []).extend(pkgs[:8])
    pm = _detect_package_manager(repo / workspace if workspace and (repo / workspace / "package.json").exists() else repo)
    return {"manifests": manifests, "package_manager": pm, "libs": found}


def render_integration_guide(repo: Path, *, workspace: str | None, repo_role: str) -> str:
    tpl = INTEGRATION_GUIDE_TEMPLATE.read_text(encoding="utf-8")
    stack = detect_stack(repo, workspace)
    lines = [f"> {BRAND_LINE}", ""]
    lines.append(tpl.split("\n", 1)[0])  # title line
    lines += ["", "## Autodetekce (Pflanzer `init-pr`, " + date.today().isoformat() + ")", "",
              "> Předvyplněno z manifestů — jen názvy knihoven. Ověř a doplň konkrétní",
              "> patterns v sekcích níže (placeholdery `<…>`), pak smaž, co neplatí.", ""]
    lines.append(f"- Repo role: `{repo_role}`")
    if workspace:
        lines.append(f"- **Monorepo workspace pro Pflanzer varianty: `{workspace}`** — "
                     f"kód variant patří do `{workspace}/`.")
    if stack["manifests"]:
        lines.append("- Manifesty: " + ", ".join(f"`{m}`" for m in stack["manifests"]))
    if stack["package_manager"]:
        lines.append(f"- Package manager: `{stack['package_manager']}`")
    for cat, libs in sorted(stack["libs"].items()):
        lines.append(f"- {cat}: " + ", ".join(f"`{x}`" for x in libs))
    if not stack["libs"]:
        lines.append("- _(žádné známé knihovny nedetekovány — vyplň ručně)_")
    rest = tpl.split("\n", 1)[1] if "\n" in tpl else ""
    return "\n".join(lines) + "\n" + rest


def _init_missing(clone: Path, base_ref: str) -> list[str]:
    """Which AI-readiness files the base branch lacks (N14)."""
    missing = []
    has_guide = any(_git(clone, "cat-file", "-e", f"{base_ref}:{p}")[0] == 0
                    for p in ("docs/INTEGRATION_GUIDE.md", "INTEGRATION_GUIDE.md"))
    if not has_guide:
        missing.append("docs/INTEGRATION_GUIDE.md")
    rc, out, _ = _git(clone, "show", f"{base_ref}:CLAUDE.md")
    if rc != 0 or PFLANZER_START not in out:
        missing.append("CLAUDE.md (Pflanzer sekce)")
    return missing


# --------------------------------------------------------------------------
# setup
# --------------------------------------------------------------------------


def setup(slug: str, *, install_deps: bool = True, mode: str | None = None,
          run_guard: bool = True, fix_gitignore: bool = True) -> WorktreeSetup:
    """Setup worktrees for in-room session pro `slug` projekt.

    Args:
        slug: project slug.
        install_deps: auto npm/pnpm/yarn install per worktree (JS repa).
        mode: 'parallel' (A/B/C) | 'mob' (1 worktree); None → projects.session_mode.
        run_guard: data leakage guard per worktree (N13).
    """
    proj = load_project(slug)
    mode = mode or proj.get("session_mode") or "parallel"
    if mode not in ("parallel", "mob"):
        raise ValueError(f"mode must be 'parallel' or 'mob', got '{mode}'")
    repos = load_target_repos(slug, proj)
    if not repos:
        raise ValueError(
            f"Project '{slug}' has no target_repo_url / target_repos set. "
            "Mandatory pro pilot/production profil — re-run /pflanzer wizard "
            "(KROK 3: Target repo(s)) nebo nastav `projects.target_repos`."
        )

    builders = _variant_builders(int(proj["id"]))
    variants = PARALLEL_VARIANTS if mode == "parallel" else MOB_VARIANTS
    repo_results: list[dict[str, Any]] = []
    guard_rows: list[dict[str, str]] = []
    init_missing: list[dict[str, Any]] = []

    for i, repo in enumerate(repos):
        primary = i == 0
        print(f"[setup] {repo.role}: {repo.url} (base {repo.branch}"
              f"{', workspace ' + repo.workspace if repo.workspace else ''})", file=sys.stderr)
        clone = _ensure_target_clone(repo.url, repo.branch)
        wts = _create_worktrees(clone, slug, repo.branch, mode=mode, repo=repo, primary=primary)
        claude_md: dict[str, str] = {}
        for variant, wt in zip(variants, wts):
            builder = builders.get(variant) or (next(iter(builders.values()), None)
                                                if mode == "mob" else None) or DEFAULT_BUILDER
            _configure_worktree(clone, wt, variant=variant_label(slug, variant), builder=builder)
            if run_guard:
                for r in guard_worktree(wt, fix_gitignore=fix_gitignore):
                    guard_rows.append({"repo": repo.role, "variant": variant, **r})
            claude_md[variant] = _write_worktree_claude_md(
                clone, wt, slug=slug, variant=variant, workspace=repo.workspace)

        pm = _detect_package_manager(clone)
        install_results: list[dict[str, Any]] = []
        if install_deps:
            install_results = _install_deps(wts, pm)
        hook = _install_trailer_hook(clone)  # after install: husky may set core.hooksPath
        missing = _init_missing(clone, _resolve_base_ref(clone, repo.branch))
        if missing:
            init_missing.append({"repo": repo.role, "missing": missing})
        repo_results.append({
            **repo.to_dict(), "primary": primary, "clone_path": str(clone),
            "worktrees": {v: str(w) for v, w in zip(variants, wts)},
            "package_manager": pm, "install_results": install_results,
            "hook": hook, "claude_md": claude_md,
        })

    primary_res = repo_results[0]
    with transaction() as conn:
        audit(
            conn, action="worktree.setup", target_type="project", target_id=int(proj["id"]),
            payload={
                "slug": slug, "mode": mode,
                "target_repo_url": repos[0].url, "target_branch": repos[0].branch,
                "repos": [{"role": r["role"], "url": r["url"], "worktrees": r["worktrees"],
                           "hook": r["hook"]["status"]} for r in repo_results],
                "package_manager": primary_res["package_manager"],
                "install_ok": sum(1 for r in repo_results for x in r["install_results"]
                                  if x["status"] in ("ok", "cached")),
                "guard_findings": sum(1 for g in guard_rows if g["status"] != "OK"),
            },
        )

    return WorktreeSetup(
        slug=slug, target_repo_url=repos[0].url, target_branch=repos[0].branch,
        target_clone_path=Path(primary_res["clone_path"]),
        worktrees=[Path(p) for p in primary_res["worktrees"].values()],
        package_manager=primary_res["package_manager"],
        install_results=primary_res["install_results"],
        mode=mode, repos=repo_results, guard=guard_rows, init_missing=init_missing,
    )


# --------------------------------------------------------------------------
# init-pr (N14)
# --------------------------------------------------------------------------


def init_pr(slug: str) -> list[dict[str, Any]]:
    """First PR of the pilot: INTEGRATION_GUIDE + CLAUDE.md into the target repo(s)."""
    proj = load_project(slug)
    repos = load_target_repos(slug, proj)
    if not repos:
        raise ValueError(f"Project '{slug}' nemá target repo.")
    results = []
    for i, repo in enumerate(repos):
        clone = _ensure_target_clone(repo.url, repo.branch)
        base_ref = _resolve_base_ref(clone, repo.branch)
        missing = _init_missing(clone, base_ref)
        branch = f"pflanzer/{slug}-init"
        res: dict[str, Any] = {"repo": repo.role, "url": repo.url, "missing": missing}
        if not missing:
            res["status"] = "nothing-to-do"
            results.append(res)
            continue
        wt = worktree_dir(slug, "init", repo, i == 0)
        _git(clone, "worktree", "prune")
        _add_worktree(clone, wt, branch, base_ref)
        _configure_worktree(clone, wt, variant=f"{slug}-init", builder="manual", session="1")

        changed: list[str] = []
        guide = wt / "docs" / "INTEGRATION_GUIDE.md"
        if not guide.exists() and not (wt / "INTEGRATION_GUIDE.md").exists():
            guide.parent.mkdir(parents=True, exist_ok=True)
            guide.write_text(render_integration_guide(wt, workspace=repo.workspace, repo_role=repo.role),
                             encoding="utf-8")
            changed.append("docs/INTEGRATION_GUIDE.md")
        if upsert_claude_md(wt / "CLAUDE.md", render_claude_md(slug=None, workspace=repo.workspace)) != "unchanged":
            changed.append("CLAUDE.md")
        env_rows = [r for r in check_env_files(wt, fix_gitignore=True) if r["check"] == ".env* v .gitignore"]
        if env_rows and env_rows[0]["status"] != "OK":
            changed.append(".gitignore")

        if changed:
            _git(wt, "add", "-f", "--", *changed)
            msg = (
                f"docs({slug}): add AI-readiness context (INTEGRATION_GUIDE + CLAUDE.md)\n\n"
                "First PR of the Pflanzer pilot: repo context for AI builders so the next\n"
                "pilot on this repo starts from a ready baseline.\n\n"
                f"Pflanzer-Variant: {slug}-init\nPflanzer-Session: 1\n"
            )
            rc, out, err = _git(wt, "commit", "-m", msg)
            if rc != 0:
                raise RuntimeError(
                    f"git commit v {wt} selhal: {(err or out).strip()} — "
                    "zkontroluj `git config user.name` / `user.email` (autor = dev u klávesnice)."
                )
            res["status"] = "committed"
        else:
            res["status"] = "already-on-branch"
        res["changed"] = changed

        body_dir = INIT_PR_DIR / slug
        body_dir.mkdir(parents=True, exist_ok=True)
        body = body_dir / f"{repo.role}-pr-body.md"
        body.write_text(
            f"> {BRAND_LINE}\n\n"
            f"## AI-readiness: INTEGRATION_GUIDE + CLAUDE.md\n\n"
            f"První PR Pflanzer pilotu `{slug}` — trvalý kontext pro AI buildery v tomto repu.\n"
            "Druhý pilot na stejném repu startuje z hotového kontextu.\n\n"
            "- `docs/INTEGRATION_GUIDE.md` — předvyplněno autodetekcí manifestů; "
            "**reviewer doplní placeholdery `<…>`** (auth, API client, logger, flags).\n"
            "- `CLAUDE.md` — sekce „Pflanzer session rules“ (žádná prod data, `.env*` mimo prompt, "
            "trailery, branch naming).\n"
            + ("- `.gitignore` — `.env*` patterny (data leakage guard).\n" if ".gitignore" in changed else "")
            + "\nKód neobsahuje žádnou logiku; merge nemá runtime dopad.\n",
            encoding="utf-8",
        )
        res.update({
            "worktree": str(wt), "branch": branch, "pr_body": str(body),
            "commands": [
                f"git -C {wt} push -u origin {branch}",
                f"cd {wt} && gh pr create --base {repo.branch} --head {branch} "
                f"--title \"[Pflanzer] {slug}: AI-readiness (INTEGRATION_GUIDE + CLAUDE.md)\" "
                f"--label pflanzer --label \"pflanzer:{slug}\" --body-file {body}",
            ],
        })
        results.append(res)

    with transaction() as conn:
        audit(conn, action="worktree.init_pr", target_type="project", target_id=int(proj["id"]),
              payload={"slug": slug, "results": [{k: r.get(k) for k in ("repo", "status", "missing")}
                                                  for r in results]})
    return results


# --------------------------------------------------------------------------
# set-session / set-url
# --------------------------------------------------------------------------


def set_session(slug: str, session: str, variant: str | None = None) -> list[dict[str, str]]:
    if session not in SESSION_VALUES:
        raise ValueError(f"session musí být jedna z {SESSION_VALUES}, ne '{session}'.")
    repos = load_target_repos(slug)
    out = []
    for repo, v, path in _existing_worktrees(slug, repos):
        if variant and v != variant:
            continue
        rc, _, err = _git(path, "config", "--worktree", "pflanzer.session", session)
        out.append({"repo": repo.role, "variant": v, "path": str(path),
                    "status": "ok" if rc == 0 else f"failed: {err.strip()}"})
    if not out:
        raise ValueError(f"Žádné worktrees pro '{slug}'" + (f" / variantu {variant}" if variant else "") + ".")
    return out


def set_prototype_url(slug: str, variant: str, url: str) -> bool:
    """Write variants.prototype_url for the latest Session 1 row. False = no row yet."""
    with transaction() as conn:
        row = conn.execute(
            "SELECT v.id FROM variants v JOIN sessions s ON s.id = v.session_id "
            "JOIN projects p ON p.id = s.project_id "
            "WHERE p.slug = ? AND s.type = 1 AND v.name = ? ORDER BY v.id DESC LIMIT 1",
            (slug, variant),
        ).fetchone()
        if not row:
            return False
        conn.execute("UPDATE variants SET prototype_url = ? WHERE id = ?", (url, int(row[0])))
        audit(conn, action="variant.prototype_url", target_type="variant", target_id=int(row[0]),
              payload={"slug": slug, "variant": variant, "url": url})
    return True


# --------------------------------------------------------------------------
# preview (N9)
# --------------------------------------------------------------------------


def detect_preview_env(repo: Path) -> list[str]:
    hits = [f for f in ("vercel.json", "netlify.toml") if (repo / f).exists()]
    wf = repo / ".github" / "workflows"
    if wf.is_dir():
        hits += [f".github/workflows/{p.name}" for p in sorted(wf.iterdir())
                 if "preview" in p.name.lower() and p.suffix in (".yml", ".yaml")]
    return hits


def _commits_ahead(wt: Path, base: str) -> int:
    rc, out, _ = _git(wt, "rev-list", "--count", f"{base}..HEAD")
    return int(out.strip()) if rc == 0 and out.strip().isdigit() else 0


def _variants_for_mode(slug: str, repos: list[TargetRepo]) -> list[str]:
    present = {v for _, v, _ in _existing_worktrees(slug, repos)}
    return [v for v in PARALLEL_VARIANTS + MOB_VARIANTS if v in present]


def preview_draft_pr(slug: str, *, run: bool = False) -> list[dict[str, Any]]:
    repos = load_target_repos(slug)
    builders = _variant_builders(int(load_project(slug)["id"]))
    results = []
    for variant in _variants_for_mode(slug, repos):
        for idx, (repo, wt) in enumerate(variant_worktrees(slug, repos, variant)):
            if not wt.is_dir():
                continue
            branch = f"pflanzer/{slug}-{variant}"
            base_ref = _resolve_base_ref(wt, repo.branch)
            ahead = _commits_ahead(wt, base_ref)
            builder = builders.get(variant) or DEFAULT_BUILDER
            envs = detect_preview_env(wt)
            body_dir = PREVIEWS_DIR / slug / variant
            body_dir.mkdir(parents=True, exist_ok=True)
            body = body_dir / f"pr-body-{repo.role}.md"
            body.write_text(
                f"> {BRAND_LINE}\n\n"
                f"## Pflanzer preview — `{slug}` varianta {variant} ({repo.role})\n\n"
                "Draft PR jen pro **preview mezi sessions** (non-tech stakeholdeři hodnotí ve "
                "web hubu). Nemergovat — winner jde do prod přes Ship gate (`handoff_pr.py`).\n\n"
                "## AI provenance\n"
                f"- **Builder**: {builder}\n"
                "- **Model family**: " + ("Claude" if builder == "claude-code" else builder) + "\n"
                f"- **Varianta**: {variant} (branch `{branch}`)\n"
                "- **U klávesnice**: <jméno> (git author commitů)\n"
                f"- **Decision log**: `data/sessions/{slug}/_summary.md`\n",
                encoding="utf-8",
            )
            title = f"[Pflanzer] {slug} variant {variant}" + ("" if idx == 0 else f" ({repo.role})")
            labels = ["pflanzer", f"pflanzer:{slug}"] + (["ai-generated"] if builder != "manual" else [])
            label_args = " ".join(f"--label \"{lb}\"" for lb in labels)
            push_cmd = ["git", "-C", str(wt), "push", "-u", "origin", branch]
            pr_cmd = ["gh", "pr", "create", "--draft", "--base", repo.branch, "--head", branch,
                      "--title", title, "--body-file", str(body)]
            for lb in labels:
                pr_cmd += ["--label", lb]
            res: dict[str, Any] = {
                "repo": repo.role, "variant": variant, "branch": branch, "worktree": str(wt),
                "commits_ahead": ahead, "preview_env": envs,
                "commands": [
                    " ".join(push_cmd),
                    f"cd {wt} && gh pr create --draft --base {repo.branch} --head {branch} "
                    f"--title \"{title}\" {label_args} --body-file {body}",
                ],
                "note": (f"Preview env detekováno ({', '.join(envs)}) — preview URL se objeví v PR checks."
                         if envs else "Preview env nedetekováno — PR ukáže jen diff; "
                                      "zvaž `--mode playwright` pro stakeholdery."),
            }
            if ahead == 0:
                res["warning"] = "Varianta nemá žádné commity nad base — PR by byl prázdný."
            if run:
                if ahead == 0:
                    res["status"] = "skipped (no commits)"
                    results.append(res)
                    continue
                rc, out, err = _run(push_cmd, timeout=300)
                if rc != 0:
                    res["status"] = f"push failed: {err.strip()[-200:]}"
                    results.append(res)
                    continue
                for lb in labels:  # gh pr create fails on unknown labels
                    _run(["gh", "label", "create", lb, "--force"], cwd=wt, timeout=60)
                rc, out, err = _run(pr_cmd, cwd=wt, timeout=120)
                if rc != 0:
                    res["status"] = f"gh pr create failed: {(err or out).strip()[-300:]}"
                    results.append(res)
                    continue
                pr_url = next((ln for ln in reversed(out.splitlines()) if ln.startswith("http")), out.strip())
                res["pr_url"] = pr_url
                if idx == 0:
                    stored = set_prototype_url(slug, variant, pr_url)
                    res["prototype_url_stored"] = stored
                    if not stored:
                        res["how_to_store"] = (
                            f"Varianta {variant} ještě není v DB (voting neproběhl) — ve vote specu "
                            f"předej `real_urls: {{\"{variant}\": \"{pr_url}\"}}`, nebo po votingu "
                            f"`python tool/cli/worktree.py set-url --slug {slug} --variant {variant} --url {pr_url}`."
                        )
                res["status"] = "created"
            else:
                res["status"] = "dry-run"
                if idx == 0:
                    res["how_to_store"] = (
                        f"Po vytvoření PR: `python tool/cli/worktree.py set-url --slug {slug} "
                        f"--variant {variant} --url <PR URL>` (nebo `real_urls` ve vote specu)."
                    )
            results.append(res)
    return results


PLAYWRIGHT_WRAPPER = """// Generated by Pflanzer Method (worktree.py preview) — local only, not committed.
import {{ defineConfig }} from '@playwright/test';
{base_import}
export default defineConfig({base_arg}{{
  testDir: './{test_dir}',
  use: {{ video: 'on', trace: 'on', screenshot: 'on' }},
}});
"""


def _has_playwright(project_dir: Path) -> bool:
    try:
        data = json.loads((project_dir / "package.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return any("@playwright/test" in (data.get(k) or {}) for k in ("dependencies", "devDependencies"))


def preview_playwright(slug: str) -> list[dict[str, Any]]:
    """Record acceptance runs (html report + trace + video) per variant for stakeholders."""
    repos = load_target_repos(slug)
    primary = repos[0]
    results = []
    for variant in _variants_for_mode(slug, repos):
        wt = worktree_dir(slug, variant, primary, True)
        project_dir = wt / primary.workspace if primary.workspace and (wt / primary.workspace / "package.json").exists() else wt
        spec = project_dir / "tests" / "acceptance" / f"{slug}.spec.ts"
        res: dict[str, Any] = {"variant": variant, "project_dir": str(project_dir)}
        missing = []
        if not _has_playwright(project_dir):
            missing.append("`@playwright/test` v package.json (devDependencies)")
        elif not (project_dir / "node_modules" / "@playwright" / "test").exists():
            missing.append("nainstalované závislosti (`npm ci` / setup bez `--no-install`)")
        if not spec.exists():
            missing.append(f"`tests/acceptance/{slug}.spec.ts` (Playwright převod scénářů z `.feature`)")
        if missing:
            res.update({"status": "missing", "missing": missing,
                        "hint": "Browsery instaluje tým (`npx playwright install chromium`) — Pflanzer je neinstaluje."})
            results.append(res)
            continue
        dest = PREVIEWS_DIR / slug / variant
        if dest.exists():
            shutil.rmtree(dest / "report", ignore_errors=True)
            shutil.rmtree(dest / "test-results", ignore_errors=True)
        dest.mkdir(parents=True, exist_ok=True)
        base_cfg = next((c for c in ("playwright.config.ts", "playwright.config.js", "playwright.config.mjs")
                         if (project_dir / c).exists()), None)
        wrapper = project_dir / "pflanzer.preview.config.ts"
        wrapper.write_text(PLAYWRIGHT_WRAPPER.format(
            base_import=f"import base from './{Path(base_cfg).stem}';" if base_cfg else "",
            base_arg="base, " if base_cfg else "", test_dir="tests/acceptance",
        ), encoding="utf-8")
        _exclude_locally(wt, "pflanzer.preview.config.ts")
        cmd = ["npx", "--no-install", "playwright", "test", f"tests/acceptance/{slug}.spec.ts",
               "--config", wrapper.name, "--reporter=html", "--trace", "on",
               "--output", str(dest / "test-results")]
        env = {"PLAYWRIGHT_HTML_OPEN": "never", "PW_TEST_HTML_REPORT_OPEN": "never",
               "PLAYWRIGHT_HTML_OUTPUT_DIR": str(dest / "report"),
               "PLAYWRIGHT_HTML_REPORT": str(dest / "report")}
        rc, out, err = _run(cmd, cwd=project_dir, timeout=1200, env=env)
        local_report = project_dir / "playwright-report"
        if not (dest / "report").exists() and local_report.exists():
            shutil.copytree(local_report, dest / "report", dirs_exist_ok=True)
        res.update({
            "status": "passed" if rc == 0 else "failed",
            "command": " ".join(cmd), "report": str(dest / "report" / "index.html"),
            "artifacts": str(dest / "test-results"),
            "tail": (out + err)[-400:],
        })
        results.append(res)
    return results


# --------------------------------------------------------------------------
# verify (pre-flight, ADR-0009)
# --------------------------------------------------------------------------


def verify_cwd_in_target(slug: str, cwd: Path) -> tuple[bool, str]:
    """Pre-flight check: cwd's git remote must match one of the project's target repos."""
    try:
        repos = load_target_repos(slug)
    except ValueError as exc:
        return False, str(exc)
    if not repos:
        return False, "No target_repo_url for this project"

    rc, out, _ = _run(["git", "remote", "get-url", "origin"], cwd=cwd)
    if rc != 0:
        return False, f"Not in a git repo: {cwd}"
    actual = out.strip()
    if any(_norm_url(actual) == _norm_url(r.url) for r in repos):
        return True, "OK"
    expected = ", ".join(r.url for r in repos)
    return False, (
        f"Wrong repo: cwd remote = {actual}, expected {expected}. "
        "Run `python tool/cli/worktree.py setup --slug X` first."
    )


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------


def _md_table(headers: list[str], rows: list[list[str]]) -> str:
    esc = [[str(c).replace("|", "\\|") for c in r] for r in rows]
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    out += ["| " + " | ".join(r) + " |" for r in esc]
    return "\n".join(out)


def render_guard_table(rows: list[dict[str, str]]) -> str:
    return _md_table(["Repo", "Varianta", "Kontrola", "Stav", "Detail"],
                     [[r["repo"], r["variant"], r["check"], r["status"], r["detail"]] for r in rows])


def render_setup(s: WorktreeSetup) -> str:
    lines = [f"{BRAND_LINE}", "", f"## Worktrees — `{s.slug}` (mode: {s.mode})", ""]
    rows = []
    for r in s.repos:
        inst = {x["path"]: x["status"] for x in r["install_results"]}
        for v, p in r["worktrees"].items():
            rows.append([f"{r['role']}{' (primary)' if r['primary'] else ''}", v,
                         f"pflanzer/{s.slug}-{v}", p, r.get("workspace") or "—",
                         inst.get(p, "—"), r["claude_md"].get(v, "—")])
    lines.append(_md_table(["Repo", "Varianta", "Branch", "Path", "Workspace", "Install", "CLAUDE.md"], rows))
    lines += ["", "### Commit trailery (AI code provenance)", ""]
    for r in s.repos:
        h = r["hook"]
        lines.append(f"- {r['role']}: hook `{h['status']}`" + (f" — {h['message']}" if h.get("message") else ""))
    if s.guard:
        lines += ["", "### Data leakage guard", "", render_guard_table(s.guard)]
    lines += ["", "### Další kroky", ""]
    if s.mode == "mob":
        lines.append(f"- `cd {s.worktrees[0]} && claude` — MOB session, všichni u 1 monitoru (ADR-0011); "
                     "driver/navigator rotace 8 min, hard break 25 min")
    else:
        for r in s.repos:
            for v, p in r["worktrees"].items():
                lines.append(f"- `cd {p} && claude`  # varianta {v} ({r['role']})")
    if s.init_missing:
        miss = "; ".join(f"{m['repo']}: {', '.join(m['missing'])}" for m in s.init_missing)
        lines += ["", f"> Připomínka (N14): target repo nemá AI-readiness soubory ({miss}). "
                      f"Spusť `python tool/cli/worktree.py init-pr --slug {s.slug}` — první PR pilotu."]
    return "\n".join(lines)


def _setup_json(s: WorktreeSetup) -> dict[str, Any]:
    d = asdict(s)
    d["target_clone_path"] = str(s.target_clone_path)
    d["worktrees"] = [str(w) for w in s.worktrees]
    return d


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    p_setup = sub.add_parser("setup", help="Clone target repo(s) + create worktrees + hook + guard")
    p_setup.add_argument("--slug", required=True)
    p_setup.add_argument("--mode", choices=["parallel", "mob"], default=None,
                         help="parallel = 3 worktrees A/B/C; mob = 1 worktree (ADR-0011). "
                              "Default: projects.session_mode, jinak parallel")
    p_setup.add_argument("--no-install", "--skip-install", dest="no_install", action="store_true",
                         help="Skip package-manager install (faster, ale gates skipnou)")
    p_setup.add_argument("--no-guard", action="store_true", help="Přeskočit data leakage guard")
    p_setup.add_argument("--strict", action="store_true", help="Nenulový exit při nálezu guardu")
    p_setup.add_argument("--json", action="store_true", help="Strojový JSON výstup místo tabulek")

    p_guard = sub.add_parser("guard", help="Data leakage guard (secrets, .env*, prod dumpy)")
    p_guard.add_argument("--slug", required=True)
    p_guard.add_argument("--strict", action="store_true", help="Nenulový exit při nálezu")
    p_guard.add_argument("--no-fix", action="store_true", help="Needitovat .gitignore")
    p_guard.add_argument("--json", action="store_true")

    p_init = sub.add_parser("init-pr", help="První PR pilotu: INTEGRATION_GUIDE + CLAUDE.md do target repa")
    p_init.add_argument("--slug", required=True)
    p_init.add_argument("--json", action="store_true")

    p_prev = sub.add_parser("preview", help="Preview per varianta pro non-tech stakeholdery")
    p_prev.add_argument("--slug", required=True)
    p_prev.add_argument("--mode", choices=["draft-pr", "playwright"], default="draft-pr")
    p_prev.add_argument("--run", action="store_true",
                        help="draft-pr: opravdu pushnout + gh pr create (default jen vytiskne příkazy)")

    p_sess = sub.add_parser("set-session", help="Přepnout Pflanzer-Session trailer (1 | 2 | ship)")
    p_sess.add_argument("--slug", required=True)
    p_sess.add_argument("--session", required=True, choices=list(SESSION_VALUES))
    p_sess.add_argument("--variant", default=None, help="Jen jedna varianta (A/B/C/mob)")

    p_url = sub.add_parser("set-url", help="Uložit preview/PR URL do variants.prototype_url")
    p_url.add_argument("--slug", required=True)
    p_url.add_argument("--variant", required=True)
    p_url.add_argument("--url", required=True)

    p_verify = sub.add_parser("verify", help="Verify cwd is in target repo")
    p_verify.add_argument("--slug", required=True)
    p_verify.add_argument("--cwd", default=".")

    args = p.parse_args()

    if args.cmd == "setup":
        s = setup(args.slug, install_deps=not args.no_install, mode=args.mode,
                  run_guard=not args.no_guard)
        print(json.dumps(_setup_json(s), ensure_ascii=False, indent=2) if args.json else render_setup(s))
        if args.strict and any(g["status"] != "OK" for g in s.guard):
            sys.exit(2)
    elif args.cmd == "guard":
        rows = guard(args.slug, fix_gitignore=not args.no_fix)
        print(json.dumps(rows, ensure_ascii=False, indent=2) if args.json
              else f"{BRAND_LINE}\n\n## Data leakage guard — `{args.slug}`\n\n" + render_guard_table(rows))
        if args.strict and any(r["status"] != "OK" for r in rows):
            sys.exit(2)
    elif args.cmd == "init-pr":
        res = init_pr(args.slug)
        if args.json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            print(f"{BRAND_LINE}\n\n## init-pr — `{args.slug}`\n")
            for r in res:
                if r["status"] == "nothing-to-do":
                    print(f"- {r['repo']}: AI-readiness soubory už v base jsou — nic k inicializaci.")
                    continue
                print(f"- {r['repo']}: {r['status']} ({', '.join(r['changed']) or 'bez změn'}) "
                      f"v `{r['worktree']}` na `{r['branch']}`")
                for c in r["commands"]:
                    print(f"    {c}")
    elif args.cmd == "preview":
        if args.mode == "draft-pr":
            res = preview_draft_pr(args.slug, run=args.run)
        else:
            res = preview_playwright(args.slug)
        print(json.dumps({"brand": BRAND_LINE, "slug": args.slug, "mode": args.mode, "results": res},
                         ensure_ascii=False, indent=2))
    elif args.cmd == "set-session":
        print(json.dumps(set_session(args.slug, args.session, args.variant), ensure_ascii=False, indent=2))
    elif args.cmd == "set-url":
        ok = set_prototype_url(args.slug, args.variant, args.url)
        print(json.dumps({"ok": ok, "message": "uloženo" if ok else
                          f"varianta {args.variant} v DB neexistuje — nejdřív voting (quick_session.py vote)"},
                         ensure_ascii=False))
        sys.exit(0 if ok else 1)
    else:
        ok, msg = verify_cwd_in_target(args.slug, Path(args.cwd).resolve())
        print(json.dumps({"ok": ok, "message": msg}))
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
