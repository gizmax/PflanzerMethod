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


# --------------------------------------------------------------------------
# Podmínky / produkční blokace z triage (pilot Kladivo)
# --------------------------------------------------------------------------
#
# Triage agenti vrací podmínky strukturovaně (`conditions`: [{"id": "K1", "text": "…"}] nebo
# řetězce), případně jako řádky `- [K1] text` v `artefact_md` (sekce „Podmínky“); jako
# nouzovou cestu čteme i věty typu `Požadavky: K1 text; K2 text`. Uložíme je do audit logu
# (`triage.conditions`), podpis okna je převezme (`taken_conditions`) nebo vědomě odpustí
# (`--waive K3 --rationale …`; `waived_conditions`). SHIP.md, těla PR a compliance.md je ukážou.

COND_ID = r"[A-Za-z]{1,6}(?:-[A-Za-z]{1,4})?\d{1,3}"
_COND_BULLET = re.compile(r"^\s*(?:[-*\u2022]|\d+[.)])\s*\[(" + COND_ID + r")\]\s*[:\u2013\u2014-]?\s*(\S.*?)\s*$")
_COND_LEAD = re.compile(r"(?i)po[\u017ez]adavk|podm[\u00edi]nk|dolo[\u017ez]it|blokac|blokuj|conditions|requirements|blockers")
_COND_ITEM = re.compile(r"^\s*(" + COND_ID + r")(?:\s*[:.)\u2013\u2014-]\s*|\s+)(\S.*?)\s*$")
_COND_TEXT_ID = re.compile(r"^\s*\[?(" + COND_ID + r")\]?\s*[:.)\u2013\u2014-]?\s+(\S.*)$")
COND_PREFIX = {"discovery": "C", "security": "K", "legal": "D", "platform": "P"}
COND_KEYS = ("conditions", "production_blockers", "blockers")
WINDOW_FOR_COND_TRACK = {"discovery": "zadani", "security": "bezpecnost", "legal": "bezpecnost",
                         "platform": "provoz"}


def _clean_cond(text: str) -> str:
    return " ".join(str(text or "").replace("**", "").split()).strip(" -\u2022*")


def extract_conditions(result: dict[str, Any]) -> list[dict[str, str]]:
    """Podmínky/blokace jednoho triage tracku: [{id, text}] (strukturovaně + z `artefact_md`)."""
    track = str(result.get("track") or "")
    found: dict[str, str] = {}
    order: list[str] = []

    def put(cid: str, text: str) -> None:
        text = _clean_cond(text)
        cid = cid.upper()
        if text and cid not in found:
            found[cid] = text
            order.append(cid)

    counters: dict[str, int] = {}
    for key in COND_KEYS:
        items = result.get(key)
        if not isinstance(items, list) or (key == "blockers" and result.get("status") == "blocked"):
            continue
        for it in items:
            cid, text = "", ""
            if isinstance(it, dict):
                cid, text = str(it.get("id") or ""), str(it.get("text") or it.get("title") or "")
            elif isinstance(it, str):
                m = _COND_TEXT_ID.match(it)
                cid, text = (m.group(1), m.group(2)) if m else ("", it)
            if not text.strip():
                continue
            if not cid:
                pre = (COND_PREFIX.get(track, "X") if key != "blockers" else "B")
                counters[pre] = counters.get(pre, 0) + 1
                cid = f"{pre}{counters[pre]}"
                while cid.upper() in found:
                    counters[pre] += 1
                    cid = f"{pre}{counters[pre]}"
            put(cid, text)
    for line in str(result.get("artefact_md") or "").splitlines():
        m = _COND_BULLET.match(line)
        if m:
            put(m.group(1), m.group(2))
            continue
        head, sep, rest = line.partition(":")
        if sep and _COND_LEAD.search(head):
            for part in rest.split(";"):
                mi = _COND_ITEM.match(part)
                if mi:
                    put(mi.group(1), mi.group(2))
    return [{"id": cid, "text": found[cid]} for cid in order]


def condition_key(track: str, cid: str) -> str:
    return f"{track}:{cid.upper()}"


def store_conditions(conn: sqlite3.Connection, project_id: int, track: str,
                     conds: list[dict[str, str]]) -> None:
    """Zapíše aktuální seznam podmínek tracku (poslední záznam platí; prázdný seznam maže)."""
    prev = [c for c in triage_conditions(conn, project_id) if c["track"] == track]
    if not conds and not prev:
        return
    audit(conn, action="triage.conditions", target_type="project", target_id=project_id,
          payload={"track": track, "conditions": conds})


def triage_conditions(conn: sqlite3.Connection, project_id: int) -> list[dict[str, Any]]:
    """Podmínky z triage se stavem: open | taken (převzal podpis okna) | waived (odpuštěno)."""
    latest: dict[str, list[dict[str, str]]] = {}
    states: dict[str, dict[str, Any]] = {}
    rows = conn.execute(
        "SELECT action, payload_json FROM audit_log WHERE target_type = 'project' AND target_id = ? "
        "AND (action = 'triage.conditions' OR action LIKE 'checkpoint.%') ORDER BY id",
        (project_id,)).fetchall()
    for action, raw in rows:
        try:
            pl = json.loads(raw or "{}")
        except (ValueError, TypeError):
            continue
        if action == "triage.conditions":
            latest[str(pl.get("track"))] = [c for c in pl.get("conditions") or []
                                            if isinstance(c, dict) and c.get("id") and c.get("text")]
            continue
        if pl.get("status") != "ok":
            continue
        window = action.split(".", 1)[1]
        for k in pl.get("taken_conditions") or []:
            states[str(k)] = {"state": "taken", "window": window, "by": pl.get("by"),
                              "rationale": ""}
        for w in pl.get("waived_conditions") or []:
            if isinstance(w, dict) and w.get("key"):
                states[str(w["key"])] = {"state": "waived", "window": window,
                                         "by": pl.get("by"), "rationale": w.get("rationale") or ""}
    out: list[dict[str, Any]] = []
    for track in EXPECTED_TRACKS:
        for c in latest.get(track, []):
            key = condition_key(track, str(c["id"]))
            st = states.get(key) or {"state": "open", "window": None, "by": None, "rationale": ""}
            out.append({"track": track, "id": str(c["id"]).upper(), "key": key,
                        "text": str(c["text"]), "window_for": WINDOW_FOR_COND_TRACK[track], **st})
    return out


BUILD_TRACKS = ("security", "legal", "platform")


def build_constraints(slug: str) -> list[dict[str, Any]]:
    """Omezení z triage relevantní pro Build (security/legal/platform), bez odpuštěných."""
    try:
        with transaction() as conn:
            row = conn.execute("SELECT id FROM projects WHERE slug = ?", (slug,)).fetchone()
            if not row:
                return []
            conds = triage_conditions(conn, int(row[0]))
    except Exception:  # noqa: BLE001 — prompty nesmí spadnout na starší DB
        return []
    return [c for c in conds if c["track"] in BUILD_TRACKS and c["state"] != "waived"]


def triage_changed_brief(slug: str) -> str | None:
    """Věta pro status: triage přidala omezení zadání (jinak None)."""
    cons = build_constraints(slug)
    if not cons:
        return None
    parts = []
    for t in BUILD_TRACKS:
        ids = [c["id"] for c in cons if c["track"] == t]
        if ids:
            parts.append(f"{t} {ids[0]}" + (f"–{ids[-1]}" if len(ids) > 1 else ""))
    return ("Triage změnila zadání: " + ", ".join(parts) + f" ({len(cons)} omezení) — prompty to "
            f"už obsahují (`pflanzer prompts --slug {slug}`); zvažte úpravu Charteru "
            f"(`data/charters/{slug}.md`, nebo nový `pflanzer charter --spec …`).")


VALID_TRIAGE_STATUS = ("ok", "blocked", "deferred", "pending")
OPT_OUT_EXAMPLE = (
    '  {"track": "discovery", "status": "deferred", "signed_by": "Karel Dvořák",\n'
    '   "rationale": "opt-out: interní nástroj, persony známe z 10 let telefonních rezervací",\n'
    '   "conditions": [{"id": "C1", "text": "persona do 30 dní"}], "artefact_md": "…"}\n'
    "  (opt-out = status `deferred`, `signed_by` je jméno Decidera (člověk), `rationale` začíná "
    "„opt-out:“ a uvádí důvod)"
)


def validate_results(results: list[Any]) -> None:
    """Česká chyba, když spec triage nedává smysl (nezná track/stav, špatný opt-out)."""
    seen: set[str] = set()
    for i, r in enumerate(results, 1):
        if not isinstance(r, dict):
            raise ValueError(f"Výsledek č. {i} v `results` musí být objekt "
                             '{"track": …, "status": …, "signed_by": …, "artefact_md": …}.')
        track = r.get("track")
        if track not in EXPECTED_TRACKS:
            raise ValueError(f"Výsledek č. {i}: neznámý track ‚{track}‘. Povolené: "
                             + ", ".join(EXPECTED_TRACKS) + ".")
        if track in seen:
            raise ValueError(f"Track ‚{track}‘ je ve specu víckrát — pošli každý jednou.")
        seen.add(track)
        if r.get("status") not in VALID_TRIAGE_STATUS:
            raise ValueError(f"Track ‚{track}‘: stav ‚{r.get('status')}‘ neexistuje. Povolené: "
                             + " | ".join(VALID_TRIAGE_STATUS) + ".")
        if track == "discovery":
            score = r.get("discovery_debt_score")
            if score is not None and (isinstance(score, bool) or not isinstance(score, (int, float))
                                      or not 0 <= score <= 10):
                raise ValueError("Discovery: `discovery_debt_score` musí být číslo 0–10 "
                                 f"(dostal jsem ‚{score}‘).")
            text = f"{r.get('rationale') or ''} {r.get('artefact_md') or ''}"
            if re.search(r"(?i)opt-?out", text):
                why = re.sub(r"(?i)^\s*opt-?out\s*[:\u2013\u2014-]?\s*", "",
                             str(r.get("rationale") or "")).strip()
                problems = []
                if r.get("status") == "ok":
                    problems.append("opt-out se nezapisuje jako `ok` — je `deferred` (debt zůstává)")
                if len(why) < 15:
                    problems.append("chybí důvod v `rationale` (aspoň věta, proč personu/JTBD/OST "
                                    "nepotřebujete)")
                if problems:
                    raise ValueError("Opt-out z Discovery není ve správném formátu: "
                                     + "; ".join(problems) + ".\nPříklad:\n" + OPT_OUT_EXAMPLE)



def aggregate(slug: str, results: list[dict[str, Any]]) -> dict[str, Any]:
    """Persist 4 triage outputs + gate decision.

    Args:
        slug: project slug.
        results: list of 4 dicts (1 per track) with keys:
            track, status (ok|blocked|deferred), artefact_md, signed_by, ...

    Returns:
        dict with overall_status, blockers, warnings, summary_path.
    """
    validate_results(results)
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
        if not _human_name(str(disc.get("signed_by") or "")):
            warnings.append("[discovery] opt-out nepotvrdil jmenovitě člověk (Decider) — doplňte "
                            "`signed_by` se jménem; AI opt-out nenahrazuje.")
        opt_out_discovery = True
    else:
        opt_out_discovery = False

    overall = "blocked" if blockers else ("pending" if pending else "ok")
    cond_by_track = {r["track"]: extract_conditions(r) for r in results}
    n_conds = sum(len(v) for v in cond_by_track.values())
    if n_conds:
        listing = ", ".join(f"{t} {v[0]['id']}" + (f"–{v[-1]['id']}" if len(v) > 1 else "")
                            for t, v in cond_by_track.items() if v)
        warnings.append(f"Triage vrátila {n_conds} podmínek/blokací ({listing}) — podpis okna je "
                        "převezme (`pflanzer checkpoint … --waive ID --rationale …` je odpustí), "
                        "SHIP.md, PR a compliance.md je ukážou, prompty Buildu je obsahují.")
    if cond_by_track.get("discovery"):
        warnings.append("[discovery] podmínky " + cond_by_track["discovery"][0]["id"]
                        + " … nejsou splněny jen proto, že je Zadání podepsané — potvrdí je "
                        "re-sign okna `zadani` (nebo je odpusťte s `--waive`).")

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
            store_conditions(conn, project_id, track, cond_by_track[track])
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

    summary_md = render_summary_md(slug, project_id, overall, results, blockers, warnings,
                                   cond_by_track)
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
        "conditions": {t: v for t, v in cond_by_track.items() if v},
        "tracks": {r["track"]: r["status"] for r in results},
    }


def render_summary_md(
    slug: str, project_id: int, overall: str, results: list[dict[str, Any]],
    blockers: list[str], warnings: list[str],
    conditions: dict[str, list[dict[str, str]]] | None = None,
) -> str:
    cond_section = ""
    if conditions and any(conditions.values()):
        cond_section = "\n## Podmínky a blokace z triage\n\n" + "\n".join(
            f"- `{t}` [{c['id']}] {c['text']}" for t, cs in conditions.items() for c in cs) + "\n"
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
{block_section}{cond_section}{warn_section}
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


def _window_row(window: str, label: str, mine: list[dict[str, Any]],
                owner: str | None) -> dict[str, Any]:
    statuses = {t["status"] for t in mine}
    state = ("ok" if statuses == {"ok"} else "blocked" if "blocked" in statuses
             else "pending" if "pending" in statuses
             else "deferred" if "deferred" in statuses else "missing")
    signer = next((t["signed_by"] for t in mine if t["signed_by"]), None)
    return {"window": window, "label": label, "state": state, "owner": owner,
            "signed_by": signer}


def triage_windows(conn: sqlite3.Connection, project_id: int,
                   tracks: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Stav oken (zadani | bezpecnost | provoz) s jmény: kdo má podepsat a čím."""
    tracks = tracks if tracks is not None else triage_tracks(conn, project_id)
    owners = path_owners(conn, project_id)
    decider = conn.execute("SELECT decider_name FROM projects WHERE id = ?",
                           (project_id,)).fetchone()
    out: list[dict[str, Any]] = []
    from tool.cli.checkpoint import (
        MERGED,
        _load_signers,
        _merged_owner,
        _merged_signers,
        merged_applies,
    )
    from tool.cli.checkpoint import WINDOWS as CP_WINDOWS
    if merged_applies(conn, project_id):
        # Pilot bez osobních dat: bezpečnost + provoz (+ právo) = jedno okno se čtyřmi tracky.
        for window, label in WINDOW_LABEL.items():
            if window != "zadani":
                continue
            mine = [t for t in tracks if WINDOW_FOR_TRACK.get(t["track"]) == window]
            out.append(_window_row(window, label, mine, _human_name(
                owners.get(WINDOW_OWNER_KEY[window]))
                or (_human_name(decider[0]) if decider else None)))
        msig = _merged_signers(_load_signers(conn, project_id))
        mowner = _merged_owner(owners, msig)
        merged_who = _human_name(mowner) or _human_name(msig.get("bezpecnost"))
        mine = [t for t in tracks if t["track"] in CP_WINDOWS[MERGED]["tracks"]]
        out.append(_window_row(MERGED, CP_WINDOWS[MERGED]["label"], mine,
                               merged_who))
        return out
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
