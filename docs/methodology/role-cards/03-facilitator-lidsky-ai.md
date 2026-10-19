Pflanzer Method | pflanzer.cz/method

# Role card #3 — Facilitátor (lidský + AI)

> Za 15 minut před Buildem připravíš agendu a časy; pak vedeš Kickoff, Build i Rozhodnutí a hlídáš pořadí hlasování.

**Krok cesty:** Produkt (vedení Buildu) · **Kde jsi:** jádro — celý Build, Async a Rozhodnutí

Status v catalogu: **povinná** · Kdy se zve: vždy (core role)

## Přines do svého okna
- Plán energie podle stupně (Quick 60–90 min / Lean 3 h / Full 5–6 h)
- Zadání z Kickoffu, jména zástupců a agendu s časovými boxy
- Potvrzený vývojářský pár u klávesnice pro každou variantu
- Pro hlubší kontrolu (stupeň Full): šablonu parking lotu a decision logu s lidskou atribucí

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
**Režim 1 — Vlastnické a vetovací (vždy člověk).** Může tě nahradit AI? **Ne.** Facilitátor je součást kroku Produkt (ADR-0023 ho nenahrazuje); AI konflikt mezi lidmi nevyřeší, jen píše zápis. Sub-agent: `.claude/agents/facilitator.md`.

---

Detail: `docs/methodology/02-role-catalog.md` § 3 · stupně: `docs/methodology/00-lean-pflanzer.md` § Tři stupně jedné metody
