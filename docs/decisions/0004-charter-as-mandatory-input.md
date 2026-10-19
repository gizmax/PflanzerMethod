# ADR-0004 — Business Charter jako povinný vstup do Session 1

**Status:** Accepted
**Date:** 2026-05-05
**Context source:** perspektivy 01 (Zadavatel), 02 (PdM), synthesis 02 (key themes)

## Kontext

Pflanzerova metoda v0 popisuje „hlavní přípravy" před Session 1, ale
**nedefinuje, co konkrétně musí Zadavatel doručit**. Důsledek z perspektivy
01 (Zadavatel): bez Charteru je metoda „hezký den" — chybí ROI argument do
exec committee, success threshold pro Go/Kill, kill-switch protokol,
reinforcement track. Z perspektivy 02 (PdM): bez explicitního success metric
se Pflanzer stává feature factory s drahým prototypem.

## Rozhodnutí

**Business Charter** je **povinný vstup do Session 1**. Bez podepsaného
Charteru se Session 1 nekoná.

### Struktura Charteru (1 stránka A4)

```
# Pflanzer Charter — <projekt>

## Hypotéza (XYZ format)
Věříme, že [persona] s [JTBD] potřebuje [řešení],
což měříme růstem [metric] o [delta] během [time window].

## Decider + eskalační řetězec
- Decider: <jméno>, role, mandát od <CPO/sponzor>, datum, podpis.
- CPO / sponzor (eskalační kontakt dle ADR-0001 Scenario A/B): <jméno>, datum, podpis.
- Backup Decider (volitelné, automatická delegace při PTO): <jméno>.
- **Eskalační protokol**: aplikuje se **kanonický Decider eskalační protokol**
  z `docs/decisions/0001-decider-model.md`. Charter ho neduplikuje, jen odkazuje.

## Success threshold
- Primary lagging metric: <X po Y dnech>.
- Leading metric (proxy): <měřitelné v Z dnech>.
- Guardrail metric: nesmí <regrese parametru>.

## Kill criteria
- Pokud <X po Y dnech>, projekt zrušíme.
- Pokud <Z>, eskalace na exec.

## Kapacitní commit
- Eng kapacita: <Z person-days za PI>.
- Sponzor uvolnil/neuvolnil commit features.
- IP iteration availability: <ano/ne, kdy>.

## Risk profile
- AI Act risk-tier: <Minimal / Limited / High>.
- Data classification: <L1/L2/L3>.
- Throw-away vs evolve prototype: <volba s důvodem (viz ADR-0005)>.

## Reinforcement track — explicit budget commit (v0.3, Útok 11 resolution)
Charter podpisem sponzor a EM commitují **rozpočet a vlastníky** každého
readoutu. Bez tohoto commitu Session 1 neodstartuje. Detail viz
`docs/methodology/03-pre-session-priprava.md` Krok 1a (True Cost Worksheet).

| Readout | Vlastník | Min. PD | Akceptační kritérium | Sankce za vynechání |
|---------|----------|---------|---------------------|---------------------|
| T+7 | Champion (#17) | 0.5 PD | Handoff přijatý dev týmem, SHIP.md status řádek aktualizovaný | Flag do T+30 retro, Method Steward data feed |
| T+30 | PdM + EM + Champion | 2.0 PD | Leading metric check (handoff acceptance ≥ 80 %), retro 60 min | Method Steward warning, audit-grade pilot disqualified |
| T+60 | PdM + Champion | 1.0 PD | Scope creep audit, Method Steward 1-page update | Method-level T+6 report flaguje pilot „incomplete reinforcement" |
| T+90 | Decider + PdM + EM + Champion | 2.5 PD | Guardrail metric (re-work %) vyhodnocen, **Go / Iterate / Kill rozhodnutí formálně v ADR** per ADR-0001 protokolu | Silence = Kill (ADR-0001 Scenario B) |

**Σ Reinforcement commit (default profil): min 6 PD souhrnně.**
Zdroj rozpočtu (cost center / BU budget line) musí být uveden v sign-off
sekci Charteru, ne jen „dohodneme se".

**Audit dotaz po pilotu** (Method Steward T+6 method-level report):
> *„Z plánovaných N reinforcement PD bylo skutečně utraceno M. Pokud
> M/N < 0.7, T+90 Go-rozhodnutí má warning: reinforcement neproběhl,
> success claim není falsifikovatelný; per ADR-0007 method-level
> pilot není započítán do success rate."*
```

### Vlastnictví a podpisy

- **Píše:** Zadavatel (#1) + PdM (#2).
- **Podpisuje:** Decider (jmenovitě) + Sponsor (CPO nebo CTO-side).
- **Reviewuje (pre-read 48 h):** Security (#7), Legal (#10), EM (#9).
- **Ukládá se:** v `decisions/charters/<project-slug>.md` v projektovém repu.

### Kdy se Charter aktualizuje

- Po Session 2: aktualizuje se s rozhodnutím Decideru.
- Po T+30/T+60/T+90 review: success threshold porovnán s reálnou metrikou.

## Důsledky

**Pozitivní:**
- ROI argument do exec committee existuje **před** workshopem, ne po něm.
- Decider má písemný mandát (závaznost).
- Kill criteria předem zdokumentovaná → snižuje sunk-cost fallacy.
- Reinforcement track 30/60/90 řeší post-launch loop (perspektiva 13).

**Negativní:**
- Příprava Charteru = ~4 hodiny zadavatele/PM.
- Některé projekty „nemají hypotézu" — to je signál, že Pflanzer není správný
  nástroj (anti-pattern viz `01-filozofie-a-kdy-pouzit.md`).

**Mitigace:**
- Template Charteru je součástí toolu (fáze 2) — vyplnění průvodcem.
- Charter-light pro discovery-fáze projekty (bez success threshold, místo toho
  „learning agenda").

## Reference

- Knapp, J. *Sprint* — Long-term goal definition.
- Cagan, M. *Inspired* — Outcome over output.
- Torres, T. — Opportunity Solution Tree.
