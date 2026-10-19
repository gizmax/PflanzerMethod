Pflanzer Method | pflanzer.cz/method

# Role card #13 — Customer support proxy

> Za 20 minut v Asyncu odhadneš, kolik dotazů na podporu varianty přidají nebo ubere, a co zákazníci řeknou.

**Krok cesty:** Provoz (podpora) · **Kde jsi:** okno — Async okno nad preview a příprava Shipu

Status v catalogu: **doporučená** · Kdy se zve: Customer base > 1000 active users + user-facing change?

## Přines do svého okna
- 10 nejčastějších důvodů ticketů za 90 dní
- Pár doslovných citací zákazníků k dotčenému flow
- Článek v nápovědě, který se změní
- Pro hlubší kontrolu (stupeň Full): churn radar, ticket prediction worksheet, termíny D-7 KB / D-2 makra / D+30 retro

## Podepisuješ
- Ticket prediction worksheet per varianta
- Support docs deadline: D-7 KB → D-2 makra / training → D+30 retro

## Kdy jsi u toho
- Quick (60–90 min) — **async**: ticket prediction v Async okně
- Lean (3 h) — **async**: AI proxy draft (s přístupem k ticketům) + tvůj sign-off v Async okně
- Full (5–6 h) — **celý běh**: vedeš úvodní Voice of Customer ritual (30 min)

## Hlasuješ o
Skóruješ všechny 4 dimenze; risk za tebe znamená dopad na support a churn.

Preference matrix: `user_value` · `effort` · `risk` · `strategic_fit`; tvoje váha: **user_value**, **risk**. K tomu commitment level 0–3 pro Async okno.

## Okamžitě hlas
- Varianta mění flow z top ticket kategorií bez plánu pro support
- Chybí error nebo empty state = nové tickety
- Launch bez KB článku a maker

## AI proxy
**Režim 2 — Konzultativní (AI proxy + human sign-off 24-48 h).** Může tě nahradit AI? **Není to krok cesty** (ADR-0023); AI pomůže jen s přístupem k historii ticketů, odhad podepisuješ ty. Sub-agent: `.claude/agents/cs-proxy-expert.md`.

---

Detail: `docs/methodology/02-role-catalog.md` § 13 · stupně: `docs/methodology/00-lean-pflanzer.md` § Tři stupně jedné metody
