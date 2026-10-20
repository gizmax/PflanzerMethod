"""`pflanzer feedback add|list` — offline zápis feedbacku (Async).

Hub je pohodlný, ale feedback musí jít zapsat i bez něj (zástupce kroku
cesty pošle připomínku e-mailem, facilitátor ji vloží). Zápis jde do stejné
tabulky `feedback` jako z hubu, takže `/pm feedback` (feedback_pull) ho vidí.

    pflanzer feedback add --slug S --variant A --role "Bezpečnost" \\
        --by "Jméno" --severity critical|major|minor --text "..."
    pflanzer feedback list --slug S [--variant A] [--json]

Závažnost: critical | major | minor (aliasy: high = major, medium, low = minor).
V DB je critical/high/medium/low; lidsky se ukazují tři úrovně: Kritické (blokuje nasazení) /
Důležité (high, major) / Drobné (medium, low, minor).
Hodnocení `--score` je 0–1 (vyšší = lepší); bez něj se odvodí ze závažnosti.
"""
from __future__ import annotations

import json
import sys
import unicodedata
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tool.cli._compat import ProjectNotFound, count, exit_if_project_missing, tips  # noqa: E402
from tool.cli.db import audit, current_actor, transaction  # noqa: E402
from tool.cli.ux import (  # noqa: E402
    CzechArgumentParser,
    die,
    emit,
    normalize_severity,
    severity_group,
    severity_label,
)

BRAND_LINE = "**Pflanzer Method | pflanzer.cz/method**"

SEVERITY_ALIASES = {
    "critical": "critical", "major": "high", "high": "high",
    "medium": "medium", "minor": "low", "low": "low",
}
# Skóre 0..1 (vyšší = lepší); odvozené ze severity, pokud není zadáno --score
SEVERITY_SCORE = {"critical": 0.1, "high": 0.3, "medium": 0.5, "low": 0.7}
AI_ONLY_CAP = 0.5

# Krok cesty -> (zobrazený název oddělení, catalog_idx rolí, které krok zastupují)
STEP_ALIASES: dict[str, tuple[str, tuple[int, ...]]] = {
    "byznys": ("Byznys", (1,)),
    "produkt": ("Produkt", (2,)),
    "design": ("Design", (6,)),
    "vyvoj": ("Vývoj", (4, 5)),
    "bezpecnost": ("Bezpečnost & právo", (7, 10)),
    "pravo": ("Bezpečnost & právo", (10, 7)),
    "provoz": ("Provoz", (15, 9)),
}


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFD", text)
    return "".join(c for c in text if unicodedata.category(c) != "Mn").casefold().strip()


def _resolve_role(conn, project_id: int, role_text: str) -> tuple[int | None, str]:
    """Return (role_id | None, department label) for a free-text role."""
    key = _norm(role_text)
    rows = conn.execute(
        "SELECT id, catalog_idx, catalog_label, human_owner FROM roles WHERE project_id = ? "
        "ORDER BY catalog_idx", (project_id,),
    ).fetchall()

    step_hit = next((v for k, v in STEP_ALIASES.items() if key.startswith(k)), None)
    if step_hit:
        label, idxs = step_hit
        for idx in idxs:
            for r in rows:
                if r[1] == idx:
                    return int(r[0]), label
        return None, label
    for r in rows:
        if key and (key in _norm(r[2]) or (r[3] and key == _norm(r[3]))):
            return int(r[0]), role_text.strip()
    return None, role_text.strip()


def _find_variant(conn, project_id: int, name: str) -> int | None:
    row = conn.execute(
        """
        SELECT v.id FROM variants v JOIN sessions s ON s.id = v.session_id
        WHERE s.project_id = ? AND upper(v.name) = upper(?)
        ORDER BY v.id DESC LIMIT 1
        """,
        (project_id, name),
    ).fetchone()
    return int(row[0]) if row else None


def add_feedback(
    *, slug: str, variant: str, role: str, severity: str, text: str,
    author: str | None = None, category: str = "general",
    score: float | None = None, ai_only: bool = False,
) -> dict[str, Any]:
    sev = normalize_severity(severity)
    if not text.strip():
        raise ValueError("Text feedbacku nesmí být prázdný (rationale je povinné).")
    if score is not None and not 0 <= score <= 1:
        raise ValueError("--score je hodnocení 0–1 (vyšší = lepší), např. --score 0.3.")
    val = score if score is not None else SEVERITY_SCORE[sev]
    if ai_only and val > AI_ONLY_CAP:
        val = AI_ONLY_CAP

    with transaction() as conn:
        proj = conn.execute("SELECT id FROM projects WHERE slug = ?", (slug,)).fetchone()
        if not proj:
            raise ProjectNotFound(slug)
        project_id = int(proj[0])
        variant_id = _find_variant(conn, project_id, variant)
        if variant_id is None:
            raise ValueError(
                f"Varianta '{variant}' u projektu '{slug}' není zapsaná v toolu. "
                "Nejdřív zapiš varianty po Buildu (`/pm build`)."
            )
        role_id, department = _resolve_role(conn, project_id, role)
        actor = (author or "").strip() or current_actor()
        if actor == "unknown":
            raise ValueError(
                "Nevím, kdo feedback píše — doplňte `--by \"Jméno\"` (autor jde do decision "
                "logu a SHIP.md), nebo nastavte `git config user.name`.")
        cur = conn.execute(
            """
            INSERT INTO feedback (variant_id, role_id, severity, department, category,
                                  score, rationale, is_ai_only, submitted_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (variant_id, role_id, sev, department, category, val, text.strip(),
             1 if ai_only else 0, actor),
        )
        fid = int(cur.lastrowid)
        audit(
            conn, action="feedback.create", target_type="feedback", target_id=fid,
            payload={"variant_id": variant_id, "severity": sev, "department": department,
                     "ai_only": ai_only, "via": "cli"},
        )
        focus: list[str] = []
        if sev == "critical":
            from tool.cli.session_2 import focus_variants
            focus = focus_variants(conn, project_id)
    return {
        "id": fid, "slug": slug, "variant": variant.upper(), "department": department,
        "role_matched": role_id is not None, "severity": sev, "score": val,
        "submitted_by": actor, "focus_variants": focus, "category": category,
        "blocks_go": sev == "critical" and variant.upper() in focus,
    }


NON_CODE_CATEGORIES = {"scope", "rozsah", "duplicate", "duplicita", "strategy", "strategie",
                       "business", "byznys"}


def is_business_critical(department: str, category: str | None) -> bool:
    """Critical od kroku Byznys nebo z kategorie, kterou nespraví kód (rozsah/duplicita/strategie)."""
    return (_norm(department or "") in ("byznys", "business")
            or _norm(category or "") in NON_CODE_CATEGORIES)


def list_feedback(slug: str, variant: str | None = None) -> list[dict[str, Any]]:
    with transaction() as conn:
        proj = conn.execute("SELECT id FROM projects WHERE slug = ?", (slug,)).fetchone()
        if not proj:
            raise ProjectNotFound(slug)
        cols = {r[1] for r in conn.execute("PRAGMA table_info(feedback)")}
        resolved = "f.resolved_at" if "resolved_at" in cols else "NULL"
        res_note = "f.resolved_note" if "resolved_note" in cols else "NULL"
        sql = f"""
            SELECT f.id, v.name AS variant, f.department, f.severity, f.score,
                   f.rationale, f.is_ai_only, f.submitted_by, f.submitted_at,
                   {resolved} AS resolved_at, {res_note} AS resolved_note
            FROM feedback f
            JOIN variants v ON v.id = f.variant_id
            JOIN sessions s ON s.id = v.session_id
            WHERE s.project_id = ?
        """
        params: list[Any] = [int(proj[0])]
        if variant:
            sql += " AND upper(v.name) = upper(?)"
            params.append(variant)
        sql += " ORDER BY f.id"
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


ADD_EXAMPLE = ('pflanzer feedback add --slug moje-appka --variant A --role Bezpečnost '
               '--severity major --text "Export nemá kontrolu oprávnění" --by Lucie')


def _counts(rows: list[dict[str, Any]]) -> str:
    parts = []
    for k in ("critical", "high", "low"):
        items = [r for r in rows if severity_group(r["severity"]) == k]
        if not items:
            continue
        done = sum(1 for r in items if r.get("resolved_at"))
        label = severity_label(k)
        if done and done == len(items):
            parts.append(f"{label} vyřešené {done}")
        elif done:
            parts.append(f"{label} otevřené {len(items) - done}, vyřešené {done}")
        else:
            parts.append(f"{label} {len(items)}")
    return ", ".join(parts) or "bez připomínek"


def _list_view(slug: str, rows: list[dict[str, Any]]) -> tuple[str, list[str], str, dict[str, Any]]:
    """Lidský výpis: počty po variantách, pak řádky „varianta · role (jméno) · závažnost · text“
    od critical po minor; vyřešené zvlášť."""
    from tool.cli.feedback_pull import feedback_row_line, open_resolved

    variants = sorted({r["variant"] for r in rows})
    lines = [f"Varianta {v}: {_counts([r for r in rows if r['variant'] == v])}" for v in variants[:3]]
    open_rows, done_rows = open_resolved(rows)
    lines += [f"#{r['id']} {feedback_row_line(r)}" for r in open_rows]
    lines += [f"Vyřešeno #{r['id']} {feedback_row_line(r)}"
              + (f" — {r['resolved_note']}" if r.get("resolved_note") else "")
              for r in done_rows]
    crit = [r for r in open_rows if r["severity"] == "critical"]
    if crit:
        nxt = (f"`pflanzer session_2 resolve --slug {slug} --feedback-id {crit[0]['id']} "
               f"--by JMÉNO --note \"…\"`")
    else:
        nxt = f"`pflanzer feedback_pull --slug {slug}` (souhrn + kdo ještě mlčí)"
    return (f"Feedback {slug}: {count(len(rows), 'připomínka', 'připomínky', 'připomínek')}",
            lines, nxt, {"open_critical": bool(crit)})


def main() -> None:
    p = CzechArgumentParser(prog="pflanzer feedback", description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True, parser_class=CzechArgumentParser)

    a = sub.add_parser("add", help="Zapíše jeden feedback (offline)")
    a.add_argument("--slug", required=True)
    a.add_argument("--variant", required=True, help="A / B / C (nebo mob)")
    a.add_argument("--role", required=True,
                   help="Krok cesty nebo role, např. \"Bezpečnost\", \"Design\", \"Provoz\"")
    a.add_argument("--severity", required=True, help="critical | major | minor")
    a.add_argument("--text", required=True, help="Co je špatně / co chybí (povinné)")
    a.add_argument("--author", "--by", dest="author",
                   help="Kdo to řekl (jméno zástupce; bez něj se vezme git user)")
    a.add_argument("--category", default="general")
    a.add_argument("--score", type=float, help="hodnocení 0–1, vyšší = lepší (default dle závažnosti)")
    a.add_argument("--ai-only", action="store_true", help="Feedback od AI persony (skóre max 0.5)")
    a.add_argument("--json", action="store_true")

    ls_p = sub.add_parser("list", help="Vypíše feedback projektu")
    ls_p.add_argument("--slug", required=True)
    ls_p.add_argument("--variant")
    ls_p.add_argument("--json", action="store_true")

    args = p.parse_args()
    try:
        if args.cmd == "add":
            res = add_feedback(
                slug=args.slug, variant=args.variant, role=args.role,
                severity=args.severity, text=args.text, author=args.author,
                category=args.category, score=args.score, ai_only=args.ai_only,
            )
            lines = [f"Varianta {res['variant']}, krok {res['department']}, "
                     f"{severity_label(res['severity'])}, autor {res['submitted_by']}"]
            if not args.author:
                lines.append(f"Autor je git user ({res['submitted_by']}), ne zástupce kroku — "
                             "za někoho jiného zapiš `--by \"Jméno\"`.")
            if not res["role_matched"]:
                lines.append("Role v projektu nenalezena — uloženo jen jako oddělení.")
            if res["severity"] == "critical":
                fid, sl = res["id"], res["slug"]
                if res["blocks_go"]:
                    lines.append(f"Kritické na {res['variant']} blokuje Go, dokud se nevyřeší.")
                    if is_business_critical(res["department"], res.get("category")):
                        nxt = (f"Byznysový critical: zvažte Kill (problém je vyřešen jinde) nebo "
                               f"vědomé `--override-critical \"důvod\"` Deciderem při Go "
                               f"(`pflanzer session_2 decide --slug {sl} go --winner "
                               f"{res['variant']} …`)")
                    else:
                        nxt = (f"oprav to ve variantě {res['variant']} a pak "
                               f"`pflanzer session_2 resolve --slug {sl} --feedback-id {fid} "
                               f"--by JMÉNO --note \"co se opravilo\"`; nebo Decider přebije při Go: "
                               f"`--override-critical \"důvod\"`")
                else:
                    lines.append(f"Kritické na {res['variant']} Go neblokuje, pokud vyhraje jiná "
                                 f"varianta ({'/'.join(res['focus_variants']) or '—'}).")
                    nxt = (f"`pflanzer session_2 resolve --slug {sl} --feedback-id {fid} "
                           f"--by JMÉNO --note \"proč je to mimo vítěze\"`, nebo nech být: "
                           f"`pflanzer feedback list --slug {sl}`")
                phase = "after_critical"
            else:
                nxt, phase = f"`pflanzer feedback list --slug {res['slug']}`", "async"
            emit(res, title=f"Feedback #{res['id']} zapsán", lines=lines,
                 next_step=nxt,
                 tips=tips(res["slug"], phase, {}, limit=2), as_json=args.json)
        else:
            rows = list_feedback(args.slug, args.variant)
            if args.json:
                print(json.dumps(rows, ensure_ascii=False, indent=2, default=str))
                return
            if not rows:
                emit({}, title=f"Feedback {args.slug}: zatím nic",
                     lines=["Nikdo zatím nenapsal žádnou připomínku."],
                     next_step=ADD_EXAMPLE)
                return
            title, lines, nxt, ctx = _list_view(args.slug, rows)
            emit(rows, title=title, lines=lines, next_step=nxt,
                 tips=tips(args.slug, "async", ctx, limit=2))
    except ValueError as e:
        exit_if_project_missing(e)
        die(str(e), ADD_EXAMPLE if args.cmd == "add" else "")


if __name__ == "__main__":
    main()
