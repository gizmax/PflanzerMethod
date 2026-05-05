# ADR-0005 — Throw-away vs evolve prototype (default = throw-away)

**Status:** Accepted
**Date:** 2026-05-05
**Context source:** perspektivy 04 (FE/Vibe-coding lead), 08 (QA), 15 (DevOps), synthesis 01 (conflict matrix Top 5)

## Kontext

Pflanzerova metoda v0 mlčí o **vztahu vibe-prototypu k produkčnímu kódu**.
Z perspektivy 04 (FE) je to **největší strukturální díra**: bez explicitního
rozhodnutí vzniká **production by stealth** — prototyp se pomalu „dostane"
do produkce bez code review, bez testů, bez observability, s halucionovaným
schema. Tento vzor je opakovaně pojmenován v perspektivách 04, 08, 15.

## Varianty

1. **Default evolve** — prototyp je seedem produkce. Riziko: tech debt,
   shadow IT, design system drift, P2P bez testů (perspektiva 04, 08).
2. **Default throw-away** — prototyp je discovery artefakt, produkce se píše
   znovu na základě Handoff package. Bezpečnější, ale dražší.
3. **Per-project rozhodnutí v Charteru** (varianta 1 nebo 2 podle kontextu).

## Rozhodnutí

**Variant 3 s defaultem throw-away.** Charter (ADR-0004) povinně obsahuje
sekci **Throw-away vs evolve** s explicitní volbou:

### Default — throw-away

- Prototyp je **discovery artefakt** s 24h TTL sandbox.
- Produkce se píše znovu na základě **Handoff package** (`07-handoff-do-vyvoje.md`).
- Žádná direct cesta z sandbox URL do produkce.
- Code z prototypu lze copy-paste-adapt, ne git-merge.

### Opt-in — evolve

Volitelný pro projekty, kde:
- Tým, který bude v produkci, je v session 1 přítomen v plné síle.
- Stack v session = stack v produkci (žádný v0.dev pro production-grade Next.js).
- Code review proces aplikuje se i na vibe-generated code (žádné free pass).
- Design system compliance ≥ 90 % (token compliance check).
- Test pyramide split předem stanoven (perspektiva 08).
- Promote-to-prod gate checklist projde (perspektiva 15).

**Rozhodnutí evolve nezávisí na facilitátorovi ani AI** — vlastní ho **FE lead
(#4) + EM (#9) + DevOps (#15)** společně, podpis v Charteru.

### Konsekvence pro Handoff

Throw-away → Handoff package = **specifikace + draft kódu jako reference**.
Evolve → Handoff package = **specifikace + repo s commit history + Promote-to-prod gate**.

Detail v `07-handoff-do-vyvoje.md`.

## Důsledky

**Pozitivní:**
- Eliminuje „production by stealth" pattern — explicitní governance volba.
- Throw-away default chrání kvalitu (perspektiva 04, 08, 15).
- Evolve opt-in je možný pro týmy, které mají disciplínu (champion model).

**Negativní:**
- Throw-away znamená duplicitní práce (prototyp + produkce).
- Pro některé Decideri to vypadá „ztracený čas" — adresováno v Charteru
  (Charter explicitně počítá s rewriting effortem).

**Mitigace:**
- AI co-pilot fáze 2 generuje **Handoff package** přímo z prototypu, takže
  rewrite není „od nuly" — je to specs-driven re-implementation.
- Evolve cesta je dostupná, ale vyžaduje 6 podmínek splnit (governance gate).

## Reference

- Savoia, A. *The Right It* — pretotyping vs prototyping.
- Cagan, M. — discovery vs delivery prototypes.
- Perspektivy 04 / 08 / 15.
