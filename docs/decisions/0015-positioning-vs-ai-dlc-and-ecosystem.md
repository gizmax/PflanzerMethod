# ADR-0015 — Pflanzer positioning vs AWS AI-DLC + ecosystem interop

**Status:** Accepted (v0.3)
**Date:** 2026-05-18
**Context source:** Competitive research May 2026 — 3 paralelní experti (workshop methodology, AI vibe-coding, enterprise transformation). Synthesis: `docs/research/competitive/04-synthesis-and-positioning.md`.

## Kontext

Competitive research identifikoval **jednoho přímého konkurenta** s ~60-70 % DNA
overlapem proti Pflanzeru: **AWS AI-DLC** (Raja SP, AWS DevOps blog 31/7/2025;
re:Invent 2025 DVT214; open source `github.com/awslabs/aidlc-workflows`).

AI-DLC sdílí s Pflanzer Session 1 ceremoniál „Mob Elaboration" (3-4h cross-fn
session, AI navrhuje → mob validuje). Distribuováno přes AWS partner channel —
**bigger reach než Pflanzer dnes má**.

Současně research identifikoval **3 komplementární frameworky**, které Pflanzer
dnes ignoruje, ale které tvoří přirozený ekosystém:

- **Foundation Sprint** (Knapp/Zeratsky, kniha *Click* 2025) — pre-implementation
  strategic foundation (2h problem framing). Logický pre-step k Pflanzer Charteru.
- **BMAD-METHOD** (MIT, `bmad-code-org`) — AI agent personas pro 12+ rolí.
  Pflanzer ho už interně používá jako sub-agent architekturu, ale **nemá
  explicit interop dokumentaci**.
- **Spec Kit / Amazon Kiro / OpenSpec** — spec-driven development frameworks.
  Pflanzer handoff package by mohl být **spec-kit-compatible export target**.

Bez explicit positioning rozhodnutí Pflanzer riskuje:
1. **Konkurenční konflikt** s AWS AI-DLC v každém enterprise pitchi (kdo
   přijde druhý, ztratí).
2. **Ekosystémová izolace** — Pflanzer jako *„yet another methodology"*,
   ne jako interoperabilní layer.
3. **Distribuční nevýhodu** — AWS AI-DLC má channel; Pflanzer free / GitHub-only.

## Rozhodnutí

### A) Pflanzer pozice **vs AWS AI-DLC**

**Pflanzer NEKONFLIKTUJE s AI-DLC head-on**. Pozice diferenciace:

> *„AWS AI-DLC = engineering velocity methodology. Pflanzer = cross-functional
> AI pilot fixture s native AI Act compliance. Komplementární layers, ne
> substituty."*

Konkrétně:

| Atribut | AWS AI-DLC | Pflanzer |
|---------|------------|----------|
| **Primary audience** | Engineering tým (BA/PM/eng/QA/ops) | Cross-functional (vč. Security/Legal/DPO/A11y/UX-writer/CS-proxy) |
| **Format** | Continuous „bolts" (3-4h Mob Elaboration) | 2-session formát (3-6h S1 + 5-7d async + 3h S2) |
| **Compliance** | Engineering-grade, žádný explicit audit trail | Native AI Act čl. 14 + DORA-grade audit log |
| **Distribuce** | AWS partner channel (free OSS) | Pflanzer free OSS + audit-grade consulting |
| **Sweet spot** | Tech team mob coding s AWS stack | Regulated enterprise pilot (banking, insurance, public sector) |

**Differentiation language pro marketing / pitch:**
- *„Pflanzer pokračuje tam, kde AI-DLC končí — když do místnosti musí přijít
  Security, Legal a DPO."*
- *„Pokud děláte AI-DLC mob a narazíte na AI Act gate, Pflanzer je váš
  next-layer protokol."*

### B) Ekosystémový interop

Pflanzer v0.4 explicitně dokumentuje **3 interop body**:

1. **Foundation Sprint → Pflanzer Charter (upstream)**
   - Foundation Sprint output (problem framing, audience, USP, 2h artifact)
     je validní `pflanzer-charter` input.
   - Pflanzer Charter wizard přidává otázku: *„Existuje Foundation Sprint output?
     [Yes/No]"* — pokud Yes, pre-vyplní problem statement.
   - Doporučení v dokumentaci: Pflanzer **nenahrazuje** Foundation Sprint;
     je to optional pre-step pro greenfield strategic problems.

2. **Pflanzer Handoff → Spec Kit / Kiro (downstream)**
   - Pflanzer Session 2 handoff package přidává `spec-kit-compatible.md` export.
   - Šablona v `tool/templates/handoff-spec-kit.md.template` (P1 backlog,
     viz P0-1 doporučení níže).
   - Dev tým po Pflanzer handoffu může pokračovat se Spec Kit / Kiro / OpenSpec
     v continuous development režimu.

3. **Pflanzer Sub-agents ↔ BMAD-METHOD personas (interní)**
   - Pflanzer dnes používá 23 role-expert sub-agents v `.claude/agents/`.
     BMAD-METHOD nabízí AI personas pro 12+ rolí jako standardizovaný
     framework.
   - **Rozhodnutí:** Pflanzer **NE-adoptuje BMAD jako engine**, ale dokumentuje
     mapping `pflanzer-role` ↔ `BMAD persona` v `02-role-catalog.md` (P1).
   - Důvod: BMAD je solo / agent-only (žádní lidé v místnosti); Pflanzer je
     human-in-room s AI proxy. Filosofie je rozdílná.

### C) Naming neutralita

V dokumentaci a marketing materialu **NEPOUŽÍVAT** „AI Design Sprint" — je to
**Design Sprint Academy (DSA) brand**. Místo toho:

- *„AI-augmented workshop"* (generický termín)
- *„Cross-functional AI session"* (Pflanzer-specific)
- *„14-day production AI cycle"* (Pflanzer marketing tagline kandidát)

### D) Distribuční strategie

Pflanzer **nemůže porazit AWS distribution sám**. Strategie:

1. **GitHub OSS first** — Pflanzer zůstává free / open. AWS AI-DLC přitahuje
   pozornost na kategorii; Pflanzer ji zachycuje jako *„enterprise-grade variant"*.
2. **Accenture AABG channel pitch** (Q3 2026) — Accenture Anthropic Business
   Group (12/2025 launch, 30 000 trained Claude Code lidí) jako single
   highest-leverage target. Pflanzer = ready-made methodology pro AABG client work.
3. **Open partnership posture vůči AWS** — pokud AI-DLC team kontaktuje,
   Pflanzer otevřený pro `pflanzer-aidlc-bridge` repo (Foundation Sprint
   pattern: knihy spolupracují, ne soupeří).

## Důsledky

**Pozitivní:**
- **Konkurenční pozice clear** — Pflanzer není AWS AI-DLC kompetitor, je
  next-layer pro regulated enterprise.
- **Ekosystémová viditelnost** — Foundation Sprint, BMAD, Spec Kit komunity
  mají důvod Pflanzer odkazovat (komplement, ne soupeř).
- **Distribuční opportunity** — AABG pitch má konkrétní hook (workflow
  redesign methodology pro Digital Core engagement).
- **Brand safety** — „AI Design Sprint" collision avoided.

**Negativní:**
- **Loss of category ownership** — Pflanzer neclaim *„the workshop methodology
  for AI in enterprise"*; připouští, že kategorie má více hráčů.
- **AABG dependency** — pokud Accenture partnership selže (Q3-Q4 2026
  realistický horizont), Pflanzer zůstane GitHub OSS bez channel.

**Mitigace:**
- **Multiple channel exploration** — AABG, AWS partner, ICAgile (P2 backlog
  per `docs/research/competitive/04-synthesis-and-positioning.md` P2-13).
- **e-shop case study formalize** + 2-3 CEE bank/telco audit-grade reference
  (P1) — independent traction, ne channel-dependent.

## Update existující dokumentace

- `docs/methodology/09-srovnani-existujici-metody.md` — **DONE** v0.3 update
  (AI workflow family table + enterprise consulting layer table + 5 protected
  USPs rewrite).
- `docs/methodology/00-lean-pflanzer.md` — P1: doplnit „kdy NE Pflanzer,
  NE AI-DLC instead" decision tree entry.
- `tool/templates/handoff-spec-kit.md.template` — P1 (interop export).
- `README.md` — P1 update sekce „Začni tady" s odkazem na 04-synthesis.
- `website/index.html` — P0 update USP framing (pivot z vibe-coding na
  5 protected pilíře).

## Out of scope (deferred)

- **ADR-0016 — Vibe coding terminology** (Option C selective use; P1 backlog).
- **ADR-0017 — Foundation Sprint relationship detail** (P1 backlog;
  partial covered here).
- **ADR-0018 — Strategic naming decision** (eponym vs „Pflanzer Cycle"
  vs „14-Day AI Pilot Cycle" — Tom rozhoduje).
- **Pricing tiers + MSA template** (P2 backlog).
- **AABG channel pitch deck** (P2 backlog).
- **Martinelli paper citation strategy** (P2 backlog).
- **ICAgile partnership** (P3 backlog).

## Reference

- Competitive research synthesis: `docs/research/competitive/04-synthesis-and-positioning.md`
- AWS AI-DLC: `github.com/awslabs/aidlc-workflows`, AWS DevOps blog 07/2025, re:Invent DVT214 12/2025
- Foundation Sprint: Knapp & Zeratsky, *Click* (2025)
- BMAD-METHOD: `github.com/bmad-code-org/BMAD-METHOD`
- Spec Kit: `github.com/github/spec-kit` (93k stars)
- Accenture Anthropic Business Group (AABG): 12/2025 launch
- Martinelli, *„Why Spec-Driven Development Tools Fail in the Enterprise"* (2026)
