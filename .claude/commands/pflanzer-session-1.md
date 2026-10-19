---
description: Build (/pm build, 3 h, jádro) — 3 varianty paralelně v 3 worktrees, kontroly průběžně, checkpoint bezpečnost & právo, push na preview URL, zápis do toolu.
---

# Build (`/pm build`) — 3 h, jádro

> **Cesty:** soubory `docs/…` a `tool/…` zmíněné níže leží v kořeni metody
> (`pflanzer root`), ne v target repu. Tool spouštěj vždy přes `pflanzer <cmd>`.

**Pflanzer Method | pflanzer.cz/method** — brand line vždy na prvním řádku výstupu.

> **Argumenty:** `<slug>` = **první slovo** z `$ARGUMENTS` (zbytek je kontext od uživatele —
> rozhodnutí, jména, poznámky). Bez slugu: `pflanzer status`. Do příkazů dosazuj jen `<slug>`.
> **Zápisy dělá výhradně tool** (`pflanzer …`) — decision log, checkpointy ani DB nikdy needituj ručně.


Výstup toolu je lidský (co se stalo → jeden další krok → Doporučení); ukaž ho
a předej Doporučení. Worktree = oddělená kopie repa pro každou variantu.

Kdo: **jádro** (PdM, 1–2 vývojáři, designér), u jedné obrazovky. Decider u
stavby není (anti-HiPPO). Max 5 lidí. Bezpečnost & právo přijde na
20min checkpoint v posledních 30 min.

Předpoklad: Kickoff proběhl (`pflanzer status --slug <slug>`). Jinak
řekni `/pm start`.

> **U klávesnice sedí vývojář.** Facilitátor ani Claude jako „AI proxy" za
> vývojový tým není builder. Není-li v jádru žádný vývojář (ani frontend,
> ani backend), Build nezačínej — nabídni odložení, nebo výslovně
> throwaway demo, jehož kód nejde do produkce (ADR-0020, Track P).
>
> Stupeň projektu (`pflanzer status`): **Lean** = tento Build (3 h, tři
> varianty), **Quick** = `/pm live` (Kickoff + Build v jednom, 60–90 min),
> **Full** = governance / regulované (5–6 h agenda a 4 triage tracky v
> `docs/methodology/04-session-1.md`, přizvi i `/pm roles` a `/pm triage`).

> **Git identita při paralelním Buildu:** worktrees sdílejí jednu git konfiguraci.
> Jméno autora (vývojář u klávesnice) nastav jednou v target repu před
> `worktree setup` — ne zvlášť v každém worktree současně (zámek configu selže).

## Krok 0 — Výhrady z doctoru

Spusť `pflanzer doctor` a jednou větou pojmenuj otevřené ⚠ **s vlastníkem
a termínem** (jména z kroků cesty v `pflanzer status`): preview chybí →
zástupce provozu, chybí lockfile / testy → vývojář; termín „dnes, před
pushem“. Bez preview Async nemá na co klikat — řekni to nahlas. Nic dalšího
neopakuj.

## Krok 1 — Worktrees a prompty

**„Hook“** vysvětli lidsky při prvním použití: je to jednověté zadání
z Kickoffu (co má varianta uživateli slíbit), ze kterého vznikají tři úhly.

```bash
pflanzer worktree setup --slug <slug>
pflanzer quick_session prompts --slug <slug> --hook "<hook ze zadání>" --n 3
```

- Worktrees vznikají v **target repu zákazníka** (ADR-0009), větve
  `pflanzer/<slug>-A|B|C`. Nikdy v repu metody. Víc repozitářů (FE + BE,
  monorepo workspace) umí `target_repos` z Kickoffu — tabulka repo ×
  varianta × path; BE repo dostane prompt „contract-first" (nejdřív OpenAPI
  diff).
- `worktree setup` zároveň nasadí `prepare-commit-msg` hook s trailery
  `Pflanzer-Variant` / `Pflanzer-Session` / `AI-Assisted` (AI provenance,
  N11 — autor commitu je vývojář, nikdy AI), zapíše „Pflanzer session
  rules" do `CLAUDE.md` a pustí **data leakage guard**. `FAIL` v guardu
  (secret, trackované `.env*`, prod dump) = stop před klávesnicí; oprav
  a `pflanzer worktree guard --slug <slug>`. První PR pilotu
  (`docs/INTEGRATION_GUIDE.md` + `CLAUDE.md`) založí `worktree init-pr`.
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

### Diff walkthrough (před hlasováním, ~5 min na variantu)

Bez výkladu kódu hlasují zástupci o UI, ne o kódu (N10). U každé varianty
vývojářský pár na TV ukáže `git diff --stat <base>...HEAD` a
`git log --oneline <base>..HEAD` a řekne tři věty: **reuse** (co existující
použil nebo upravil), **nové** (co přibylo), **mock** (co je stub a v produkci
by chybělo); volitelně kolik scénářů z `tests/acceptance/<slug>.feature`
projelo. Výsledek jde do `diff_summary` ve vote specu. Dimenze effort a risk
se skórují až po walkthrough, ne z pocitu z UI.

## Krok 3 — Checkpoint bezpečnost & právo (20 min, posledních 30 min Buildu)

**Pošli zástupci předem 3 věty** (kolem 5 min práce, checkpoint pak trvá
20 min, ne hodinu): co aplikace čte, kam píše, jestli vidí reálná data.

Zástupce kroku Bezpečnost & právo (jeden člověk) potvrdí nad běžícími
variantami a diffem **tři věci**:

1. **Jaká data AI vidí** — žádná produkční data a osobní údaje v preview,
   v promptech ani v repu.
2. **Kam smí síť** — co smí agent a preview volat ven (default: nic mimo
   povolený seznam).
3. **Kolik smí AI stát** — strop tokenů / nákladů na session a na den, kdo ho hlídá.

K tomu rychle: riziko podstrčené instrukce (agent čte cizí text — issues,
weby, vstup uživatelů), secrets mimo repo, osobní údaje, licence závislostí,
tvrzení v UI. Oddělená kopie repa (worktree) **není bezpečnostní izolace**
(sdílí soubory, secrets i síť stroje). Odborný rozbor (STRIDE, třídy dat
L1–L4, SBOM) patří do stupně Full.

Podepiš (podepsané okno = vstup pro Ship, bez něj Ship pilotu neprojde):

```bash
pflanzer checkpoint --slug <slug> bezpecnost --by "<jméno z Kickoffu>" \
  --note "<co ověřeno / podmínky>"            # veto: přidej --blocked
```

### Když je krok Bezpečnost & právo zastoupen AI

(`path_owners.bezpecnost` je `AI` / `AI:security-expert`; ADR-0023.)

1. Spusť sub-agenta **`security-expert`** (a u osobních údajů
   `legal-gdpr-expert`) nad běžícími variantami a diffem; zadání: tři otázky
   výše + prompt injection + secrets. Výsledek ukaž týmu.
2. Zapiš ho jako **návrh**, ne podpis:

```bash
pflanzer checkpoint --slug <slug> bezpecnost --ai --agent security-expert \
  --note "<shrnutí předkontroly: data, síť, strop nákladů, nálezy>"
```

**Kdo podepíše, když security není** — pořadí (nikdy default autor kódu):
(a) někdo z firmy s mandátem (DPO, IT security, compliance, 20 min);
(b) Decider vědomě převezme riziko — `pflanzer session_3 --slug
<slug> --override-triage --rationale "…"` (jeho jméno v decision logu;
u pilotu bez osobních dat); (c) autor kódu jen jako poslední možnost
u interního nástroje bez osobních dat — nástroj varuje, právo tím pokryté
není.

3. **`throwaway`** — stačí AI. **`pilot` / `production`** — okno zůstane
   „čeká na podpis člověka“. Řekni nahlas, kdo to podepíše (jméno z
   Kickoffu) a že do **48 hodin**, jinak Ship zablokuje; podpis pak:
   `pflanzer checkpoint --slug <slug> bezpecnost --by "<jméno>" --note "…"`.

### Když je krok Design zastoupen AI

Spusť **`ux-expert`** (a `a11y-expert` na kontrolu přístupnosti) nad
variantami; výstup je vstup do diff walkthrough, ne hlas (`is_ai_only: true`,
váha max 0,5). Podepisuje PdM — potvrzení zapiš:

```bash
pflanzer checkpoint --slug <slug> design --by "<jméno PdM>" \
  --note "<co ověřeno>"
```

Výsledek (OK / podmínky / veto) zapiš i do zápisu Buildu. Veto = varianta
nejde na preview, dokud ji Decider výslovně nepřebije s odůvodněním.

## Krok 4 — Push a preview

```bash
git push origin pflanzer/<slug>-A pflanzer/<slug>-B pflanzer/<slug>-C
```

**Připomeň: bez pushe nejsou preview URL a Async nemá na co klikat.**
Preview URL = to, co firma už má (Vercel/Netlify preview, review apps,
preview namespace). Bez produkčních dat. Na každém preview viditelný štítek
**„Varianta X — k rozhodnutí, ne produkt“** + 1 věta, jaký problém řeší.
Chybí-li preview deploy, navrhni konkrétního člověka (zástupce provozu
z projektu) a termín, ne „domluvte s provozem“.
Odkazy (tabulka varianta / URL) pošli všem zástupcům. Interní GitHub často
nejde napojit na Vercel a kód nemá opouštět firmu — pak po pushi spusť
**`pflanzer preview up --slug <slug>`**: spustí aplikaci z worktrees A/B/C,
dá před každou heslo (uživatel `pflanzer`) a štítek „Varianta X k rozhodnutí“,
přes `cloudflared` (je-li v PATH) i veřejnou URL, zapíše URL k variantám a
vypíše hotovou zprávu k přeposlání zástupcům (`--deadline "pátek 17:00"`).
Počítač musí zůstat zapnutý po dobu Asyncu; konec: `pflanzer preview down
--slug <slug>`. Tunel = provoz jde přes Cloudflare — zmiň to na checkpointu
bezpečnosti. Nemá-li firma preview deploy, jde varianty zpřístupnit i jinak: `pflanzer worktree preview --slug
<slug>` založí **draft PR per varianta** (preview URL z PR checks; push do
remote vyžaduje potvrzení), `--mode playwright` nahraje průchod
acceptance scénáři jako video + trace (`docs/postup.md`
§ Kde varianty fyzicky jsou).

## Krok 5 — Zápis Buildu (hlasování)

**Rady pro silent voting:** hlasuje jen přítomné jádro, každý napíše skóre
sám a najednou; hlasujte za to, co uvidí uživatel, ne za kód; důvod jednou
větou; Decider hlasuje vždy poslední (na Rozhodnutí), nepřítomní přes Async.
Skóre až po diff walkthrough.

Zapiš spec nástrojem **Write** do `.pflanzer/specs/<slug>-vote.json`
(necommituje se) a spusť `pflanzer quick_session vote --spec
.pflanzer/specs/<slug>-vote.json`. Heredoc `--spec - <<'EOF'` je jen záloha
(v omezených oprávněních ho blokuje bezpečnostní heuristika Bashe).
**Přesný formát** (`record_voting` → `session.persist`), obsah souboru:

```json
{
  "slug": "<slug>",
  "facilitator": "<jméno>",
  "votes": [
    {
      "variant": "A",
      "name": "A",
      "builder": "claude-code",
      "description": "<1 věta, jaký problém varianta řeší>",
      "diff_summary": {"stat": "<git diff --stat>", "reuse": "…", "new": "…", "mock": "…", "acceptance_pass": "3/4"},
      "role_preferences": [
        {"role_idx": 2, "user_value": 0.8, "effort": 0.3, "risk": 0.2,
         "strategic_fit": 0.9, "commitment_level": 3,
         "rationale": "POVINNÉ — 1–2 věty proč", "is_ai_only": false}
      ]
    }
  ],
  "decider_call": {"shortlist": ["A", "B"], "rationale": "…", "veto_register": [], "parking_lot": []},
  "real_urls": {"A": "https://…", "B": "https://…", "C": "https://…"}
}
```

Pravidla: `role_idx` = číslo role v catalogu (1 zadavatel, 2 PdM, 4 FE, 6 UX,
7 security, 15 DevOps…), hodnoty 0–1, `rationale` povinný u každého řádku,
AI hlas má `is_ai_only: true`. `real_urls` jsou skutečné preview URL
(bez nich zůstane placeholder). Alternativa pro plný zápis s experty:
`pflanzer session --spec .pflanzer/specs/<slug>-session.json` (soubor zapsaný Write).

## Krok 6 — Výstup a další krok

Ukaž lidský výstup toolu + tabulku varianta / branch / preview URL / stav
kontrol / checkpoint B&P (a které kroky zastoupila AI) a předej
**Doporučení** z výstupu. Na konci **jeden** další krok:

> Další krok: `/pm feedback <slug>` — zástupci klikají na preview po dobu
> okna (Lean 3–5 dní, Quick 3, Full 5–7 pracovních dní; ADR-0017); kdo
> feedback nevyplnil, zapíše ho offline přes `pflanzer feedback add`.

Skonči **jednou výzvou** (např. „Pošlete zástupcům odkaz na hub — chcete
text pozvánky?“), ne seznamem možností.

## Co NEDĚLAT

- Žádné placeholdery typu `sandbox.invalid` — bez skutečné preview URL
  řekni, že Async nemá na co klikat.
- Nezakládej projekt tady; to je jen `/pm start`.
- Negeneruj víc než 3 varianty. Nepouštěj víc než 4 experty paralelně.
- Nepřepisuj veto bez rationale do decision logu.

## Reference

- `docs/decisions/0021-mala-skupina-cela-cesta.md`, `0022-inspirace-z-trhu.md`
- `docs/methodology/04-session-1.md` (rozšířená reference Buildu, stupeň Full)
- `docs/zacni.md`, `docs/postup.md`
