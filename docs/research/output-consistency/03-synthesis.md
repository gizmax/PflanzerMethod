# Output Consistency — Synthesis

> Synthesis 2 paralelních auditů (May 2026):
> - `01-methodology-audit.md` (~698 ř., 11 methodology souborů)
> - `02-marketing-audit.md` (~392 ř., website + 1-pager + README)
>
> User clarification: *„Pflanzer metoda by ti měla dát již reálný běžící
> produkt, proto je tam od startu programátor, aby to šlo rovnou nasadit.
> Žádná specka se programátorům nedává. Výstup z Pflanzer metody je
> hotový produkt."*

---

## TLDR

**Disconnect mezi positioning copy a metodologickou dokumentací.**
Marketing v hero/CTA říká *„kód v produkci za 14 dní"*. Methodology v 7
z 11 souborů říká *„handoff package, který tým vývoje může vzít a postavit
z něj produkt"*. Tyto dvě věty se vylučují. ADR-0005 throw-away default
říká *„produkce se píše znovu jako specs-driven re-implementation"* —
**doslovný protiklad** user claim.

Najít a opravit P0 (12 míst napříč 8 soubory): ~3 PD práce.

---

## Pflanzer claim states (per user)

- Output Pflanzer cyklu = **běžící produkt na URL, ne handoff package**
- Vývojář v room od minuty 0 = právě proto, aby kód šel rovnou do prod
- Žádná specka se po Session 2 nepředává — kód JE deliverable
- Quality gates ≥ 80/100 = **production threshold** (ne „prototype hardening threshold")
- Session 3 / extract step = nice-to-have polish, ne mandatory production prerequisite

---

## Top 12 P0 fixes

### Marketing (5 mist, biggest leverage)

| # | File:Line | Current | Fix |
|---|-----------|---------|-----|
| **M1** | `website/index.html:~2077` (sekce 02b col-pflanzer) | „Funkční klikací prototyp od hodiny 1" | „Běžící produkt od hodiny 1" |
| **M2** | `website/index.html:~2173` (comparison matrix Pflanzer output) | „3 prototyp · prod kód" | „Produkční kód · deploys at D14" |
| **M3** | `website/index.html:~2293` (e-shop receipts) | „3 prototyp" | „3 produkční weby" |
| **M4** | `docs/methodology/00-tldr.md` 5 weak frází (ř. 17, 29, 33, 44, 50) | „mockupy / klikací prototypy / Prototype-to-Prod / throw-away default" | Strong product language napříč |
| **M5** | 6× „většina kódu / most code" napříč materiály | „Většina kódu jde do produkce" | „Kód jde do produkce" (drop hedge) NEBO e-shop pattern „kód jde do prod, ne jako reference pro re-implementaci" |

### Methodology (7 míst)

| # | File:Line | Current | Fix |
|---|-----------|---------|-----|
| **D1** | `07-handoff-do-vyvoje.md:3-5` (lede paragraph) | „Výstupem Session 2 není 'kód', ale podepsaný handoff package, který tým vývoje může vzít a postavit z něj produkt" | „Výstupem Session 2 je běžící produkt na URL + sign-off package (audit trail, decision log, compliance artefakty). Dev team byl v room od minuty 0 — žádná re-implementace." |
| **D2** | `01-filozofie-a-kdy-pouzit.md:147` | „Pflanzer končí handoff package, ne launchem" | „Pflanzer končí běžícím produktem v produkci. Sign-off package je audit log, ne re-impl spec." |
| **D3** | `method-charter.md` XYZ hypothesis (ř. 42-44, 62-63) | „time-to-handoff-package" metric | „time-to-production-deploy" metric (signed Charter → first commit s `#prod` tag in target repo) |
| **D4** | `ADR-0005 throw-away vs evolve` | „Default = throw-away. Produkce se píše znovu jako specs-driven re-implementation." | Inverted: **„Default = evolve (kód jde rovnou do prod). Throw-away = explicit opt-in pro 3 výjimky: (1) discovery-only pilots (2) audit-grade evidence collection (3) regulatorní gate kde MUST mít separate prod implementation."** |
| **D5** | `04-session-1.md:13-14` | „Session neproduktivuje finální feature" | „Session 1 produktivuje 3 paralelní produkční-ready varianty. Session 2 vybere winner. Žádná re-impl." |
| **D6** | `03-pre-session-priprava.md:164` (True Cost Worksheet) | FE lead: „1.0 PD (extract / hardening, viz Sprint 2)" | FE lead: „0.5 PD (polish + observability hookup pro deploy)" — drop „extract / hardening" framing |
| **D7** | **Session 3 framing** napříč repo | „Session 3 — Production hardening, extract code → 7 quality gates" | „Session 3 — Optional polish + observability + monitoring setup. Quality gates již proběhly v Session 2 handoff." NEBO úplně zrušit Session 3 jako mandatory step. |

---

## Glossary recommendation

Vytvořit `docs/methodology/glossary.md` s definicemi termínů, kde dnes
panuje nejednoznačnost:

```
**artefakt** = běžící produkční kód na URL. NE Figma mockup, NE PDF spec,
NE PowerPoint slide. Pflanzer artefakt JE deliverable, ne reference k němu.

**produkt** = primary output Pflanzer cyklu. Běžící, klikatelný, deploy-able,
auditovatelný kód v target prod repo. Po Session 2 už existuje, dev tým
ho během D11-14 doladí (observability, monitoring, edge cases).

**handoff package** (deprecated term) → REPLACE with **sign-off package**.
Sign-off = audit trail, decision log, compliance artefakty (AI Act Fáze C,
DORA 7y retention, role attribution). Ne re-implementation spec.

**prototyp** (deprecated term) — RESERVED pro 3 explicit výjimky:
discovery-only pilots, audit-grade evidence (separate from prod), regulatorní
gate. V default profilu se termín NEPOUŽÍVÁ.

**throw-away** — explicit opt-in flag v Charteru pro 3 výjimky výše.
NE default. Default = evolve (kód jde do prod).
```

---

## Honest tension audit

User claim *„výstup je hotový produkt"* je **strong claim**, který:

✅ **Funguje pro:**
- e-shop-style default pilots (eshop, internal tool, SaaS feature)
- 80 % use casů
- Hero/CTA marketing
- Persona B (VP Eng) magnet

⚠️ **Vyžaduje nuance pro:**
- Audit-grade (banks, AI Act High-risk, DORA): produkt JE deploy-ready, ale **prod deploy gate** může vyžadovat additional sign-offs (DPO, CRO, CAB approval). To není „re-implementace", to je separate compliance gate.
- Regulated industries kde **production = certified production** (FDA, IEC 62304, DO-178C). Tam Pflanzer artefakt = staging/QA-ready, certification path je separate.

⚠️ **Konflikt s:**
- ADR-0005 throw-away default — **musí se invertovat** nebo úplně přepsat
- Session 3 framing („extract → hardening") — implies S1+S2 ne-prod-ready
- True Cost Worksheet „hardening" PD — implicit doznání

---

## Doporučená sekvence implementace

### P0 batch 1 — Marketing (1 hodina, biggest leverage)

1. Fix sekce 02b „prototyp" → „produkt" (CS + EN)
2. Comparison matrix Pflanzer output: „3 prototyp · prod kód" → „Produkční kód · D14 deploy"
3. e-shop Receipts: „3 prototyp" → „3 produkční weby"
4. 00-tldr.md sweep 6 weak frází
5. 6× „většina kódu" → „kód" (drop hedge)
6. 1-pager Recipe Day 5 stage name: „Session 1 · vibe" → „Session 1 · build" (drop „vibe" if ambiguous)

### P0 batch 2 — Methodology (2 hodiny)

7. Rewrite `07-handoff-do-vyvoje.md` lede + intro (D1)
8. Rewrite `01-filozofie-a-kdy-pouzit.md:147` (D2)
9. Switch method-charter XYZ metric (D3)
10. Glossary.md vytvořit
11. Sweep 04-session-1 + 05-mezi-sessions + 06-session-2 — replace „prototyp/mockup" s „produkt" nebo „varianta"

### P0 batch 3 — Strategic (vyžaduje user rozhodnutí)

12. ADR-0005 invert (D4) — **TENTO KROK VYŽADUJE TOM CONFIRMATION** protože:
    - Vlivá na celou metodologickou logiku
    - Audit-grade vs default profile bifurcation
    - Method Charter Sunset / Kill criteria

    **Tom volba:**
    - Option A: Invert default (evolve = default, throw-away = opt-in)
    - Option B: Keep throw-away default ale redefine („throw-away = variant pruning po S1 silent vote, ne whole-app rewrite")
    - Option C: Bifurcate — lean profile = evolve, audit-grade = throw-away

---

## P0 expected impact

- **Hero/CTA marketing remains strong** (already product language)
- **Sekce 02b a comparison matrix** odstraní logickou díru (anti-SDD argument konzistentní s vlastním copy)
- **Methodology** přestane sabotovat marketing claim
- **00-tldr** (Persona A first read) přestane být kontradikce
- **Glossary** dá adoption týmům jasné termíny — řeší user feedback *„co znamená artefakt?"*
- **ADR-0005 inversion** (pokud Tom confirms) → consistent positioning napříč

---

## Reference

- `01-methodology-audit.md` (full file scan)
- `02-marketing-audit.md` (full marketing scan)
- User clarification 2026-05-28
