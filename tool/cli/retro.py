"""Retro — outcome measurement for the method's core claim (audit N4).

The method claims "≥ 80 % LOC of the winner merged without modification,
prod deploy D11–14". This module makes that claim measurable and records
the reinforcement track (T+7/30/60/90) as data instead of Charter prose.

Subcommands:
- `measure`   — reads the target repo (winner branch vs merge commit) and
                writes milestone='ship' rows into `outcomes`.
- `record`    — manual T+7/30/60/90 readouts (bugs, leading/lagging metric).
- `report`    — renders `data/retro/<slug>-retro.md` + target checks.
- `reminders` — T+7/30/60/90 reminders as .ics, markdown checklist or
                `gh issue create` commands (printed, never executed).

Stdlib + sqlite + git only. `gh` is optional (merge commit lookup) with a
fallback to an explicit `--merge-commit`.
"""
from __future__ import annotations

import argparse
import json
import re
import shlex
import shutil
import sqlite3
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tool.cli.db import audit, current_actor, transaction  # noqa: E402

RETRO_DIR = REPO_ROOT / "data" / "retro"
CHARTER_DIR = REPO_ROOT / "data" / "charters"
BRAND_LINE = "Pflanzer Method | pflanzer.cz/method"

# Method targets (README / 07-handoff-do-vyvoje.md, audit N4).
TARGET_REUSE_PCT = 80.0
TARGET_DAYS_TO_PROD = 14

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
        "t30_leading_metric": "readout leading metriky z Charteru",
        "t30_handoff_acceptance_pct": "% acceptance criteria splněných v produkci / přijetí handoffu dev týmem",
    },
    "t60": {
        "t60_rework_pct": "% shipnutých LOC přepsaných od merge (rework)",
    },
    "t90": {
        "t90_lagging_metric": "readout lagging metriky vs success criterion",
        "t90_go_iterate_kill": "verdikt T+90 readoutu: 1 = go, 0.5 = iterate, 0 = kill",
    },
}

# Default reinforcement owners from 07-handoff-do-vyvoje.md § Reinforcement
# track — used when the Charter leaves the milestone empty.
DEFAULT_OWNERS = {
    "t7": "CS proxy + Champion",
    "t30": "Data + Champion",
    "t60": "Champion + EM",
    "t90": "Data + CS + Champion",
}
DEFAULT_DELIVERABLES = {
    "t7": "Ticket category check vs prediction worksheet; bugy T+7",
    "t30": "Leading metric readout, build progress vs estimate, retro",
    "t60": "Capacity actual vs estimate, dependency drift, rework",
    "t90": "Lagging metric vs success criterion, learnings → role catalog",
}

EMPTY_MARKERS = {"", "-", "—", "tbd", "n/a"}


# --------------------------------------------------------------------------
# DB helpers
# --------------------------------------------------------------------------


def _ensure_outcomes_table(conn: sqlite3.Connection) -> None:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='outcomes'"
    ).fetchone()
    if not row:
        raise RuntimeError(
            "Tabulka `outcomes` v DB chybí. Spusť `python3 tool/db/migrate.py` "
            "(additivní migrace, data nemaže)."
        )


def _load_project(conn: sqlite3.Connection, slug: str) -> dict[str, Any]:
    row = conn.execute(
        "SELECT * FROM projects WHERE slug = ?", (slug,),
    ).fetchone()
    if not row:
        raise ValueError(f"Projekt '{slug}' neexistuje.")
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


def _go_date(conn: sqlite3.Connection, project_id: int) -> tuple[datetime | None, str]:
    """Return (Session 2 GO timestamp, source).

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
    latest Session 1 when that helper is unavailable.
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
            f"Projekt '{slug}' nemá žádnou variantu v Session 1 — winner nelze "
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
        + "). Spusť `python3 tool/cli/worktree.py setup --slug <slug> --no-install` "
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
        print(f"[retro] warn: gh pr view selhal: {res.stderr.strip()}", file=sys.stderr)
        return None
    data = json.loads(res.stdout or "{}")
    sha = (data.get("mergeCommit") or {}).get("oid")
    if not sha:
        return None
    return sha, data.get("mergedAt")


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


def measure(
    *, slug: str, pr_url: str | None = None, merge_commit: str | None = None,
    base: str | None = None, repo_path: str | None = None,
    winner: str | None = None, fetch: bool = True,
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
    - `days_to_prod` = calendar days from Session 2 GO (sessions/decisions)
      to the merge (gh `mergedAt`, else committer date of the merge commit).
      Merge is used as the prod proxy; if deploy happens later, record the
      real deploy date as a note.
    - `winner_commits` = `git rev-list --count <fork>..<winner>`.
    Works for merge commits and squash merges; for rebase merges pass the
    tip of the rebased series as `--merge-commit` and the fork as `--base`.
    """
    with transaction() as conn:
        _ensure_outcomes_table(conn)
        project = _load_project(conn, slug)
        project_id = int(project["id"])
        go_dt, go_source = _go_date(conn, project_id)
    winner_name = winner or _winner_name(slug, project_id)

    repo = _resolve_repo(project, repo_path)
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
    added_by_path = {p: a for p, (a, _r) in winner_stat.items() if a > 0}
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
    reuse_pct = round(loc_unchanged / loc_winner * 100, 1) if loc_winner else None

    winner_commits = int(_git(repo, "rev-list", "--count", f"{fork_sha}..{winner_sha}") or 0)

    merge_dt = _parse_ts(merged_at) or _parse_ts(
        _git(repo, "log", "-1", "--format=%cI", merge_sha)
    )
    days_to_prod = (
        (merge_dt.date() - go_dt.date()).days if (merge_dt and go_dt) else None
    )

    evidence = pr_url or f"commit:{merge_sha}"
    heuristic = (
        f"added(winner) - removed(winner..merge) per path; fork={fork_sha[:10]} "
        f"({fork_source}); winner={winner_sha[:10]}; merge={merge_sha[:10]} ({merge_source})"
    )
    rows: list[tuple[str, float | None, str, str]] = [
        ("loc_winner", float(loc_winner), "loc", f"{len(added_by_path)} files; {winner_branch}"),
        ("loc_merged_unchanged", float(loc_unchanged), "loc", heuristic),
        ("loc_reused_pct", reuse_pct, "%", f"target >= {TARGET_REUSE_PCT:.0f} %"),
        ("winner_commits", float(winner_commits), "commits", f"{fork_sha[:10]}..{winner_sha[:10]}"),
    ]
    if days_to_prod is not None:
        rows.append((
            "days_to_prod", float(days_to_prod), "days",
            f"GO {go_dt.date().isoformat()} ({go_source}) -> merge "
            f"{merge_dt.date().isoformat()}; target <= {TARGET_DAYS_TO_PROD}",
        ))
    else:
        print("[retro] warn: datum Session 2 GO nenalezeno — days_to_prod se nezapíše.",
              file=sys.stderr)

    actor = current_actor()
    metrics = [r[0] for r in rows]
    with transaction() as conn:
        # measure is recomputable: replace previous ship rows for these metrics
        conn.execute(
            f"DELETE FROM outcomes WHERE project_id = ? AND milestone = 'ship' "
            f"AND metric IN ({','.join('?' * len(metrics))})",
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
            payload={"slug": slug, "winner": winner_name, "merge_commit": merge_sha,
                     "pr_url": pr_url, "loc_reused_pct": reuse_pct,
                     "days_to_prod": days_to_prod},
        )

    return {
        "slug": slug,
        "winner": winner_name,
        "winner_branch": winner_ref,
        "repo": str(repo),
        "fork_point": fork_sha,
        "fork_point_source": fork_source,
        "merge_commit": merge_sha,
        "merge_commit_source": merge_source,
        "merged_at": merge_dt.isoformat() if merge_dt else None,
        "session2_go_at": go_dt.isoformat() if go_dt else None,
        "loc_winner": loc_winner,
        "loc_merged_unchanged": loc_unchanged,
        "loc_reused_pct": reuse_pct,
        "days_to_prod": days_to_prod,
        "winner_commits": winner_commits,
        "targets": {
            "reuse_ok": reuse_pct is not None and reuse_pct >= TARGET_REUSE_PCT,
            "days_to_prod_ok": days_to_prod is not None and days_to_prod <= TARGET_DAYS_TO_PROD,
        },
        "per_file": per_file,
        "evidence_url": evidence,
        "next_step": f"python3 tool/cli/retro.py report --slug {slug}",
    }


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
    if metric not in known:
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
        check("loc_reused_pct", lambda v: v >= TARGET_REUSE_PCT,
              f">= {TARGET_REUSE_PCT:.0f} %"),
        check("days_to_prod", lambda v: v <= TARGET_DAYS_TO_PROD,
              f"<= {TARGET_DAYS_TO_PROD} dní"),
    ]

    today = date.today()
    milestones = []
    for m in MILESTONES:
        due = (go_dt.date() + timedelta(days=MILESTONE_DAYS[m])) if go_dt else None
        has_rows = any(r["milestone"] == m for r in rows)
        if has_rows:
            state = "recorded"
        elif due and due < today:
            state = "overdue"
        else:
            state = "pending"
        milestones.append({"milestone": m, "due": due.isoformat() if due else None,
                           "state": state})

    return {"project": project, "go_dt": go_dt, "go_source": go_source,
            "rows": rows, "checks": checks, "milestones": milestones}


def render_report_md(slug: str, data: dict[str, Any] | None = None) -> str:
    data = data or build_report(slug)
    p = data["project"]
    go_dt = data["go_dt"]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    status_icon = {"ok": "✅ splněno", "flag": "⚠ FLAG — pod cílem",
                   "missing": "⏳ nezměřeno"}

    check_rows = "\n".join(
        f"| `{c['metric']}` | {_fmt_value(c['value'], c.get('unit'))} | "
        f"{c['target']} | {status_icon[c['status']]} |"
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
            hint = (f"`python3 tool/cli/retro.py measure --slug {slug} --pr-url <URL>`"
                    if m == "ship" else
                    f"`python3 tool/cli/retro.py record --slug {slug} --milestone {m} "
                    f"--metric {next(iter(RECOMMENDED_METRICS[m]))} --value <N>`")
            body = f"_Zatím bez dat._ Zapiš: {hint}"
        sections.append(f"{header}\n\n{body}")

    sections_md = "\n\n".join(sections)
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
> Session 2 GO: {go_dt.date().isoformat() if go_dt else '_neznámé_'} ({data['go_source']})
> Per audit N4 + `docs/methodology/07-handoff-do-vyvoje.md` § Reinforcement track.

## Cíle metody

| Metrika | Hodnota | Cíl | Stav |
|---------|---------|-----|------|
{check_rows}
{flag_note}
## Outcomes per milník

{sections_md}

## Jak čísla vznikla

- `loc_reused_pct` = řádky přidané winner branchí, které v merge commitu
  zůstaly beze změny (heuristika `added − removed` po cestách, které winner
  změnil; konzervativní dolní odhad — viz docstring `retro.py measure`).
- `days_to_prod` = kalendářní dny od Session 2 GO do merge commitu (proxy
  pro první prod deploy).
- T+7/30/60/90 = ruční readouty (`retro.py record`), evidence URL povinně
  tam, kde existuje (issue, dashboard, retro zápis).

---

*Zdroj dat: tabulka `outcomes` v `data/pflanzer.db` · další readout
zapiš přes `/pm retro {p['slug']}`.*
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
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


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
            text, source = DEFAULT_OWNERS[m], "07-handoff default"
        result[m] = (text, source)
    return result


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


def _reminder_items(
    slug: str, from_date: str | None,
) -> tuple[dict[str, Any], date, str, list[dict[str, Any]]]:
    with transaction() as conn:
        project = _load_project(conn, slug)
        go_dt, _src = _go_date(conn, int(project["id"]))
    if from_date:
        start, start_source = date.fromisoformat(from_date), "--from"
    elif go_dt:
        start, start_source = go_dt.date(), "Session 2 GO"
    else:
        raise ValueError(
            "Datum Session 2 GO v DB není. Zadej `--from YYYY-MM-DD`."
        )
    owners = _owners(slug, project)
    items = []
    for m in MILESTONES:
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
            "record_cmd": (f"python3 tool/cli/retro.py record --slug {slug} "
                           f"--milestone {m} --metric {first_metric} --value <N> "
                           f"--evidence <URL>"),
        })
    return project, start, start_source, items


def render_reminders(slug: str, fmt: str, from_date: str | None = None) -> str:
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
                f"Owner (Charter): {it['owner']}\n"
                f"Deliverable: {it['deliverable']}\n"
                f"Metriky: {', '.join(it['metrics'])}\n\n"
                f"Zápis: /pm retro {slug}\n{it['record_cmd']}"
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
        out = [BRAND_LINE, "", f"# Reinforcement připomínky — {name}", "",
               f"> Slug: `{slug}` · Od: {start.isoformat()} ({start_source})", ""]
        for it in items:
            out.append(
                f"- [ ] **{it['label']}** — {it['due'].isoformat()} · owner: "
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
            f"# Reinforcement issues pro {slug} — příkazy se NESPOUŠTĚJÍ automaticky.",
            f"gh label create {shlex.quote(label)}{repo_flag} --color 5319e7 "
            f"--description {shlex.quote('Pflanzer Method outcome tracking')} --force",
        ]
        for it in items:
            title = f"[Pflanzer {it['label']} · {it['due'].isoformat()}] Readout — {name}"
            body = (
                f"{BRAND_LINE}\n\n**Termín:** {it['due'].isoformat()}\n"
                f"**Owner (Charter):** {it['owner']}\n"
                f"**Deliverable:** {it['deliverable']}\n"
                f"**Metriky:** {', '.join(f'`{x}`' for x in it['metrics'])}\n\n"
                f"Zápis výsledku: `/pm retro {slug}` nebo\n\n"
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


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)

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
    p_measure.add_argument("--no-fetch", action="store_true", help="Nepouštět git fetch origin")

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

    p_report = sub.add_parser("report", help="Retro report → data/retro/<slug>-retro.md")
    p_report.add_argument("--slug", required=True)
    p_report.add_argument("--md", action="store_true", help="Vypiš markdown na stdout místo JSON")
    p_report.add_argument("--out", help="Jiná cesta výstupu (default data/retro/<slug>-retro.md)")

    p_rem = sub.add_parser("reminders", help="Připomínky T+7/30/60/90 (ics | md | gh-issues)")
    p_rem.add_argument("--slug", required=True)
    p_rem.add_argument("--format", choices=["ics", "md", "gh-issues"], default="md")
    p_rem.add_argument("--from", dest="from_date", help="YYYY-MM-DD (default: datum Session 2 GO)")
    p_rem.add_argument("--out", help="Zapsat do souboru místo stdout")

    args = p.parse_args()
    try:
        if args.cmd == "measure":
            out = measure(slug=args.slug, pr_url=args.pr_url,
                          merge_commit=args.merge_commit, base=args.base,
                          repo_path=args.repo_path, winner=args.winner,
                          fetch=not args.no_fetch)
            print(json.dumps(out, ensure_ascii=False, indent=2))
        elif args.cmd == "record":
            out = record(slug=args.slug, milestone=args.milestone, metric=args.metric,
                         value=args.value, unit=args.unit, evidence=args.evidence,
                         notes=args.notes)
            print(json.dumps(out, ensure_ascii=False, indent=2))
        elif args.cmd == "report":
            path, data, md = write_report(args.slug, args.out)
            if args.md:
                print(md)
            else:
                print(json.dumps({
                    "slug": args.slug,
                    "report_path": _display(path),
                    "checks": data["checks"],
                    "milestones": data["milestones"],
                    "outcome_rows": len(data["rows"]),
                }, ensure_ascii=False, indent=2, default=str))
        elif args.cmd == "reminders":
            text = render_reminders(args.slug, args.format, args.from_date)
            if args.out:
                path = Path(args.out).expanduser()
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8", newline="")
                print(json.dumps({"slug": args.slug, "format": args.format,
                                  "path": _display(path)}, ensure_ascii=False))
            else:
                sys.stdout.write(text)
    except (ValueError, RuntimeError) as exc:
        print(f"[retro] chyba: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
