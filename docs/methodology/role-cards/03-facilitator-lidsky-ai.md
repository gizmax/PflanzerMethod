Pflanzer Method | pflanzer.cz/method

# Role card #3 — Facilitátor (lidský + AI)

> Vedeš Kickoff, Build a Rozhodnutí: agendu, energii a pořadí hlasování, a deeskaluješ konflikty mezi rolemi.

**Krok cesty:** Produkt (vedení Buildu) · **Kde jsi:** jádro — celý Build, Async a Rozhodnutí

Status v catalogu: **povinná** · Kdy se zve: vždy (core role)

## Přines do svého okna
- Plán energie podle stupně (Quick 60–90 min / Lean 3 h / Full 5–6 h)
- Zadání z Kickoffu, jména zástupců a agendu s časovými boxy
- Šablonu parking lotu a decision logu s lidskou atribucí
- Potvrzený dev pár u klávesnice pro každou variantu

## Podepisuješ
- Decision log a conflict log (AI píše, ty podepisuješ)
- Hard rules: diff walkthrough před votingem, Decider hlasuje poslední

## Kdy jsi u toho
- Quick (60–90 min) — **celý běh**: vedeš `/pm live` od Kickoffu po silent vote
- Lean (3 h) — **celý běh**: vedeš Kickoff, `/pm build` i Rozhodnutí; během buildu nemáš otevřené IDE
- Full (5–6 h) — **celý běh**: pro audit-grade profil s co-facilitátorem

## Hlasuješ o
Nehlasuješ o variantách — vedeš silent vote (1-2-4-All), skóre zveřejníš až po hlasování a zapíšeš commitment level 0–3 per role.

## Okamžitě hlas
- Verbální hlasování nebo názor Decidera před silent vote (HiPPO)
- U klávesnice sedí facilitátor nebo AI proxy místo dev páru
- Víc než 10 lidí v místnosti nebo chybí senior delegát vetovací role

## AI proxy
**Režim 1 — Vlastnické a vetovací (vždy člověk).** ❌ Lidský facilitátor nutný — AI konflikt mezi rolemi nevyřeší; AI co-pilota orchestruješ ty. Sub-agent: `.claude/agents/facilitator.md`.

---

Detail: `docs/methodology/02-role-catalog.md` § 3 · stupně: `docs/methodology/00-lean-pflanzer.md` § Tři stupně jedné metody
