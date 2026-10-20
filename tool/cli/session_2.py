"""Rozhodnutí (v0.5; DB `sessions.type = 2`) — Decider's Go / Iterate / Kill.

Rozhodnutí 60–90 min: Decider + jádro, Decider hlasuje poslední (ADR-0001).
Tool zapíše rozhodnutí, vítěze a důvod do DB, do výstupní složky (DATA_ROOT)
a — pokud je cwd target repo s `.pflanzer/` — i do decision logu
`.pflanzer/decisions/<slug>.md` (commitni ho: kdo, kdy, co, proč zůstane v gitu).

Rozhraní:
    pflanzer session_2 prep    --slug S
    pflanzer session_2 decide  --slug S go|iterate|kill --rationale "…"
                               [--winner A|B|C] [--decider "Jméno"]
                               [--override-critical "důvod"] [--iterate-focus "…"]
                               [--variants A,B]   # jen Iterate: varianty druhého kola
                               [--checkpoint "Bezpečnost & právo: ok (Jana)"]...
                               [--force]   # změna už zapsaného Go/Kill; Go pod prahem commitmentu
                                           # (jen s --rationale = důvod)
    pflanzer session_2 resolve --slug S --feedback-id N [N…] --by JMÉNO --note "…"
    (všechny příkazy mají --json pro strojový výstup; default je lidský výstup)

Pravidla:
- **Go vyžaduje `--winner`** (vítězná varianta existující v Buildu: A/B/C, u mob mode `mob`).
- **Otevřený critical feedback na vítězi blokuje Go**, pokud není
  `--override-critical "<důvod>"` (důvod jde do audit logu i decision logu).
  Vyřešený critical (`resolve`) neblokuje.
- **Druhé Go/Kill po platném Go/Kill** se odmítne; změna jen přes `--force --rationale`.
- **Iterate max 1×** (další Build kolo). Třetí kolo = problém je špatně zadaný.
- Decider se bere z projektu (`decider_name`); `--decider` je jen override.
- Kill nevyžaduje vítěze ani nepodléhá blokaci critical. Decision log má sekci „Poučení“
  a seznam critical všech variant; poučení se doplní `pflanzer retro lesson --slug S --text "…"`.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tool.cli._compat import ProjectNotFound, count, exit_if_project_missing, tips  # noqa: E402
from tool.cli.conflict_resolver import detect_conflicts  # noqa: E402
from tool.cli.db import audit, current_actor, display_path, transaction  # noqa: E402
from tool.cli.extract import BRAND, DATA_ROOT, table_has_col  # noqa: E402
from tool.cli.feedback_pull import aggregate as pull_aggregate  # noqa: E402
from tool.cli.feedback_pull import critical_summary_lines  # noqa: E402
from tool.cli.ux import (  # noqa: E402
    CzechArgumentParser,
    did_you_mean,
    die,
    emit,
    plural,
    severity_label,
)

SESSIONS_DIR = DATA_ROOT / "sessions"
VALID_DECISIONS = {"go", "iterate", "kill"}
VALID_VARIANTS = ("A", "B", "C")
COMMITMENT_THRESHOLD = 0.6  # Default; over-ridable per Charter (TODO: schema field)

DECISION_LABEL = {"go": "Go", "iterate": "Iterate", "kill": "Kill"}


# --------------------------------------------------------------------------
# DB helpers (sdílené s Ship / Handoff)
# --------------------------------------------------------------------------


def open_criticals(conn: Any, project_id: int) -> list[dict[str, Any]]:
    """Otevřené critical feedbacky projektu (bez `resolved_at`, pokud sloupec existuje)."""
    clause = " AND f.resolved_at IS NULL" if table_has_col(conn, "feedback", "resolved_at") else ""
    rows = conn.execute(
        "SELECT f.id, v.name, f.department, f.category, f.rationale, f.submitted_by "
        "FROM feedback f JOIN variants v ON v.id = f.variant_id "
        "JOIN sessions s ON s.id = v.session_id "
        f"WHERE s.project_id = ? AND f.severity = 'critical'{clause} ORDER BY f.id",
        (project_id,),
    ).fetchall()
    return [{"id": r[0], "variant": r[1], "department": r[2], "category": r[3],
             "rationale": r[4], "submitted_by": r[5]} for r in rows]


def resolved_criticals(conn: Any, project_id: int) -> list[dict[str, Any]]:
    """Vyřešené critical (kdo a jak: `resolved_note` = „jméno: poznámka“)."""
    if not table_has_col(conn, "feedback", "resolved_at"):
        return []
    rows = conn.execute(
        "SELECT f.id, v.name, f.department, f.rationale, f.submitted_by, f.resolved_note "
        "FROM feedback f JOIN variants v ON v.id = f.variant_id "
        "JOIN sessions s ON s.id = v.session_id "
        "WHERE s.project_id = ? AND f.severity = 'critical' AND f.resolved_at IS NOT NULL "
        "ORDER BY f.id", (project_id,)).fetchall()
    return [{"id": r[0], "variant": r[1], "department": r[2], "rationale": r[3],
             "submitted_by": r[4], "resolved_note": r[5]} for r in rows]


_REASON_PREFIX = re.compile(r"^\s*(?:důvod|duvod|reason)\s*[:\-–—]\s*", re.IGNORECASE)
_DEADLINE_RE = re.compile(
    r"(?i)\b(?:do|until|by)\s+("
    r"\d{1,2}\.\s?\d{1,2}\.(?:\s?\d{2,4})?|\d{4}-\d{2}-\d{2}"
    r"|konce\s+\w+(?:\s+\d{4})?|příštího\s+\w+|\w+\s+\d{4}"
    r"|\d+\s+(?:dnů|dní|dny|den|týdn\w*|měsíc\w*)|\d+\s+days?|\d+\s+weeks?)")


def strip_reason(text: str | None) -> str:
    """Odstraní zdvojený prefix „Důvod:“ (štítek přidává až výstup)."""
    t = (text or "").strip()
    prev = None
    while prev != t:
        prev = t
        t = _REASON_PREFIX.sub("", t).strip()
    return t


def reason_deadline(text: str | None) -> str | None:
    """Termín z důvodu přebití („do 15. 11.“, „do konce Q4“), jinak None."""
    m = _DEADLINE_RE.search(text or "")
    return m.group(0).strip() if m else None


def overridden_criticals(conn: Any, project_id: int) -> list[dict[str, Any]]:
    """Critical na vítězi přebité Deciderem (`--override-critical`): autor nálezu, důvod, termín."""
    rows = conn.execute(
        "SELECT payload_json, ts, actor FROM audit_log WHERE action = 'session_2.decision' "
        "AND target_id = ? ORDER BY id DESC", (project_id,)).fetchall()
    for payload_json, ts, actor in rows:
        try:
            pl = json.loads(payload_json or "{}")
        except json.JSONDecodeError:
            continue
        reason = strip_reason(pl.get("override_critical"))
        ids = [int(x) for x in pl.get("overridden_criticals") or []]
        if not reason or not ids:
            continue
        out: list[dict[str, Any]] = []
        for fid in ids:
            r = conn.execute(
                "SELECT f.id, v.name, f.department, f.rationale, f.submitted_by "
                "FROM feedback f JOIN variants v ON v.id = f.variant_id WHERE f.id = ?",
                (fid,)).fetchone()
            if r:
                out.append({"id": r[0], "variant": r[1], "department": r[2], "rationale": r[3],
                            "submitted_by": r[4], "reason": reason,
                            "deadline": reason_deadline(reason),
                            "decider": pl.get("decider") or actor, "at": str(ts or "")[:10]})
        return out
    return []


def overridden_critical_md(items: list[dict[str, Any]]) -> str:
    """Sekce „Vědomě přebité riziko“ pro SHIP.md i tělo PR (prázdný řetězec, když není co)."""
    if not items:
        return ""
    lines = ["## Vědomě přebité riziko", ""]
    for c in items:
        lines.append(f"- {describe_critical(c)}")
    first = items[0]
    lines += ["",
              f"**Přebil:** {first.get('decider') or 'Decider'} (Decider)"
              + (f", {first['at']}" if first.get("at") else ""),
              f"**Důvod:** {first['reason']}",
              f"**Termín:** {first['deadline'] or 'v důvodu neuveden'}",
              "**Autor nálezu:** "
              + ", ".join(sorted({c.get('submitted_by') or 'neznámý autor' for c in items}))]
    return "\n".join(lines) + "\n"


def describe_critical(c: dict[str, Any], slug: str | None = None) -> str:
    """Lidská věta o otevřeném critical: kdo ho dal, čí krok, na které variantě."""
    text = (c.get("rationale") or "").strip().replace("\n", " ")
    text = text if len(text) <= 90 else text[:87].rsplit(" ", 1)[0] + "…"
    who = c.get("submitted_by") or "neznámý autor"
    return (f"#{c['id']} {who} (krok {c['department']}) na variantě {c['variant']}"
            + (f": „{text}“" if text else ""))


def get_winner(conn: Any, project_id: int) -> str | None:
    """Vítěz z posledního Go (sessions.winner_variant; fallback parse z decision logu)."""
    if table_has_col(conn, "sessions", "winner_variant"):
        row = conn.execute(
            "SELECT winner_variant FROM sessions WHERE project_id = ? AND type = 2 "
            "AND winner_variant IS NOT NULL ORDER BY id DESC LIMIT 1", (project_id,),
        ).fetchone()
        if row and row[0]:
            return str(row[0])
    row = conn.execute(
        "SELECT body_md FROM decisions WHERE project_id = ? AND type = 'handoff' "
        "ORDER BY id DESC LIMIT 1", (project_id,),
    ).fetchone()
    if row:
        m = re.search(r"\*\*Vítěz\*\*:\s*\*\*([\w-]+)\*\*", row[0] or "")
        if m:
            return m.group(1)
    return None


def get_shortlist(conn: Any, project_id: int) -> list[str]:
    """Shortlist z Buildu (audit `session_1.persist`), fallback prázdný seznam."""
    row = conn.execute(
        "SELECT payload_json FROM audit_log WHERE action = 'session_1.persist' "
        "AND target_id IN (SELECT id FROM sessions WHERE project_id = ? AND type = 1) "
        "ORDER BY id DESC LIMIT 1", (project_id,),
    ).fetchone()
    if row and row[0]:
        try:
            return [str(x) for x in json.loads(row[0]).get("shortlist", []) or []]
        except (json.JSONDecodeError, AttributeError):
            return []
    return []


def focus_variants(conn: Any, project_id: int) -> list[str]:
    """Varianty, o kterých se rozhoduje: vítěz z Go, jinak shortlist z Buildu, jinak nejlépe hlasovaná.

    Critical na těchto variantách blokuje Go; critical na ostatních je jen informativní.
    """
    winner = get_winner(conn, project_id)
    if winner:
        return [winner]
    sl = get_shortlist(conn, project_id)
    names = {r[0] for r in conn.execute(
        "SELECT v.name FROM variants v JOIN sessions s ON s.id = v.session_id "
        "WHERE s.project_id = ? AND s.type = 1", (project_id,)).fetchall()}
    sl = [n for n in sl if n in names]
    if sl:
        return sl
    top = conn.execute(
        "SELECT v.name FROM variants v JOIN sessions s ON s.id = v.session_id "
        "WHERE s.project_id = ? AND s.type = 1 ORDER BY v.preference_score DESC, v.name LIMIT 1",
        (project_id,)).fetchone()
    return [top[0]] if top else []


def recommended_winner(conn: Any, project_id: int) -> str:
    """Doporučený `--winner`: vedoucí varianta podle hlasů jádra.

    Varianty bez otevřeného critical mají přednost; při shodě skóre vyhrává ta ze shortlistu
    (potom abecedně). Nikdy natvrdo „B“ — bez variant padá zpět na první z focus / „A“."""
    focus = focus_variants(conn, project_id)
    crit = {c["variant"] for c in open_criticals(conn, project_id)}
    ranked = sorted(_votes_summary(conn, project_id),
                    key=lambda v: (v["variant"] in crit, -v["score"],
                                   v["variant"] not in focus, v["variant"]))
    if ranked:
        return str(ranked[0]["variant"])
    return (focus or ["A"])[0]


def split_criticals(criticals: list[dict[str, Any]], focus: list[str]
                    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """(na vítězi / shortlistu, ostatní)."""
    return ([c for c in criticals if c["variant"] in focus],
            [c for c in criticals if c["variant"] not in focus])


def _votes_summary(conn: Any, project_id: int) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT v.name, v.preference_score, COUNT(rp.id), AVG(rp.commitment_level) "
        "FROM variants v JOIN sessions s ON s.id = v.session_id "
        "LEFT JOIN role_preferences rp ON rp.variant_id = v.id "
        "WHERE s.project_id = ? AND s.type = 1 GROUP BY v.id ORDER BY v.name",
        (project_id,),
    ).fetchall()
    return [{"variant": r[0], "score": round(float(r[1] or 0), 2), "votes": int(r[2] or 0),
             "avg_commitment": round(float(r[3]), 1) if r[3] is not None else None}
            for r in rows]


# --------------------------------------------------------------------------
# Prep
# --------------------------------------------------------------------------


def _top_commitments(conn: Any, project_id: int) -> list[int]:
    """Commitment úrovně (0–3) zástupců u vedoucí varianty Buildu (stejně jako `prep`)."""
    sess1 = conn.execute(
        "SELECT id FROM sessions WHERE project_id = ? AND type = 1", (project_id,)).fetchone()
    if not sess1:
        return []
    top_variant = conn.execute(
        "SELECT id FROM variants WHERE session_id = ? ORDER BY preference_score DESC LIMIT 1",
        (sess1[0],)).fetchone()
    if not top_variant:
        return []
    rows = conn.execute(
        "SELECT commitment_level FROM role_preferences "
        "WHERE variant_id = ? AND commitment_level IS NOT NULL", (top_variant[0],)).fetchall()
    return [int(c[0]) for c in rows]


def prep(slug: str) -> dict[str, Any]:
    """Příprava Rozhodnutí: agregace feedbacku + konflikty. Read-only."""
    agg = pull_aggregate(slug)
    conflicts = detect_conflicts(slug)

    with transaction() as conn:
        proj = conn.execute(
            "SELECT id, status, kill_criteria, xyz_hypothesis, decider_name, session_mode "
            "FROM projects WHERE slug = ?", (slug,),
        ).fetchone()
        if not proj:
            raise ProjectNotFound(slug)
        project_id, status, kill, xyz, decider = (
            int(proj[0]), proj[1], proj[2], proj[3], proj[4],
        )
        session_mode = proj[5] or "parallel"

        commitments = _top_commitments(conn, project_id)
        criticals = open_criticals(conn, project_id)
        resolved_crit = resolved_criticals(conn, project_id)
        iterate_used = conn.execute(
            "SELECT COUNT(*) FROM sessions WHERE project_id = ? AND type = 3",
            (project_id,),
        ).fetchone()[0]
        votes = _votes_summary(conn, project_id)
        shortlist = get_shortlist(conn, project_id)
        focus = focus_variants(conn, project_id)
        recommended = recommended_winner(conn, project_id)

    commitment_index = (
        sum(commitments) / (3 * len(commitments)) if commitments else 0.0
    )  # Normalized 0..1 (max 3 per role)

    return {
        "slug": slug,
        "project_status": status,
        "session_mode": session_mode,
        "decider": decider or current_actor(),
        "xyz": xyz,
        "kill_criteria": kill,
        "commitment_index": round(commitment_index, 3),
        "commitments_count": len(commitments),
        "commitment_threshold": COMMITMENT_THRESHOLD,
        "ready_for_decision": commitment_index >= COMMITMENT_THRESHOLD,
        "variants": votes,
        "shortlist": shortlist,
        "iterate_used": int(iterate_used),
        "iterate_available": int(iterate_used) < 1,
        "feedback_summary": {
            "count": agg["feedback_count"],
            "by_severity": agg["by_severity"],
            "ai_only_ratio": agg["ai_only_ratio"],
            "critical_flags": len(agg["critical_flags"]),
            "open_critical": len(criticals),
            "resolved_critical": len(resolved_crit),
        },
        "open_critical": criticals,
        "focus_variants": focus,
        "recommended_winner": recommended,
        "winner": agg["winner"],
        "critical_on_all_variants": agg["critical_on_all_variants"],
        "conflicts": conflicts["top_conflicts"][:3],  # top 3
        "unmapped_conflicts": conflicts["unmapped_count"],
        "next_action": _suggest_next_action(commitment_index, len(criticals), conflicts),
    }


def _suggest_next_action(
    commitment_index: float, open_critical: int, conflicts: dict[str, Any],
) -> str:
    if open_critical > 0:
        return "RESOLVE_CRITICALS_FIRST"
    if commitment_index < COMMITMENT_THRESHOLD:
        return "GATHER_MORE_FEEDBACK"
    if conflicts["unmapped_count"] > 0:
        return "REVIEW_UNMAPPED_CONFLICTS"
    return "DECIDER_CALL_READY"


# --------------------------------------------------------------------------
# Resolve critical
# --------------------------------------------------------------------------


def resolve_feedback(*, slug: str, feedback_ids: list[int], note: str | None = None,
                     by: str | None = None) -> dict[str, Any]:
    """Označ critical feedback jako vyřešený (opraveno / varianta ven / mimo scope).

    `by` (kdo to vyřešil) i `note` (jak) jsou povinné; neexistující id je chyba.
    """
    if not (by or "").strip():
        raise ValueError("Chybí --by: kdo feedback vyřešil (jméno z Kickoffu).")
    if not (note or "").strip():
        raise ValueError("Chybí --note: jak byl problém vyřešen (opraveno v PR, varianta ven…).")
    by, note = by.strip(), note.strip()
    with transaction() as conn:
        proj = conn.execute("SELECT id FROM projects WHERE slug = ?", (slug,)).fetchone()
        if not proj:
            raise ProjectNotFound(slug)
        if not table_has_col(conn, "feedback", "resolved_at"):
            raise RuntimeError("DB nemá sloupec feedback.resolved_at - spusť `pflanzer update` "
                               "(migrace).")
        pid = int(proj[0])
        known = {r[0]: r for r in conn.execute(
            "SELECT f.id, v.name, f.severity FROM feedback f JOIN variants v ON v.id = f.variant_id "
            "JOIN sessions s ON s.id = v.session_id WHERE s.project_id = ?", (pid,)).fetchall()}
        missing = [f for f in feedback_ids if f not in known]
        if missing:
            raise ValueError(
                "Feedback " + ", ".join(f"#{m}" for m in missing) + f" v projektu {slug} neexistuje. "
                f"Seznam: `pflanzer feedback list --slug {slug}`.")
        done: list[int] = []
        for fid in feedback_ids:
            conn.execute("UPDATE feedback SET resolved_at = CURRENT_TIMESTAMP, resolved_note = ? "
                         "WHERE id = ?", (f"{by}: {note}", fid))
            done.append(fid)
        audit(conn, action="session_2.resolve_feedback", target_type="project",
              target_id=pid, payload={"slug": slug, "resolved": done, "by": by, "note": note})
        remaining = open_criticals(conn, pid)
        focus = focus_variants(conn, pid)
        recommended = recommended_winner(conn, pid)
    on_win, other = split_criticals(remaining, focus)
    return {"slug": slug, "resolved": done, "not_found": [], "by": by, "note": note,
            "open_critical_left": len(remaining), "open_critical": remaining,
            "focus_variants": focus, "recommended_winner": recommended,
            "open_critical_on_winner": on_win,
            "open_critical_other": other}


# --------------------------------------------------------------------------
# Decide
# --------------------------------------------------------------------------


def record_decision(
    *, slug: str, decision: str, rationale: str,
    decider_attribution: str | None = None,
    iterate_focus: str | None = None,
    winner: str | None = None,
    override_critical: str | None = None,
    checkpoints: list[str] | None = None,
    force: bool = False,
    iterate_variants: list[str] | str | None = None,
) -> dict[str, Any]:
    """Persist Decider's call (idempotentní per projekt: jedna session type=2)."""
    if decision not in VALID_DECISIONS:
        near = did_you_mean(decision, sorted(VALID_DECISIONS))
        raise ValueError(f"Neznámé rozhodnutí „{decision}“."
                         + (f" Myslel jste „{near}“?" if near else "")
                         + " Možnosti: go, iterate, kill.")
    if not rationale or not rationale.strip():
        raise ValueError("--rationale je POVINNÉ (decision log: kdo, co, proč; DORA / AI Act čl. 14).")
    winner = winner.strip() if winner else None
    override_critical = strip_reason(override_critical) or None
    rationale = strip_reason(rationale) or rationale
    checkpoints = [c.strip() for c in (checkpoints or []) if c and c.strip()]
    if decision == "go" and not winner:
        raise ValueError(
            "Go vyžaduje --winner <varianta> (vítězná varianta, kterou půjde Ship; "
            "u mob mode `mob`, jinak A, B nebo C). "
            f"Příklad: pflanzer session_2 decide --slug {slug} go --winner A --rationale \"…\""
        )
    if decision != "go":
        winner = None  # vítěz dává smysl jen u Go
    if isinstance(iterate_variants, str):
        iterate_variants = [x for x in re.split(r"[,\s]+", iterate_variants) if x]
    iterate_variants = [str(x).strip() for x in (iterate_variants or []) if str(x).strip()]
    if iterate_variants and decision != "iterate":
        raise ValueError("--variants patří jen k Iterate (které varianty jdou do druhého kola).")

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    with transaction() as conn:
        proj = conn.execute(
            "SELECT id, status, decider_name FROM projects WHERE slug = ?", (slug,),
        ).fetchone()
        if not proj:
            raise ProjectNotFound(slug)
        project_id = int(proj[0])
        decider = (decider_attribution or "").strip() or (proj[2] or "").strip() or current_actor()

        # Druhé Go/Kill po platném Go/Kill: jen přes --force --rationale (rationale je povinné vždy).
        prev = conn.execute(
            "SELECT decision, winner_variant FROM sessions WHERE project_id = ? AND type = 2 "
            "ORDER BY id DESC LIMIT 1", (project_id,),
        ).fetchone() if table_has_col(conn, "sessions", "winner_variant") else None
        if prev and prev[0] in ("go", "kill") and proj[1] in ("handoff", "killed") and not force:
            what = f"Go ({prev[1]})" if prev[0] == "go" and prev[1] else DECISION_LABEL[prev[0]]
            new_win = winner or prev[1] or "A"
            raise ValueError(
                f"Už je {what}. Změna jen přes `--force --rationale \"…\"`, např. "
                f"`pflanzer session_2 decide --slug {slug} {decision} "
                f"{f'--winner {new_win} ' if decision == 'go' else ''}--force "
                f"--rationale \"proč měníme rozhodnutí\"`; původní rozhodnutí zůstane "
                f"v decision logu."
            )
        variants = [r[0] for r in conn.execute(
            "SELECT v.name FROM variants v JOIN sessions s ON s.id = v.session_id "
            "WHERE s.project_id = ? AND s.type = 1", (project_id,)).fetchall()]
        if winner:   # velikost písmen nerozhoduje: `a` = `A`, `MOB` = `mob`
            by_lower = {v.lower(): v for v in variants}
            winner = by_lower.get(winner.lower(), winner.upper() if not variants else winner)
        if iterate_variants:
            by_lower = {v.lower(): v for v in variants}
            bad = [x for x in iterate_variants if x.lower() not in by_lower]
            if bad:
                raise ValueError(
                    f"--variants {','.join(bad)}: varianta v Buildu neexistuje "
                    f"(jsou: {', '.join(sorted(variants)) or 'žádné'}). "
                    f"Příklad: --variants {','.join(sorted(variants)[:2]) or 'A,B'}")
            iterate_variants = sorted(dict.fromkeys(by_lower[x.lower()] for x in iterate_variants))
        if winner and winner not in variants:
            raise ValueError(
                f"--winner {winner}: varianta '{winner}' v Buildu neexistuje (jsou: {', '.join(sorted(variants)) or 'žádné'})."
            )

        # Critical na vítězi blokuje Go (poražené varianty do produkce nejdou).
        # Iterate neblokuje — právě v něm se critical opravuje; Kill taky ne.
        criticals = [c for c in open_criticals(conn, project_id)
                     if decision == "go" and c["variant"] == winner]
        if criticals and not override_critical:
            listing = "; ".join(describe_critical(c) for c in criticals[:3])
            first = criticals[0]
            raise ValueError(
                f"Otevřený critical ({len(criticals)}×) blokuje {DECISION_LABEL[decision]}: {listing}. "
                f"Vyřeš ho s autorem ({first.get('submitted_by') or 'autor'}): "
                f"`pflanzer session_2 resolve --slug {slug} --feedback-id {first['id']} "
                f"--by JMÉNO --note \"co se opravilo\"`, nebo Decider přebije: "
                f"`--override-critical \"důvod\"`."
            )

        # Go pod prahem commitmentu: jen vědomě (--force + důvod), ať hláška „na Go stačí 60 %“
        # a zápis Go nejsou ve sporu.
        below_commitment: float | None = None
        if decision == "go":
            commits = _top_commitments(conn, project_id)
            idx = sum(commits) / (3 * len(commits)) if commits else None
            if idx is not None and idx < COMMITMENT_THRESHOLD - 1e-9:
                below_commitment = round(idx, 3)
                if not force:
                    raise ValueError(
                        f"Tým se za vedoucí variantu postaví jen z {idx:.0%}, na Go stačí "
                        f"{COMMITMENT_THRESHOLD:.0%}. Nejdřív doplňte feedback "
                        f"(`pflanzer feedback_pull --slug {slug}`), nebo Decider jde do Go vědomě: "
                        f"`pflanzer session_2 decide --slug {slug} go --winner {winner} --force "
                        f"--rationale \"proč Go i pod prahem\"` (důvod půjde do decision logu).")
                rationale = (f"[Go pod prahem commitmentu: {idx:.0%} < "
                             f"{COMMITMENT_THRESHOLD:.0%}, vědomě přes --force] " + rationale)

        sess = conn.execute(
            "SELECT id FROM sessions WHERE project_id = ? AND type = 2", (project_id,),
        ).fetchone()

        iterate_round = 0
        if decision == "iterate":
            iterate_round = conn.execute(
                "SELECT COUNT(*) FROM sessions WHERE project_id = ? AND type = 3", (project_id,),
            ).fetchone()[0]
            if iterate_round >= 1:
                raise ValueError(
                    "Iterate už proběhlo 1× (max 1×). Třetí kolo = problém je špatně zadaný "
                    "→ zpět na Kickoff (`/pm start`), nebo Go / Kill."
                )

        # --- zápisy ---------------------------------------------------------
        if sess:
            session_id = int(sess[0])
            conn.execute(
                "UPDATE sessions SET decision = ?, decision_atribuce = ?, "
                "decision_ts = CURRENT_TIMESTAMP, ends_at = CURRENT_TIMESTAMP WHERE id = ?",
                (decision, decider, session_id),
            )
        else:
            cur = conn.execute(
                "INSERT INTO sessions (project_id, type, starts_at, ends_at, "
                "decision, decision_atribuce, decision_ts) VALUES (?, 2, ?, ?, ?, ?, ?)",
                (project_id, now, now, decision, decider, now),
            )
            session_id = cur.lastrowid
        if table_has_col(conn, "sessions", "winner_variant"):
            conn.execute(
                "UPDATE sessions SET winner_variant = ?, override_critical_reason = ? WHERE id = ?",
                (winner, override_critical, session_id),
            )

        if decision == "iterate":
            conn.execute(
                "INSERT INTO sessions (project_id, type, starts_at, decision, notes_md) "
                "VALUES (?, 3, ?, 'pending', ?)",
                (project_id, now, iterate_focus or rationale),
            )

        votes = _votes_summary(conn, project_id)
        all_open = open_criticals(conn, project_id) if decision == "kill" else []
        decision_md = render_decision_md(
            slug, decision, rationale, decider, iterate_focus,
            iterate_variants=iterate_variants, winner=winner, override_critical=override_critical,
            criticals=criticals, votes=votes, checkpoints=checkpoints,
            all_criticals=all_open,
        )
        conn.execute(
            "INSERT INTO decisions (project_id, type, body_md, atribuce_user, atribuce_ts) "
            "VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
            (project_id,
             "kill" if decision == "kill" else ("handoff" if decision == "go" else "preference"),
             decision_md, decider),
        )

        new_status = {"go": "handoff", "iterate": "session_2", "kill": "killed"}[decision]
        conn.execute(
            "UPDATE projects SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (new_status, project_id),
        )

        audit(
            conn,
            action="session_2.decision",
            target_type="project",
            target_id=project_id,
            payload={
                "slug": slug, "decision": decision, "winner": winner,
                "decider": decider,
                "iterate_focus": iterate_focus,
                "iterate_variants": iterate_variants,
                "override_critical": override_critical,
                "overridden_criticals": [c["id"] for c in criticals] if override_critical else [],
                "forced": bool(force),
                "below_commitment": below_commitment,
                "checkpoints": checkpoints,
            },
        )

    summary_path = _write_summary(slug, project_id, session_id, decision_md)
    repo_log = write_repo_decision_log(slug, decision_md, label=DECISION_LABEL[decision])

    out: dict[str, Any] = {
        "project_id": project_id,
        "session_id": session_id,
        "slug": slug,
        "decision": decision,
        "winner": winner,
        "decider": decider,
        "new_status": new_status,
        "override_critical": override_critical,
        "open_critical_overridden": len(criticals) if override_critical else 0,
        "below_commitment": below_commitment,
        "summary_path": display_path(summary_path),
        "decision_log_repo": repo_log,
        "next_step": _next_step_label(decision, slug, winner),
    }
    if decision == "iterate":
        out["iterate_variants"] = iterate_variants
        out["iterate_variants_dropped"] = (sorted(set(variants) - set(iterate_variants))
                                           if iterate_variants else [])
    if decision == "kill":
        from tool.cli.status import cleanup_steps
        out["cleanup"] = cleanup_steps(slug)
    if repo_log:
        out["git_commands"] = decision_log_git_commands(slug, repo_log, DECISION_LABEL[decision])
        out["hint"] = ("Decision log je zatím jen lokálně — do originu: "
                       + " && ".join(out["git_commands"]))
    else:
        out["hint"] = ("cwd neobsahuje `.pflanzer/` - decision log je jen ve výstupní složce "
                       "(`pflanzer data`). Spusť příkaz z target repa, ať ho můžeš commitnout.")
    return out


def decision_log_git_commands(slug: str, repo_log: str, label: str) -> list[str]:
    """Přesné příkazy, kterými decision log (a podpisy oken) dojdou do originu. Tool je nespouští."""
    return [f"git add {repo_log}",
            f'git commit -m "docs({slug}): decision log — {label}"',
            "git push -u origin HEAD"]


def render_decision_md(
    slug: str, decision: str, rationale: str, decider: str, iterate_focus: str | None,
    *, winner: str | None = None, override_critical: str | None = None,
    iterate_variants: list[str] | None = None,
    criticals: list[dict[str, Any]] | None = None,
    votes: list[dict[str, Any]] | None = None, checkpoints: list[str] | None = None,
    all_criticals: list[dict[str, Any]] | None = None,
) -> str:
    when = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M %Z").strip()
    lines = [
        f"## Rozhodnutí — {DECISION_LABEL[decision]}",
        "",
        f"- **Rozhodnutí**: **{decision.upper()}**",
        f"- **Projekt**: `{slug}`",
        f"- **Decider**: {decider} · {when}",
    ]
    if winner:
        lines.append(f"- **Vítěz**: **{winner}**")
    lines += ["", "### Důvod", "", rationale.strip(), ""]
    if votes:
        lines += ["### Hlasy jádra (agregované skóre variant)", "",
                  "| Varianta | Skóre | Hlasů | Prům. závaznost |", "|---|---|---|---|"]
        for v in votes:
            mark = " (vítěz)" if winner == v["variant"] else ""
            ac = v["avg_commitment"] if v["avg_commitment"] is not None else "—"
            lines.append(f"| {v['variant']}{mark} | {v['score']:.2f} | {v['votes']} | {ac} |")
        lines.append("")
    if override_critical:
        lines += ["### Override critical", "", f"Důvod: {strip_reason(override_critical)}", ""]
        for c in criticals or []:
            lines.append(f"- {describe_critical(c)}")
        lines.append("")
    if checkpoints:
        lines += ["### Checkpointy", ""] + [f"- {c}" for c in checkpoints] + [""]
    if decision == "iterate":
        lines += ["### Iterate (max 1×)", "", (iterate_focus or rationale).strip(), ""]
        if iterate_variants:
            lines += [f"Do druhého kola jdou: **{', '.join(iterate_variants)}** "
                      "(ostatní varianty končí).", ""]
    if decision == "kill":
        lines += ["### Critical všech variant (v době Kill)", ""]
        if all_criticals:
            lines += [f"- {describe_critical(c)}" for c in all_criticals]
        else:
            lines.append("- žádné otevřené")
        lines.append("")
    return "\n".join(lines)


def _next_step_label(decision: str, slug: str, winner: str | None = None) -> str:
    if decision == "go":
        return (f"`/pm ship {slug}` — quality gates na vítěze ({winner}), checkpoint provozu, PR. "
                "Pak `/pm handoff`.")
    if decision == "iterate":
        return (f"`/pm build {slug}` — jedno další Build kolo (jen to, co se mění), pak znovu "
                f"`/pm feedback {slug}` a `/pm decide {slug}`. **Max 1× Iterate.**")
    return (f"Projekt ukončen (Kill). Zapiš poučení: "
            f"`pflanzer retro lesson --slug {slug} --text \"co jsme se dozvěděli\"`.")


def _write_summary(slug: str, project_id: int, session_id: int, decision_md: str) -> Path:
    project_dir = SESSIONS_DIR / slug
    project_dir.mkdir(parents=True, exist_ok=True)
    md = f"{BRAND}\n\n# Rozhodnutí — {slug}\n\n> Project ID: {project_id} · Session ID: {session_id}\n\n{decision_md}"
    out = project_dir / "_session_2_summary.md"
    out.write_text(md, encoding="utf-8")
    return out


def write_repo_decision_log(slug: str, section_md: str, *, label: str) -> str | None:
    """Append sekci do `.pflanzer/decisions/<slug>.md` v cwd (target repo). None, pokud cwd není target repo.

    Vrací cestu relativní k cwd. Nikdy neselže hlasitě - decision log v DB je zdroj pravdy.
    """
    base = Path.cwd() / ".pflanzer"
    if not base.is_dir():
        return None
    try:
        log_dir = base / "decisions"
        log_dir.mkdir(parents=True, exist_ok=True)
        path = log_dir / f"{slug}.md"
        if not path.exists():
            path.write_text(
                f"{BRAND}\n\n# Decision log — {slug}\n\n"
                "> Kdo, kdy, co a proč. Commitni spolu s kódem. Zdroj pravdy je DB toolu, "
                "tento soubor je kopie pro git.\n\n", encoding="utf-8")
        today = datetime.now().astimezone().strftime("%Y-%m-%d")
        with path.open("a", encoding="utf-8") as fh:
            fh.write(f"\n---\n\n<!-- {today} · {label} -->\n\n{section_md.rstrip()}\n")
        return str(path.relative_to(Path.cwd()))
    except OSError:
        return None


def append_lesson_to_log(slug: str, text: str, who: str) -> str | None:
    """Poučení do `.pflanzer/decisions/<slug>.md`: jedna sekce „### Poučení“, další jen odrážky."""
    bullet = f"- {text} — {who}"
    path = Path.cwd() / ".pflanzer" / "decisions" / f"{slug}.md"
    try:
        body = path.read_text(encoding="utf-8")
    except OSError:
        return write_repo_decision_log(slug, f"### Poučení\n\n{bullet}\n", label="Poučení")
    idx = body.rfind("### Poučení")
    if idx != -1 and "\n---" not in body[idx:] and "\n## " not in body[idx:]:
        try:
            path.write_text(body.rstrip("\n") + f"\n{bullet}\n", encoding="utf-8")
            return str(path.relative_to(Path.cwd()))
        except OSError:
            return None
    return write_repo_decision_log(slug, f"### Poučení\n\n{bullet}\n", label="Poučení")


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def _prep_view(out: dict[str, Any]) -> tuple[str, list[str], list[str], str, dict[str, Any]]:
    slug = out["slug"]
    crit = out["open_critical"]
    focus = out.get("focus_variants") or []
    on_win, other = split_criticals(crit, focus)
    lines: list[str] = []
    ranked = sorted(out["variants"], key=lambda v: -v["score"])
    if ranked:
        lines.append("Hlasy jádra: " + ", ".join(
            f"{v['variant']} {v['score']:.2f} ({count(v['votes'], 'hlas', 'hlasy', 'hlasů')})"
            for v in ranked[:3]))
    if out.get("session_mode") == "mob" or [v["variant"] for v in out["variants"]] == ["mob"]:
        lines.append("Mob mode: stavěla se jedna společná varianta, takže není co porovnávat. "
                     "Decider rozhoduje, jestli výsledek jde do Shipu (Go), nebo se doladí (Iterate).")
    fb = out["feedback_summary"]
    n_open, n_res = fb.get("open_critical", 0), fb.get("resolved_critical", 0)

    def _sev_item(k: str, n: int) -> str:
        if k == "critical" and n_res:
            note = ("vyřešeno" if not n_open else
                    f"otevřených {n_open}, vyřešeno {n_res}")
            return f"{severity_label(k)}: {n} ({note})"
        return f"{severity_label(k)}: {n}"

    sev = ", ".join(_sev_item(k, n) for k, n in
                    sorted(fb["by_severity"].items(), key=lambda kv: ["critical", "high", "medium",
                                                                       "low"].index(kv[0])
                           if kv[0] in ("critical", "high", "medium", "low") else 9))
    lines.append(f"Feedback: {fb['count']}" + (f" ({sev})" if sev else ""))
    lines += critical_summary_lines(crit, focus, out.get("winner"),
                                    out.get("critical_on_all_variants", False))
    if out.get("commitments_count"):
        lines.append(f"Jak moc se tým za vedoucí variantu postaví: {out['commitment_index']:.0%} "
                     f"(na Go stačí {out['commitment_threshold']:.0%}"
                     + ("" if out["ready_for_decision"] else
                        "; pod prahem jde Go jen vědomě přes `--force` s důvodem")
                     + ")")
    for c in out["conflicts"][:1]:
        lines.append(f"Hlavní spor u varianty {c['variant']}: {c['role_a']['label']} vs. "
                     f"{c['role_b']['label']}")
    if on_win:
        c0 = on_win[0]
        nxt = (f"kritické #{c0['id']} ({c0['submitted_by']}) na variantě {c0['variant']}: buď ho "
               f"oprav a `pflanzer session_2 resolve --slug {slug} --feedback-id {c0['id']} --by JMÉNO "
               f"--note \"…\"`, nebo na Rozhodnutí zvolte Iterate s cílem ho opravit "
               f"(`pflanzer session_2 decide --slug {slug} iterate --variants {','.join(focus or ['A'])} --iterate-focus \"…\" --rationale \"…\"`)")
    elif not out["ready_for_decision"]:
        nxt = ("tým se zatím dost pevně nepostavil za žádnou variantu — sežeň víc hlasů "
               f"a feedbacku: `pflanzer feedback add --slug {slug} --variant A --role Produkt "
               "--severity major --text \"…\"`")
    else:
        nxt = (f"Decider rozhodne: `pflanzer session_2 decide --slug {slug} go "
               f"--winner {out.get('recommended_winner') or (focus or ['A'])[0]} "
               "--rationale \"proč\"`")
    return (f"Příprava Rozhodnutí: {slug}", lines[:8], [], nxt,
            {"open_critical": bool(on_win)})


def _decision_view(out: dict[str, Any]) -> tuple[str, list[str], list[str], str, str]:
    slug, dec = out["slug"], out["decision"]
    label = DECISION_LABEL[dec]
    lines = [f"Rozhodl: {out['decider']}"]
    if out.get("winner"):
        lines.append(f"Vítěz: {out['winner']}")
    if out.get("below_commitment") is not None:
        lines.append(f"Go pod prahem commitmentu ({out['below_commitment']:.0%} < "
                     f"{COMMITMENT_THRESHOLD:.0%}) zapsáno vědomě přes --force; důvod je v decision logu.")
    if out.get("override_critical"):
        lines.append("Decider přebil "
                     + plural(out["open_critical_overridden"], "kritický", "kritické", "kritických")
                     + f": {out['override_critical']}")
    lines.append("Zapsáno do decision logu"
                 + (f" ({out['decision_log_repo']}) — zatím jen v pracovní kopii, do originu ho "
                    "dostaneš až commitem a pushem:" if out.get("decision_log_repo")
                    else "; z target repa se zapíše i do `.pflanzer/decisions/`."))
    for cmd in out.get("git_commands") or []:
        lines.append(f"    {cmd}")
    nxt = out["next_step"]
    phase = ("iterate" if dec == "iterate" else "after_go" if dec == "go"
             else "after_kill" if dec == "kill" else "decide")
    if dec == "iterate" and out.get("iterate_variants"):
        lines.append("Do druhého kola jdou: " + ", ".join(out["iterate_variants"])
                     + (f" (vypadly: {', '.join(out['iterate_variants_dropped'])})"
                        if out.get("iterate_variants_dropped") else ""))
    elif dec == "iterate":
        lines.append("Varianty druhého kola nebyly určeny — jdou ty z hlasování Buildu "
                     "(příště: `--variants A,B`).")
    if dec == "kill":
        for step in out.get("cleanup") or []:
            lines.append("Úklid: " + step)
        nxt = (f"zapiš 1–3 poučení: `pflanzer retro lesson --slug {slug} "
               "--text \"co jsme se dozvěděli o problému, uživatelích nebo zadání\"`")
    return f"Rozhodnutí {slug}: {label}", lines, [], nxt, phase


RESOLVE_EXAMPLE = ('pflanzer session_2 resolve --slug moje-appka --feedback-id 3 '
                   '--by Ondra --note "opraveno v PR #12"')
DECIDE_EXAMPLE = ('pflanzer session_2 decide --slug moje-appka go --winner A '
                  '--rationale "A je nejrychlejší a bezpečnost je v pořádku"')


def main() -> None:
    p = CzechArgumentParser(prog="pflanzer session_2", description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True, parser_class=CzechArgumentParser)

    p_prep = sub.add_parser("prep", help="Příprava Rozhodnutí: agregace + spory (read-only)")
    p_prep.add_argument("--slug", required=True)
    p_prep.add_argument("--json", action="store_true")

    p_dec = sub.add_parser("decide", help="Zapiš Go / Iterate / Kill")
    p_dec.add_argument("--slug", required=True)
    p_dec.add_argument("decision_pos", nargs="?", metavar="{go,iterate,kill}",
                       help="rozhodnutí (alternativa k --decision)")
    p_dec.add_argument("--decision", default=None, metavar="{go,iterate,kill}")
    p_dec.add_argument("--rationale", default=None, help="důvod, 1–2 věty (povinné)")
    p_dec.add_argument("--winner", default=None, help="vítěz: varianta z Buildu (A, B, C; u mob mode `mob`); povinné u Go")
    p_dec.add_argument("--decider", default=None,
                       help="override; default = decider_name z projektu")
    p_dec.add_argument("--override-critical", default=None, metavar="DŮVOD",
                       help="Decider přebíjí otevřený critical (důvod do auditu a decision logu)")
    p_dec.add_argument("--iterate-focus", default=None)
    p_dec.add_argument("--variants", default=None, metavar="A,B",
                       help="jen u Iterate: které varianty jdou do druhého kola (čárkou, např. A,B)")
    p_dec.add_argument("--checkpoint", action="append", default=[],
                       help="záznam checkpointu (opakovatelné), např. 'Bezpečnost & právo: ok (Jana)'")
    p_dec.add_argument("--force", action="store_true",
                       help="změň už zapsané Go/Kill, nebo jdi do Go pod prahem commitmentu (vždy s --rationale)")
    p_dec.add_argument("--json", action="store_true")

    p_res = sub.add_parser("resolve", help="Označ critical feedback jako vyřešený")
    p_res.add_argument("--slug", required=True)
    p_res.add_argument("--feedback-id", type=int, nargs="+", required=True)
    p_res.add_argument("--by", default=None, help="kdo to vyřešil (povinné)")
    p_res.add_argument("--note", default=None, help="jak se to vyřešilo (povinné)")
    p_res.add_argument("--json", action="store_true")

    args = p.parse_args()

    try:
        if args.cmd == "prep":
            out = prep(args.slug)
            title, lines, warns, nxt, ctx = _prep_view(out)
            emit(out, title=title, lines=lines, warnings=warns, next_step=nxt,
                 tips=tips(args.slug, "decide", ctx), as_json=args.json)
        elif args.cmd == "resolve":
            out = resolve_feedback(slug=args.slug, feedback_ids=args.feedback_id,
                                   note=args.note, by=args.by)
            who = f"{out['by']}: {out['note']}"
            on_win, other = out["open_critical_on_winner"], out["open_critical_other"]
            focus = out["focus_variants"]
            ids = ", ".join("#" + str(i) for i in out["resolved"])
            if on_win:
                left_line = (f"Zbývá otevřených kritických: {len(on_win)} na vítězi"
                             f" ({'/'.join(focus)}), {len(other)} ostatní")
                nxt = (f"`pflanzer session_2 resolve --slug {args.slug} --feedback-id "
                       f"{on_win[0]['id']} --by JMÉNO --note \"…\"`")
                phase = "decide"
            else:
                left_line = ("Na vítězi" + (f" ({'/'.join(focus)})" if focus else "")
                             + " žádný kritický nezbývá"
                             + (f"; {len(other)} ostatní na poražených variantách Go neblokuje."
                                if other else "."))
                nxt = (f"`pflanzer session_2 decide --slug {args.slug} go "
                       f"--winner {out.get('recommended_winner') or (focus or ['A'])[0]} "
               "--rationale \"proč\"`")
                phase = "after_resolve"
            emit(out, title=f"Vyřešeno: {ids}",
                 lines=[f"Vyřešeno: {ids} ({who})", left_line],
                 next_step=nxt,
                 tips=tips(args.slug, phase, {"open_critical": bool(on_win)}, fallback="decide"),
                 as_json=args.json)
        else:
            decision = args.decision_pos or args.decision
            if not decision:
                die("Chybí rozhodnutí: go, iterate, nebo kill.", DECIDE_EXAMPLE)
            if decision not in VALID_DECISIONS:
                near = did_you_mean(decision, sorted(VALID_DECISIONS))
                die(f"Neznámé rozhodnutí „{decision}“."
                    + (f" Myslel jste „{near}“?" if near else "")
                    + " Možnosti: go, iterate, kill.", DECIDE_EXAMPLE)
            if args.decision_pos and args.decision and args.decision_pos != args.decision:
                die("Rozhodnutí je zadané dvakrát a různě.", DECIDE_EXAMPLE)
            out = record_decision(
                slug=args.slug, decision=decision, rationale=args.rationale or "",
                iterate_focus=args.iterate_focus, decider_attribution=args.decider,
                winner=args.winner, override_critical=args.override_critical,
                checkpoints=args.checkpoint, force=args.force,
                iterate_variants=args.variants,
            )
            title, lines, warns, nxt, phase = _decision_view(out)
            emit(out, title=title, lines=lines, warnings=warns, next_step=nxt,
                 tips=tips(args.slug, phase, {}, fallback="decide"), as_json=args.json)
    except ValueError as e:
        exit_if_project_missing(e)
        msg = str(e)
        die(msg, {"resolve": RESOLVE_EXAMPLE, "decide": DECIDE_EXAMPLE}.get(args.cmd, "")
            if ("--by" in msg or "--note" in msg or "--rationale" in msg or "--winner" in msg)
            else "")


if __name__ == "__main__":
    main()
