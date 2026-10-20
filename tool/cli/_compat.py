"""Tenké obálky nad API z `ux.py` a `checkpoint.py` s fallbackem (try-import).

Moduly Shipu, Rozhodnutí a Retra je volají, aby fungovaly i se starší verzí `ux.py`.
"""
from __future__ import annotations

import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tool.cli import ux as _ux  # noqa: E402


def parse_aware(value: Any) -> datetime | None:
    """SQLite `CURRENT_TIMESTAMP` / ISO text -> aware datetime (bez pásma = UTC)."""
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value or "").strip().replace("Z", "+00:00")
        if not text:
            return None
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def local_date(value: Any) -> date | None:
    """Kalendářní datum v místním pásmu (stejné, jaké používá decision log)."""
    dt = parse_aware(value)
    return dt.astimezone().date() if dt else None


def plural(n: int, one: str, few: str, many: str) -> str:
    """České skloňování bez čísla: 1 → one, 2–4 → few, jinak many."""
    k = abs(int(n))
    return one if k == 1 else few if 2 <= k <= 4 else many


def count(n: int, one: str, few: str, many: str) -> str:
    """`3 připomínky`, `1 hlas`, `5 dnů`."""
    return f"{n} {plural(n, one, few, many)}"


def tips(slug: str | None, phase: str, ctx: dict[str, Any] | None = None, *,
         fallback: str | None = None, limit: int = 3) -> list[str]:
    """Doporučení pro fázi; `fallback` = starší fáze, když `ux.py` novou fázi ještě nezná."""
    fn = getattr(_ux, "tips_for_project", None)
    if fn is not None and slug:
        try:
            got = fn(slug, phase, ctx or {}, limit=limit)
            if got or fallback is None:
                return got
        except Exception:  # noqa: BLE001 — tipy nikdy nesmí shodit příkaz
            pass
    got = _ux.tips_for(phase, ctx, limit)
    if not got and fallback:
        got = _ux.tips_for(fallback, ctx, limit)
    return got


def checkpoint_rows(slug: str) -> list[dict[str, Any]]:
    """Řádky `checkpoint_summary(slug)`; bez API nebo při chybě prázdný seznam."""
    try:
        from tool.cli import checkpoint as _cp
        fn = getattr(_cp, "checkpoint_summary", None)
        return list(fn(slug)) if fn else []
    except Exception:  # noqa: BLE001
        return []


def signature_conditions(slug: str) -> list[dict[str, str]]:
    """Podmínky z podepsaných oken (`checkpoint --conditions`); bez API / při chybě prázdný seznam."""
    try:
        from tool.cli import checkpoint as _cp
        fn = getattr(_cp, "signature_conditions", None)
        return list(fn(slug)) if fn else []
    except Exception:  # noqa: BLE001
        return []


def conditions_checklist(slug: str) -> list[str]:
    """`- [ ] CSRF (Bezpečnost, Lucie)` — jeden řádek na podmínku."""
    out = []
    for c in signature_conditions(slug):
        label = _WINDOW_LABELS.get(c["window"], c["window"].capitalize())
        who = f", {c['by']}" if c.get("by") else ""
        out.append(f"- [ ] {c['text']} ({label}{who})")
    return out


_WINDOW_LABELS = {"zadani": "Zadání", "design": "Design", "bezpecnost": "Bezpečnost", "provoz": "Provoz",
                  "pravo": "Právo", "data": "Data", "podpora": "Podpora"}


def ai_stand_in_line(slug: str) -> str | None:
    """„Design: AI (ux-expert), potvrdila Pavla · Bezpečnost: AI (security-expert), potvrdil Petr (autor kódu)“.

    Jen okna, kde za krok stála AI náhrada (`ai_agent` vyplněn nebo signer_kind AI draft / zástup /
    autor kódu). None = žádná AI náhrada.
    """
    parts: list[str] = []
    for r in checkpoint_rows(slug):
        kind = (r.get("signer_kind") or "").strip()
        agent = (r.get("ai_agent") or "").strip()
        if not agent and kind not in ("AI draft", "zástup", "autor kódu"):
            continue
        label = _WINDOW_LABELS.get(r.get("window") or "", (r.get("window") or "?").capitalize())
        who = (r.get("signed_by") or "").strip()
        ai = f"AI ({agent})" if agent else "AI"
        if who and r.get("state") == "ok":
            extra = f" ({kind})" if kind in ("autor kódu", "zástup") else ""
            verb = "potvrdila" if who.split()[0].lower().endswith("a") else "potvrdil"
            parts.append(f"{label}: {ai}, {verb} {who}{extra}")
        else:
            parts.append(f"{label}: {ai}, čeká na podpis člověka")
    return " · ".join(parts) or None


def signatures_line(slug: str) -> str | None:
    """„Zadání: Dana · Provoz: Karel (zástup) · Bezpečnost: Petr (autor kódu)“ — podepsaná okna.

    Podpis cizí osobou (ne zástupce kroku z Kickoffu) je vždy označený jako „zástup“.
    Okno s AI náhradou, které člověk potvrdil, se uvede s poznámkou. None = nic nepodepsáno.
    """
    parts: list[str] = []
    for r in checkpoint_rows(slug):
        kind = (r.get("signer_kind") or "").strip()
        agent = (r.get("ai_agent") or "").strip()
        who = (r.get("signed_by") or "").strip()
        if r.get("state") != "ok" or not who or kind == "AI draft":
            continue
        label = _WINDOW_LABELS.get(r.get("window") or "", (r.get("window") or "?").capitalize())
        extra = f" ({kind})" if kind in ("zástup", "autor kódu") else ""
        if agent:  # člověk potvrdil AI draft — patří mezi podepsaná okna
            extra = " (potvrdil AI draft)" + extra
        parts.append(f"{label}: {who}{extra}")
    return " · ".join(parts) or None


class ProjectNotFound(ValueError):
    """Projekt se zadaným slugem neexistuje.

    Knihovní funkce ji vyhazují (jde zachytit jako ValueError); CLI na hranici zavolá
    `ux.project_not_found(e.slug)` — česká chyba se seznamem existujících projektů.
    """

    def __init__(self, slug: str) -> None:
        self.slug = slug
        super().__init__(f"Projekt „{slug}“ neexistuje. Přehled projektů: `pflanzer status`.")


def exit_if_project_missing(exc: BaseException) -> None:
    """Na hranici CLI: `ProjectNotFound` → `ux.project_not_found(slug)` (česky, exit 2)."""
    if isinstance(exc, ProjectNotFound):
        _ux.project_not_found(exc.slug)
