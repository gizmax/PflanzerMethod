---
description: Build (/pm build, 3 h, jádro) — 3 varianty paralelně v 3 worktrees, kontroly průběžně, checkpoint bezpečnost & právo, push na preview URL, zápis do toolu.
---

# Build (`/pm build`) — 3 h, jádro

> **Cesty:** soubory `docs/…` a `tool/…` zmíněné níže leží v kořeni metody
> (`pflanzer root`), ne v target repu. Tool spouštěj vždy přes `pflanzer <cmd>`.

**Pflanzer Method | pflanzer.cz/method** — brand line vždy na prvním řádku výstupu.

Argumenty: `$ARGUMENTS` = projekt slug (jinak `pflanzer status`).

Kdo: **jádro** (PM, 1–2 vývojáři, designér), u jedné obrazovky. Decider u
stavby není (anti-HiPPO). Max 5 lidí. Bezpečnost & právo přijde na
20min checkpoint v posledních 30 min.

Předpoklad: Kickoff proběhl (`pflanzer status --slug $ARGUMENTS`). Jinak
řekni `/pm start`.

## Krok 1 — Worktrees a prompty

```bash
pflanzer worktree setup --slug $ARGUMENTS
pflanzer quick_session prompts --slug $ARGUMENTS --hook "<hook ze zadání>" --n 3
```

- Worktrees vznikají v **target repu zákazníka** (ADR-0009), větve
  `pflanzer/<slug>-A|B|C`. Nikdy v repu metody.
- Prompty A/B/C mají různý úhel (A minimum, B vedený multi-step, C chytré
  defaulty). AI v nich čte `.pflanzer/CONSTITUTION.md` a
  `docs/INTEGRATION_GUIDE.md`, **průběžně pouští lint/test/build** a každá
  varianta nese štítek „Varianta X k rozhodnutí".

## Krok 2 — Stavba (3× Claude Code paralelně)

V každém worktree samostatná session `claude` s promptem pro danou variantu.
Vývojář řídí všechny tři (nebo 2+1), zbytek jádra sedí u jedné obrazovky
a směruje. Pravidla:

- **Průběžné kontroly, ne až na konci:** po každé větší změně lint + typy +
  testy + build (+ secret scan, pokud ho repo má). Červená varianta se
  neposouvá dál, dokud není zelená.
- Facilitátor hlídá čas; tvrdý strop ~2 h 30 min na stavbu, pak kontrola.
- **Role experti (sub-agenti)** z catalogu jsou volitelný vstup — perspektiva
  nepřítomné role, ne hlas. Vlny po 3–4, nikdy všichni naráz.
- Výchozí builder = Claude Code v repu firmy. Hosted builder (v0/Bolt/Lovable)
  jen jako **opt-in** pro greenfield bez repa nebo throw-away demo; kód pak
  musí skončit jako větev v target repu.

## Krok 3 — Checkpoint bezpečnost & právo (20 min, posledních 30 min Buildu)

Zástupce kroku Bezpečnost & právo (jeden člověk) projde nad běžícími
variantami a diffem:

- [ ] **Datový tok** — odkud kam data tečou, co opouští firmu
- [ ] **Data classification** — L1–L4; žádná produkční data v preview
- [ ] **Egress limit** — co smí agent a preview volat ven (default: nic mimo
  allowlist)
- [ ] **Strop tokenů / nákladů** — limit na session a na den, kdo ho hlídá
- [ ] **Riziko prompt injection** — agent čte cizí text (issues, weby,
  uživatelský vstup)? Co se stane, když v něm bude instrukce?
- [ ] **Worktree není bezpečnostní izolace** — sdílí soubory, secrets
  i síť stroje; secrets mimo worktree, agent s minimem práv
- [ ] Právo: osobní údaje, licence závislostí, tvrzení v UI

Výsledek (OK / podmínky / veto) zapiš do zápisu Buildu. Veto = varianta
nejde na preview, dokud ji Decider výslovně nepřebije s odůvodněním.
`doctor` a gates jen doplňují, nenahrazují.

## Krok 4 — Push a preview

```bash
git push origin pflanzer/$ARGUMENTS-A pflanzer/$ARGUMENTS-B pflanzer/$ARGUMENTS-C
```

Preview URL = to, co firma už má (Vercel/Netlify preview, review apps,
preview namespace). Bez produkčních dat. Na každém preview viditelný štítek
**„Varianta X — k rozhodnutí, ne produkt"** + 1 věta, jaký problém řeší.
Odkazy pošli všem zástupcům.

## Krok 5 — Zápis Buildu

Silent dot voting jen pro přítomné (Decider hlasuje vždy poslední, na
Rozhodnutí; nepřítomní přes Async). Sestav spec a zapiš:

```bash
pflanzer quick_session vote --spec /tmp/<slug>-vote.json
# alternativa pro plný zápis s experty:
pflanzer session --spec /tmp/<slug>-build.json
```

Spec: varianty (branch, preview URL), `role_preferences` (hlas, rationale
1 věta, commitment 0–3), výsledek checkpointu B&P, veto registr, parking lot.

## Krok 6 — Výstup a další krok

Ukaž tabulku varianta / branch / preview URL / stav kontrol / checkpoint B&P.
Na konci **jeden** další krok:

> Další krok: `/pm feedback <slug>` — zástupci klikají na preview 3–5 dní;
> kdo feedback nevyplnil, zapíše ho offline přes `pflanzer feedback add`.

## Co NEDĚLAT

- Žádné placeholdery typu `sandbox.invalid` — bez skutečné preview URL
  řekni, že Async nemá na co klikat.
- Nezakládej projekt tady; to je jen `/pm start`.
- Negeneruj víc než 3 varianty. Nepouštěj víc než 4 experty paralelně.
- Nepřepisuj veto bez rationale do decision logu.

## Reference

- `docs/decisions/0021-mala-skupina-cela-cesta.md`, `0022-inspirace-z-trhu.md`
- `docs/methodology/04-session-1.md` (rozšířená reference Buildu)
- `docs/zacni.md`, `docs/postup.md`
