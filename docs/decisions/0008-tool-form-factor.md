# ADR-0008 — Tool form-factor pro Pflanzer

**Status:** Proposed (čeká na potvrzení uživatelem)
**Date:** 2026-05-05
**Context source:** plán fáze 2.1, metodika v0.2.1, baseline 02 (vibe-coding tools 2026)

## Kontext

Fáze 2 staví **tool**, který tým provede Pflanzerovou metodou end-to-end.
Před implementací musíme rozhodnout **form-factor**. Toto rozhodnutí ovlivňuje
tech stack, target audience, distribuci a dlouhodobou udržitelnost.

## Co tool musí umět (z metodiky v0.2.1)

| # | Capability | Zdroj v metodice |
|---|------------|------------------|
| 1 | Vést **wizard pre-flight** (Discovery Gate + 3 triage tracks + Charter) | `03-pre-session-priprava.md`, ADR-0002, ADR-0004 |
| 2 | Generovat **role catalog výběr** per projekt (decision tree z 02) | `02-role-catalog.md` |
| 3 | **Spouštět expert sub-agents** (1 per vybranou roli) v sessions | role catalog 3-režimová matice |
| 4 | **Generovat 1–3 mockupy** přes 1+ vibe-coding tool (v0/Bolt/Stitch/Cursor) | baseline 02 doporučení |
| 5 | **Prototype hub** — shareable URL bez accountu, version compare, embed | baseline 02, `05-mezi-sessions.md` |
| 6 | **Feedback collector** — scoring (severity × department × kategorie + AI Act tier + WCAG) | `05-mezi-sessions.md` |
| 7 | **Discovery Debt Detector** — AI audit briefů na assumptions vs evidence | `05-mezi-sessions.md` |
| 8 | **AI panel facilitace v Session 2** — agregace, conflict resolution návrhy | `06-session-2.md` |
| 9 | **Decision log s SSO atribucí** (DORA 7-letá retence) | role catalog cross-cutting |
| 10 | **Prompt audit pipeline** (vendor zero-retention + corporate custody) | devil's advocate Útok 8, `03` |
| 11 | **Handoff package generator** — per role artefakty | `07-handoff-do-vyvoje.md` |
| 12 | **Method-level metrics tracking** (per pilot + agregace pro Method Steward) | ADR-0007, `method-charter.md` |

## Tři varianty form-factoru

### Varianta A — Claude Code plugin

**Popis:** Sada slash-commands (`/pflanzer-charter`, `/pflanzer-session-1`, …)
+ sub-agents v `.claude/agents/` + skills + MCP servers pro vibe-coding tools.

**Plus:**
- **Rychlé na postavit** (4–6 týdnů) — využívá existující Claude Code primitiva.
- **Sub-agent infrastruktura zdarma** (capability #3 — expert panel za hodinu).
- Tightly integrated s vibe-coding workflow (Cursor / Composer / Artifacts).
- Decision log = git commit history + transcript = audit trail by default.
- Reusable kódbáze (CLAUDE.md konvence z user's globální config).

**Minus:**
- **Stakeholdeři bez Claude Code nemají přístup k prototype hubu**
  (capabilities #5, #6 — feedback collector). Chybí shareable URL bez
  CC instalace.
- Multi-tenant scénář (víc týmů ve firmě) složitější — každý CC instance per user.
- Prompt audit pipeline (capability #10) nutno řešit side-loaded SIEM
  ingestion (CC-side).
- Method-level metrics (capability #12) nemá dashboard — jen JSON report
  do gitu.

**Capability coverage:** 1, 2, 3, 4, 8, 9, 10 (částečně), 11, 12 (částečně) = **9 / 12**.

### Varianta B — Standalone web app

**Popis:** FastAPI + React + SQLite (dle CLAUDE.md preference). Multi-tenant
(orgs / projects), SSO, web UI pro Charter wizard, prototype hub, feedback
formulář, decision log. AI orchestrace přes Anthropic SDK.

**Plus:**
- **Plné capability coverage** — všech 12 kapabilit nativně.
- Stakeholdeři bez CC mají přístup přes shareable URL.
- Multi-tenant od začátku, SSO, multi-org.
- Method-level dashboard (capability #12) jako first-class feature.
- Prompt audit pipeline jako vestavěná feature (proxy AI vendor calls).

**Minus:**
- **Pomalé na postavit** (3–4 měsíce na MVP s 12 kapabilitami).
- Hosting / deploy / SSO / DPA — netriviální infra.
- Pflanzer pro tým s Claude Code = duplicitní UX (mají CC, pak ještě web).
- Vendor lock-in na anthropic SDK (nicméně OK, je to záměr).

**Capability coverage:** 12 / 12 ale s vyšším nákladem.

### Varianta C — Hybrid (Claude Code orchestrace + lightweight web prototype-hub)

**Popis:** Session orchestrace, expert sub-agents, Charter wizard, decision log
v Claude Code (capabilities 1, 2, 3, 4, 8, 9, 10, 11, 12). Lightweight web
hub (FastAPI + statický front) pro prototype hosting, version compare,
shareable URLs, feedback collector (capabilities 5, 6, 7).

CC and web hub komunikují přes simple API (CC posts mockupy + project meta;
web hub renderuje + sbírá feedback; CC pulluje feedback do session 2 syntézy).

**Plus:**
- **Best of both worlds** — CC pro orchestraci s sub-agents zdarma; web jen
  tam, kde je vyžadován shareable URL.
- Web kus je tenký (~1 měsíc práce vs 3–4 plně web app).
- Stakeholdeři bez CC dostanou jen prototype hub URL — žádný CC onboarding.
- Audit trail = CC commit history + web hub feedback log (oba SIEM-able).
- Postupný upgrade path: pokud později chceme plný web app, hub se rozšíří.

**Minus:**
- **Dva kódbáze místo jednoho.**
- API kontrakt mezi CC a hubem nutno definovat (small overhead).
- Onboarding pro tým = CC + web URL (mírně víc setup než A nebo B samotné).

**Capability coverage:** 12 / 12 s rozumným nákladem (~6–8 týdnů na MVP).

## Doporučená varianta

**Variant C — Hybrid.** Důvody:

1. **Capability coverage 12/12** s ~poloviční prací než plný web (B).
2. **Sub-agent infrastruktura zdarma** přes CC = expert panel za hodinu (4 paralelní agenti per vlna jako jsme dělali ve fázi 1).
3. **Stakeholdeři bez CC dostanou jen URL** (capability #5 — kritická pro non-tech sponzory v session feedback fázi).
4. **Postupné rozšíření** — můžeme začít CC-only s mock web hubem a postupně rozšiřovat.
5. **Soulad s CLAUDE.md preference** (Python + FastAPI + SQLite + React + Tailwind).

## Co je out of scope pro v0 MVP toolu

- Multi-tenant SSO (přidat až s reálným zákazníkem mimo author org).
- White-label customizace.
- Mobile app pro feedback (responzivní web stačí).
- Real-time collaboration v sessionu (CC IDE už to má).
- Marketplace template Charterů (bude organicky později).

## Důsledky

**Pozitivní:**
- Funkční MVP za ~6–8 týdnů.
- Vibe-coding tool integrace (capability #4) přes web hub iframe nebo MCP per stack.
- Decision log = CC `.claude/decisions/` + web hub `feedback.db` (sjednoceno reportingem).

**Negativní:**
- Dva kódbáze a kontrakt — mitigated tím, že hub je velmi tenký.
- Tým bez CC nemá orchestraci — explicitně out of scope pro v0
  (cílovka jsou týmy s CC v engineering, sponsor/stakeholder s URL-only access).

## Otevřené otázky pro fázi 2.2 (detailní plán)

- API kontrakt CC ↔ web hub: REST nebo file-based (sdílený volume / git)?
- Web hub deploy: gizmax.cz subdoména (`pflanzer.gizmax.cz`) nebo lokální
  `localhost:8000` per workshop?
- AI vendor pro orchestraci: Claude Sonnet 4 (CLAUDE.md production default)
  pro session, Haiku pro background utilities.
- Vibe-coding tool integrace: per stack volba (Bolt pro fullstack, v0 pro
  Next.js+shadcn, Stitch pro UI discovery, Cursor `/best-of-n` pro varianty
  ve worktreech) — tool brokeruje volbu skrze decision tree z baseline 02.
