"""Retro — outcome measurement for the method's core claim (audit N4).

The method claims "prod deploy D11–14". This module makes that claim
measurable and records the reinforcement track (T+7/30/60/90) as data
instead of Charter prose. Per ADR-0028 the share of winner LOC that survived
unchanged (`loc_reused_pct`) is reported as a plain number with no target
and no FLAG; speed-ups are never stated as an impression, only as measured
segments next to the repo baseline.

Subcommands:
- `baseline`  — median PR open→merge / open→first review of the target repo
                over the last 180 days (via `gh`), stored before the pilot
                (ADR-0028). Stored as `baseline_*` rows (milestone 'ship':
                the `outcomes` CHECK does not allow a separate milestone).
- `measure`   — reads the target repo (winner branch vs merge commit) and
                writes milestone='ship' rows into `outcomes`; with `--pr-url`
                also the three review segments (ADR-0025 point 4).
- `instability` — reverts and fix commits touching the winner's files after
                the merge (T+7 / T+30, ADR-0028 point 2).
- `record`    — manual T+7/30/60/90 readouts (bugs, leading/lagging metric).
- `report`    — renders `data/retro/<slug>-retro.md` + target checks.
- `reminders` — T+7/30/60/90 reminders as .ics, markdown checklist or
                `gh issue create` commands (printed, never executed).
- `lesson`    — poučení (hlavně po Kill): do DB (audit `retro.lesson`) a decision logu.

Stdlib + sqlite + git only. `gh` is optional (merge commit lookup, PR times,
baseline) with a fallback to an explicit `--merge-commit`.
"""
from __future__ import annotations

import argparse
import json
import re
import shlex
import shutil
import sqlite3
import statistics
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tool.cli._compat import (  # noqa: E402
    ProjectNotFound,
    count,
    exit_if_project_missing,
    local_date,
    tips,
)
from tool.cli.charter import is_ai_owner  # noqa: E402
from tool.cli.db import DATA_ROOT, audit, current_actor, transaction  # noqa: E402
from tool.cli.extract import tilde  # noqa: E402
from tool.cli.ux import CzechArgumentParser, did_you_mean, die, emit  # noqa: E402

RETRO_DIR = DATA_ROOT / "retro"
CHARTER_DIR = DATA_ROOT / "charters"
BRAND_LINE = "Pflanzer Method | pflanzer.cz/method"

# Method target (README / 07-handoff-do-vyvoje.md, audit N4). LOC survival has
# no target since ADR-0028.
TARGET_DAYS_TO_PROD = 14

# ADR-0028 point 1: baseline window and the minimum PR count for it to count.
BASELINE_DAYS = 180
BASELINE_MIN_PRS = 10
BASELINE_METRICS = ("baseline_open_to_merge_h", "baseline_open_to_first_review_h",
                    "baseline_pr_count", "baseline_after_go")
# Review segments recorded by `measure --pr-url` (hours; ADR-0025 point 4).
SEGMENT_METRICS = ("go_to_pr_open_h", "pr_open_to_first_review_h",
                   "first_review_to_merge_h", "pr_open_to_merge_h")
INSTABILITY_MILESTONES = ("t7", "t30")

MILESTONES = ("t7", "t30", "t60", "t90")
MILESTONE_DAYS = {"t7": 7, "t30": 30, "t60": 60, "t90": 90}
MILESTONE_LABELS = {"ship": "Ship", "t7": "T+7", "t30": "T+30",
                    "t60": "T+60", "t90": "T+90"}

# Recommended metric names per milestone (free-form names are allowed,
# these keep readouts comparable across pilots).
RECOMMENDED_METRICS: dict[str, dict[str, str]] = {
    "t7": {
        "t7_bugs": "počet bugů nahlášených na shipnutý kód (issues s labelem pflanzer:<slug>)",
        "t7_hotfix_commits": "počet hotfix commitů do shipnutých cest",
    },
    "t30": {
        "t30_leading_metric": "první měření ranné metriky z Kickoffu",
        "t30_handoff_acceptance_pct": "% acceptance criteria splněných v produkci / přijetí handoffu dev týmem",
    },
    "t60": {
        "t60_rework_pct": "% shipnutých LOC přepsaných od merge (rework)",
    },
    "t90": {
        "t90_lagging_metric": "měření hlavní metriky proti cíli z Kickoffu",
        "t90_go_iterate_kill": "verdikt T+90 readoutu: 1 = go, 0.5 = iterate, 0 = kill",
    },
}

# Default reinforcement owners from 07-handoff-do-vyvoje.md § Retro
# track — used when the Charter leaves the milestone empty.
# Kdo čte jednotlivé milníky: kroky cesty (klíče path_owners_json z Kickoffu).
DEFAULT_OWNER_STEPS = {
    "t7": ("provoz", "produkt"),
    "t30": ("produkt", "byznys"),
    "t60": ("vyvoj", "provoz"),
    "t90": ("byznys", "produkt"),
}
STEP_NAMES = {"byznys": "Byznys", "produkt": "Produkt", "design": "Design", "vyvoj": "Vývoj",
              "bezpecnost": "Bezpečnost a právo", "provoz": "Provoz"}
DEFAULT_OWNERS = {m: " a ".join(STEP_NAMES[s] for s in steps)
                  for m, steps in DEFAULT_OWNER_STEPS.items()}
DEFAULT_DELIVERABLES = {
    "t7": "Podívat se, jestli podpora dostává víc dotazů, než se čekalo, a kolik přišlo bugů",
    "t30": "Odečíst první metriku z Kickoffu, porovnat práci s odhadem, krátké retro",
    "t60": "Skutečná kapacita proti odhadu, co se rozbilo okolo a kolik kódu se přepsalo",
    "t90": "Hlavní metrika proti cíli z Kickoffu a co si odnést do dalšího projektu",
}

# `t42_project_metric` = měření metriky z Kickoffu v jejím vlastním horizontu (např. „do 6 týdnů“).
PROJECT_METRIC_RE = re.compile(r"^t\d{1,3}_project_metric$")

EMPTY_MARKERS = {"", "-", "—", "tbd", "n/a"}

# Soubory, které do větve přidal sám nástroj (init, guard, worktree); do reuse se nepočítají.
METHOD_FILES = {".gitignore", "CLAUDE.md", "docs/INTEGRATION_GUIDE.md", "tests/acceptance/.gitkeep"}
METHOD_PREFIXES = (".pflanzer/",)


def is_method_file(path: str) -> bool:
    """`.gitignore`, `.pflanzer/*`, … — přidal je guard nebo init, ne autor varianty."""
    name = path.rsplit("/", 1)[-1]
    return (path in METHOD_FILES or name == ".gitignore" or path.startswith(METHOD_PREFIXES)
            or name.startswith("pflanzer.gates."))


# --------------------------------------------------------------------------
# DB helpers
# --------------------------------------------------------------------------


def _ensure_outcomes_table(conn: sqlite3.Connection) -> None:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='outcomes'"
    ).fetchone()
    if not row:
        raise RuntimeError(
            "Tabulka `outcomes` v DB chybí. Spusť `pflanzer update` "
            "(additivní migrace, data nemaže)."
        )


def _load_project(conn: sqlite3.Connection, slug: str) -> dict[str, Any]:
    row = conn.execute(
        "SELECT * FROM projects WHERE slug = ?", (slug,),
    ).fetchone()
    if not row:
        raise ProjectNotFound(slug)
    return dict(row)


def _parse_ts(value: Any) -> datetime | None:
    """Parse SQLite CURRENT_TIMESTAMP / ISO strings into aware UTC datetimes."""
    if not value:
        return None
    text = str(value).strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def is_throwaway(conn: sqlite3.Connection, project: dict[str, Any]) -> bool:
    """Throwaway demo: nejde do produkce, takže se neměří přežití LOC ani T+30/60/90."""
    try:
        from tool.cli.triage import load_risk_profile
        return load_risk_profile(conn, int(project["id"])) == "throwaway"
    except Exception:  # noqa: BLE001
        return project.get("throwaway_or_evolve") == "throwaway"


def _go_date(conn: sqlite3.Connection, project_id: int) -> tuple[datetime | None, str]:
    """Return (Rozhodnutí GO timestamp, source).

    Order: sessions(type=2, decision='go').decision_ts → first decisions row
    of type 'handoff' (session_2.py writes it on GO) → None.
    """
    row = conn.execute(
        "SELECT decision_ts, ends_at FROM sessions "
        "WHERE project_id = ? AND type = 2 AND decision = 'go' "
        "ORDER BY id DESC LIMIT 1", (project_id,),
    ).fetchone()
    if row:
        dt = _parse_ts(row[0]) or _parse_ts(row[1])
        if dt:
            return dt, "sessions.type=2 decision=go"
    row = conn.execute(
        "SELECT atribuce_ts FROM decisions "
        "WHERE project_id = ? AND type = 'handoff' "
        "ORDER BY atribuce_ts ASC, id ASC LIMIT 1", (project_id,),
    ).fetchone()
    if row:
        dt = _parse_ts(row[0])
        if dt:
            return dt, "decisions.type=handoff"
    return None, "unknown"


def _winner_name(slug: str, project_id: int) -> str:
    """Winner variant name, same rule as SHIP.md (handoff_pr.py).

    Reuses `handoff_pr._fetch_ship_context` so SHIP.md and retro always
    agree on the winner; falls back to the highest preference_score of the
    latest Build when that helper is unavailable.
    """
    try:
        from tool.cli.handoff_pr import _fetch_ship_context
        ctx = _fetch_ship_context(slug)
        if ctx.get("winner"):
            return str(ctx["winner"][0])
    except Exception as exc:  # noqa: BLE001 — fallback is intentional
        print(f"[retro] warn: handoff_pr winner lookup failed ({exc}); "
              "fallback na preference_score", file=sys.stderr)
    with transaction() as conn:
        row = conn.execute(
            """
            SELECT v.name FROM variants v
            JOIN sessions s ON s.id = v.session_id
            WHERE s.project_id = ? AND s.type = 1
            ORDER BY s.id DESC, v.preference_score DESC LIMIT 1
            """, (project_id,),
        ).fetchone()
    if not row:
        raise ValueError(
            f"Projekt '{slug}' nemá žádnou variantu v Buildu — winner nelze "
            "určit. Zadej ho ručně přes `--winner A`."
        )
    return str(row[0])


# --------------------------------------------------------------------------
# git helpers
# --------------------------------------------------------------------------


def _git(repo: Path, *args: str, check: bool = True) -> str:
    res = subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, timeout=120,
    )
    if check and res.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} selhal v {repo}: {res.stderr.strip()}")
    return res.stdout.strip() if res.returncode == 0 else ""


def _rev(repo: Path, ref: str) -> str | None:
    out = _git(repo, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}", check=False)
    return out or None


def _resolve_repo(project: dict[str, Any], repo_path: str | None) -> Path:
    """Locate the local target clone.

    Order: explicit `--repo-path` → worktree.py cache
    (`~/.pflanzer/targets/<owner-repo>/`) → `target_repo_url` itself when it
    is a local git directory.
    """
    candidates: list[Path] = []
    if repo_path:
        candidates.append(Path(repo_path).expanduser())
    url = project.get("target_repo_url")
    if url:
        try:
            from tool.cli.worktree import TARGETS_CACHE, _slugify_repo
            candidates.append(TARGETS_CACHE / _slugify_repo(url))
        except (ImportError, ValueError):
            pass
        local = Path(url).expanduser()
        if local.is_absolute():
            candidates.append(local)
    for c in candidates:
        if c.is_dir() and _git(c, "rev-parse", "--git-dir", check=False):
            return c.resolve()
    raise ValueError(
        "Nenašel jsem lokální clone target repa (zkoušeno: "
        + ", ".join(str(c) for c in candidates or [Path("—")])
        + "). Spusť `pflanzer worktree setup --slug <slug> --no-install` "
        "nebo zadej `--repo-path`."
    )


def _gh_merge_info(pr_url: str) -> tuple[str, str | None] | None:
    """Return (merge_commit_sha, merged_at) via `gh`, or None when unavailable."""
    if not shutil.which("gh"):
        return None
    res = subprocess.run(
        ["gh", "pr", "view", pr_url, "--json", "mergeCommit,mergedAt"],
        capture_output=True, text=True, timeout=60,
    )
    if res.returncode != 0:
        print(f"[retro] warn: gh pr view selhal: {res.stderr.strip()} — zadej `--merge-commit <sha>`",
              file=sys.stderr)
        return None
    data = json.loads(res.stdout or "{}")
    sha = (data.get("mergeCommit") or {}).get("oid")
    if not sha:
        return None
    return sha, data.get("mergedAt")


def _gh_pr_list(repo: Path) -> list[dict[str, Any]]:
    """Merged PRs of the target repo via `gh` (createdAt, mergedAt, reviews); raises RuntimeError.

    Kept as one small function so tests can monkeypatch it (no network in tests).
    """
    if not shutil.which("gh"):
        raise RuntimeError("`gh` není nainstalované")
    res = subprocess.run(
        ["gh", "pr", "list", "--state", "merged", "--limit", "200",
         "--json", "number,createdAt,mergedAt,reviews"],
        cwd=repo, capture_output=True, text=True, timeout=120,
    )
    if res.returncode != 0:
        raise RuntimeError(f"`gh pr list` selhal: {res.stderr.strip() or res.returncode}")
    try:
        data = json.loads(res.stdout or "[]")
    except ValueError as exc:
        raise RuntimeError(f"`gh pr list` vrátil neplatný JSON: {exc}") from exc
    return data if isinstance(data, list) else []


def _gh_pr_times(pr_url: str) -> dict[str, Any]:
    """createdAt, mergedAt and reviews of one PR via `gh`; raises RuntimeError (patchable in tests)."""
    if not shutil.which("gh"):
        raise RuntimeError("`gh` není nainstalované")
    res = subprocess.run(
        ["gh", "pr", "view", pr_url, "--json", "createdAt,mergedAt,reviews"],
        capture_output=True, text=True, timeout=60,
    )
    if res.returncode != 0:
        raise RuntimeError(f"`gh pr view` selhal: {res.stderr.strip() or res.returncode}")
    try:
        return json.loads(res.stdout or "{}")
    except ValueError as exc:
        raise RuntimeError(f"`gh pr view` vrátil neplatný JSON: {exc}") from exc


def _hours(a: datetime, b: datetime) -> float:
    return round((b - a).total_seconds() / 3600, 1)


def _first_review_dt(pr: dict[str, Any]) -> datetime | None:
    """Earliest submitted review at or after the PR was opened, else None."""
    opened = _parse_ts(pr.get("createdAt"))
    times = [t for t in (_parse_ts(r.get("submittedAt")) for r in pr.get("reviews") or []
                         if isinstance(r, dict)) if t and (opened is None or t >= opened)]
    return min(times) if times else None


def compute_baseline(prs: list[dict[str, Any]], now: datetime | None = None) -> dict[str, Any]:
    """Medians over PRs merged in the last BASELINE_DAYS (pure function, no I/O)."""
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=BASELINE_DAYS)
    to_merge: list[float] = []
    to_review: list[float] = []
    for pr in prs:
        opened, merged = _parse_ts(pr.get("createdAt")), _parse_ts(pr.get("mergedAt"))
        if not opened or not merged or merged < cutoff or merged < opened:
            continue
        to_merge.append(_hours(opened, merged))
        first = _first_review_dt(pr)
        if first:
            to_review.append(_hours(opened, first))
    return {
        "pr_count": len(to_merge),
        "review_pr_count": len(to_review),
        "open_to_merge_h": round(statistics.median(to_merge), 1) if to_merge else None,
        "open_to_first_review_h": round(statistics.median(to_review), 1) if to_review else None,
    }


def _baseline_rows(conn: sqlite3.Connection, project_id: int) -> dict[str, Any]:
    """Stored baseline: {metric: value} (numeric only) plus `missing_reason` when marked absent."""
    out: dict[str, Any] = {}
    for metric, value, notes in conn.execute(
        "SELECT metric, value, notes FROM outcomes WHERE project_id = ? AND milestone = 'ship' "
        "AND metric LIKE 'baseline\\_%' ESCAPE '\\' ORDER BY recorded_at, id", (project_id,),
    ).fetchall():
        if value is None:
            out["missing_reason"] = notes
            out.pop(metric, None)
        else:
            out[metric] = float(value)
            out.pop("missing_reason", None)
    return out


def baseline(*, slug: str, repo_path: str | None = None) -> dict[str, Any]:
    """Spočítá základnu z historie target repa (ADR-0028 bod 1) a uloží ji k projektu.

    Medián hodin od otevření PR do merge a do prvního review za posledních 180 dní
    (`gh pr list --state merged`). Méně než 10 PR nebo `gh` nedostupné → neukládá se nic
    číselného, jen značka „základna není“ s důvodem. Je-li už Go zapsané, uloží se i to
    (pre-registrace, ADR-0013); dříve uloženou základnu po Go nepřepisuje.
    """
    with transaction() as conn:
        _ensure_outcomes_table(conn)
        project = _load_project(conn, slug)
        project_id = int(project["id"])
        go_dt, _src = _go_date(conn, project_id)
        existing = _baseline_rows(conn, project_id)
    after_go = go_dt is not None

    if after_go and existing.get("baseline_pr_count") and not existing.get("baseline_after_go"):
        return {"slug": slug, "stored": False, "kept_existing": True, "baseline": existing,
                "after_go": False, "reason": "základna z doby před Go už je uložená, nepřepisuji ji"}

    reason: str | None = None
    result: dict[str, Any] | None = None
    try:
        repo = _resolve_repo(project, repo_path)
        result = compute_baseline(_gh_pr_list(repo))
    except (RuntimeError, ValueError, OSError, subprocess.SubprocessError) as exc:
        reason = str(exc)
    if result is not None and result["pr_count"] < BASELINE_MIN_PRS:
        reason = (f"v repu je za posledních {BASELINE_DAYS} dní jen "
                  f"{count(result['pr_count'], 'mergnuté PR', 'mergnuté PR', 'mergnutých PR')} "
                  f"(potřeba aspoň {BASELINE_MIN_PRS})")

    actor = current_actor()
    window = f"posledních {BASELINE_DAYS} dní, medián"
    with transaction() as conn:
        conn.execute(
            f"DELETE FROM outcomes WHERE project_id = ? AND milestone = 'ship' "
            f"AND metric IN ({','.join('?' * len(BASELINE_METRICS))})",
            (project_id, *BASELINE_METRICS),
        )
        ins = ("INSERT INTO outcomes (project_id, milestone, metric, value, unit, "
               "evidence_url, notes, recorded_by) VALUES (?, 'ship', ?, ?, ?, NULL, ?, ?)")
        if reason or result is None:
            conn.execute(ins, (project_id, "baseline_open_to_merge_h", None, "h",
                               f"základna není: {reason}", actor))
        else:
            conn.execute(ins, (project_id, "baseline_open_to_merge_h",
                               result["open_to_merge_h"], "h", window, actor))
            if result["open_to_first_review_h"] is not None:
                conn.execute(ins, (project_id, "baseline_open_to_first_review_h",
                                   result["open_to_first_review_h"], "h",
                                   f"{window}; z {result['review_pr_count']} PR s review", actor))
            conn.execute(ins, (project_id, "baseline_pr_count", float(result["pr_count"]),
                               "PR", f"mergnuté za posledních {BASELINE_DAYS} dní", actor))
            if after_go:
                conn.execute(ins, (project_id, "baseline_after_go", 1.0, None,
                                   "základna změřena až po Go — nesplňuje pre-registraci "
                                   "(ADR-0013)", actor))
        audit(conn, action="retro.baseline", target_type="project", target_id=project_id,
              payload={"slug": slug, "reason": reason, "after_go": after_go,
                       "result": None if reason else result})
    return {"slug": slug, "stored": reason is None, "reason": reason, "after_go": after_go,
            "baseline": None if reason else result, "kept_existing": False}


def _segments(go_dt: datetime | None, pr: dict[str, Any]) -> tuple[dict[str, float], list[str]]:
    """Review segments in hours + Czech one-line warnings for what could not be computed."""
    seg: dict[str, float] = {}
    warns: list[str] = []
    opened, merged = _parse_ts(pr.get("createdAt")), _parse_ts(pr.get("mergedAt"))
    first = _first_review_dt(pr)
    if not opened:
        warns.append("PR nemá čas otevření — úseky se nezapíšou.")
        return seg, warns
    if go_dt is None:
        warns.append("Datum Go chybí — úsek Go → PR otevřen se nezapíše.")
    elif opened < go_dt:
        warns.append("PR bylo otevřené před Go — úsek Go → PR otevřen se nezapíše.")
    else:
        seg["go_to_pr_open_h"] = _hours(go_dt, opened)
    if first is None:
        warns.append("PR nemá žádné review — úseky přes první review se nezapíšou.")
    else:
        seg["pr_open_to_first_review_h"] = _hours(opened, first)
    if merged is None:
        warns.append("PR není mergnuté — úsek první review → merge se nezapíše.")
    else:
        if first is not None and merged >= first:
            seg["first_review_to_merge_h"] = _hours(first, merged)
        elif first is not None:
            warns.append("Merge je před prvním review — úsek první review → merge se nezapíše.")
        seg["pr_open_to_merge_h"] = _hours(opened, merged)
    return seg, warns


def _numstat(repo: Path, a: str, b: str, paths: list[str] | None = None) -> dict[str, tuple[int, int]]:
    """`git diff --numstat a b [-- paths]` → {path: (added, removed)}; binaries skipped."""
    args = ["diff", "--numstat", "--no-renames", a, b]
    if paths is not None:
        if not paths:
            return {}
        args += ["--", *paths]
    out = _git(repo, *args)
    result: dict[str, tuple[int, int]] = {}
    for line in out.splitlines():
        parts = line.split("\t", 2)
        if len(parts) != 3 or parts[0] == "-" or parts[1] == "-":
            continue
        result[parts[2]] = (int(parts[0]), int(parts[1]))
    return result


def _fork_point(repo: Path, base_ref: str, winner_sha: str, winner_branch: str) -> tuple[str, str]:
    """Commit the winner branch was forked from, plus how it was found.

    1. merge-base(base_ref, winner) — base_ref defaults to `<merge>^1`, i.e.
       the target branch just before the merge, so the merged winner does
       not collapse the range to zero.
    2. If that equals the winner tip (fast-forward / rebase merge, or an
       explicit `--base` that already contains the winner), fall back to the
       oldest reflog entry of the local winner branch (worktree.py creates it
       with `-b pflanzer/<slug>-X <base>`, so that entry is the fork point).
    """
    mb = _git(repo, "merge-base", base_ref, winner_sha, check=False)
    if mb and mb != winner_sha:
        return mb, f"merge-base({base_ref}, winner)"
    reflog = _git(repo, "reflog", "show", "--format=%H", winner_branch, check=False)
    entries = [e for e in reflog.splitlines() if e.strip()]
    if entries and entries[-1] != winner_sha:
        return entries[-1], f"reflog({winner_branch}) creation"
    raise ValueError(
        f"Nelze určit fork point winner branche (base `{base_ref}` už winner "
        "obsahuje a reflog nepomohl). Zadej `--base <sha commitu, ze kterého "
        "winner vznikl>`."
    )


# --------------------------------------------------------------------------
# measure
# --------------------------------------------------------------------------


def _split_roles(items: list[str] | dict[str, str] | None, what: str) -> dict[str, str]:
    """`ROLE=hodnota` (opakovatelné) -> {role: hodnota}."""
    if isinstance(items, dict):
        return dict(items)
    out: dict[str, str] = {}
    for it in items or []:
        role, sep, val = it.partition("=")
        if not sep or not role.strip() or not val.strip():
            raise ValueError(f"{what} očekává ROLE=hodnota (např. api=https://…), dostal jsem „{it}“.")
        out[role.strip()] = val.strip()
    return out


def _measure_repo(
    *, slug: str, winner_name: str, repo: Path, pr_url: str | None,
    merge_commit: str | None, base: str | None, fetch: bool,
) -> dict[str, Any]:
    """Měření jednoho repa (bez zápisu do DB): LOC winnera v merge, počet commitů, čas merge."""
    remotes = _git(repo, "remote", check=False).split()
    if fetch and "origin" in remotes:
        _git(repo, "fetch", "origin", "--prune")

    merged_at: str | None = None
    merge_source = "--merge-commit"
    if not merge_commit and pr_url:
        info = _gh_merge_info(pr_url)
        if info:
            merge_commit, merged_at = info
            merge_source = "gh pr view"
    if not merge_commit:
        raise ValueError(
            "Chybí merge commit. Zadej `--merge-commit <sha>` "
            "(nebo `--pr-url` s nainstalovaným a přihlášeným `gh`)."
        )
    merge_sha = _rev(repo, merge_commit)
    if not merge_sha:
        raise ValueError(f"Merge commit `{merge_commit}` v {repo} neexistuje (fetch proběhl?).")

    winner_branch = f"pflanzer/{slug}-{winner_name}"
    winner_ref = next(
        (r for r in (winner_branch, f"origin/{winner_branch}") if _rev(repo, r)), None,
    )
    if not winner_ref:
        raise ValueError(
            f"Winner branch `{winner_branch}` v {repo} neexistuje "
            "(ani na origin). Smazaná po merge? Obnov ji nebo zadej `--winner`."
        )
    winner_sha = _rev(repo, winner_ref)
    assert winner_sha

    base_ref = base or f"{merge_sha}^1"
    fork_sha, fork_source = _fork_point(repo, base_ref, winner_sha, winner_ref)

    winner_stat = _numstat(repo, fork_sha, winner_sha)
    ignored_files = sorted(p for p, (a, _r) in winner_stat.items() if a > 0 and is_method_file(p))
    added_by_path = {p: a for p, (a, _r) in winner_stat.items()
                     if a > 0 and not is_method_file(p)}
    loc_winner = sum(added_by_path.values())

    post_stat = _numstat(repo, winner_sha, merge_sha, sorted(added_by_path))
    per_file = []
    loc_unchanged = 0
    for path, added in sorted(added_by_path.items()):
        removed = post_stat.get(path, (0, 0))[1]
        kept = max(0, added - removed)
        loc_unchanged += kept
        per_file.append({"path": path, "added_winner": added,
                         "removed_after": removed, "unchanged": kept})
    winner_commits = int(_git(repo, "rev-list", "--count", f"{fork_sha}..{winner_sha}") or 0)
    merge_dt = _parse_ts(merged_at) or _parse_ts(
        _git(repo, "log", "-1", "--format=%cI", merge_sha)
    )
    return {
        "repo": repo, "winner_branch": winner_branch, "winner_ref": winner_ref,
        "winner_sha": winner_sha, "fork_sha": fork_sha, "fork_source": fork_source,
        "merge_sha": merge_sha, "merge_source": merge_source, "merge_dt": merge_dt,
        "loc_winner": loc_winner, "loc_unchanged": loc_unchanged, "per_file": per_file,
        "ignored_files": ignored_files, "winner_commits": winner_commits,
        "files": len(added_by_path), "evidence": pr_url or f"commit:{merge_sha}",
    }


def _repo_clone(slug: str, winner_name: str, target: Any, primary: bool,
                repo_path: str | None) -> Path:
    """Lokální git clone/worktree repa varianty: --repo-path, worktree `<slug>-<X>[-role]`, cache."""
    if repo_path:
        return _resolve_repo({"target_repo_url": target.url}, repo_path)
    try:
        from tool.cli.worktree import worktree_dir
        wt = worktree_dir(slug, winner_name, target, primary)
        if wt.is_dir() and _git(wt, "rev-parse", "--git-dir", check=False):
            return wt.resolve()
    except (ImportError, ValueError):
        pass
    return _resolve_repo({"target_repo_url": target.url}, None)


def _pct(unchanged: int, total: int) -> float | None:
    return round(unchanged / total * 100, 1) if total else None


def measure(
    *, slug: str, pr_url: str | None = None, merge_commit: str | None = None,
    base: str | None = None, repo_path: str | None = None,
    winner: str | None = None, fetch: bool = True,
    repo_prs: list[str] | dict[str, str] | None = None,
    repo_merges: list[str] | dict[str, str] | None = None,
) -> dict[str, Any]:
    """Measure how much of the winner branch reached production unchanged.

    Heuristic (documented, conservative):
    - `loc_winner` = lines added by the winner branch:
      `git diff --numstat <fork>..<winner>` where fork = merge-base of the
      winner and `--base` (default `<merge_commit>^1`).
    - For each path the winner added lines to, `removed` = lines deleted in
      `git diff --numstat <winner> <merge_commit> -- <paths>` (lines present
      on the winner tip but not in the merged result).
    - `loc_merged_unchanged` = Σ max(0, added_winner(path) − removed(path)).
      Any removal in a winner-touched file counts against reuse, including
      removals of pre-existing lines or by unrelated commits that landed on
      the target branch before the merge → the number is a lower bound.
      A modified line counts as one removal (+ one addition, ignored).
    - `loc_reused_pct` = loc_merged_unchanged / loc_winner × 100.
    - `days_to_prod` = calendar days from Rozhodnutí GO (sessions/decisions)
      to the merge (gh `mergedAt`, else committer date of the merge commit).
      Merge is used as the prod proxy; if deploy happens later, record the
      real deploy date as a note.
    - `winner_commits` = `git rev-list --count <fork>..<winner>`.
    Multi-repo projekt (`target_repos`): měří se **každé repo zvlášť** (worktree
    `<slug>-<X>-<role>`, větev `pflanzer/<slug>-<X>` v každém repu) a navíc součet.
    Primární repo bere `--pr-url` / `--merge-commit`, ostatní `--repo-pr ROLE=URL`
    a `--repo-merge ROLE=SHA`; repo bez PR/merge se neměří a výstup to řekne
    („měřeno jen web“).
    Works for merge commits and squash merges; for rebase merges pass the
    tip of the rebased series as `--merge-commit` and the fork as `--base`.
    """
    with transaction() as conn:
        _ensure_outcomes_table(conn)
        project = _load_project(conn, slug)
        project_id = int(project["id"])
        go_dt, go_source = _go_date(conn, project_id)
    winner_name = winner or _winner_name(slug, project_id)

    targets: list[Any] = []
    try:
        from tool.cli.worktree import load_target_repos
        targets = load_target_repos(slug, project)
    except Exception:  # noqa: BLE001 — bez target_repos měříme jedno repo jako dřív
        targets = []
    multi = len(targets) > 1
    prs, merges = _split_roles(repo_prs, "--repo-pr"), _split_roles(repo_merges, "--repo-merge")
    unknown = sorted(r for r in {*prs, *merges} if r not in {t.role for t in targets})
    if unknown:
        raise ValueError(f"Repo {', '.join(unknown)} v projektu není "
                         f"(jsou: {', '.join(t.role for t in targets) or 'jedno repo'}).")

    repo_results: list[dict[str, Any]] = []  # změřená repa
    unmeasured: list[dict[str, str]] = []
    if not multi:
        res = _measure_repo(slug=slug, winner_name=winner_name,
                            repo=_resolve_repo(project, repo_path), pr_url=pr_url,
                            merge_commit=merge_commit, base=base, fetch=fetch)
        res["role"] = targets[0].role if targets else None
        repo_results.append(res)
    else:
        for idx, t in enumerate(targets):
            primary = idx == 0
            t_pr = pr_url if primary else prs.get(t.role)
            t_merge = merge_commit if primary else merges.get(t.role)
            if primary and not (t_pr or t_merge):
                raise ValueError(
                    f"Chybí PR nebo merge commit primárního repa `{t.role}`: "
                    "`--pr-url <URL>` nebo `--merge-commit <sha>`; ostatní repa "
                    + ", ".join(f"`--repo-pr {x.role}=<URL>`" for x in targets[1:]) + ".")
            if not (t_pr or t_merge):
                unmeasured.append({"role": t.role,
                                   "reason": f"chybí `--repo-pr {t.role}=<URL>` "
                                             f"(nebo `--repo-merge {t.role}=<sha>`)"})
                continue
            clone = _repo_clone(slug, winner_name, t, primary, repo_path if primary else None)
            res = _measure_repo(slug=slug, winner_name=winner_name, repo=clone, pr_url=t_pr,
                                merge_commit=t_merge, base=base if primary else None,
                                fetch=fetch)
            res["role"] = t.role
            repo_results.append(res)

    loc_winner = sum(r["loc_winner"] for r in repo_results)
    loc_unchanged = sum(r["loc_unchanged"] for r in repo_results)
    reuse_pct = _pct(loc_unchanged, loc_winner)
    winner_commits = sum(r["winner_commits"] for r in repo_results)
    merge_dts = [r["merge_dt"] for r in repo_results if r["merge_dt"]]
    merge_dt = max(merge_dts) if merge_dts else None  # hotovo, až je ve všech změřených repech
    # oba okamžiky jako aware datetime, kalendářní dny v jednom (místním) pásmu
    go_day = local_date(go_dt) if go_dt else None
    merge_day = local_date(merge_dt) if merge_dt else None
    days_to_prod = (merge_day - go_day).days if (merge_day and go_day) else None
    for r in repo_results:
        d = local_date(r["merge_dt"]) if r["merge_dt"] else None
        r["days_to_prod"] = (d - go_day).days if (d and go_day) else None

    first = repo_results[0]
    measured_names = [r["role"] for r in repo_results]
    coverage = ""
    if multi:
        coverage = ("měřeno: " + ", ".join(measured_names)
                    + ("; neměřeno: " + ", ".join(u["role"] for u in unmeasured)
                       if unmeasured else ""))
    ignored_files = sorted({f for r in repo_results for f in r["ignored_files"]})
    evidence = first["evidence"]
    heuristic = (
        f"added(winner) - removed(winner..merge) per path; fork={first['fork_sha'][:10]} "
        f"({first['fork_source']}); winner={first['winner_sha'][:10]}; "
        f"merge={first['merge_sha'][:10]} ({first['merge_source']})"
    )
    n_files = sum(r["files"] for r in repo_results)
    rows: list[tuple[str, float | None, str, str]] = [
        ("loc_winner", float(loc_winner), "loc",
         f"{n_files} files; {first['winner_branch']}"
         + (f"; ignorováno {len(ignored_files)} souborů nástroje" if ignored_files else "")
         + (f"; součet repa ({coverage})" if multi else "")),
        ("loc_merged_unchanged", float(loc_unchanged), "loc",
         heuristic + (f"; součet repa ({coverage})" if multi else "")),
        ("loc_reused_pct", reuse_pct, "%",
         "údaj bez cíle (ADR-0028)" + (f"; {coverage}" if multi else "")),
        ("winner_commits", float(winner_commits), "commits",
         f"{first['fork_sha'][:10]}..{first['winner_sha'][:10]}"
         + (f"; součet repa ({coverage})" if multi else "")),
    ]
    if days_to_prod is not None:
        rows.append((
            "days_to_prod", float(days_to_prod), "days",
            f"GO {go_day.isoformat()} ({go_source}) -> merge "
            f"{merge_day.isoformat()}; target <= {TARGET_DAYS_TO_PROD}"
            + (f"; poslední z repa ({coverage})" if multi else ""),
        ))
    else:
        print("[retro] warn: datum Rozhodnutí (Go) nenalezeno — days_to_prod se nezapíše.",
              file=sys.stderr)
    if multi:  # per repo: metrika@role
        for r in repo_results:
            role = r["role"]
            rows += [
                (f"loc_winner@{role}", float(r["loc_winner"]), "loc",
                 f"{r['files']} files; {r['winner_branch']} v repu {role}"),
                (f"loc_merged_unchanged@{role}", float(r["loc_unchanged"]), "loc",
                 f"merge={r['merge_sha'][:10]} ({r['merge_source']}) v repu {role}"),
                (f"loc_reused_pct@{role}", _pct(r["loc_unchanged"], r["loc_winner"]), "%",
                 f"repo {role}"),
                (f"winner_commits@{role}", float(r["winner_commits"]), "commits",
                 f"{r['fork_sha'][:10]}..{r['winner_sha'][:10]} v repu {role}"),
            ]
            if r["days_to_prod"] is not None:
                rows.append((f"days_to_prod@{role}", float(r["days_to_prod"]), "days",
                             f"repo {role}"))

    # ADR-0025 point 4: Go -> PR opened -> first review -> merge (hours), only with --pr-url.
    segments: dict[str, float] = {}
    segment_warnings: list[str] = []
    if pr_url:
        try:
            segments, segment_warnings = _segments(go_dt, _gh_pr_times(pr_url))
        except RuntimeError as exc:
            segment_warnings.append(f"Časy PR nejsou dostupné ({exc}) — úseky review se nezapíšou.")
        for w in segment_warnings:
            print(f"[retro] warn: {w}", file=sys.stderr)
        seg_notes = {
            "go_to_pr_open_h": f"Go -> PR otevřen (hodiny); {pr_url}",
            "pr_open_to_first_review_h": f"PR otevřen -> první review (hodiny); {pr_url}",
            "first_review_to_merge_h": f"první review -> merge (hodiny); {pr_url}",
            "pr_open_to_merge_h": f"PR otevřen -> merge (hodiny), srovnatelné se základnou; {pr_url}",
        }
        rows += [(m, segments[m], "h", seg_notes[m]) for m in SEGMENT_METRICS if m in segments]

    actor = current_actor()
    metrics = [r[0] for r in rows]
    with transaction() as conn:
        baseline_now = _baseline_rows(conn, project_id)
        # measure is recomputable: replace previous ship rows for these metrics
        conn.execute(
            f"DELETE FROM outcomes WHERE project_id = ? AND milestone = 'ship' "
            f"AND (metric IN ({','.join('?' * len(metrics))}) "
            f"OR (metric GLOB '*@*' AND metric GLOB '[ldw]*'))",
            (project_id, *metrics),
        )
        for metric, value, unit, notes in rows:
            conn.execute(
                "INSERT INTO outcomes (project_id, milestone, metric, value, unit, "
                "evidence_url, notes, recorded_by) VALUES (?, 'ship', ?, ?, ?, ?, ?, ?)",
                (project_id, metric, value, unit, evidence, notes, actor),
            )
        audit(
            conn, action="retro.measure", target_type="project", target_id=project_id,
            payload={"slug": slug, "winner": winner_name, "merge_commit": first["merge_sha"],
                     "pr_url": pr_url, "loc_reused_pct": reuse_pct,
                     "days_to_prod": days_to_prod, "repos": measured_names,
                     "unmeasured": [u["role"] for u in unmeasured]},
        )

    out = {
        "slug": slug,
        "winner": winner_name,
        "winner_branch": first["winner_ref"],
        "repo": str(first["repo"]),
        "fork_point": first["fork_sha"],
        "fork_point_source": first["fork_source"],
        "merge_commit": first["merge_sha"],
        "merge_commit_source": first["merge_source"],
        "merged_at": merge_dt.isoformat() if merge_dt else None,
        "session2_go_at": go_dt.isoformat() if go_dt else None,
        "loc_winner": loc_winner,
        "loc_merged_unchanged": loc_unchanged,
        "loc_reused_pct": reuse_pct,
        "days_to_prod": days_to_prod,
        "winner_commits": winner_commits,
        "segments_h": segments,
        "segment_warnings": segment_warnings,
        "baseline": baseline_now,
        "targets": {
            "days_to_prod_ok": days_to_prod is not None and days_to_prod <= TARGET_DAYS_TO_PROD,
        },
        "per_file": first["per_file"] if not multi else [
            {**f, "repo": r["role"]} for r in repo_results for f in r["per_file"]],
        "ignored_files": ignored_files,
        "evidence_url": evidence,
        "measured_repos": measured_names,
        "unmeasured_repos": unmeasured,
        "next_step": f"pflanzer retro report --slug {slug}",
    }
    if multi:
        out["per_repo"] = [
            {"role": r["role"], "repo": str(r["repo"]), "loc_winner": r["loc_winner"],
             "loc_merged_unchanged": r["loc_unchanged"],
             "loc_reused_pct": _pct(r["loc_unchanged"], r["loc_winner"]),
             "days_to_prod": r["days_to_prod"], "winner_commits": r["winner_commits"],
             "merge_commit": r["merge_sha"]} for r in repo_results]
    return out


# --------------------------------------------------------------------------
# record
# --------------------------------------------------------------------------


def record(
    *, slug: str, milestone: str, metric: str, value: float,
    unit: str | None = None, evidence: str | None = None, notes: str | None = None,
) -> dict[str, Any]:
    if milestone not in MILESTONES:
        raise ValueError(f"milestone musí být jedno z {MILESTONES}")
    known = {m for ms in RECOMMENDED_METRICS.values() for m in ms}
    if metric not in known and not PROJECT_METRIC_RE.match(metric):
        print(f"[retro] warn: `{metric}` není doporučený název metriky "
              f"({', '.join(sorted(known))}); zapisuji i tak.", file=sys.stderr)
    actor = current_actor()
    with transaction() as conn:
        _ensure_outcomes_table(conn)
        project_id = int(_load_project(conn, slug)["id"])
        cur = conn.execute(
            "INSERT INTO outcomes (project_id, milestone, metric, value, unit, "
            "evidence_url, notes, recorded_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (project_id, milestone, metric, value, unit, evidence, notes, actor),
        )
        audit(
            conn, action="retro.record", target_type="outcome", target_id=cur.lastrowid,
            payload={"slug": slug, "milestone": milestone, "metric": metric, "value": value},
        )
    return {"slug": slug, "outcome_id": cur.lastrowid, "milestone": milestone,
            "metric": metric, "value": value, "unit": unit, "recorded_by": actor}


# --------------------------------------------------------------------------
# instability (ADR-0028 point 2)
# --------------------------------------------------------------------------

_REVERT_RE = re.compile(r"\brevert", re.IGNORECASE)
_FIX_RE = re.compile(r"\b(?:hotfix|fix(?:es|ed|ing)?)\b", re.IGNORECASE)


def classify_subject(subject: str) -> str | None:
    """`revert` | `fix` | None by the commit subject (a revert is never also counted as a fix)."""
    if _REVERT_RE.search(subject):
        return "revert"
    if _FIX_RE.search(subject):
        return "fix"
    return None


def _last_merge_sha(project_id: int) -> str | None:
    """Merge commit from the latest `retro measure` of the project (audit payload)."""
    with transaction() as conn:
        row = conn.execute(
            "SELECT payload_json FROM audit_log WHERE action = 'retro.measure' "
            "AND target_type = 'project' AND target_id = ? ORDER BY id DESC LIMIT 1",
            (project_id,)).fetchone()
    if not row:
        return None
    try:
        return str(json.loads(row[0] or "{}").get("merge_commit") or "") or None
    except (ValueError, TypeError):
        return None


def instability(
    *, slug: str, milestone: str, repo_path: str | None = None,
    merge_commit: str | None = None, fetch: bool = True,
) -> dict[str, Any]:
    """Reverty a opravné commity nad soubory vítěze po merge (T+7 / T+30, ADR-0028 bod 2).

    - Soubory vítěze = `git diff --name-only <merge>^1 <merge>` bez souborů nástroje.
    - Počítají se commity (bez merge commitů) po merge commitu, které se dotýkají těchto
      souborů a vznikly do `milestone` dnů od merge: `reverts` = předmět obsahuje „revert“,
      `fix_commits` = předmět obsahuje fix / fixes / hotfix (revert se nepočítá dvakrát).
    - Merge commit se bere z posledního `retro measure`, nebo z `--merge-commit`.
    """
    if milestone not in INSTABILITY_MILESTONES:
        raise ValueError(f"milestone musí být jedno z {INSTABILITY_MILESTONES}")
    with transaction() as conn:
        _ensure_outcomes_table(conn)
        project = _load_project(conn, slug)
        project_id = int(project["id"])
    repo = _resolve_repo(project, repo_path)
    if fetch and "origin" in _git(repo, "remote", check=False).split():
        _git(repo, "fetch", "origin", "--prune")
    sha_in = merge_commit or _last_merge_sha(project_id)
    if not sha_in:
        raise ValueError("Chybí merge commit: nejdřív `pflanzer retro measure` "
                         "nebo zadej `--merge-commit <sha>`.")
    merge_sha = _rev(repo, sha_in)
    if not merge_sha:
        raise ValueError(f"Merge commit `{sha_in}` v {repo} neexistuje (fetch proběhl?).")

    changed = [f for f in _git(repo, "diff", "--name-only", "--no-renames",
                               f"{merge_sha}^1", merge_sha).splitlines()
               if f.strip() and not is_method_file(f)]
    merge_dt = _parse_ts(_git(repo, "log", "-1", "--format=%cI", merge_sha))
    until = (merge_dt + timedelta(days=MILESTONE_DAYS[milestone])).isoformat() if merge_dt else None
    head = "HEAD"
    if _rev(repo, "origin/HEAD") and subprocess.run(
            ["git", "merge-base", "--is-ancestor", merge_sha, "origin/HEAD"],
            cwd=repo, capture_output=True).returncode == 0:
        head = "origin/HEAD"

    commits: dict[str, str] = {}
    for i in range(0, len(changed), 400):  # keep the argument list short
        args = ["log", "--no-merges", "--format=%H%x09%s", f"{merge_sha}..{head}"]
        if until:
            args.append(f"--until={until}")
        out = _git(repo, *args, "--", *changed[i:i + 400])
        for line in out.splitlines():
            sha, _t, subject = line.partition("\t")
            commits[sha] = subject
    kinds = {sha: classify_subject(subj) for sha, subj in commits.items()}
    reverts = sum(1 for k in kinds.values() if k == "revert")
    fixes = sum(1 for k in kinds.values() if k == "fix")

    actor = current_actor()
    evidence = f"commit:{merge_sha}"
    note = (f"po merge {merge_sha[:10]}, do {MILESTONE_DAYS[milestone]} dní, "
            f"nad {len(changed)} soubory vítěze")
    with transaction() as conn:
        conn.execute("DELETE FROM outcomes WHERE project_id = ? AND milestone = ? "
                     "AND metric IN ('reverts', 'fix_commits')", (project_id, milestone))
        for metric, value in (("reverts", reverts), ("fix_commits", fixes)):
            conn.execute(
                "INSERT INTO outcomes (project_id, milestone, metric, value, unit, "
                "evidence_url, notes, recorded_by) VALUES (?, ?, ?, ?, 'commits', ?, ?, ?)",
                (project_id, milestone, metric, float(value), evidence, note, actor))
        audit(conn, action="retro.instability", target_type="project", target_id=project_id,
              payload={"slug": slug, "milestone": milestone, "reverts": reverts,
                       "fix_commits": fixes, "merge_commit": merge_sha})
    return {"slug": slug, "milestone": milestone, "merge_commit": merge_sha, "repo": str(repo),
            "files": len(changed), "reverts": reverts, "fix_commits": fixes,
            "commits": [{"sha": sha[:10], "subject": subj, "kind": kinds[sha]}
                        for sha, subj in commits.items() if kinds[sha]]}


def _project_killed(project: dict[str, Any]) -> bool:
    return str(project.get("status") or "") == "killed"


def lessons(slug: str) -> list[dict[str, Any]]:
    """Poučení projektu (audit `retro.lesson`), od nejstaršího."""
    with transaction() as conn:
        pid = int(_load_project(conn, slug)["id"])
        rows = conn.execute(
            "SELECT actor, payload_json, ts FROM audit_log WHERE action = 'retro.lesson' "
            "AND target_type = 'project' AND target_id = ? ORDER BY id", (pid,)).fetchall()
    out: list[dict[str, Any]] = []
    for i, r in enumerate(rows, 1):
        try:
            payload = json.loads(r[1] or "{}")
        except (ValueError, TypeError):
            payload = {}
        out.append({"n": payload.get("n", i), "text": payload.get("text", ""),
                    "by": payload.get("by") or r[0], "at": r[2]})
    return out


def killed_notice(slug: str, what: str) -> dict[str, Any] | None:
    """U zabitého projektu vysvětlení místo chyby (None, když projekt Kill není)."""
    with transaction() as conn:
        if not _project_killed(_load_project(conn, slug)):
            return None
    ls = lessons(slug)
    lines = [f"Projekt {slug} skončil Kill — {what}, protože do produkce nic nešlo."]
    lines += [f"Poučení: {x['text']} — {x['by']}" for x in ls] or ["Poučení zatím není zapsané."]
    nxt = (f"`pflanzer retro lesson --slug {slug} --text \"…\"`" if not ls
           else "vezmi poučení do zadání dalšího Kickoffu (`/pm start`)")
    return {"slug": slug, "killed": True, "lessons": ls, "lines": lines, "next_step": nxt}


def lesson(*, slug: str, text: str, by: str | None = None) -> dict[str, Any]:
    """Zapiš poučení (hlavně po Kill): do DB (audit `retro.lesson`) a do decision logu v cwd."""
    text = (text or "").strip()
    if not text:
        raise ValueError("Chybí --text: jedna věta, co jsme se dozvěděli "
                         "(o problému, o uživatelích, o zadání).")
    who = (by or "").strip()
    with transaction() as conn:
        project = _load_project(conn, slug)
        pid = int(project["id"])
        if not who:
            actor = current_actor()
            who = actor if actor and actor != "unknown" else (
                str(project.get("decider_name") or "").strip() or "neuvedeno (--by JMÉNO)")
        n = int(conn.execute(
            "SELECT COUNT(*) FROM audit_log WHERE action = 'retro.lesson' "
            "AND target_type = 'project' AND target_id = ?", (pid,)).fetchone()[0]) + 1
        audit(conn, action="retro.lesson", target_type="project", target_id=pid,
              payload={"slug": slug, "n": n, "text": text, "by": who})
    from tool.cli.session_2 import SESSIONS_DIR, append_lesson_to_log

    section = f"### Poučení\n\n- {text} — {who}\n"
    repo_log = append_lesson_to_log(slug, text, who)
    summary = SESSIONS_DIR / slug / "_session_2_summary.md"
    if summary.is_file():
        try:
            with summary.open("a", encoding="utf-8") as fh:
                fh.write(f"\n{section}" if n == 1 else f"- {text} — {who}\n")
        except OSError:
            pass
    return {"slug": slug, "lesson_id": n, "text": text, "by": who,
            "killed": _project_killed(project), "decision_log_repo": repo_log}


# --------------------------------------------------------------------------
# report
# --------------------------------------------------------------------------


def _fmt_value(value: Any, unit: str | None) -> str:
    if value is None:
        return "—"
    v = float(value)
    txt = f"{int(v)}" if v.is_integer() else f"{v:.1f}"
    if unit == "%":
        return f"{txt} %"
    return f"{txt} {unit}" if unit else txt


def _md_cell(text: Any) -> str:
    return str(text or "—").replace("|", "\\|").replace("\n", " ")


def ai_stand_in_share(project: dict[str, Any]) -> dict[str, Any]:
    """Podíl kroků cesty, za které stála AI náhrada (ADR-0023), z `path_owners_json`."""
    try:
        owners = json.loads(project.get("path_owners_json") or "{}")
    except (json.JSONDecodeError, TypeError):
        owners = {}
    steps = [k for k in STEP_NAMES if str(owners.get(k) or "").strip()]
    # AI náhrada = vlastník „AI:…“ v Kickoffu, nebo skutečný `--ai` podpis okna (stejně jako SHIP.md)
    signed_ai: set[str] = set()
    if project.get("slug"):
        from tool.cli._compat import ai_stand_in_steps
        signed_ai = ai_stand_in_steps(str(project["slug"]))
    ai = [k for k in steps if is_ai_owner(owners.get(k)) or k in signed_ai]
    pct = round(len(ai) / len(steps) * 100) if steps else None
    return {"ai_steps": ai, "total_steps": len(steps), "pct": pct,
            "names": [STEP_NAMES[k] for k in ai]}


def _ai_stand_in_text(info: dict[str, Any]) -> str:
    if not info["total_steps"]:
        return "kroky cesty nejsou v Kickoffu vyplněné"
    if not info["ai_steps"]:
        return f"0 z {count(info['total_steps'], 'kroku', 'kroků', 'kroků')} — všude člověk"
    return (f"{info['pct']} % ({len(info['ai_steps'])} z "
            f"{count(info['total_steps'], 'kroku', 'kroků', 'kroků')}: "
            f"{', '.join(info['names'])})")


def _primary_metric(project: dict[str, Any], latest: dict[tuple[str, str], dict[str, Any]]
                    ) -> dict[str, Any]:
    """Metrika úspěchu z Kickoffu + poslední změřená hodnota (T+90, jinak T+30)."""
    text = str(project.get("primary_lagging_metric") or "").strip()
    if text.lower() in EMPTY_MARKERS or re.search(r"doplnit|nezad[aá]n", text, re.I):
        text = ""
    reading = None
    for key in (("t90", "t90_lagging_metric"), ("t30", "t30_leading_metric")):
        r = latest.get(key)
        if r and r["value"] is not None:
            reading = {"milestone": key[0], "metric": key[1], "value": r["value"],
                       "unit": r["unit"]}
            break
    if reading is None:
        for (ms, metric), r in latest.items():
            if PROJECT_METRIC_RE.match(metric) and r["value"] is not None and ms in MILESTONE_LABELS:
                reading = {"milestone": ms, "metric": metric, "value": r["value"],
                           "unit": r["unit"]}
                break
    return {"text": text, "reading": reading}


def _primary_line(primary: dict[str, Any]) -> str:
    text = primary["text"] or "není v Kickoffu zadaná"
    r = primary["reading"]
    measured = (f"{_fmt_value(r['value'], r['unit'])} ({MILESTONE_LABELS[r['milestone']]})"
                if r else "zatím neměřeno")
    return f"Metrika: {text} — změřeno: {measured}"


def _build_metrics(project_id: int) -> dict[str, Any]:
    """Metriky Buildu pro report po Kill: varianty, hlasy jádra, feedback, critical."""
    with transaction() as conn:
        variants = [{"variant": r[0], "builder": r[1], "score": round(float(r[2] or 0), 2)}
                    for r in conn.execute(
            "SELECT v.name, v.builder, v.preference_score FROM variants v "
            "JOIN sessions s ON s.id = v.session_id WHERE s.project_id = ? AND s.type = 1 "
            "ORDER BY v.name", (project_id,)).fetchall()]
        fb = conn.execute(
            "SELECT COUNT(*), SUM(CASE WHEN f.severity = 'critical' THEN 1 ELSE 0 END) "
            "FROM feedback f JOIN variants v ON v.id = f.variant_id "
            "JOIN sessions s ON s.id = v.session_id WHERE s.project_id = ?",
            (project_id,)).fetchone()
    return {"variants": variants, "feedback": int(fb[0] or 0), "critical": int(fb[1] or 0)}


def _tokens_text(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}".replace(".", ",") + " M tokenů"
    if n >= 1_000:
        return f"{round(n / 1_000)} tis. tokenů"
    return f"{n} tokenů"


def _usd_czk_rate() -> float | None:
    """Kurz USD→Kč jen z `PFLANZER_USD_CZK` (nic si nevymýšlíme); jinak None."""
    import os
    try:
        rate = float(os.environ.get("PFLANZER_USD_CZK", "").replace(",", "."))
    except ValueError:
        return None
    return rate if rate > 0 else None


def leadership_numbers(slug: str) -> dict[str, Any]:
    """4 čísla pro vedení na jednom místě (retro report, `pflanzer report`).

    days-to-prod (cíl ≤ 14), % LOC vítěze, které přežilo (údaj bez cíle, ADR-0028), AI náklad na Go
    (tokeny + odhad USD/Kč z `ai_usage`) a podíl kroků se zástupcem AI (ADR-0023).
    Co není změřené, má `None` — nikdy nic neodhadujeme.
    """
    with transaction() as conn:
        project = _load_project(conn, slug)
        pid = int(project["id"])
        ship = {r[0]: r[1] for r in conn.execute(
            "SELECT metric, value FROM outcomes WHERE project_id = ? AND milestone = 'ship' "
            "AND metric IN ('days_to_prod', 'loc_reused_pct') AND value IS NOT NULL "
            "ORDER BY recorded_at, id", (pid,)).fetchall()}
        usage = conn.execute(
            "SELECT COUNT(*), COALESCE(SUM(input_tokens + output_tokens), 0), "
            "SUM(est_usd) FROM ai_usage WHERE project_id = ?", (pid,)).fetchone()
        throwaway = is_throwaway(conn, project)
    days = ship.get("days_to_prod")
    reuse = ship.get("loc_reused_pct")
    rows, tokens, usd = int(usage[0] or 0), int(usage[1] or 0), usage[2]
    rate = _usd_czk_rate()
    share = ai_stand_in_share(project)
    return {
        "days_to_prod": {"value": days, "target": TARGET_DAYS_TO_PROD,
                         "ok": None if days is None else days <= TARGET_DAYS_TO_PROD},
        "loc_survival_pct": {"value": reuse},  # údaj bez cíle (ADR-0028)
        "ai_cost": {"measured": bool(rows), "tokens": tokens if rows else None,
                    "usd": None if usd is None else round(float(usd), 2),
                    "czk": (round(float(usd) * rate) if usd is not None and rate else None)},
        "ai_share": {"pct": share["pct"], "ai_steps": share["ai_steps"],
                     "total_steps": share["total_steps"], "names": share["names"]},
        "throwaway": throwaway,
        "measured": days is not None or reuse is not None,
    }


def leadership_ai_cost_text(cost: dict[str, Any]) -> str:
    """„1,2 M tokenů, odhad ≈ $4.20 (≈ 96 Kč)“ / „tokeny změřené, cena neznámá“ / „neměřeno“."""
    if not cost["measured"]:
        return "neměřeno"
    txt = _tokens_text(int(cost["tokens"] or 0))
    if cost["usd"] is None:
        return txt + ", cena nenastavená (ceník v tool/templates/README-ai-usage.md)"
    txt += f", odhad ≈ ${cost['usd']:.2f}"
    if cost["czk"] is not None:
        txt += f" (≈ {cost['czk']} Kč)"
    return txt


def leadership_lines(nums: dict[str, Any]) -> list[str]:
    """Čtyři řádky „Název: hodnota — cíl“ (stejné pro retro report i `pflanzer report`)."""
    d, r = nums["days_to_prod"], nums["loc_survival_pct"]
    mark = {True: "cíl splněn", False: "pod cílem", None: ""}
    days = (f"{_fmt_value(d['value'], 'dní')} (cíl ≤ {d['target']}) — {mark[d['ok']]}"
            if d["value"] is not None else f"neměřeno (cíl ≤ {d['target']} dní)")
    loc = (f"{_fmt_value(r['value'], '%')} (údaj bez cíle)"
           if r["value"] is not None else "neměřeno")
    s = nums["ai_share"]
    if not s["total_steps"]:
        share = "kroky cesty nejsou v Kickoffu vyplněné"
    else:
        share = (f"{s['pct']} % ({len(s['ai_steps'])} z "
                 f"{count(s['total_steps'], 'kroku', 'kroků', 'kroků')} cesty)")
    return [f"Dny do produkce (Go → merge): {days}",
            f"Kód vítěze, který přežil: {loc}",
            f"AI náklad na Go: {leadership_ai_cost_text(nums['ai_cost'])}",
            f"Podíl kroků se zástupcem AI (ADR-0023): {share}"]


def leadership_block_md(slug: str) -> str:
    """Blok „Pro vedení: 4 čísla“ na začátek retro reportu."""
    lines = leadership_lines(leadership_numbers(slug))
    return "## Pro vedení: 4 čísla\n\n" + "\n".join(f"- {x}" for x in lines) + "\n"


def build_report(slug: str) -> dict[str, Any]:
    with transaction() as conn:
        _ensure_outcomes_table(conn)
        project = _load_project(conn, slug)
        project_id = int(project["id"])
        go_dt, go_source = _go_date(conn, project_id)
        rows = [dict(r) for r in conn.execute(
            "SELECT milestone, metric, value, unit, evidence_url, notes, "
            "recorded_by, recorded_at FROM outcomes WHERE project_id = ? "
            "ORDER BY recorded_at, id", (project_id,),
        ).fetchall()]

    latest: dict[tuple[str, str], dict[str, Any]] = {}
    for r in rows:
        latest[(r["milestone"], r["metric"])] = r

    def check(metric: str, ok_fn, target_txt: str) -> dict[str, Any]:
        r = latest.get(("ship", metric))
        if not r or r["value"] is None:
            return {"metric": metric, "value": None, "target": target_txt,
                    "status": "missing"}
        return {"metric": metric, "value": r["value"], "unit": r["unit"],
                "target": target_txt, "status": "ok" if ok_fn(r["value"]) else "flag"}

    checks = [
        check("loc_reused_pct", lambda v: True, "bez cíle"),
        check("days_to_prod", lambda v: v <= TARGET_DAYS_TO_PROD,
              f"<= {TARGET_DAYS_TO_PROD} dní"),
    ]

    today = date.today()
    milestones = []
    for m in MILESTONES:
        due = (local_date(go_dt) + timedelta(days=MILESTONE_DAYS[m])) if go_dt else None
        has_rows = any(r["milestone"] == m for r in rows)
        if has_rows:
            state = "recorded"
        elif due and due < today:
            state = "overdue"
        else:
            state = "pending"
        milestones.append({"milestone": m, "due": due.isoformat() if due else None,
                           "state": state})

    killed = _project_killed(project)
    with transaction() as conn:
        throwaway = is_throwaway(conn, project)
    return {"throwaway": throwaway, "project": project, "go_dt": go_dt, "go_source": go_source,
            "rows": rows, "checks": checks, "milestones": milestones,
            "primary": _primary_metric(project, latest),
            "ai_stand_ins": ai_stand_in_share(project),
            "killed": killed,
            "lessons": lessons(slug) if killed else [],
            "build_metrics": _build_metrics(int(project["id"])) if killed else None}


def render_killed_report_md(slug: str, data: dict[str, Any]) -> str:
    """Retro po Kill: poučení + metriky Buildu. Žádné T+7..90 readouty ani připomínky."""
    p = data["project"]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    bm = data["build_metrics"] or {"variants": [], "feedback": 0, "critical": 0}
    if data["lessons"]:
        lessons_md = "\n".join(f"{x['n']}. {x['text']} — {x['by']}" for x in data["lessons"])
    else:
        lessons_md = (f"_Zatím žádné._ Zapiš: `pflanzer retro lesson --slug {slug} "
                      "--text \"co jsme se dozvěděli\"`")
    var_rows = "\n".join(f"| {v['variant']} | `{v['builder']}` | {v['score']:.2f} |"
                         for v in bm["variants"]) or "| — | — | — |"
    return f"""{BRAND_LINE}

# Retro po Kill — {p['name']}

> Slug: `{p['slug']}` · Vygenerováno: {now} · Stav projektu: `killed`
> Projekt skončil Kill: do produkce nic nešlo, takže se neměří přežití kódu
> a nejsou žádná čtení ani připomínky po Shipu.

## Poučení

{lessons_md}

## Metriky Buildu

| Varianta | Builder | Hlasy jádra (0–1) |
|----------|---------|-------------------|
{var_rows}

- Feedback celkem: {bm['feedback']}, z toho kritických: {bm['critical']}

---

*Další pilot: vezmi poučení do zadání nového Kickoffu (`/pm start`).*
"""


def render_throwaway_report_md(slug: str, data: dict[str, Any]) -> str:
    """Retro throwaway dema: jen metrika/kill v termínu, bez přežití LOC a T+30/60/90."""
    p = data["project"]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    _proj, _start, _src, items = _reminder_items(slug, None) if data["go_dt"] else (p, None, "", [])
    due = items[0] if items else None
    measured = [r for r in data["rows"] if r["milestone"] != "ship"]
    rows_md = "\n".join(f"- `{r['metric']}` = {_fmt_value(r['value'], r['unit'])}"
                        f" ({_md_cell(r['evidence_url'])})" for r in measured) or "_Zatím bez dat._"
    due_md = (f"{due['due'].isoformat()} — {due['deliverable']}\n  Zápis: `{due['record_cmd']}`"
              if due else "_Termín se určí podle data Rozhodnutí (Go)._")
    return f"""{BRAND_LINE}

# Retro (throwaway demo) — {p['name']}

> Slug: `{p['slug']}` · Vygenerováno: {now} · Stav projektu: `{p['status']}`
> Throwaway kód nejde do produkce, proto se neměří přežití kódu (LOC)
> ani čtení T+30/60/90. Měří se jen metrika dema v jejím termínu.

**{_primary_line(data['primary'])}**

## Metrika dema

{due_md}

## Zapsané hodnoty

{rows_md}
"""


def _latest_ship(rows: list[dict[str, Any]], milestone: str = "ship") -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for r in rows:
        if r["milestone"] == milestone:
            out[r["metric"]] = r
    return out


def _h(value: Any) -> str:
    return "—" if value is None else _fmt_value(value, "h")


def review_segments_md(rows: list[dict[str, Any]], slug: str) -> str:
    """Úseky review vedle základny repa; bez základny se nic neporovnává (ADR-0028)."""
    ship = _latest_ship(rows)
    base = {m: r["value"] for m, r in ship.items() if m.startswith("baseline_")
            and r["value"] is not None}
    marker = ship.get("baseline_open_to_merge_h")
    lines = ["## Úseky review a základna repa", ""]
    if base:
        n = int(base.get("baseline_pr_count") or 0)
        lines.append(f"Základna repa: medián z {n} PR mergnutých za posledních {BASELINE_DAYS} dní. "
                     "Je to historie téhož repa, ne kontrolní skupina.")
        if "baseline_after_go" in base:
            lines.append("⚠ Základna byla změřena až po Go, takže nesplňuje pre-registraci (ADR-0013).")
    elif marker is not None:
        lines.append(f"Základna není: {_md_cell(marker['notes']).removeprefix('základna není: ')}. "
                     "Úseky se neporovnávají.")
    else:
        lines.append(f"Základna zatím není změřená: `pflanzer retro baseline --slug {slug}`.")
    seg = {m: ship[m]["value"] for m in SEGMENT_METRICS if m in ship and ship[m]["value"] is not None}
    if not seg:
        lines += ["", "_Úseky zatím neměřeno._ "
                  f"`pflanzer retro measure --slug {slug} --pr-url <URL PR>`"]
    else:
        def cmp(metric: str | None) -> str:
            v = base.get(metric) if metric else None
            return f"medián {_fmt_value(v, 'h')}" if v is not None else "—"
        table = [("Go → PR otevřen", "go_to_pr_open_h", None),
                 ("PR otevřen → první review", "pr_open_to_first_review_h",
                  "baseline_open_to_first_review_h"),
                 ("První review → merge", "first_review_to_merge_h", None),
                 ("PR otevřen → merge (celkem)", "pr_open_to_merge_h", "baseline_open_to_merge_h")]
        lines += ["", "| Úsek | Naměřeno | Základna repa |", "|------|----------|---------------|"]
        lines += [f"| {name} | {_h(seg.get(m))} | {cmp(b)} |" for name, m, b in table]
    lines += ["", "Zrychlení se v reportu nikdy neuvádí jako dojem týmu, jen jako naměřené "
                  "úseky vedle základny.", ""]
    return "\n".join(lines)


def instability_md(rows: list[dict[str, Any]], slug: str) -> str:
    """Reverty a opravné commity po merge na T+7 / T+30 (vedle dnů, ne místo nich)."""
    lines = ["## Nestabilita po merge", ""]
    for m in INSTABILITY_MILESTONES:
        got = _latest_ship(rows, m)
        if "reverts" in got and "fix_commits" in got:
            lines.append(f"- {MILESTONE_LABELS[m]}: reverty {_fmt_value(got['reverts']['value'], None)}, "
                         f"opravné commity {_fmt_value(got['fix_commits']['value'], None)} "
                         f"({_md_cell(got['reverts']['notes'])})")
        else:
            lines.append(f"- {MILESTONE_LABELS[m]}: neměřeno — "
                         f"`pflanzer retro instability --slug {slug} --milestone {m}`")
    return "\n".join(lines) + "\n"


def render_report_md(slug: str, data: dict[str, Any] | None = None) -> str:
    data = data or build_report(slug)
    if data.get("killed"):
        return render_killed_report_md(slug, data)
    if data.get("throwaway"):
        return render_throwaway_report_md(slug, data)
    p = data["project"]
    go_dt = data["go_dt"]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    status_icon = {"ok": "✅ splněno", "flag": "⚠ FLAG — pod cílem",
                   "missing": "⏳ nezměřeno"}
    status_icon_info = {"ok": "změřeno (údaj)", "flag": "změřeno (údaj)", "missing": "⏳ nezměřeno"}

    check_rows = "\n".join(
        f"| `{c['metric']}` | {_fmt_value(c['value'], c.get('unit'))} | "
        f"{c['target']} | "
        f"{(status_icon_info if c['target'] == 'bez cíle' else status_icon)[c['status']]} |"
        for c in data["checks"]
    )

    sections = []
    for m in ("ship", *MILESTONES):
        ms_rows = [r for r in data["rows"] if r["milestone"] == m]
        header = f"### {MILESTONE_LABELS[m]}"
        if m != "ship":
            info = next(x for x in data["milestones"] if x["milestone"] == m)
            state_txt = {"recorded": "zapsáno", "overdue": "⏰ po termínu, readout chybí",
                         "pending": "čeká"}[info["state"]]
            header += f" — termín {info['due'] or '?'} · {state_txt}"
        if ms_rows:
            body = "| Metrika | Hodnota | Evidence | Poznámka | Zapsal | Kdy |\n" \
                   "|---------|---------|----------|----------|--------|-----|\n"
            body += "\n".join(
                f"| `{r['metric']}` | {_fmt_value(r['value'], r['unit'])} | "
                f"{_md_cell(r['evidence_url'])} | {_md_cell(r['notes'])} | "
                f"{_md_cell(r['recorded_by'])} | {_md_cell(r['recorded_at'])} |"
                for r in ms_rows
            )
        else:
            hint = (f"`pflanzer retro measure --slug {slug} --pr-url <URL>`"
                    if m == "ship" else
                    f"`pflanzer retro record --slug {slug} --milestone {m} "
                    f"--metric {next(iter(RECOMMENDED_METRICS[m]))} --value <N>`")
            body = f"_Zatím bez dat._ Zapiš: {hint}"
        sections.append(f"{header}\n\n{body}")

    sections_md = "\n\n".join(sections)
    review_md = review_segments_md(data["rows"], slug)
    instability_block = instability_md(data["rows"], slug)
    flags = [c for c in data["checks"] if c["status"] == "flag"]
    flag_note = ""
    if flags:
        flag_note = (
            "\n> ⚠ **Cíl metody nesplněn** ("
            + ", ".join(f"`{c['metric']}`" for c in flags)
            + "). Doplň do T+30 retro příčinu (rework v review? scope změna? "
              "chybějící acceptance criteria?) — je to vstup pro kalibraci "
              "metody, ne selhání týmu.\n"
        )

    return f"""{BRAND_LINE}

# Retro — {p['name']}

> Slug: `{p['slug']}` · Vygenerováno: {now} · Stav projektu: `{p['status']}`
> Rozhodnutí (Go): {local_date(go_dt).isoformat() if go_dt else '_neznámé_'} ({data['go_source']})
> Postup měření: `docs/methodology/07-handoff-do-vyvoje.md`, kapitola Retro.

{leadership_block_md(slug)}
**{_primary_line(data['primary'])}**

Podíl kroků s AI náhradou: {_ai_stand_in_text(data['ai_stand_ins'])}

## Cíle a údaje metody

| Metrika | Hodnota | Cíl | Stav |
|---------|---------|-----|------|
{check_rows}
{flag_note}
{review_md}
{instability_block}
## Outcomes per milník

{sections_md}

## Jak čísla vznikla

- `loc_reused_pct` = řádky přidané winner branchí, které v merge commitu
  zůstaly beze změny (heuristika `added − removed` po cestách, které winner
  změnil; konzervativní dolní odhad — viz `pflanzer retro measure --help`).
  Je to údaj bez cíle (ADR-0028): oprava chyby při review snižuje číslo právem.
- `baseline_*` = medián z historie téhož repa (`pflanzer retro baseline`); úseky review
  v hodinách z `measure --pr-url`; `reverts` / `fix_commits` z `pflanzer retro instability`.
- U projektu přes víc repozitářů je `loc_*` / `winner_commits` / `days_to_prod` bez přípony
  součet (dny: poslední merge) za **změřená** repa (poznámka řádku říká, která) a řádky
  `metrika@role` jsou per repo.
- `days_to_prod` = kalendářní dny od Rozhodnutí (Go) do merge commitu (proxy
  pro první prod deploy).
- T+7/30/60/90 = ruční readouty (`pflanzer retro record`), evidence URL povinně
  tam, kde existuje (issue, dashboard, retro zápis).

---

*Zdroj dat: tabulka `outcomes` v DB toolu (`pflanzer db`) · další readout
zapiš přes `/pm retro {p['slug']}` nebo v terminálu `pflanzer retro record --slug {p['slug']}
--milestone T+30 --metric <metrika> --value <N>`; po merge změř kód vítěze přes
`pflanzer retro measure --slug {p['slug']} --pr-url <URL PR>` (nebo `--merge-commit <sha>`).*
"""


def write_report(slug: str, out: str | None = None) -> tuple[Path, dict[str, Any], str]:
    data = build_report(slug)
    md = render_report_md(slug, data)
    path = Path(out).expanduser() if out else RETRO_DIR / f"{slug}-retro.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(md, encoding="utf-8")
    with transaction() as conn:
        audit(conn, action="retro.report", target_type="project",
              target_id=int(data["project"]["id"]),
              payload={"slug": slug, "path": _display(path)})
    return path, data, md


# --------------------------------------------------------------------------
# reminders
# --------------------------------------------------------------------------


def _display(path: Path) -> str:
    """Absolutní cesta (pod $HOME jako ~/…), aby šla zkopírovat; kam se zapisuje, je vidět."""
    return tilde(Path(path).expanduser().resolve())


def _charter_owner_line(slug: str, milestone: str) -> str | None:
    """Parse `- **T+7**: ...` from data/charters/<slug>.md (charter.py format)."""
    path = CHARTER_DIR / f"{slug}.md"
    if not path.exists():
        return None
    label = MILESTONE_LABELS[milestone].replace("+", r"\+")
    m = re.search(rf"^- \*\*{label}\*\*:\s*(.+)$", path.read_text(encoding="utf-8"),
                  re.MULTILINE)
    return m.group(1).strip() if m else None


def _owners(slug: str, project: dict[str, Any]) -> dict[str, tuple[str, str]]:
    """milestone → (owner/commitment text, source).

    Source order: projects.reinforcement_tN (charter.py persists them) →
    data/charters/<slug>.md line → methodology default owner.
    """
    result: dict[str, tuple[str, str]] = {}
    for m in MILESTONES:
        text = (project.get(f"reinforcement_{m}") or "").strip()
        source = "charter (DB)"
        if text.lower() in EMPTY_MARKERS:
            text = (_charter_owner_line(slug, m) or "").strip()
            source = "charter (MD)"
        if text.lower() in EMPTY_MARKERS:
            text, source = _default_owner(project, m), "kroky cesty z Kickoffu"
        result[m] = (text, source)
    return result


def _default_owner(project: dict[str, Any], milestone: str) -> str:
    """„Provoz (Karel) a Produkt (Eva)“ podle jmen z Kickoffu; bez jmen jen názvy kroků."""
    try:
        owners = json.loads(project.get("path_owners_json") or "{}")
    except (json.JSONDecodeError, TypeError):
        owners = {}
    parts = []
    for step in DEFAULT_OWNER_STEPS[milestone]:
        name = str(owners.get(step) or "").strip()
        parts.append(STEP_NAMES[step] + (f" ({name})" if name and not name.upper().startswith("AI")
                                         else ""))
    return " a ".join(parts)


def _ics_escape(text: str) -> str:
    return (text.replace("\\", "\\\\").replace(";", "\\;")
            .replace(",", "\\,").replace("\n", "\\n"))


def _ics_fold(line: str) -> str:
    """Fold content lines at 75 octets (RFC 5545 § 3.1)."""
    raw = line.encode("utf-8")
    if len(raw) <= 75:
        return line
    parts, current = [], b""
    for ch in line:
        enc = ch.encode("utf-8")
        limit = 75 if not parts else 74  # continuation lines start with a space
        if len(current) + len(enc) > limit:
            parts.append(current.decode("utf-8"))
            current = b""
        current += enc
    parts.append(current.decode("utf-8"))
    return "\r\n ".join(parts)


_HORIZON_RE = re.compile(
    r"(?i)\bdo\s+(\d{1,3})\s*(dn[ůu]|dn[íi]|dny|den|t[ýy]dn\w*|t\.)")


def metric_horizon_days(project: dict[str, Any]) -> tuple[int, str] | None:
    """Horizont metriky z Kickoffu („do 14 dnů“, „do 2 týdnů“) -> (dny, text metriky)."""
    for key in ("primary_lagging_metric", "leading_metric"):
        text = str(project.get(key) or "").strip()
        m = _HORIZON_RE.search(text)
        if m:
            n = int(m.group(1))
            days = n * 7 if m.group(2).lower().startswith(("t", "týd")) else n
            if 0 < days <= 365:
                return days, text
    return None


_KILL_HORIZON_RE = re.compile(
    r"(?i)\b(?:po|do|za|během|behem)\s+(\d{1,3})\s*(dn[ůu]|dn[íi]|dny|den|t[ýy]dn\w*|měsíc\w*|mesic\w*)")


def kill_horizon_days(project: dict[str, Any]) -> tuple[int, str] | None:
    """Termín kill kritéria z Kickoffu („po 4 týdnech“, „do 30 dnů“) -> (dny, text kritéria)."""
    text = str(project.get("kill_criteria") or "").strip()
    m = _KILL_HORIZON_RE.search(text)
    if not m:
        return None
    n, unit = int(m.group(1)), m.group(2).lower()
    days = n * 7 if unit.startswith(("t", "týd")) else n * 30 if unit.startswith(("měs", "mes")) else n
    return (days, text) if 0 < days <= 365 else None


def _reminder_items(
    slug: str, from_date: str | None,
) -> tuple[dict[str, Any], date, str, list[dict[str, Any]]]:
    with transaction() as conn:
        project = _load_project(conn, slug)
        go_dt, _src = _go_date(conn, int(project["id"]))
    if from_date:
        start, start_source = date.fromisoformat(from_date), "--from"
    elif go_dt:
        start, start_source = local_date(go_dt), "Rozhodnutí (Go)"
    else:
        raise ValueError(
            "Datum Rozhodnutí (Go) v DB není. Zadej `--from YYYY-MM-DD`."
        )
    owners = _owners(slug, project)
    with transaction() as conn:
        throwaway = is_throwaway(conn, project)
    items = []
    for m in ([] if throwaway else MILESTONES):
        owner, source = owners[m]
        metrics = RECOMMENDED_METRICS[m]
        first_metric = next(iter(metrics))
        items.append({
            "milestone": m,
            "label": MILESTONE_LABELS[m],
            "due": start + timedelta(days=MILESTONE_DAYS[m]),
            "owner": owner,
            "owner_source": source,
            "deliverable": DEFAULT_DELIVERABLES[m],
            "metrics": list(metrics),
            "record_cmd": (f"pflanzer retro record --slug {slug} "
                           f"--milestone {m} --metric {first_metric} --value <N> "
                           f"--evidence <URL>"),
        })
    hz = metric_horizon_days(project)
    if hz and (throwaway or hz[0] not in MILESTONE_DAYS.values()):
        days, mtext = hz
        nearest = next((m for m in MILESTONES if MILESTONE_DAYS[m] >= days), MILESTONES[-1])
        # Měří se metrika projektu z Kickoffu (ne obecný rework z T+60).
        metrics = [f"t{days}_project_metric"]
        items.append({
            "milestone": f"t{days}",
            "label": f"Metrika z Kickoffu (T+{days}, zapíše se jako {MILESTONE_LABELS[nearest]})",
            "due": start + timedelta(days=days),
            "owner": owners[nearest][0],
            "owner_source": "horizont metriky z Kickoffu",
            "deliverable": f"Změřit metriku z Kickoffu (horizont {days} dní): {mtext}",
            "metrics": metrics,
            "record_cmd": (f"pflanzer retro record --slug {slug} "
                           f"--milestone {nearest} --metric {metrics[0]} --value <N> "
                           f"--evidence <URL>"),
        })
    kh = kill_horizon_days(project)
    if kh:
        days, ktext = kh
        nearest = next((m for m in MILESTONES if MILESTONE_DAYS[m] >= days), MILESTONES[-1])
        metric = f"t{days}_project_metric"
        items.append({
            "milestone": f"kill{days}",
            "label": f"Kill kritérium (T+{days}, zapíše se jako {MILESTONE_LABELS[nearest]})",
            "due": start + timedelta(days=days),
            "owner": owners["t30"][0] if "t30" in owners else owners[nearest][0],
            "owner_source": "kill kritérium z Kickoffu",
            "deliverable": (f"Vyhodnotit kill kritérium z Kickoffu („{ktext}“): "
                            "splněno -> Kill a poučení, jinak pokračovat"),
            "metrics": [metric],
            "record_cmd": (f"pflanzer retro record --slug {slug} "
                           f"--milestone {nearest} --metric {metric} --value <N> "
                           f"--evidence <URL>"),
        })
    if throwaway:
        # Demo: jedna připomínka — metrika/kill v jejím termínu (nejbližší), jinak za 14 dní.
        if items:
            items = [min(items, key=lambda it: it["due"])]
        else:
            items = [{
                "milestone": "demo14", "label": "Vyhodnocení dema",
                "due": start + timedelta(days=TARGET_DAYS_TO_PROD),
                "owner": owners["t30"][0], "owner_source": "throwaway demo",
                "deliverable": "Vyhodnotit metriku dema z Kickoffu: platí, nebo Kill",
                "metrics": ["demo_metric"],
                "record_cmd": (f"pflanzer retro record --slug {slug} --milestone t7 "
                               f"--metric demo_metric --value <N> --evidence <URL>"),
            }]
    items.sort(key=lambda it: it["due"])
    return project, start, start_source, items


def render_reminders(slug: str, fmt: str, from_date: str | None = None) -> str:
    with transaction() as _conn:
        if _project_killed(_load_project(_conn, slug)):
            raise ValueError(
                f"Projekt {slug} skončil Kill — T+7/30/60/90 připomínky nedávají smysl "
                f"(do produkce nic nešlo). Zapiš poučení: "
                f"`pflanzer retro lesson --slug {slug} --text \"…\"`.")
    project, start, start_source, items = _reminder_items(slug, from_date)
    name = project["name"]

    if fmt == "ics":
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Pflanzer Method//pflanzer.cz/method retro//CS",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            f"X-WR-CALNAME:{_ics_escape(f'Pflanzer retro — {slug}')}",
        ]
        for it in items:
            desc = (
                f"{BRAND_LINE}\n\nProjekt: {name} ({slug})\n"
                f"Kdo: {it['owner']}\n"
                f"Co udělat: {it['deliverable']}\n"
                f"Metriky: {', '.join(it['metrics'])}\n\n"
                f"Zápis: /pm retro {slug} nebo v terminálu\n{it['record_cmd']}"
            )
            due = it["due"]
            summary = f"Pflanzer {it['label']} readout — {slug}"
            lines += [
                "BEGIN:VEVENT",
                f"UID:{slug}-{it['milestone']}@pflanzer.cz",
                f"DTSTAMP:{stamp}",
                f"DTSTART;VALUE=DATE:{due.strftime('%Y%m%d')}",
                f"DTEND;VALUE=DATE:{(due + timedelta(days=1)).strftime('%Y%m%d')}",
                f"SUMMARY:{_ics_escape(summary)}",
                f"DESCRIPTION:{_ics_escape(desc)}",
                f"CATEGORIES:pflanzer,{slug}",
                "TRANSP:TRANSPARENT",
                "BEGIN:VALARM",
                "ACTION:DISPLAY",
                f"DESCRIPTION:{_ics_escape(summary)}",
                "TRIGGER:-PT15H",
                "END:VALARM",
                "END:VEVENT",
            ]
        lines.append("END:VCALENDAR")
        return "\r\n".join(_ics_fold(line) for line in lines) + "\r\n"

    if fmt == "md":
        out = [BRAND_LINE, "", f"# Připomínky — {name}", "",
               f"> Slug: `{slug}` · Od: {start.isoformat()} ({start_source})", ""]
        for it in items:
            out.append(
                f"- [ ] **{it['label']}** — {it['due'].isoformat()} · kdo: "
                f"{it['owner']} _({it['owner_source']})_  \n"
                f"  {it['deliverable']}. Metriky: "
                + ", ".join(f"`{m}`" for m in it["metrics"])
                + f"  \n  Zápis: `{it['record_cmd']}`"
            )
        return "\n".join(out) + "\n"

    if fmt == "gh-issues":
        label = f"pflanzer:{slug}"
        repo_flag = ""
        m = re.search(r"github\.com[:/]([\w.-]+)/([\w.-]+?)(?:\.git)?/?$",
                      project.get("target_repo_url") or "")
        if m:
            repo_flag = f" --repo {shlex.quote(f'{m.group(1)}/{m.group(2)}')}"
        out = [
            f"# {BRAND_LINE}",
            f"# Připomínky jako GitHub issues pro {slug} — příkazy se NESPOUŠTĚJÍ automaticky.",
            f"gh label create {shlex.quote(label)}{repo_flag} --color 5319e7 "
            f"--description {shlex.quote('Pflanzer Method outcome tracking')} --force",
        ]
        for it in items:
            title = f"[Pflanzer {it['label']} · {it['due'].isoformat()}] Readout — {name}"
            body = (
                f"{BRAND_LINE}\n\n**Termín:** {it['due'].isoformat()}\n"
                f"**Kdo:** {it['owner']}\n"
                f"**Co udělat:** {it['deliverable']}\n"
                f"**Metriky:** {', '.join(f'`{x}`' for x in it['metrics'])}\n\n"
                f"Zápis výsledku: `/pm retro {slug}` nebo v terminálu\n\n"
                f"```\n{it['record_cmd']}\n```\n"
            )
            out.append(
                f"gh issue create{repo_flag} --title {shlex.quote(title)} "
                f"--label {shlex.quote(label)} --body {shlex.quote(body)}"
            )
        return "\n".join(out) + "\n"

    raise ValueError(f"neznámý formát: {fmt}")


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def _metrics_help() -> str:
    lines = ["Doporučené názvy metrik:"]
    for m, metrics in RECOMMENDED_METRICS.items():
        for name, desc in metrics.items():
            lines.append(f"  {m:<4} {name:<28} {desc}")
    return "\n".join(lines)


SUBCOMMANDS = ("measure", "record", "report", "reminders", "lesson", "baseline", "instability")


def _usage_help(first: str | None) -> str:
    del first  # nikdy nedosazujeme zadané slovo (překlep) jako slug
    return "pflanzer retro report --slug <slug>   (další: baseline, measure, instability, record, reminders, lesson)"


def _baseline_text(b: dict[str, Any]) -> str:
    parts = []
    if b.get("baseline_open_to_merge_h") is not None:
        parts.append(f"PR → merge medián {_h(b['baseline_open_to_merge_h'])}")
    if b.get("baseline_open_to_first_review_h") is not None:
        parts.append(f"PR → první review medián {_h(b['baseline_open_to_first_review_h'])}")
    return ", ".join(parts) or "bez číselných hodnot"


def _segment_lines(seg: dict[str, float], base: dict[str, Any]) -> list[str]:
    """Úseky review pro výstup `measure`; základna vedle, když existuje (nikdy dojem)."""
    if not seg:
        return []
    def vs(metric: str, base_key: str) -> str:
        v = base.get(base_key)
        return (f" (základna repa: medián {_h(v)})" if v is not None else "")
    parts = []
    if "go_to_pr_open_h" in seg:
        parts.append(f"Go → PR otevřen {_h(seg['go_to_pr_open_h'])}")
    if "pr_open_to_first_review_h" in seg:
        parts.append("PR otevřen → první review " + _h(seg["pr_open_to_first_review_h"])
                     + vs("pr_open_to_first_review_h", "baseline_open_to_first_review_h"))
    if "first_review_to_merge_h" in seg:
        parts.append(f"první review → merge {_h(seg['first_review_to_merge_h'])}")
    lines = ["Úseky review: " + "; ".join(parts)] if parts else []
    if "pr_open_to_merge_h" in seg:
        lines.append(f"PR otevřen → merge celkem {_h(seg['pr_open_to_merge_h'])}"
                     + vs("pr_open_to_merge_h", "baseline_open_to_merge_h"))
    if not base.get("baseline_pr_count"):
        lines.append("Základna repa není, úseky se neporovnávají "
                     "(`pflanzer retro baseline --slug <slug>`).")
    return lines


def main() -> None:
    argv = sys.argv[1:]
    if not argv or argv[0] not in SUBCOMMANDS and argv[0] not in ("-h", "--help"):
        first = argv[0] if argv else None
        if first and not first.startswith("-"):
            near = did_you_mean(first, SUBCOMMANDS)
            msg = (f"Neznámý příkaz „{first}“. Myslel jste „{near}“?" if near else
                   f"Za `pflanzer retro` chybí, co se má udělat (zadáno jen „{first}“).")
        else:
            msg = "Za `pflanzer retro` chybí, co se má udělat."
        die(msg, _usage_help(first))
    p = CzechArgumentParser(description=__doc__.split("\n")[0], prog="pflanzer retro")
    sub = p.add_subparsers(dest="cmd", required=True, parser_class=CzechArgumentParser)

    p_measure = sub.add_parser(
        "measure", help="Změř %% LOC winneru v merge commitu + days-to-prod (milestone ship)",
        description=measure.__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_measure.add_argument("--slug", required=True)
    p_measure.add_argument("--pr-url", help="URL mergnutého PR (evidence; s `gh` i merge commit)")
    p_measure.add_argument("--merge-commit", help="SHA merge (nebo squash) commitu v target branchi")
    p_measure.add_argument("--base", help="Base ref pro fork point (default: <merge-commit>^1)")
    p_measure.add_argument("--repo-path", help="Lokální clone target repa (default: ~/.pflanzer/targets/<repo>)")
    p_measure.add_argument("--winner", help="Jméno winner varianty (default: stejné pravidlo jako SHIP.md)")
    p_measure.add_argument("--repo-pr", action="append", default=[], metavar="ROLE=URL",
                           help="Multi-repo: mergnuté PR sekundárního repa (opakovatelné)")
    p_measure.add_argument("--repo-merge", action="append", default=[], metavar="ROLE=SHA",
                           help="Multi-repo: merge commit sekundárního repa (opakovatelné)")
    p_measure.add_argument("--no-fetch", action="store_true", help="Nepouštět git fetch origin")

    p_base = sub.add_parser(
        "baseline", help="Základna repa: medián PR → merge a PR → první review (před Kickoffem)",
        description=baseline.__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_base.add_argument("--slug", required=True)
    p_base.add_argument("--repo", "--repo-path", dest="repo_path",
                        help="Lokální clone target repa (default: ~/.pflanzer/targets/<repo>)")

    p_inst = sub.add_parser(
        "instability", help="Reverty a opravné commity nad soubory vítěze po merge (T+7 / T+30)",
        description=instability.__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_inst.add_argument("--slug", required=True)
    p_inst.add_argument("--milestone", required=True, choices=INSTABILITY_MILESTONES)
    p_inst.add_argument("--repo", "--repo-path", dest="repo_path",
                        help="Lokální clone target repa (default: ~/.pflanzer/targets/<repo>)")
    p_inst.add_argument("--merge-commit", help="SHA merge commitu (default: z posledního `retro measure`)")
    p_inst.add_argument("--no-fetch", action="store_true", help="Nepouštět git fetch origin")

    p_record = sub.add_parser(
        "record", help="Ruční readout T+7/30/60/90",
        epilog=_metrics_help(), formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_record.add_argument("--slug", required=True)
    p_record.add_argument("--milestone", required=True, choices=MILESTONES)
    p_record.add_argument("--metric", required=True, help="viz doporučené názvy níže")
    p_record.add_argument("--value", required=True, type=float)
    p_record.add_argument("--unit")
    p_record.add_argument("--evidence", help="URL (issue list, dashboard, retro zápis)")
    p_record.add_argument("--notes")

    p_report = sub.add_parser("report", help="Retro report → <datová složka>/retro/<slug>-retro.md")
    p_report.add_argument("--slug", required=True)
    p_report.add_argument("--md", action="store_true", help="Vypiš markdown na stdout místo JSON")
    p_report.add_argument("--out", help="Jiná cesta výstupu (default <datová složka>/retro/<slug>-retro.md)")

    p_rem = sub.add_parser("reminders", help="Připomínky T+7/30/60/90 (ics | md | gh-issues)")
    p_rem.add_argument("--slug", required=True)
    p_rem.add_argument("--format", choices=["ics", "md", "gh-issues"], default="md")
    p_rem.add_argument("--from", dest="from_date", help="YYYY-MM-DD (default: datum Rozhodnutí (Go))")
    p_rem.add_argument("--out", help="Zapsat do souboru místo stdout")

    p_les = sub.add_parser("lesson", help="Zapiš poučení (hlavně po Kill)")
    p_les.add_argument("--slug", required=True)
    p_les.add_argument("--text", required=True, help="co jsme se dozvěděli (jedna věta)")
    p_les.add_argument("--by", default=None, help="kdo to říká (default: git user)")

    for sp in (p_measure, p_record, p_report, p_rem, p_les, p_base, p_inst):
        sp.add_argument("--json", action="store_true", help="Výstup jako JSON (pro skripty)")

    args = p.parse_args()
    examples = {
        "measure": "pflanzer retro measure --slug moje-appka --pr-url https://github.com/firma/repo/pull/12",
        "baseline": "pflanzer retro baseline --slug moje-appka --repo ~/cesta/k/repu",
        "instability": "pflanzer retro instability --slug moje-appka --milestone t7",
        "record": ("pflanzer retro record --slug moje-appka --milestone t7 --metric t7_bugs "
                   "--value 2 --evidence https://github.com/firma/repo/issues"),
        "report": "pflanzer retro report --slug moje-appka",
        "lesson": "pflanzer retro lesson --slug moje-appka --text \"uživatelé problém nemají\"",
        "reminders": "pflanzer retro reminders --slug moje-appka --format ics --out pripominky.ics",
    }
    try:
        if args.cmd in ("measure", "reminders"):
            what = {"measure": "není co měřit (žádný merge, žádný kód v produkci)",
                    "reminders": "připomínky T+7/30/60/90 nejsou potřeba"}[args.cmd]
            kn = killed_notice(args.slug, what)
            if kn:
                emit(kn, title=f"Retro po Kill: {args.slug}", lines=kn["lines"],
                     next_step=kn["next_step"], tips=tips(args.slug, "after_kill", {}),
                     as_json=getattr(args, "json", False))
                return
        if args.cmd == "baseline":
            out = baseline(slug=args.slug, repo_path=args.repo_path)
            b = out["baseline"] or {}
            if out["kept_existing"]:
                lines = [f"Základna je už uložená z doby před Go ({_baseline_text(b)}); {out['reason']}."]
            elif out["stored"]:
                lines = [f"Základna z posledních {BASELINE_DAYS} dní, "
                         f"{count(b['pr_count'], 'mergnuté PR', 'mergnuté PR', 'mergnutých PR')}:",
                         f"medián PR otevřen → merge: {_h(b['open_to_merge_h'])}",
                         "medián PR otevřen → první review: "
                         + (_h(b['open_to_first_review_h']) if b["open_to_first_review_h"] is not None
                            else "není (žádné PR s review)")]
            else:
                lines = [f"Základna není: {out['reason']}.",
                         "Nic číselného se neuložilo, výsledek pilotu se s repem nebude porovnávat."]
            warns = []
            if out["after_go"] and out["stored"]:
                warns.append("Základna se měří až po Go, takže nesplňuje pre-registraci (ADR-0013). "
                             "Zapsáno u ní.")
            emit(out, title=f"Retro: základna {args.slug}", lines=lines, warnings=warns,
                 next_step=f"`pflanzer retro measure --slug {args.slug} --pr-url <URL PR>`",
                 tips=tips(args.slug, "retro", {}), as_json=args.json)
            return
        if args.cmd == "instability":
            out = instability(slug=args.slug, milestone=args.milestone, repo_path=args.repo_path,
                              merge_commit=args.merge_commit, fetch=not args.no_fetch)
            lines = [f"{MILESTONE_LABELS[args.milestone]}: reverty {out['reverts']}, "
                     f"opravné commity {out['fix_commits']} "
                     f"(nad {count(out['files'], 'souborem', 'soubory', 'soubory')} vítěze po merge "
                     f"{out['merge_commit'][:10]})"]
            lines += [f"  {c['sha']} {c['kind']}: {c['subject']}" for c in out["commits"]]
            emit(out, title=f"Retro: nestabilita {args.slug}", lines=lines,
                 next_step=f"`pflanzer retro report --slug {args.slug}`",
                 tips=tips(args.slug, "retro", {}), as_json=args.json)
            return
        if args.cmd == "measure":
            with transaction() as _c:
                _proj = _load_project(_c, args.slug)
                _throw = is_throwaway(_c, _proj)
            if _throw:
                _p, _st, _src, _its = _reminder_items(args.slug, None)
                it = _its[0]
                emit({"slug": args.slug, "throwaway": True, "measured": False},
                     title=f"Retro: měření {args.slug} — throwaway",
                     lines=["Throwaway demo nejde do produkce, takže se neměří, kolik kódu "
                            "přežilo (LOC), ani čtení T+30/60/90.",
                            f"Změř jen metriku dema v jejím termínu ({it['due'].isoformat()}): "
                            f"{it['deliverable']}."],
                     next_step=f"`{it['record_cmd']}`",
                     tips=tips(args.slug, "retro", {}), as_json=args.json)
                return
            out = measure(slug=args.slug, pr_url=args.pr_url,
                          merge_commit=args.merge_commit, base=args.base,
                          repo_path=args.repo_path, winner=args.winner,
                          fetch=not args.no_fetch, repo_prs=args.repo_pr,
                          repo_merges=args.repo_merge)
            lines = [f"Varianta {out['winner']}: {out['loc_merged_unchanged']} z {out['loc_winner']} "
                     f"nových řádků zůstalo beze změny"
                     + (f" ({out['loc_reused_pct']:g} %, údaj bez cíle)"
                        if out["loc_reused_pct"] is not None else "")]
            if out["days_to_prod"] is not None:
                lines.append(f"Od Go do merge: "
                             f"{count(out['days_to_prod'], 'den', 'dny', 'dní')} "
                             f"(cíl ≤ {TARGET_DAYS_TO_PROD})")
            for r in out.get("per_repo") or []:
                lines.append(f"  repo {r['role']}: {r['loc_merged_unchanged']} z "
                             f"{r['loc_winner']} řádků beze změny"
                             + (f" ({r['loc_reused_pct']:g} %)"
                                if r["loc_reused_pct"] is not None else ""))
            if out["unmeasured_repos"]:
                lines.append("Měřeno jen " + ", ".join(out["measured_repos"]) + "; neměřeno: "
                             + "; ".join(f"{u['role']} ({u['reason']})"
                                         for u in out["unmeasured_repos"]))
            if out["ignored_files"]:
                n_ign = len(out["ignored_files"])
                lines.append(f"Nepočítám {count(n_ign, 'soubor', 'soubory', 'souborů')} "
                             "přidaných nástrojem (.gitignore, .pflanzer/…).")
            lines += _segment_lines(out["segments_h"], out["baseline"])
            warns = list(out["segment_warnings"])
            emit(out, title=f"Retro: měření {args.slug}", lines=lines, warnings=warns,
                 next_step=f"`pflanzer retro report --slug {args.slug}`",
                 tips=tips(args.slug, "retro", {}), as_json=args.json)
        elif args.cmd == "record":
            out = record(slug=args.slug, milestone=args.milestone, metric=args.metric,
                         value=args.value, unit=args.unit, evidence=args.evidence,
                         notes=args.notes)
            emit(out, title=f"Retro: zapsáno {MILESTONE_LABELS[args.milestone]}",
                 lines=[f"{out['metric']} = {_fmt_value(out['value'], out['unit'])} "
                        f"(zapsal {out['recorded_by']})"],
                 next_step=f"`pflanzer retro report --slug {args.slug}`",
                 tips=tips(args.slug, "retro", {}), as_json=args.json)
        elif args.cmd == "lesson":
            out = lesson(slug=args.slug, text=args.text, by=args.by)
            nxt = (f"další poučení: `pflanzer retro lesson --slug {args.slug} --text \"…\"`; "
                   f"shrnutí: `pflanzer retro report --slug {args.slug}`"
                   if out["killed"] else f"`pflanzer retro report --slug {args.slug}`")
            lines = [f"Zapsáno poučení #{out['lesson_id']}: „{out['text']}“"]
            lines.append("Přidáno do decision logu " + (f"({out['decision_log_repo']}) — commitni ho."
                         if out["decision_log_repo"] else "(z target repa se zapíše i do "
                         "`.pflanzer/decisions/`)."))
            emit(out, title=f"Zapsáno poučení #{out['lesson_id']}", lines=lines, next_step=nxt,
                 tips=tips(args.slug, "after_kill" if out["killed"] else "retro", {}),
                 as_json=args.json)
        elif args.cmd == "report":
            path, data, md = write_report(args.slug, args.out)
            if args.md:
                print(md)
            elif data.get("throwaway"):
                out = {"slug": args.slug, "report_path": _display(path), "throwaway": True,
                       "outcome_rows": len(data["rows"])}
                lines = ["Throwaway demo: neměří se přežití kódu ani T+30/60/90, jen metrika "
                         "dema v termínu.", _primary_line(data["primary"]),
                         f"Report: {_display(path)}"]
                emit(out, title=f"Retro (throwaway): {args.slug}", lines=lines,
                     next_step=f"`pflanzer retro reminders --slug {args.slug} --format ics "
                               f"--out {args.slug}-pripominka.ics`",
                     tips=tips(args.slug, "retro", {}), as_json=args.json)
            elif data.get("killed"):
                bm = data["build_metrics"]
                out = {"slug": args.slug, "report_path": _display(path), "killed": True,
                       "lessons": data["lessons"], "build_metrics": bm}
                lines = ["Projekt skončil Kill — jen poučení a metriky Buildu, bez měření a připomínek."]
                lines += [f"Poučení #{x['n']}: {x['text']}" for x in data["lessons"]] or [
                    "Zatím žádné poučení."]
                lines.append(f"Build: {count(len(bm['variants']), 'varianta', 'varianty', 'variant')}, "
                             f"feedback {bm['feedback']} (kritických {bm['critical']})")
                lines.append(f"Report: {_display(path)}")
                nxt = (f"`pflanzer retro lesson --slug {args.slug} --text \"…\"`"
                       if not data["lessons"] else "vezmi poučení do zadání dalšího Kickoffu (`/pm start`)")
                emit(out, title=f"Retro po Kill: {args.slug}", lines=lines, next_step=nxt,
                     tips=tips(args.slug, "after_kill", {}), as_json=args.json)
            else:
                out = {
                    "slug": args.slug,
                    "report_path": _display(path),
                    "checks": data["checks"],
                    "milestones": data["milestones"],
                    "outcome_rows": len(data["rows"]),
                }
                status = {"ok": "splněno", "flag": "pod cílem", "missing": "zatím neměřeno"}
                lines = [_primary_line(data["primary"])]
                lines += [f"{c['metric']}: {_fmt_value(c['value'], c.get('unit'))} "
                          + (f"(bez cíle) — {'změřeno' if c['value'] is not None else 'zatím neměřeno'}"
                             if c["target"] == "bez cíle"
                             else f"(cíl {c['target']}) — {status[c['status']]}")
                          for c in data["checks"]]
                lines.append("Podíl kroků s AI náhradou: " + _ai_stand_in_text(data["ai_stand_ins"]))
                latest_rows: dict[tuple[str, str], dict[str, Any]] = {}
                for r in data["rows"]:
                    if r["milestone"] != "ship":
                        latest_rows[(r["milestone"], r["metric"])] = r
                for (ms, metric), r in latest_rows.items():
                    lines.append(f"{MILESTONE_LABELS[ms]} {metric}: "
                                 f"{_fmt_value(r['value'], r['unit'])}")
                overdue = [m for m in data["milestones"] if m["state"] == "overdue"]
                if overdue:
                    lines.append("Po termínu chybí čtení: " + ", ".join(
                        MILESTONE_LABELS[m["milestone"]] for m in overdue))
                lines.append(f"Report: {_display(path)}")
                nxt = (f"`pflanzer retro record --slug {args.slug} --milestone "
                       f"{overdue[0]['milestone']} --metric "
                       f"{next(iter(RECOMMENDED_METRICS[overdue[0]['milestone']]))} --value <N>`"
                       if overdue else f"`pflanzer retro reminders --slug {args.slug} "
                                       f"--format ics --out {args.slug}-pripominky.ics`")
                emit(out, title=f"Retro: {args.slug}", lines=lines, next_step=nxt,
                     tips=tips(args.slug, "retro", {}), as_json=args.json)
        elif args.cmd == "reminders":
            text = render_reminders(args.slug, args.format, args.from_date)
            n_rem_txt = (f"{count(4, 'připomínka', 'připomínky', 'připomínek')}: T+7, T+30, T+60, T+90")
            with transaction() as _c:
                if is_throwaway(_c, _load_project(_c, args.slug)):
                    n_rem_txt = "1 připomínka: metrika dema v termínu (throwaway)"
            if args.out:
                path = Path(args.out).expanduser()
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8", newline="")
                emit({"slug": args.slug, "format": args.format, "path": _display(path)},
                     title="Připomínky uloženy",
                     lines=[f"Soubor {_display(path)} ({n_rem_txt})",
                            "Importuj ho do kalendáře (ics), nebo ho předej Provozu a Produktu."],
                     next_step=f"`pflanzer retro report --slug {args.slug}`",
                     as_json=args.json)
            else:
                sys.stdout.write(text)
    except (ValueError, RuntimeError) as exc:
        exit_if_project_missing(exc)
        die(str(exc), examples.get(args.cmd, ""))


if __name__ == "__main__":
    main()
