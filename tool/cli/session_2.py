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
                               [--checkpoint "Bezpečnost & právo: ok (Jana)"]...
                               [--force]   # změna už zapsaného Go/Kill (jen s --rationale)
    pflanzer session_2 resolve --slug S --feedback-id N [N…] --by JMÉNO --note "…"
    (všechny příkazy mají --json pro strojový výstup; default je lidský výstup)

Pravidla:
- **Go vyžaduje `--winner`** (vítězná varianta A/B/C existující v Buildu).
- **Otevřený critical feedback na vítězi blokuje Go**, pokud není
  `--override-critical "<důvod>"` (důvod jde do audit logu i decision logu).
  Vyřešený critical (`resolve`) neblokuje.
- **Druhé Go/Kill po platném Go/Kill** se odmítne; změna jen přes `--force --rationale`.
- **Iterate max 1×** (další Build kolo). Třetí kolo = problém je špatně zadaný.
- Decider se bere z projektu (`decider_name`); `--decider` je jen override.
- Kill nevyžaduje vítěze ani nepodléhá blokaci critical.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tool.cli.conflict_resolver import detect_conflicts  # noqa: E402
from tool.cli.db import audit, current_actor, display_path, transaction  # noqa: E402
from tool.cli.extract import BRAND, DATA_ROOT, table_has_col  # noqa: E402
from tool.cli.feedback_pull import aggregate as pull_aggregate  # noqa: E402
from tool.cli.ux import die, emit, severity_label, tips_for  # noqa: E402

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
        m = re.search(r"\*\*Vítěz\*\*:\s*\*\*([A-C])\*\*", row[0] or "")
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


def prep(slug: str) -> dict[str, Any]:
    """Příprava Rozhodnutí: agregace feedbacku + konflikty. Read-only."""
    agg = pull_aggregate(slug)
    conflicts = detect_conflicts(slug)

    with transaction() as conn:
        proj = conn.execute(
            "SELECT id, status, kill_criteria, xyz_hypothesis, decider_name "
            "FROM projects WHERE slug = ?", (slug,),
        ).fetchone()
        if not proj:
            raise ValueError(f"Project '{slug}' not found.")
        project_id, status, kill, xyz, decider = (
            int(proj[0]), proj[1], proj[2], proj[3], proj[4],
        )

        sess1 = conn.execute(
            "SELECT id FROM sessions WHERE project_id = ? AND type = 1",
            (project_id,),
        ).fetchone()
        commitments: list[int] = []
        if sess1:
            top_variant = conn.execute(
                "SELECT id FROM variants WHERE session_id = ? "
                "ORDER BY preference_score DESC LIMIT 1", (sess1[0],),
            ).fetchone()
            if top_variant:
                commit_rows = conn.execute(
                    "SELECT commitment_level FROM role_preferences "
                    "WHERE variant_id = ? AND commitment_level IS NOT NULL",
                    (top_variant[0],),
                ).fetchall()
                commitments = [int(c[0]) for c in commit_rows]
        criticals = open_criticals(conn, project_id)
        iterate_used = conn.execute(
            "SELECT COUNT(*) FROM sessions WHERE project_id = ? AND type = 3",
            (project_id,),
        ).fetchone()[0]
        votes = _votes_summary(conn, project_id)
        shortlist = get_shortlist(conn, project_id)

    commitment_index = (
        sum(commitments) / (3 * len(commitments)) if commitments else 0.0
    )  # Normalized 0..1 (max 3 per role)

    return {
        "slug": slug,
        "project_status": status,
        "decider": decider or current_actor(),
        "xyz": xyz,
        "kill_criteria": kill,
        "commitment_index": round(commitment_index, 3),
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
        },
        "open_critical": criticals,
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
            raise ValueError(f"Project '{slug}' not found.")
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
    return {"slug": slug, "resolved": done, "not_found": [], "by": by, "note": note,
            "open_critical_left": len(remaining), "open_critical": remaining}


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
) -> dict[str, Any]:
    """Persist Decider's call (idempotentní per projekt: jedna session type=2)."""
    if decision not in VALID_DECISIONS:
        raise ValueError(f"decision must be one of {sorted(VALID_DECISIONS)}")
    if not rationale or not rationale.strip():
        raise ValueError("--rationale je POVINNÉ (decision log: kdo, co, proč; DORA / AI Act čl. 14).")
    winner = winner.strip().upper() if winner else None
    if winner and winner not in VALID_VARIANTS:
        raise ValueError(f"--winner musí být jedna z {', '.join(VALID_VARIANTS)}, ne '{winner}'.")
    override_critical = (override_critical or "").strip() or None
    checkpoints = [c.strip() for c in (checkpoints or []) if c and c.strip()]
    if decision == "go" and not winner:
        raise ValueError(
            "Go vyžaduje --winner <A|B|C> (vítězná varianta, kterou půjde Ship). "
            f"Příklad: pflanzer session_2 decide --slug {slug} go --winner A --rationale \"…\""
        )
    if decision != "go":
        winner = None  # vítěz dává smysl jen u Go

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    with transaction() as conn:
        proj = conn.execute(
            "SELECT id, status, decider_name FROM projects WHERE slug = ?", (slug,),
        ).fetchone()
        if not proj:
            raise ValueError(f"Project '{slug}' not found.")
        project_id = int(proj[0])
        decider = (decider_attribution or "").strip() or (proj[2] or "").strip() or current_actor()

        # Druhé Go/Kill po platném Go/Kill: jen přes --force --rationale (rationale je povinné vždy).
        prev = conn.execute(
            "SELECT decision, winner_variant FROM sessions WHERE project_id = ? AND type = 2 "
            "ORDER BY id DESC LIMIT 1", (project_id,),
        ).fetchone() if table_has_col(conn, "sessions", "winner_variant") else None
        if prev and prev[0] in ("go", "kill") and proj[1] in ("handoff", "killed") and not force:
            what = f"Go ({prev[1]})" if prev[0] == "go" and prev[1] else DECISION_LABEL[prev[0]]
            raise ValueError(
                f"Už je {what}. Změna jen přes `--force --rationale \"…\"`; "
                f"původní rozhodnutí zůstane v decision logu."
            )
        variants = [r[0] for r in conn.execute(
            "SELECT v.name FROM variants v JOIN sessions s ON s.id = v.session_id "
            "WHERE s.project_id = ? AND s.type = 1", (project_id,)).fetchall()]
        if decision == "go" and winner not in variants:
            raise ValueError(
                f"Varianta '{winner}' v Buildu neexistuje (jsou: {', '.join(sorted(variants)) or 'žádné'})."
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
        decision_md = render_decision_md(
            slug, decision, rationale, decider, iterate_focus,
            winner=winner, override_critical=override_critical,
            criticals=criticals, votes=votes, checkpoints=checkpoints,
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
                "override_critical": override_critical,
                "overridden_criticals": [c["id"] for c in criticals] if override_critical else [],
                "forced": bool(force),
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
        "summary_path": display_path(summary_path),
        "decision_log_repo": repo_log,
        "next_step": _next_step_label(decision, slug, winner),
    }
    if repo_log:
        out["hint"] = f"Commitni decision log do target repa: git add {repo_log} && git commit"
    else:
        out["hint"] = ("cwd neobsahuje `.pflanzer/` - decision log je jen ve výstupní složce "
                       "(`pflanzer data`). Spusť příkaz z target repa, ať ho můžeš commitnout.")
    return out


def render_decision_md(
    slug: str, decision: str, rationale: str, decider: str, iterate_focus: str | None,
    *, winner: str | None = None, override_critical: str | None = None,
    criticals: list[dict[str, Any]] | None = None,
    votes: list[dict[str, Any]] | None = None, checkpoints: list[str] | None = None,
) -> str:
    when = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
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
        lines += ["### Override critical", "", f"Důvod: {override_critical}", ""]
        for c in criticals or []:
            lines.append(f"- {describe_critical(c)}")
        lines.append("")
    if checkpoints:
        lines += ["### Checkpointy", ""] + [f"- {c}" for c in checkpoints] + [""]
    if decision == "iterate":
        lines += ["### Iterate (max 1×)", "", (iterate_focus or rationale).strip(), ""]
    return "\n".join(lines)


def _next_step_label(decision: str, slug: str, winner: str | None = None) -> str:
    if decision == "go":
        return (f"`/pm ship {slug}` — quality gates na vítěze ({winner}), checkpoint provozu, PR. "
                "Pak `/pm handoff`.")
    if decision == "iterate":
        return (f"`/pm build {slug}` — jedno další Build kolo (jen to, co se mění), pak znovu "
                f"`/pm feedback {slug}` a `/pm decide {slug}`. **Max 1× Iterate.**")
    return "Projekt ukončen (Kill). Krátká retro do decision logu: co jsme se naučili."


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


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def _prep_view(out: dict[str, Any]) -> tuple[str, list[str], list[str], str, dict[str, Any]]:
    slug = out["slug"]
    crit = out["open_critical"]
    lines: list[str] = []
    ranked = sorted(out["variants"], key=lambda v: -v["score"])
    if ranked:
        lines.append("Hlasy jádra: " + ", ".join(
            f"{v['variant']} {v['score']:.2f} ({v['votes']} hlasů)" for v in ranked[:3]))
    fb = out["feedback_summary"]
    sev = ", ".join(f"{severity_label(k)}: {n}" for k, n in
                    sorted(fb["by_severity"].items(), key=lambda kv: ["critical", "high", "medium",
                                                                       "low"].index(kv[0])
                           if kv[0] in ("critical", "high", "medium", "low") else 9))
    lines.append(f"Feedback: {fb['count']}" + (f" ({sev})" if sev else ""))
    for c in crit[:2]:
        lines.append("Otevřené kritické: " + describe_critical(c))
    if len(crit) > 2:
        lines.append(f"…a dalších {len(crit) - 2} kritických")
    for c in out["conflicts"][:1]:
        lines.append(f"Hlavní spor u varianty {c['variant']}: {c['role_a']['label']} vs. "
                     f"{c['role_b']['label']}")
    if crit:
        c0 = crit[0]
        nxt = (f"vyřeš kritické #{c0['id']} s autorem ({c0['submitted_by']}): `pflanzer session_2 "
               f"resolve --slug {slug} --feedback-id {c0['id']} --by JMÉNO --note \"…\"`")
    elif not out["ready_for_decision"]:
        nxt = (f"sežeň víc hlasů a feedbacku (závaznost {out['commitment_index']:.0%}, "
               f"cíl {out['commitment_threshold']:.0%}): `pflanzer feedback add --slug {slug} …`")
    else:
        nxt = (f"Decider rozhodne: `pflanzer session_2 decide --slug {slug} go --winner A "
               f"--rationale \"proč\"`")
    return (f"Příprava Rozhodnutí: {slug}", lines[:6], [], nxt,
            {"open_critical": bool(crit)})


def _decision_view(out: dict[str, Any]) -> tuple[str, list[str], list[str], str, str]:
    slug, dec = out["slug"], out["decision"]
    label = DECISION_LABEL[dec]
    lines = [f"Rozhodl: {out['decider']}"]
    if out.get("winner"):
        lines.append(f"Vítěz: {out['winner']}")
    if out.get("override_critical"):
        lines.append(f"Decider přebil {out['open_critical_overridden']} kritických: "
                     f"{out['override_critical']}")
    lines.append("Zapsáno do decision logu"
                 + (f" ({out['decision_log_repo']}) — commitni ho." if out.get("decision_log_repo")
                    else "; z target repa se zapíše i do `.pflanzer/decisions/`."))
    nxt = out["next_step"]
    phase = "iterate" if dec == "iterate" else "decide"
    return f"Rozhodnutí {slug}: {label}", lines, [], nxt, phase


RESOLVE_EXAMPLE = ('pflanzer session_2 resolve --slug moje-appka --feedback-id 3 '
                   '--by Ondra --note "opraveno v PR #12"')
DECIDE_EXAMPLE = ('pflanzer session_2 decide --slug moje-appka go --winner A '
                  '--rationale "A je nejrychlejší a bezpečnost je v pořádku"')


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    p_prep = sub.add_parser("prep", help="Příprava Rozhodnutí: agregace + spory (read-only)")
    p_prep.add_argument("--slug", required=True)
    p_prep.add_argument("--json", action="store_true")

    p_dec = sub.add_parser("decide", help="Zapiš Go / Iterate / Kill")
    p_dec.add_argument("--slug", required=True)
    p_dec.add_argument("decision_pos", nargs="?", choices=sorted(VALID_DECISIONS),
                       metavar="{go,iterate,kill}", help="rozhodnutí (alternativa k --decision)")
    p_dec.add_argument("--decision", choices=sorted(VALID_DECISIONS), default=None)
    p_dec.add_argument("--rationale", default=None, help="důvod, 1–2 věty (povinné)")
    p_dec.add_argument("--winner", default=None, help="vítěz A|B|C (povinné u Go)")
    p_dec.add_argument("--decider", default=None,
                       help="override; default = decider_name z projektu")
    p_dec.add_argument("--override-critical", default=None, metavar="DŮVOD",
                       help="Decider přebíjí otevřený critical (důvod do auditu a decision logu)")
    p_dec.add_argument("--iterate-focus", default=None)
    p_dec.add_argument("--checkpoint", action="append", default=[],
                       help="záznam checkpointu (opakovatelné), např. 'Bezpečnost & právo: ok (Jana)'")
    p_dec.add_argument("--force", action="store_true",
                       help="změň už zapsané Go/Kill (vyžaduje --rationale)")
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
                 tips=tips_for("decide", ctx), as_json=args.json)
        elif args.cmd == "resolve":
            out = resolve_feedback(slug=args.slug, feedback_ids=args.feedback_id,
                                   note=args.note, by=args.by)
            who = f"{out['by']}: {out['note']}"
            left = out["open_critical"]
            emit(out, title=f"Vyřešeno: {', '.join('#' + str(i) for i in out['resolved'])}",
                 lines=[f"Vyřešeno: {', '.join('#' + str(i) for i in out['resolved'])} ({who})",
                        (f"Zbývá otevřených kritických: {len(left)}" if left
                         else "Žádný otevřený kritický feedback nezbývá.")],
                 next_step=(f"`pflanzer session_2 resolve --slug {args.slug} --feedback-id "
                            f"{left[0]['id']} --by JMÉNO --note \"…\"`" if left
                            else f"`pflanzer session_2 decide --slug {args.slug} go --winner A "
                                 f"--rationale \"proč\"`"),
                 tips=tips_for("decide", {"open_critical": bool(left)}), as_json=args.json)
        else:
            decision = args.decision_pos or args.decision
            if not decision:
                die("Chybí rozhodnutí: go, iterate, nebo kill.", DECIDE_EXAMPLE)
            if args.decision_pos and args.decision and args.decision_pos != args.decision:
                die("Rozhodnutí je zadané dvakrát a různě.", DECIDE_EXAMPLE)
            out = record_decision(
                slug=args.slug, decision=decision, rationale=args.rationale or "",
                iterate_focus=args.iterate_focus, decider_attribution=args.decider,
                winner=args.winner, override_critical=args.override_critical,
                checkpoints=args.checkpoint, force=args.force,
            )
            title, lines, warns, nxt, phase = _decision_view(out)
            emit(out, title=title, lines=lines, warnings=warns, next_step=nxt,
                 tips=tips_for(phase, {}), as_json=args.json)
    except ValueError as e:
        msg = str(e)
        die(msg, {"resolve": RESOLVE_EXAMPLE, "decide": DECIDE_EXAMPLE}.get(args.cmd, "")
            if ("--by" in msg or "--note" in msg or "--rationale" in msg or "--winner" in msg)
            else "")


if __name__ == "__main__":
    main()
