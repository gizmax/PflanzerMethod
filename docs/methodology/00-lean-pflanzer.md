# Lean Pflanzer — default profil (1-pager)

> **Tohle čti první**, pokud chceš metodu **použít**, ne studovat.
> Pro audit-grade variantu (banky, DORA, AI Act High-risk) viz
> `method-charter.md` + ADR-0011/0012/0013/0014.
>
> Default profil = **~80 % use casů**: B2B / B2C eshop / SaaS / interní tool,
> non-mission-critical, žádný regulatorní gate. e-shop, marketing site, app
> feature, internal dashboard, CRM rework.

## Co Pflanzer skutečně je

Sedm lidí (sponzor + 5 z workflow + facilitátor), 2 setkání, 1 týden mezi nimi,
většina kódu jde rovnou do produkce. Pomáhá korporátu nasadit AI na zrychlení
rigidních procesů (sériový handoff zadavatel → produkt → vývoj → security → deploy).

**To je vše.** Vše ostatní v `docs/methodology/` (Method Steward, pre-registration,
compliance score, leading indicators, DORA prompt audit pipeline, AI Act Fáze A/B/C)
je **audit-grade overhead** — relevantní pouze pro regulated industries, kde
audit committee tě po roce zeptá *„jak víte, že to funguje?"*.

## Real-world recept (~14 dní calendar, ~10 PD effort)

```
Den 0: 1× kávový meeting (60 min)
  Sponzor + 5 lidi z workflow napříč rolemi (zadavatel → vývojář)
  → kdo, kdy, co bude na stole, jaký je success threshold (1 věta)

Den 5: Session 1 — vibe (3 h, in-room)
  /pflanzer "<problém v 1 větě>"
  → 2-3 paralelně postavené weby v Bolt / v0 / Lovable / Claude Code
  → silent voting + Decider's shortlist
  → 1-page MD shrnutí, kdo co reviewuje

Den 6-9: async iterace (4 dni)
  Stakeholdeři klikají, komentují v shared docu nebo PR komentech
  Builder lead doplňuje variantu podle feedbacku
  /pflanzer-feedback-pull <slug>  (volitelné, agreguje per role)

Den 10: Session 2 — doladění + rozhodnutí (3 h)
  /pflanzer-session-2 <slug>
  → Decider's Go / Iterate / Kill, anti-HiPPO (hlasuje poslední)
  → Winner finalized, scope locked

Den 11-14: Ship to prod (1-2 dny vývojářů)
  /pflanzer-session-3 <slug>   # extract → quality gates score 0-100
  /pflanzer-handoff <slug>     # PR-ready package
  Vývojáři doladí edge-case bugy, deploy, monitorování.
```

## Co tým dostane

- **3 funkční weby** (ne mockupy v Figmě) — clickable, deployed v sandbox URL,
  stakeholdeři je vidí ve svém prohlížeči.
- **Winner kód** (≥80/100 gate score) — Vite + React + TS + ESLint + Vitest,
  exportovatelný do target repu.
- **Per-role handoff** s odkazy na konkrétní soubory (ne TBD placeholders).
- **Decision log** kdo co rozhodl proč (DORA-friendly bez DORA-grade overhead).

## Co tým NEpotřebuje (vs audit-grade)

Default profil **vědomě vynechává**:

| Audit-grade vyžaduje | Default vynechává | Proč |
|----------------------|--------------------|------|
| Method Steward 0.5 FTE €100-150k/rok | – | Method-level kalkulace má smysl až po 3+ pilotech v org |
| Pre-registration document signed pre-S1 | – | Stačí jednověté success threshold v meeting notes |
| Pflanzer Compliance Score 12 elementů ex-post | – | Steward neexistuje; PM si po pilotu napíše 1 řádek learning |
| AI Act Fáze A/B/C dvoufázový protokol | – | Pokud projekt není High-risk per AI Act, žádné fáze. Limited tier = checkbox. |
| DORA prompt audit pipeline (SIEM ingest, 7y retention) | – | Pokud nejsi banka / pojišťovna, DORA tě nezajímá. |
| True Cost Worksheet per-role × per-phase | Stačí orientační ~10 PD odhad | Detailní worksheet má smysl tam, kde sponzor hlídá KAŽDÝ PD |
| Blind external EM panel z jiných BU | – | Operational EM acceptance + 1× retro stačí pro non-regulated |
| ADR-0001 Decider eskalační protokol (Scenario A/B/C) | Decider má tie-breaker, sponzor je informován | Lightweight eskalace stačí |
| Leading indicators dashboard (LI-1 až LI-5) | – | Method-level dashboard má smysl po 3+ pilotech |

**Realistický effort pro default profil:** ~10 PD (per `03-pre-session-priprava.md`
True Cost Worksheet § Default profil). Z toho:
- Pre-flight + Charter: 1.5 PD (sponzor + PM)
- Session 1 + builder prep: 2 PD (facilitator + builder lead)
- Mezi-session iterace: 2.5 PD (builder + stakeholder review)
- Session 2 + Decider's call: 1.5 PD
- Handoff + extract + quality gates: 1.5 PD
- T+7 a T+30 reinforcement (light): 1 PD

## Kdy default NEsTAČÍ — upgrade na audit-grade

Přidej kompletní overhead z `method-charter.md` v0.3, pokud platí **kterékoli**:

1. **AI Act High-risk** (čl. 6 + Annex III: HR, education, critical infra,
   biometrics, law enforcement, …) → Fáze A/B/C protokol povinný.
2. **DORA scope** (banking, pojišťovny EU) → prompt audit pipeline + 7-letá retence.
3. **PSD2 SCA / payment flow** → standardní SDLC, **Pflanzer se nehraje**
   (per `01-filozofie-a-kdy-pouzit.md` antipattern).
4. **Public sector / GDPR special category data** → DPIA full + RoPA + Privacy Notice.
5. **Method-level rollout** — chceš metodu zavést jako proces napříč
   organizací → Method Steward, compliance score, T+18 sunset checkpoint, et al.
   (Pflanzer méně než pilot = nepotřebuješ ADR-0011/12/13/14.)

Pokud projekt **nesplňuje ANI JEDEN bod výše**, jdeš s default profilem.
Pro e-shop-style eshop → default. Tečka.

## Role catalog v default profilu

Z 18-position catalogu (`02-role-catalog.md`) v default profilu **stačí
6-7 lidí v místnosti**:

| Role | Z catalogu | Default profil |
|------|------------|----------------|
| Zadavatel / Sponzor | #1 | Povinný |
| PM | #2 | Povinný |
| Facilitátor | #3 | Povinný (často PM nebo dedikovaný) |
| FE / Vibe-coding lead | #4 | Povinný |
| BE / API lead | #5 | Povinný (pokud projekt má backend) |
| UX / Designer | #6 | Doporučený |
| EM | #9 | Doporučený (signs off capacity) |

**Vynecháno proti audit-grade:** Security (#7), Legal/DPO (#10), A11y (#11),
UX writer (#12), Data analyst (#13), Solution architect (#14), DevOps (#15),
CS proxy (#16), Champion (#17), Compliance auditor.

Security a Legal v default profilu **NEjsou v místnosti** — checklist
1-pager je dostatečný (data classification L1/L2, žádný external pen test
vyžadovaný, žádná special category data).

## Anti-patterny default profilu

Default profil **selhává**, pokud:

- **Sponzor není v 1. setkání.** Pflanzer cyklus má 2 sessions; bez sponzor
  buy-in v meeting #1 metoda generuje krásné mockupy, které nikdo nepřevezme.
- **Vývojářský tým nevidí Session 1 prototyp.** Pokud builder lead je sólo
  AI vyvojář a dev tým dostává jen handoff, kvalita předání klesá.
- **3+ stakeholdery se nehlásí mezi-session.** Async feedback nemůže být
  >20% absentee rate, jinak Session 2 dělá rozhodnutí s neúplnými daty.
- **Decider hlasuje první.** Anti-HiPPO je core differentiator Pflanzeru
  i v default profilu. Pokud sponzor řekne *„já chci variantu B"* před silent
  voting, ostatní role rubber-stampují a metoda neabsorbuje cross-fn alignment.

## Vztah k ostatním dokumentům

- **Tohle (00-lean-pflanzer.md)** = default profil quick-start.
- **`00-tldr.md`** = management 1-pager (proč to dělat, ROI argument).
- **`01-filozofie-a-kdy-pouzit.md`** = kdy ano / kdy ne (fit criteria + anti-patterns).
- **`02-role-catalog.md` až `09-srovnani-existujici-metody.md`** = detail pro audit-grade.
- **`method-charter.md` + ADR-0011/12/13/14** = method-level governance
  (jen pokud děláš method-level rollout, ne single pilot).

**Single-pilot e-shop-shape projekt = potřebuješ jen tento dokument
+ `01-filozofie-a-kdy-pouzit.md` + `04-session-1.md` (jako reference pro průběh).**

## Reference

- Case study: `docs/case-studies/eshop-2026.md` — reálný průběh.
- Tool quick-start: `README.md` § Quick start.
- Detail per fáze: `03-pre-session-priprava.md`, `04-session-1.md`,
  `05-mezi-sessions.md`, `06-session-2.md`, `07-handoff-do-vyvoje.md`.