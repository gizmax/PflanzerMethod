"""Pre-flight triage aggregator (volitelný krok pro regulované projekty).

The 4 triage sub-agents (discovery-readiness, security-triage, legal-triage,
platform-triage) run in parallel via Claude Code Agent calls. Each returns
a JSON with a `track` field + `status` + artefact_md. This module:

1. Persists the 4 triage rows in DB.
2. Computes overall pre-flight gate status (all 4 must be 'ok' or 'deferred').
3. Updates project status to 'triage' (if all clear) or keeps 'charter'
   (if any 'blocked').
"""
from __future__ import annotations

import json
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tool.cli._compat import ProjectNotFound, exit_if_project_missing  # noqa: E402
from tool.cli.db import audit, current_actor, transaction  # noqa: E402
from tool.cli.ux import CzechArgumentParser, die, emit, read_spec  # noqa: E402

try:  # výstupy mimo repo metody (DATA_ROOT z tool.cli.db); fallback <repo>/data
    from tool.cli.db import DATA_ROOT  # type: ignore[attr-defined]  # noqa: E402
except ImportError:  # pragma: no cover
    DATA_ROOT = REPO_ROOT / "data"

BRAND = "**Pflanzer Method | pflanzer.cz/method**"
TRIAGE_DIR = DATA_ROOT / "triage"
EXPECTED_TRACKS = ("discovery", "security", "legal", "platform")


def _clip_text(text: str, n: int) -> str:
    t = " ".join(text.split())
    return t if len(t) <= n else t[: n - 1].rstrip() + "…"


def aggregate(slug: str, results: list[dict[str, Any]]) -> dict[str, Any]:
    """Persist 4 triage outputs + gate decision.

    Args:
        slug: project slug.
        results: list of 4 dicts (1 per track) with keys:
            track, status (ok|blocked|deferred), artefact_md, signed_by, ...

    Returns:
        dict with overall_status, blockers, warnings, summary_path.
    """
    seen_tracks = {r["track"] for r in results}
    missing = set(EXPECTED_TRACKS) - seen_tracks
    if missing:
        raise ValueError("Chybí výsledky triage pro: " + ", ".join(sorted(missing)) + ".")

    # Návrh AI subagenta není podpis (ADR-0023): `ok` bez lidského podpisu = `pending`.
    # Převod děláme PŘED agregací, aby výstup i _summary.md ukázaly skutečný stav.
    normalized: list[dict[str, Any]] = []
    for r in results:
        signer = str(r.get("signed_by") or "")
        if r["status"] == "ok" and (not signer.strip()
                                    or re.search(r"(?i)pending|agent|\bAI\b", signer)):
            r = {**r, "status": "pending",
                 "rationale": (str(r.get("rationale") or "").strip()
                               + " (čeká na podpis člověka)").strip(),
                 "signed_by": signer or "pending"}
        normalized.append(r)
    results = normalized

    # Aggregate
    blockers: list[str] = []
    warnings: list[str] = []
    by_track = {r["track"]: r for r in results}
    for r in results:
        if r["status"] == "blocked":
            blockers.append(f"[{r['track']}] {r.get('rationale', 'no rationale')}")
        if r.get("warnings"):
            warnings.extend(f"[{r['track']}] {w}" for w in r["warnings"])

    pending = [r["track"] for r in results if r["status"] == "pending"]
    for t in pending:
        who = _human_name(by_track[t].get("signed_by")) or "<jméno>"
        warnings.append(f"[{t}] čeká na podpis {who} — AI návrh není podpis (ADR-0023); "
                        f"`pflanzer checkpoint --slug {slug} <okno> --by \"{who}\" --note …`")
    # Dvě DPIA triggery + odložené právo: nesmí vypadat jako „v pořádku“ bez varování.
    legal = by_track.get("legal") or {}
    dpia_hits = len(re.findall(r"(?i)dpia", str(legal.get("artefact_md") or ""))) \
        + len(legal.get("dpia_triggers") or [])
    dpia_n = len(legal.get("dpia_triggers") or []) or (2 if dpia_hits >= 2 else 0)
    if legal.get("status") == "deferred" and (dpia_n >= 2 or dpia_hits >= 2):
        warnings.append("[legal] DPIA odložena i přes více triggerů — před Shipem musí DPO "
                        "DPIA dokončit a podepsat okno `pravo`.")
    elif legal.get("status") == "deferred":
        warnings.append("[legal] právo odloženo — Ship ho bez podpisu nepustí.")
    disc = by_track.get("discovery") or {}
    disc_text = f"{disc.get('rationale') or ''} {disc.get('artefact_md') or ''}"
    if re.search(r"(?i)opt-?out", disc_text) and disc.get("status") in ("ok", "deferred", "pending"):
        why = _clip_text(str(disc.get("rationale") or disc_text), 160)
        warnings.append(f"[discovery] opt-out z discovery (justifikace: {why}) — zapsáno do "
                        "audit logu; discovery debt zůstává.")
        opt_out_discovery = True
    else:
        opt_out_discovery = False

    overall = "blocked" if blockers else ("pending" if pending else "ok")

    # Persist
    TRIAGE_DIR.mkdir(parents=True, exist_ok=True)
    project_dir = TRIAGE_DIR / slug
    project_dir.mkdir(parents=True, exist_ok=True)

    with transaction() as conn:
        row = conn.execute("SELECT id FROM projects WHERE slug = ?", (slug,)).fetchone()
        if not row:
            raise ProjectNotFound(slug)
        project_id = int(row[0])

        for r in results:
            track = r["track"]
            artefact_md = r.get("artefact_md", "")
            if track == "discovery" and r["status"] != "ok":
                # Podpis Kickoffu (Zadání) nepřepisujeme návrhem/opt-outem z triage.
                kept = conn.execute(
                    "SELECT status, artefact_md FROM triage WHERE project_id = ? "
                    "AND track = 'discovery'", (project_id,)).fetchone()
                if kept and kept[0] == "ok" and "Kickoff" in (kept[1] or "")[:80]:
                    warnings.append("[discovery] podpis Zadání z Kickoffu zůstává; triage "
                                    "discovery ho nepřepsal.")
                    continue
            signer = str(r.get("signed_by") or "")
            (project_dir / f"{track}.md").write_text(artefact_md, encoding="utf-8")

            conn.execute(
                """
                INSERT INTO triage (project_id, track, status, artefact_md, signed_by, signed_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(project_id, track) DO UPDATE SET
                    status = excluded.status,
                    artefact_md = excluded.artefact_md,
                    signed_by = excluded.signed_by,
                    signed_at = CURRENT_TIMESTAMP
                """,
                (project_id, track, r["status"], artefact_md, r.get("signed_by", current_actor())),
            )

        # Gate decision: update project status if all clear
        new_status = "charter" if overall == "blocked" else "triage"
        conn.execute(
            "UPDATE projects SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (new_status, project_id),
        )

        audit(
            conn,
            action="triage.aggregate",
            target_type="project",
            target_id=project_id,
            payload={"overall": overall, "blockers": blockers, "warnings": warnings,
                     "pending": pending, "opt_out_discovery": opt_out_discovery},
        )
        if opt_out_discovery:
            audit(conn, action="triage.discovery_opt_out", target_type="project",
                  target_id=project_id,
                  payload={"slug": slug, "status": disc.get("status"),
                           "rationale": str(disc.get("rationale") or "")[:400]})

    summary_md = render_summary_md(slug, project_id, overall, results, blockers, warnings)
    summary_path = project_dir / "_summary.md"
    summary_path.write_text(summary_md, encoding="utf-8")

    return {
        "project_id": project_id,
        "slug": slug,
        "overall_status": overall,
        "blockers": blockers,
        "warnings": warnings,
        "summary_path": str(summary_path),
        "pending": pending,
        "opt_out_discovery": opt_out_discovery,
        "tracks": {r["track"]: r["status"] for r in results},
    }


def render_summary_md(
    slug: str, project_id: int, overall: str, results: list[dict[str, Any]],
    blockers: list[str], warnings: list[str],
) -> str:
    rows = "\n".join(
        f"| {r['track']} | {r['status']} | {r.get('signed_by', '—')} | {r.get('rationale', '—')} |"
        for r in results
    )
    block_section = ""
    if blockers:
        block_section = "\n## Blockers\n\n" + "\n".join(f"- {b}" for b in blockers) + "\n"
    warn_section = ""
    if warnings:
        warn_section = "\n## Warnings\n\n" + "\n".join(f"- {w}" for w in warnings) + "\n"

    pend = [r for r in results if r["status"] == "pending"]
    pend_note = ""
    if pend:
        pend_note = ("\n> Čeká na podpis: " + ", ".join(
            f"{r['track']} ({_human_name(r.get('signed_by')) or '<jméno>'})" for r in pend)
            + " — AI návrh není podpis; Ship je bez podpisů blokovaný.\n")
    next_step = (
        "`/pm build " + slug + "` — Build (3 varianty paralelně)." if overall in ("ok", "pending")
        else "**Build odložen.** Vyřešte blockers a spusťte triage pro `" + slug + "` znovu."
    )

    return f"""{BRAND}

# Pre-flight Triage — {slug}

> Project ID: {project_id} · Overall: **{overall.upper()}**
> Per ADR-0002 (Pre-flight triage tracks).
{pend_note}
| Track | Status | Signed by | Rationale |
|-------|--------|-----------|-----------|
{rows}
{block_section}{warn_section}
## Další krok

{next_step}
"""


# --------------------------------------------------------------------------
# Ship — triage hard gate (audit N5)
# --------------------------------------------------------------------------

# Risk profiles where Ship refuses production_ready without signed
# triage. Throwaway never ships, so it is not gated.
SHIP_GATED_PROFILES = ("pilot", "production")
TRIAGE_OVERRIDE_MARKER = "pflanzer:triage-override"
_OVERRIDE_RE = re.compile(r"<!-- " + re.escape(TRIAGE_OVERRIDE_MARKER) + r" (\{.*?\}) -->")

# DB status -> display status used in SHIP.md / readiness report.
_DISPLAY_STATUS = {"ok": "ok", "deferred": "deferred", "blocked": "failed",
                   "pending": "pending"}


def derive_risk_profile(
    *, throwaway_or_evolve: str | None, production_readiness_target: int | None,
    capacity_profile: str | None = None, explicit: str | None = None,
) -> str:
    """Return 'throwaway' | 'pilot' | 'production'.

    `projects` has no dedicated risk_profile column (quick_session maps the
    profile onto Charter fields), so it is reconstructed from them:
    throwaway = throwaway_or_evolve='throwaway' or readiness target 0;
    production = regulated/audit-grade capacity or target >= 85; else pilot.
    An explicit `risk_profile` column wins if a later migration adds one.
    """
    if explicit in ("throwaway", "pilot", "production"):
        return explicit
    target = production_readiness_target
    if throwaway_or_evolve == "throwaway" or (target is not None and int(target) == 0):
        return "throwaway"
    if capacity_profile in ("regulated", "audit-grade") or (target is not None and int(target) >= 85):
        return "production"
    return "pilot"


def load_risk_profile(conn: sqlite3.Connection, project_id: int) -> str:
    row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not row:
        raise ValueError(f"Projekt č. {project_id} neexistuje. Přehled: `pflanzer status`.")
    keys = row.keys()
    return derive_risk_profile(
        throwaway_or_evolve=row["throwaway_or_evolve"],
        production_readiness_target=row["production_readiness_target"],
        capacity_profile=row["capacity_profile"],
        explicit=row["risk_profile"] if "risk_profile" in keys else None,
    )


def triage_tracks(conn: sqlite3.Connection, project_id: int) -> list[dict[str, Any]]:
    """Per-track triage state; a missing row is reported as status 'missing'."""
    rows = {
        r[0]: r for r in conn.execute(
            "SELECT track, status, signed_by, signed_at FROM triage WHERE project_id = ?",
            (project_id,),
        ).fetchall()
    }
    out: list[dict[str, Any]] = []
    for track in EXPECTED_TRACKS:
        r = rows.get(track)
        status = r[1] if r else "missing"
        out.append({
            "track": track,
            "status": status,
            "display": _DISPLAY_STATUS.get(status, status),
            "signed_by": (r[2] if r else None),
            "signed_at": (r[3] if r else None),
        })
    return out


# Okna kroků cesty (checkpoint.py) <- triage tracky; lidská jména podle Kickoffu.
WINDOW_FOR_TRACK = {"discovery": "zadani", "security": "bezpecnost", "legal": "bezpecnost",
                    "platform": "provoz"}
WINDOW_LABEL = {"zadani": "Zadání", "bezpecnost": "Bezpečnost & právo", "provoz": "Provoz"}
WINDOW_OWNER_KEY = {"zadani": "byznys", "bezpecnost": "bezpecnost", "provoz": "provoz"}


def path_owners(conn: sqlite3.Connection, project_id: int) -> dict[str, str]:
    """Jména zástupců kroků cesty z Kickoffu (prázdné, pokud nejsou zadána)."""
    cols = {r[1] for r in conn.execute("PRAGMA table_info(projects)")}
    if "path_owners_json" not in cols:
        return {}
    row = conn.execute("SELECT path_owners_json FROM projects WHERE id = ?",
                       (project_id,)).fetchone()
    try:
        data = json.loads(row[0]) if row and row[0] else {}
    except (json.JSONDecodeError, TypeError):
        return {}
    return {k: str(v) for k, v in data.items() if v} if isinstance(data, dict) else {}


def _human_name(value: str | None) -> str | None:
    """Jméno člověka; „AI“ (náhrada kroku) není podpis."""
    v = (value or "").strip()
    return None if not v or v.upper().startswith("AI") or v.lower() == "pending" else v


def triage_windows(conn: sqlite3.Connection, project_id: int,
                   tracks: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Stav oken (zadani | bezpecnost | provoz) s jmény: kdo má podepsat a čím."""
    tracks = tracks if tracks is not None else triage_tracks(conn, project_id)
    owners = path_owners(conn, project_id)
    decider = conn.execute("SELECT decider_name FROM projects WHERE id = ?",
                           (project_id,)).fetchone()
    out: list[dict[str, Any]] = []
    sec = next((t for t in tracks if t["track"] == "security"), None)
    legal = next((t for t in tracks if t["track"] == "legal"), None)
    # Plný triage odložil právo (DPIA) a bezpečnost je podepsaná → samostatné okno „pravo".
    split_legal = bool(sec and legal and sec["status"] == "ok" and legal["status"] != "ok")
    for window, label in WINDOW_LABEL.items():
        mine = [t for t in tracks if WINDOW_FOR_TRACK.get(t["track"]) == window]
        if split_legal and window == "bezpecnost":
            mine = [sec]
        statuses = {t["status"] for t in mine}
        state = ("ok" if statuses == {"ok"} else "blocked" if "blocked" in statuses
                 else "pending" if "pending" in statuses
                 else "deferred" if "deferred" in statuses else "missing")
        signer = next((t["signed_by"] for t in mine if t["signed_by"]), None)
        owner = (_human_name(owners.get(WINDOW_OWNER_KEY[window]))
                 or (_human_name(decider[0]) if decider and window == "zadani" else None))
        out.append({"window": window, "label": label, "state": state, "owner": owner,
                    "signed_by": signer})
    if split_legal:
        st = legal["status"]
        out.append({"window": "pravo", "label": "Právo (DPIA)",
                    "state": "blocked" if st == "blocked" else "pending" if st == "pending"
                    else "deferred",
                    "owner": _human_name(legal.get("signed_by")) or "DPO",
                    "signed_by": legal.get("signed_by")})
    return out


def checkpoint_command(slug: str, window: dict[str, Any]) -> str:
    """Příkaz, kterým člověk z kroku cesty okno podepíše."""
    who = window["owner"] or "JMÉNO"
    who = f'"{who}"' if " " in who else who
    return f"pflanzer checkpoint --slug {slug} {window['window']} --by {who} --note …"


def human_triage_blockers(slug: str, windows: list[dict[str, Any]]) -> list[str]:
    """Věty po oknech: kdo ještě nepodepsal a jakým příkazem."""
    msgs: list[str] = []
    for w in windows:
        if w["state"] == "ok":
            continue
        who = w["owner"]
        cmd = f"`{checkpoint_command(slug, w)}`"
        if w["state"] == "pending":
            msgs.append(f"AI draft čeká na podpis: {who or 'člověk z kroku ' + w['label']} — {cmd}")
        elif w["state"] == "blocked":
            msgs.append(f"{w['label']} ({w['signed_by'] or who or '—'}) označilo okno jako "
                        f"blokované; po opravě znovu podepiš: {cmd}")
        else:
            msgs.append(f"{w['label']} ({who or 'jméno chybí v Kickoffu'}) ještě nepodepsal: {cmd}")
    return msgs


def _latest_override(conn: sqlite3.Connection, project_id: int) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT id, body_md, atribuce_user, atribuce_ts FROM decisions "
        "WHERE project_id = ? AND type = 'triage' AND body_md LIKE ? "
        "ORDER BY id DESC LIMIT 1",
        (project_id, f"%{TRIAGE_OVERRIDE_MARKER}%"),
    ).fetchone()
    if not row:
        return None
    m = _OVERRIDE_RE.search(row[1] or "")
    payload = json.loads(m.group(1)) if m else {}
    return {
        "decision_id": int(row[0]),
        "blocked_by": list(payload.get("blocked_by", [])),
        "rationale": payload.get("rationale", ""),
        "decider": payload.get("decider") or "",
        "by": row[2],
        "at": row[3],
    }


def ship_triage_gate(conn: sqlite3.Connection, project_id: int) -> dict[str, Any]:
    """Evaluate the triage hard gate for Ship.

    For pilot/production every track must be 'ok'; anything else (deferred,
    pending, blocked, missing row) blocks production_ready. A Decider
    override only counts if it covers every current blocker (a new blocker
    after the override re-blocks).
    """
    risk = load_risk_profile(conn, project_id)
    tracks = triage_tracks(conn, project_id)
    gated = risk in SHIP_GATED_PROFILES
    raw_blockers = (
        [f"triage:{t['track']} {t['display']}" for t in tracks if t["status"] != "ok"]
        if gated else []
    )
    override = _latest_override(conn, project_id) if raw_blockers else None
    covered = bool(override) and set(raw_blockers) <= set(override["blocked_by"])
    windows = triage_windows(conn, project_id, tracks)
    return {
        "risk_profile": risk,
        "gated": gated,
        "windows": windows,
        "tracks": tracks,
        "raw_blocked_by": raw_blockers,
        "blocked_by": [] if covered else raw_blockers,
        "override": override if covered else None,
    }


def decider_label(name: str | None) -> str:
    """Jméno Decidera z Kickoffu; prázdné nebo placeholder → „Decider“ (ne git user)."""
    v = (name or "").strip()
    return "Decider" if not v or re.search(r"doplnit|doplň|nezad|^tbd", v, re.I) else v


def record_triage_override(
    conn: sqlite3.Connection, *, project_id: int, slug: str,
    blocked_by: list[str], rationale: str, actor: str | None = None,
    decider: str | None = None,
) -> int:
    """Persist a Decider override of the triage gate (decisions + audit log)."""
    if not rationale or not rationale.strip():
        raise ValueError(
            "--override-triage vyžaduje --rationale \"…\" (DORA / AI Act čl. 14)."
        )
    actor = actor or current_actor()
    decider_name = decider_label(decider)
    payload = {"blocked_by": blocked_by, "rationale": rationale.strip(), "decider": decider_name}
    body = (
        f"# Triage override (Ship) — {slug}\n\n"
        f"<!-- {TRIAGE_OVERRIDE_MARKER} {json.dumps(payload, ensure_ascii=False)} -->\n\n"
        f"**Decider override:** production_ready povoleno i přes nedokončený triage "
        f"(výjimku schválil: {decider_name}).\n\n"
        f"**Blokace, které override pokrývá:** {', '.join(blocked_by)}\n\n"
        f"**Rationale:** {rationale.strip()}\n\n"
        f"**Atribuce:** {actor}\n"
    )
    cur = conn.execute(
        "INSERT INTO decisions (project_id, type, body_md, atribuce_user, atribuce_ts) "
        "VALUES (?, 'triage', ?, ?, CURRENT_TIMESTAMP)",
        (project_id, body, actor),
    )
    audit(
        conn, actor=actor, action="ship_gate.triage_override",
        target_type="project", target_id=project_id,
        payload={"slug": slug, **payload, "decision_id": cur.lastrowid},
    )
    return int(cur.lastrowid)


THRESHOLD_OVERRIDE_MARKER = "pflanzer:threshold-override"
_THRESHOLD_RE = re.compile(
    r"<!-- " + re.escape(THRESHOLD_OVERRIDE_MARKER) + r" (\{.*?\}) -->")


def record_threshold_override(
    conn: sqlite3.Connection, *, project_id: int, slug: str, decider: str | None,
    score: int, target: int, rationale: str, actor: str | None = None,
) -> int:
    """Persist a Decider override of the Ship score threshold (decisions + audit log)."""
    if not rationale or not rationale.strip():
        raise ValueError("--override-threshold vyžaduje --rationale \"…\" (zapisuje se do decision logu).")
    actor = actor or current_actor()
    decider = decider_label(decider)
    payload = {"score": int(score), "target": int(target), "decider": decider,
               "rationale": rationale.strip()}
    body = (
        f"# Výjimka z prahu (Ship) — {slug}\n\n"
        f"<!-- {THRESHOLD_OVERRIDE_MARKER} {json.dumps(payload, ensure_ascii=False)} -->\n\n"
        f"**Verdikt:** pod prahem — Ship na odpovědnost Decidera ({decider}).\n\n"
        f"**Skóre:** {score}/100 (práh {target})\n\n"
        f"**Rationale:** {rationale.strip()}\n\n"
        f"**Atribuce:** {actor}\n"
    )
    cur = conn.execute(
        "INSERT INTO decisions (project_id, type, body_md, atribuce_user, atribuce_ts) "
        "VALUES (?, 'escalation', ?, ?, CURRENT_TIMESTAMP)",
        (project_id, body, actor),
    )
    audit(
        conn, actor=actor, action="ship_gate.threshold_override",
        target_type="project", target_id=project_id,
        payload={"slug": slug, **payload, "decision_id": cur.lastrowid},
    )
    return int(cur.lastrowid)


def latest_threshold_override(
    conn: sqlite3.Connection, project_id: int, *, score: int, target: int,
) -> dict[str, Any] | None:
    """Latest threshold override, valid only for the same score/threshold it was given for."""
    row = conn.execute(
        "SELECT id, body_md, atribuce_user, atribuce_ts FROM decisions "
        "WHERE project_id = ? AND type = 'escalation' AND body_md LIKE ? "
        "ORDER BY id DESC LIMIT 1",
        (project_id, f"%{THRESHOLD_OVERRIDE_MARKER}%"),
    ).fetchone()
    m = _THRESHOLD_RE.search(row[1] or "") if row else None
    if not m:
        return None
    payload = json.loads(m.group(1))
    if payload.get("score") != int(score) or payload.get("target") != int(target):
        return None
    return {"decision_id": int(row[0]), "score": payload["score"], "target": payload["target"],
            "decider": payload.get("decider", ""), "rationale": payload.get("rationale", ""),
            "by": row[2], "at": row[3]}


TRIAGE_SPEC_EXAMPLE = (
    '  echo \'{"slug": "moje-appka", "results": [{"track": "security", "status": "ok", '
    '"signed_by": "Lucie", "artefact_md": "…"}, …]}\' | pflanzer triage --spec -\n'
    "  (4 tracky: discovery, security, legal, platform; status ok|blocked|deferred)"
)


def run_from_json(path: Path | str) -> dict[str, Any]:
    spec = read_spec(path, example=TRIAGE_SPEC_EXAMPLE)
    if "slug" not in spec or not isinstance(spec.get("results"), list):
        raise ValueError("Spec musí obsahovat `slug` a seznam `results` (4 tracky).")
    return aggregate(spec["slug"], spec["results"])


def main() -> None:
    parser = CzechArgumentParser(prog="pflanzer triage", description=__doc__.split("\n")[0])
    parser.add_argument("--spec", required=True,
                        help="JSON se 4 výsledky triage (soubor, nebo `-` pro stdin)")
    parser.add_argument("--json", action="store_true", help="Výstup jako JSON")
    args = parser.parse_args()
    try:
        out = run_from_json(args.spec)
    except (ValueError, KeyError) as e:
        exit_if_project_missing(e)
        die(str(e) if isinstance(e, ValueError) else f"V specu chybí klíč {e}.",
            TRIAGE_SPEC_EXAMPLE)
    slug = out["slug"]
    ok = out["overall_status"] in ("ok", "pending")
    title = ("blokováno" if not ok else
             "čeká na podpis (" + ", ".join(out["pending"]) + ")" if out["pending"]
             else "v pořádku")
    emit(out, title=f"Triage {slug}: {title}",
         lines=[f"{t}: {st}" for t, st in out["tracks"].items()] + out["blockers"][:2],
         warnings=out["warnings"][:4],
         next_step=(f"`/pm build {slug}`" if ok
                    else "vyřeš blokace a spusť triage znovu; okna podepisuje "
                         f"`pflanzer checkpoint --slug {slug} bezpecnost --by JMÉNO --note …`"),
         as_json=args.json)


if __name__ == "__main__":
    main()
