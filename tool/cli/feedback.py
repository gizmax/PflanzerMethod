"""`pflanzer feedback add|list` — offline zápis feedbacku (Async).

Hub je pohodlný, ale feedback musí jít zapsat i bez něj (zástupce kroku
cesty pošle připomínku e-mailem, facilitátor ji vloží). Zápis jde do stejné
tabulky `feedback` jako z hubu, takže `/pm feedback` (feedback_pull) ho vidí.

    pflanzer feedback add --slug S --variant A --role "Bezpečnost" \\
        --severity critical|major|minor --text "..." [--author "Jméno"]
    pflanzer feedback list --slug S [--variant A] [--json]

Severity: critical | major | minor (aliasy: high = major, medium, low = minor;
DB ukládá critical/high/medium/low, `major` -> high, `minor` -> low).
"""
from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tool.cli.db import audit, current_actor, transaction  # noqa: E402

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
    sev = SEVERITY_ALIASES.get(severity.lower())
    if not sev:
        raise ValueError("severity musí být critical, major nebo minor "
                         f"(dostal jsem '{severity}').")
    if not text.strip():
        raise ValueError("Text feedbacku nesmí být prázdný (rationale je povinné).")
    if score is not None and not 0 <= score <= 1:
        raise ValueError("--score musí být v rozsahu 0..1.")
    val = score if score is not None else SEVERITY_SCORE[sev]
    if ai_only and val > AI_ONLY_CAP:
        val = AI_ONLY_CAP

    with transaction() as conn:
        proj = conn.execute("SELECT id FROM projects WHERE slug = ?", (slug,)).fetchone()
        if not proj:
            raise ValueError(f"Projekt '{slug}' neexistuje (zkus `pflanzer status`).")
        project_id = int(proj[0])
        variant_id = _find_variant(conn, project_id, variant)
        if variant_id is None:
            raise ValueError(
                f"Varianta '{variant}' u projektu '{slug}' není zapsaná v toolu. "
                "Nejdřív zapiš varianty po Buildu (`/pm build`)."
            )
        role_id, department = _resolve_role(conn, project_id, role)
        actor = author or current_actor()
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
    return {
        "id": fid, "slug": slug, "variant": variant.upper(), "department": department,
        "role_matched": role_id is not None, "severity": sev, "score": val,
        "submitted_by": actor,
    }


def list_feedback(slug: str, variant: str | None = None) -> list[dict[str, Any]]:
    with transaction() as conn:
        proj = conn.execute("SELECT id FROM projects WHERE slug = ?", (slug,)).fetchone()
        if not proj:
            raise ValueError(f"Projekt '{slug}' neexistuje (zkus `pflanzer status`).")
        sql = """
            SELECT f.id, v.name AS variant, f.department, f.severity, f.score,
                   f.rationale, f.is_ai_only, f.submitted_by, f.submitted_at
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


def main() -> None:
    p = argparse.ArgumentParser(prog="pflanzer feedback", description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="Zapíše jeden feedback (offline)")
    a.add_argument("--slug", required=True)
    a.add_argument("--variant", required=True, help="A / B / C (nebo mob)")
    a.add_argument("--role", required=True,
                   help="Krok cesty nebo role, např. \"Bezpečnost\", \"Design\", \"Provoz\"")
    a.add_argument("--severity", required=True, help="critical | major | minor")
    a.add_argument("--text", required=True, help="Co je špatně / co chybí (povinné)")
    a.add_argument("--author", help="Kdo to řekl (default: git user)")
    a.add_argument("--category", default="general")
    a.add_argument("--score", type=float, help="0..1 (default dle severity)")
    a.add_argument("--ai-only", action="store_true", help="Feedback od AI persony (skóre max 0.5)")

    l = sub.add_parser("list", help="Vypíše feedback projektu")
    l.add_argument("--slug", required=True)
    l.add_argument("--variant")
    l.add_argument("--json", action="store_true")

    args = p.parse_args()
    try:
        if args.cmd == "add":
            res = add_feedback(
                slug=args.slug, variant=args.variant, role=args.role,
                severity=args.severity, text=args.text, author=args.author,
                category=args.category, score=args.score, ai_only=args.ai_only,
            )
            print(BRAND_LINE)
            print()
            print(f"✓ Feedback #{res['id']} zapsán — varianta {res['variant']}, "
                  f"{res['department']}, {res['severity']}, autor {res['submitted_by']}")
            if not res["role_matched"]:
                print("  (role v projektu nenalezena — uloženo jen jako oddělení)")
            print(f"  Další: `pflanzer feedback list --slug {res['slug']}` nebo `/pm feedback`")
        else:
            rows = list_feedback(args.slug, args.variant)
            if args.json:
                print(json.dumps(rows, ensure_ascii=False, indent=2, default=str))
                return
            print(BRAND_LINE)
            print()
            if not rows:
                print(f"Žádný feedback u '{args.slug}' — sbírej přes hub nebo "
                      "`pflanzer feedback add`.")
                return
            print(f"Feedback — {args.slug} ({len(rows)})\n")
            print("| # | Var | Oddělení | Severity | Skóre | Autor | Text |")
            print("|---|-----|----------|----------|-------|-------|------|")
            for r in rows:
                txt = r["rationale"].replace("\n", " ").replace("|", "/")
                print(f"| {r['id']} | {r['variant']} | {r['department']} | {r['severity']} "
                      f"| {r['score']:.2f} | {r['submitted_by']} | {txt[:80]} |")
            crit = sum(1 for r in rows if r["severity"] == "critical")
            if crit:
                print(f"\n⚠ Critical: {crit} — vyřeš před Rozhodnutím.")
    except ValueError as e:
        print(f"CHYBA: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
