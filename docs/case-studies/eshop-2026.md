# e-shop — Pflanzer pilot 2026

> **Status:** Live case study (rolling update). Reálný průběh Pflanzer pilotu
> v Notinu, default profil. Slouží jako *„jak to skutečně vypadá"* reference,
> ne audit artefakt.
>
> **Zdroj:** session notes + retrospektiva facilitátora.
> **Verze:** v0 (2026-05-17, initial write-up); doplnit po T+30 / T+90 retro.

## Kontext

**Organizace:** e-shop — e-commerce platforma (kosmetika / parfémy / beauty),
~7M MAU, ~3000 FTE, primárně CZ/SK/PL/RO trhy.

**Problém:** Rigidní interní workflow od nápadu k programátorům prochází
sériovým handoffem (zadavatel → produkt → UX → vývoj). Kolo trvá řádově
týdny, většina práce v handoff hand-off ztrácí kontext, rozhodnutí jsou
„v emailu", ne v artefaktech.

**Cíl pilotu:** Nasadit AI vibe-coding tak, aby od první alignment session
k produktivnímu kódu trvalo **týdny, ne měsíce**, a aby **většina kódu
z vibe-session šla přímo do produkce** — ne jako reference pro
re-implementaci.

**Profil:** Default (per `00-lean-pflanzer.md`).

**Track designation (per ADR-0020 v0.4):** **Track P (preferred default)** —
dev tým byl v room od minuty 0, output = produkt do prod (ne handoff package
k re-implementaci). e-shop nesplňuje žádný ze 4 Track S triggers (žádný
PSD2 SCA, žádný AI Act High-risk, žádný DORA scope, ne distributed dev,
ne sponsor mandate spec-as-deliverable) — tj. Track S by **nebyl validní**
pro tento pilot, Track P je správná volba.

**Output (per ADR-0005 v0.4):** **evolve** (default) — winner varianta
jde rovnou do produkce.

## Sestava (6 lidí)

Z 18-position role catalogu (`02-role-catalog.md`):

| Role | Catalog # | e-shop assignment |
|------|-----------|---------------------|
| Zadavatel / Sponsor | #1 | _< business owner / VP-level >_ |
| Produkt manažer | #2 | _< PM odpovědný za oblast >_ |
| Facilitátor | #3 | _< facilitator role >_ |
| FE / Vibe-coding lead | #4 | _< FE / vibe lead >_ |
| BE / API lead | #5 | _< BE lead >_ |
| UX / Designer | #6 | _< UX designer >_ |

**Vědomě vynecháno:** Security (#7), Legal (#10), A11y (#11), Champion (#17),
Method Steward — non-regulated default profil je nepotřebuje v místnosti.

## Průběh

### Setkání #1 — vibe session (3 h, in-room)

**Setup:** Všech 6 lidí ve stejné místnosti. AI vibe-coding tools připraveny
(Bolt + v0 + Lovable, paralelně). Sponzor přinesl 1-věty problém,
PM rámcový kontext (kdo, proč, jaký success).

**Aktivita:**
- Tým verbálně rozkládá problém, AI poslouchá kontext.
- Builder lead spouští 3 paralelní vibe-coding runs, každý jinou variantou.
- Po cca 90 minutách: **3 funkční weby** (clickable, deployed).
- Stakeholdeři klikají, anotují, dávají feedback per role.
- Tým rozhodl o shortlistu pro mezi-session iteraci.

**Output:**
- 3 deployed weby (sandbox URL, watermark, noindex).
- 1-page summary kdo co reviewuje a co je open question.
- Žádný formal Charter signed (default profil; success threshold byl
  ústně dohodnut).

### Mezi-session (~5 dní, async)

**Aktivita:**
- Stakeholdeři klikají, anotují weby v shared docu / přes komentáře.
- Builder lead aplikuje feedback do prioritního variantu (winner candidate).
- 1× sync check (15 min) v polovině týdne — *„jdeme dobrým směrem?"*.

**Co fungovalo:**
- 3 reálné weby _>_ tisíc Figma frames. Stakeholdeři dávali konkrétní
  připomínky k chování, ne k vizuálu.
- Cross-fn alignment **rostl mezi setkáními**, ne degradoval — opposite
  patternu sériového handoffu.

### Setkání #2 — doladění (post-feedback session)

**Aktivita:**
- AI prezentuje aggregate feedback per role (heatmap, severity).
- Tým doladil winner variant (final tweaks).
- Decider's Go-call **anti-HiPPO** (zadavatel hlasoval poslední).
- Handoff package pro vývojáře finalized.

**Output:**
- **Winner kód** s definovaným scope.
- Per-role handoff (BE: API contracts; FE: components; UX: design tokens;
  PM: epic + acceptance criteria).
- Konkrétní timeline pro produktové nasazení.

### Ship to production

**Cíl:** Většina kódu z vibe-coding session jde **rovnou do produkce**, ne
jako reference pro re-implementaci.

_< Doplnit po skutečném deploy:_
- Kolik % winner kódu zůstalo v prod commit?
- Kolik dnů od Session 2 → first prod deploy?
- Kolik bugů našel dev tým post-handoff (rework T+7)?
- Jaká byla stakeholder reakce při retrospective?
_>_

## Learnings (initial)

**Co fungovalo:**
1. **3 paralelní weby místo 1 prototypu.** Decision-making accelerated —
   stakeholdeři viděli trade-offs, ne *„this is the option"* presentation.
2. **6 lidí, ne 12.** Decision throughput byl reálný; bez Security/Legal
   v místnosti se neztrácel čas na compliance check, který v default
   profilu není potřeba.
3. **AI vibe-coding ne jako tool, ale jako facilitační páka.** Verbální
   input → instant artefakt → instant feedback. Klasický workshop dělá
   *post-it na flipchart*; tady jsme dělali *kód, který tým hned mohl klikat*.
4. **Anti-HiPPO Decider's call.** Sponzor hlasoval poslední; ostatní role
   měly reálný vliv na výběr varianty, ne jen rubber-stamp.

**Co bych příště udělal jinak:**

_< Doplnit po retro:_
- _Builder kapacita: 1 builder na 3 paralelní weby v 90 min byl tight; možná 2 builders?_
- _Mezi-session ownership: kdo aplikuje feedback do varianty? Builder lead = single point._
- _Decider mandate: ústní success threshold sufficient, nebo 1-row Charter potřebný?_
- _Tech stack consistency: 3 weby na 3 různých builderech → migration overhead. Same builder všechny varianty?_
_>_

## Co tento case study NENÍ

- **Není audit artefakt.** e-shop není regulated; pre-registration, compliance
  score, method-level metrics nemají v tomto případě smysl.
- **Není N=1 statistical evidence.** Single-pilot result je *anecdotal*
  per Akademik perspective (`docs/research/method-falsifiability/04-akademik.md`).
  Generalizace vyžaduje N=12+ napříč orgs.
- **Není proof, že Pflanzer funguje vždy.** Je to *existence proof* —
  konkrétní pilot, který default profil zvládl. Anti-patterns
  (`01-filozofie-a-kdy-pouzit.md`) zůstávají v platnosti.

## Vztah k method-level metrikám

e-shop pilot **NENÍ pre-registered** dle ADR-0013 protokolu — tj. NEZAPOČÍTÁVÁ
se do method-level XYZ hypothesis validation (`method-charter.md` § Success
threshold). To je consistent s default profilem: organizace, která nedělá
multi-pilot rollout, nepotřebuje akademickou disciplínu.

Pokud e-shop spustí **druhý a třetí pilot** stejné metody, doporučujeme:
- Retrospektivně přidat pre-registration template (alespoň fit criteria
  + success threshold) pro nové piloty.
- Method Steward role volitelná (může to být sám facilitátor v 0.1 FTE).
- Po N=3-5 pilotech method-level review smysl dává.

Pod 3 piloty: zůstává jako **case study v `docs/case-studies/`**, ne method-level data.

## Open items (post-T+30 / T+90)

- [ ] Doplnit production deploy outcome (% kódu, dny do prodů, bugy T+7).
- [ ] Stakeholder retrospective notes — co by sponzor / PM / vývojáři dělali jinak.
- [ ] Lagging metric vs baseline — historicky podobný projekt v Notinu trval kolik dní?
- [ ] Pokud druhý e-shop pilot startuje, link sem.

## Reference

- `docs/methodology/00-lean-pflanzer.md` — default profil definice.
- `docs/methodology/01-filozofie-a-kdy-pouzit.md` — fit criteria + anti-patterns.
- `docs/methodology/04-session-1.md` — Session 1 detail (kde e-shop použil
  3h core vibe místo 5-6h audit-grade variantu).
- `docs/research/method-falsifiability/` — proč method-level metrics
  vyžadují N=12+ (e-shop samotný do toho nezapadá).