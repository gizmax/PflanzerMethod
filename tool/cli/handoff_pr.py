"""Handoff — SHIP.md + podklady pro `gh pr create` (v0.5).

SHIP.md je primární handoff artefakt: 1 stránka s tím, co se mění, kdo to merguje,
skóre quality gates vítěze ("X/100, práh Y"), kill kritériem, měřením a copy-paste
příkazem pro PR. Osm souborů per role (`handoff.py`) je doplněk pro audit.

Pravidla výstupu:
- první řádek je brand line,
- žádné absolutní lokální cesty v textu určeném do PR (jen větev, SHA, název),
- výstupy do `<DATA_ROOT>/handoffs/<slug>/`.

Rozhraní:
    pflanzer handoff_pr --slug S [--print]
"""
from __future__ import annotations

import argparse
import json
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tool.cli.db import audit, display_path, transaction  # noqa: E402
from tool.cli.extract import (  # noqa: E402
    BRAND, DATA_ROOT, clean_text, public_repo_ref, table_has_col, tilde,
)
from tool.cli.session_2 import get_winner  # noqa: E402

SHIP_DIR = DATA_ROOT / "handoffs"
TEMPLATES_DIR = REPO_ROOT / "tool" / "templates" / "handoff"

_FALLBACK_MEASURE_30D = """## Změř po 30 dnech

Termín: 30 dní po merge. Změř: (1) kolik kódu vítěze (`{branch}` @ `{head_sha_short}`)
přežilo v `main`, (2) incidenty způsobené změnou, (3) metriku úspěchu vs. cíl
({metric_primary}). Kill kritérium: {kill}
"""


def load_template(name: str, fallback: str = "") -> str:
    path = TEMPLATES_DIR / name
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return fallback


def render_measure_30d(values: dict[str, Any]) -> str:
    tpl = load_template("measure-30d.md.template", _FALLBACK_MEASURE_30D)
    safe = {k: ("—" if v in (None, "") else v) for k, v in values.items()}
    for key, val in safe.items():
        tpl = tpl.replace("{" + key + "}", str(val))
    return tpl


def _fetch_ship_context(slug: str) -> dict[str, Any]:
    with transaction() as conn:
        proj = conn.execute(
            """
            SELECT id, name, slug, status, xyz_hypothesis, decider_name,
                   target_repo_url, target_branch, target_branch_owner,
                   shadow_pm, kill_criteria, throwaway_or_evolve,
                   ai_act_tier, data_class, gate_score_latest,
                   production_readiness_target, acceptance_criteria_md,
                   primary_lagging_metric, leading_metric, guardrail_metric
            FROM projects WHERE slug = ?
            """, (slug,),
        ).fetchone()
        if not proj:
            raise ValueError(f"Project '{slug}' not found.")
        project_id = int(proj[0])

        sess1 = conn.execute(
            "SELECT id FROM sessions WHERE project_id = ? AND type = 1", (project_id,),
        ).fetchone()
        winner = None
        decided = get_winner(conn, project_id)
        if sess1:
            has_branch = table_has_col(conn, "variants", "head_sha")
            cols = ("v.name, v.builder, v.prototype_url, v.preference_score, v.description_md, v.id"
                    + (", v.branch, v.head_sha" if has_branch else ", NULL, NULL"))
            if decided:
                winner = conn.execute(
                    f"SELECT {cols} FROM variants v WHERE v.session_id = ? AND v.name = ?",
                    (sess1[0], decided),
                ).fetchone()
            if winner is None:
                winner = conn.execute(
                    f"SELECT {cols} FROM variants v JOIN extracted_code e ON e.variant_id = v.id "
                    "WHERE v.session_id = ? ORDER BY e.id DESC LIMIT 1", (sess1[0],),
                ).fetchone() or conn.execute(
                    f"SELECT {cols} FROM variants v WHERE v.session_id = ? "
                    "ORDER BY v.preference_score DESC LIMIT 1", (sess1[0],),
                ).fetchone()

        ext = None
        gate_rows: list = []
        if winner:
            has_diff = table_has_col(conn, "extracted_code", "diff_loc_added")
            ext = conn.execute(
                "SELECT e.id, e.local_path, e.extraction_method, e.files_count, e.total_loc"
                + (", e.diff_loc_added, e.diff_loc_removed, e.diff_files" if has_diff
                   else ", NULL, NULL, NULL")
                + " FROM extracted_code e WHERE e.variant_id = ? ORDER BY e.id DESC LIMIT 1",
                (winner[5],),
            ).fetchone()
            if ext:
                gate_rows = list(conn.execute(
                    "SELECT gate_type, status, metric_value, details_md "
                    "FROM quality_gates WHERE extracted_id = ? ORDER BY id", (ext[0],),
                ).fetchall())

        decision = conn.execute(
            "SELECT body_md, atribuce_user, atribuce_ts FROM decisions "
            "WHERE project_id = ? AND type = 'handoff' ORDER BY id DESC LIMIT 1", (project_id,),
        ).fetchone()

    return {"project": proj, "winner": winner, "decided": decided, "extracted": ext,
            "gates": gate_rows, "decision": decision}


def _render_gate_badges(gates: list) -> tuple[str, int, int]:
    """Řádek `PASS build · WARN a11y · SKIP types …` + (aplikovatelné, celkem)."""
    if not gates:
        return "(quality gates ještě neběžely - `/pm ship`)", 0, 0
    label = {"pass": "PASS", "warn": "WARN", "fail": "FAIL", "skipped": "SKIP", "unsupported": "SKIP"}
    line = " · ".join(f"{label.get(g[1], '?')} {g[0]}" for g in gates)
    applicable = sum(1 for g in gates if g[1] in ("pass", "warn", "fail"))
    return line, applicable, len(gates)


def _verdict(score: int, target: int) -> str:
    if target <= 0:
        return "informativně (throwaway)"
    return "splňuje práh" if score >= target else "pod prahem"


def build_pr(slug: str) -> dict[str, Any]:
    """Sestaví titulek, tělo PR (bez absolutních cest) a metadata."""
    ctx = _fetch_ship_context(slug)
    p, w, e, gates = ctx["project"], ctx["winner"], ctx["extracted"], ctx["gates"]
    name, decider = p[1], p[5]
    metric_primary = clean_text(p[17], "doplnit při Rozhodnutí")
    metric_leading = clean_text(p[18], "doplnit při Rozhodnutí")
    metric_guardrail = clean_text(p[19], "doplnit při Rozhodnutí")
    gate_score = int(p[14] or 0)
    target = int(p[15]) if p[15] is not None else 80
    kill = p[10] or "(nezadáno v Kickoffu)"
    badges, applicable, total = _render_gate_badges(gates)
    dec_user = ctx["decision"][1] if ctx["decision"] else None
    dec_ts = str(ctx["decision"][2])[:10] if ctx["decision"] else None

    branch = w[6] if w and w[6] else (f"pflanzer/{slug}-{w[0]}" if w else None)
    head_sha = w[7] if w else None
    loc_added = e[5] if e else None
    loc_removed = e[6] if e else None
    diff_files = e[7] if e else None
    acceptance = next((f"{int(g[2])} %" for g in gates
                       if g[0] == "acceptance" and g[1] != "skipped" and g[2] is not None), "N/A")

    decider_line = decider or dec_user or "(Decider nezadán)"
    if dec_user and decider and dec_user.strip() != decider.strip():
        decider_line += f" (zapsal {dec_user})"
    if dec_ts:
        decider_line += f", rozhodnutí Go {dec_ts}"

    size_line = ""
    if loc_added is not None:
        size_line = f"+{loc_added}" + (f" / -{loc_removed}" if loc_removed is not None else "") + " řádků"
        if diff_files is not None:
            size_line += f" v {diff_files} souborech"

    pr_title = f"feat({slug}): {name[:60]}"
    body_lines = [
        BRAND, "",
        "## Co se mění", p[4] or name, "",
        "## Výstup Pflanzer Method",
        f"- Varianta: `{w[0] if w else '—'}` (`{w[1] if w else '—'}`), větev `{branch or '—'}`"
        + (f" @ `{head_sha[:10]}`" if head_sha else ""),
        f"- Skóre z Buildu: {float(w[3] or 0):.2f}" if w else "- Skóre z Buildu: —",
        f"- Gate skóre: **{gate_score}/100 (práh {target})** - {_verdict(gate_score, target)}",
        f"- Acceptance: {acceptance}",
        f"- Rozsah: {size_line or '—'}", "",
        f"## Quality gates ({applicable} z {total} aplikovatelných)", badges, "",
        "## Decider", decider_line, "",
        "## Kill kritéria", kill, "",
        "## Měření",
        f"- Primary (lagging): {metric_primary}",
        f"- Leading: {metric_leading}",
        f"- Guardrail: {metric_guardrail}", "",
        "---", "*Vygenerováno Pflanzer Method (`/pm handoff`).*",
    ]
    return {
        "ctx": ctx, "title": pr_title, "body": "\n".join(body_lines),
        "branch": branch, "head_sha": head_sha, "loc_added": loc_added,
        "gate_score": gate_score, "target": target, "badges": badges,
        "metrics": (metric_primary, metric_leading, metric_guardrail),
        "applicable": applicable, "total": total, "kill": kill,
    }


def render_ship_md(slug: str) -> str:
    pr = build_pr(slug)
    ctx = pr["ctx"]
    p, w, e = ctx["project"], ctx["winner"], ctx["extracted"]
    name, decider = p[1], p[5]
    target_repo = public_repo_ref(p[6])
    target_branch = p[7] or "main"
    branch_owner = p[8] or "(target_branch_owner nezadán)"
    shadow_pm = p[9] or "(shadow_pm nezadán)"
    score, target = pr["gate_score"], pr["target"]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    verdict = _verdict(score, target)

    winner_info = pr_command = ""
    if w and e:
        reviewer = branch_owner if (" " not in branch_owner and not branch_owner.startswith("(")) else "YOUR-GH-HANDLE"
        winner_info = f"""## Vítěz

- **Varianta**: `{w[0]}` (`{w[1]}`)
- **Větev**: `{pr['branch']}`{f" @ `{pr['head_sha'][:10]}`" if pr['head_sha'] else ''} v `{target_repo}`
- **Rozsah**: {pr['loc_added'] if pr['loc_added'] is not None else '—'} přidaných řádků
- **Gate skóre**: **{score}/100 (práh {target})** - {verdict}

### Quality gates ({pr['applicable']} z {pr['total']} aplikovatelných)

{pr['badges']}
"""
        pr_command = f"""## Otevři PR (copy-paste)

```bash
cd {tilde(e[1])}
git push -u origin {pr['branch']}

gh pr create \\
  --title {shlex.quote(pr['title'])} \\
  --body "$(cat <<'PRBODY'
{pr['body']}
PRBODY
)" \\
  --base {target_branch} \\
  --reviewer {reviewer} \\
  --label pflanzer
```
"""

    measure = render_measure_30d({
        "branch": pr["branch"], "head_sha_short": (pr["head_sha"] or "")[:10],
        "loc_added": pr["loc_added"], "metric_primary": pr["metrics"][0],
        "guardrail": pr["metrics"][2], "kill": pr["kill"],
    })

    return f"""{BRAND}

# SHIP — {name}

> Projekt: `{p[2]}` · Vygenerováno: {today} · {verdict}
> SHIP.md je primární handoff (1 stránka). Soubory per role jsou doplněk pro audit.

## Co se mění

{p[4]}

## Odpovědnosti

| Role | Kdo |
|------|-----|
| **Decider** | {decider or '(nezadán)'} |
| **Branch owner / merger** | {branch_owner} |
| **Shadow PM** (hlídá Async) | {shadow_pm} |

{winner_info}
## Rizikový profil

- **AI Act tier**: `{p[12]}` · **Data class**: `{p[13]}` · **Profil**: `{p[11]}`

## Kill kritéria

{pr['kill']}

## Měření

- **Primary (lagging)**: {pr['metrics'][0]}
- **Leading**: {pr['metrics'][1]}
- **Guardrail**: {pr['metrics'][2]}
- **Instrumentace hotová**: 2 dny před nasazením

{pr_command}
## Co dál (T+0 → T+90)

- **Dnes**: PR otevřený, branch owner dělá review
- **T+1 den**: PR merged, preview odkaz sdílen
- **T+7 dní**: feature flag 10 % uživatelů; kontrola instrumentace
- **T+14 dní**: 50 % uživatelů; první čtení metrik
- **T+30 dní**: plný rollout, nebo rollback podle kill kritérií; **změř, co z kódu přežilo** (níže)
- **T+60–90 dní**: retrospektiva, příspěvek do `method-metrics.json`

{measure}
## Audit trail

- Audit log a decision log jsou v DB toolu (7letá retence, DORA); cesta: `pflanzer db`.
- Decision log pro git: `.pflanzer/decisions/{p[2]}.md` v target repu (commitnutý při Rozhodnutí).
- AI Act: pokud `tier=high`, Annex IV technická dokumentace před produkcí.
- GDPR: pokud `data_class=L3+`, aktualizace RoPA a DPIA.

---

*Soubory per role: `decision, be, fe, qa, platform, data, support, compliance` (`.md`) ve
výstupní složce (`pflanzer data`) slouží pro audit a hlubší pohled; u stolu je nikdo nečte.*
"""


def write_ship(slug: str) -> Path:
    project_dir = SHIP_DIR / slug
    project_dir.mkdir(parents=True, exist_ok=True)
    out = project_dir / "SHIP.md"
    out.write_text(render_ship_md(slug), encoding="utf-8")

    with transaction() as conn:
        proj = conn.execute("SELECT id FROM projects WHERE slug = ?", (slug,)).fetchone()
        if proj:
            audit(
                conn, action="ship.render",
                target_type="project", target_id=int(proj[0]),
                payload={"slug": slug, "file": out.name},
            )
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--slug", required=True)
    p.add_argument("--print", action="store_true",
                   help="Vypiš SHIP.md na stdout (default: zapiš do výstupní složky)")
    p.add_argument("--pr-body", action="store_true",
                   help="Vypiš jen tělo PR (pro `gh pr create --body-file -`)")
    args = p.parse_args()

    if args.pr_body:
        print(build_pr(args.slug)["body"])
    elif args.print:
        print(render_ship_md(args.slug))
    else:
        path = write_ship(args.slug)
        print(json.dumps({
            "slug": args.slug,
            "ship_path": tilde(path),
            "next_step": (
                "Ukaž SHIP.md týmu. Decider nebo branch owner spustí `gh pr create` příkaz "
                "z konce SHIP.md (z worktree vítěze)."
            ),
        }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
