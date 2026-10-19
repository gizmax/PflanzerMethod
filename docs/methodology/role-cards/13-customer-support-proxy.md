Pflanzer Method | pflanzer.cz/method

# Role card #13 — Customer support proxy

> Přinášíš hlas zákazníka z ticketů — co dnes bolí a kolik ticketů varianta přidá nebo ubere.

Status v catalogu: **doporučená** · Kdy se zve: Customer base > 1000 active users + user-facing change?

## Přines do Session 1
- Top-10 ticket kategorií za 90 dní
- 20 verbatim citací zákazníků
- Frikční místa současného flow a churn radar
- KB článek baseline

## Podepisuješ
- Ticket prediction worksheet per varianta
- Support docs deadline: D-7 KB → D-2 makra / training → D+30 retro

## Kdy jsi v místnosti
- Quick (60–90 min) — **async**: ticket prediction v mezi-session okně
- Lean (3 h) — **async**: AI proxy draft (s přístupem k ticketům) + tvůj sign-off
- Full (5–6 h) — **celá session**: vedeš úvodní Voice of Customer ritual (30 min)

## Hlasuješ o
Skóruješ všechny 4 dimenze; risk za tebe znamená dopad na support a churn.

Preference matrix: `user_value` · `effort` · `risk` · `strategic_fit`; tvoje váha: **user_value**, **risk**. K tomu commitment level 0–3 pro mezi-session práci.

## Okamžitě hlas
- Varianta mění flow z top ticket kategorií bez plánu pro support
- Chybí error nebo empty state = nové tickety
- Launch bez KB článku a maker

## AI proxy
**Režim 2 — Konzultativní (AI proxy + human sign-off 24-48 h).** ⚠️ Jen pokud má AI přístup k ticket history; jinak člověk. Sub-agent: `.claude/agents/cs-proxy-expert.md`.

---

Detail: `docs/methodology/02-role-catalog.md` § 13 · stupně: `docs/methodology/00-lean-pflanzer.md` § Tři stupně jedné metody
