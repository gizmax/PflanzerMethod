# Competitive Synthesis & Positioning — Pflanzer v0.3 (May 2026)

> Synthesis 3 paralelních expertních perspectives:
> - `01-workshop-methodology-landscape.md` (GV Sprint, IDEO, Liberating Structures, AJ&Smart)
> - `02-vibecoding-methodologies-2026.md` (AI-DLC, BMAD, Spec Kit, Cursor, Lovable, „Vibe Coding" kategorie)
> - `03-enterprise-ai-adoption-frameworks.md` (McKinsey, BCG, Accenture, Deloitte, Capgemini, SAFe, Spotify model 2024-2026)
>
> **Datum:** 2026-05-18

---

## Přímá odpověď na 3 otázky

### 1. Existuje něco takového jako Pflanzerova metoda?

**Ano — částečně.** Existuje **jeden přímý competitor** a několik **adjacent/komplementárních** metod. Žádná z nich ale **nebundluje všechny core Pflanzer prvky najednou**.

| Co existuje | Kdo | Jak se překrývá | Kde se liší |
|---|---|---|---|
| **AWS AI-DLC** (open source `awslabs/aidlc-workflows`) | AWS / Raja SP, 07/2025; re:Invent DVT214 12/2025 | ~60-70 % DNA s Pflanzer Session 1 přes ceremoniál „Mob Elaboration" (3-4h, cross-fn, AI navrhuje → mob validuje) | Jen engineering tým (BA/PM, eng, QA, ops); **žádné non-tech role**, žádné score závaznosti, žádný 2-session formát s týdenním asyncem, žádný audit trail per AI Act |
| **Thoughtworks AI/works + „3-3-3"** (Q1 2026) | Thoughtworks consulting | Direct enterprise competitor — *„90 days idea → MVP"* claim | 90 dní vs 14 dní; consulting engagement model, ne self-serve framework |
| **McKinsey „AI Operating Model"** (QuantumBlack, 2024+) | McKinsey | Top-down enterprise transformation, multi-month | Strategy-grade, $1M–$10M+ engagement; ne pilot-level fixture |
| **AJ&Smart Sprint 2.0** + Lovable/Bolt stack | AJ&Smart community | Vibe-coding v Design Sprint 5-day formátu | 5 dní vs 14 dní; žádný 2-session split, žádný audit trail |
| **Foundation Sprint** (Knapp/Zeratsky, kniha *Click* 2025) | GV alumni | **Komplement**, ne competitor — pre-Pflanzer foundation phase | Strategická foundation (2h), ne implementation cycle |
| **BMAD-METHOD** (MIT, `bmad-code-org`) | OSS community | AI personas pro 12+ rolí | Agent orchestration framework, žádní lidé v místnosti |
| **Spec Kit / Kiro / OpenSpec** (Spec-Driven Development) | GitHub, Amazon, OSS | **Komplement** — upstream/downstream interop target | Specification discipline pre/post Pflanzer cyklu |

**Bottom line:** **Pflanzer nemá vlastníka kategorie**. Sedí v mezeře mezi McKinsey transformations ($1M+, 12+ týdnů) a AWS AI-DLC / hackathon frameworks (single-shot, slabý handoff, žádné non-tech role). Tu mezeru zatím nikdo nezaplnil.

### 2. V čem se liší?

#### Pflanzer drží **5 protected USPs** (květen 2026):

| USP | Status | Důvod |
|-----|--------|--------|
| **Non-tech v místnosti od minuty 0** | ✅ Protected | Žádný direct competitor nemá Security + Legal/DPO + A11y + UX writer + CS proxy v primary session. AI-DLC = jen engineering. McKinsey = consulting workshop, ne single-session in-room. Organizational moat, ne tooling. |
| **Score závaznosti per role + AI deflation -0.5** | ✅ Protected, 12-měsíční náskok | Workshop expert independent confirmation: žádný direct competitor v 2026. AI-DLC, Sprint 2.0, IDEO neformalizují *„líbí se mi" vs „commitnu"* hranici. |
| **Pre-flight triage 4 tracks** (Discovery + Security + Legal + Platform) | ✅ Protected | Žádná konkurenční metoda nemá 48-72h async pre-read jako MUST gate. |
| **Decision log s human attribution per AI Act čl. 14** | ✅ Hardest defensible moat | Enterprise expert: out-of-the-box compliance artefakt, který McKinsey/BCG/Accenture nemají. Procurement-ready pro CRO/DPO. |
| **Decider hlasuje poslední (anti-HiPPO)** + decision protokol | ✅ Protected | Formalizace v ADR-0001 Scenario A/B/C; žádná jiná metoda nemá kanonický eskalační protokol. |

#### Pflanzer **NE-protected** USPs (2026):

| Bývalý claim | Status | Důvod |
|--------------|--------|--------|
| **„Real-time AI vibe-coding"** | ❌ Commoditizováno | Sprint 2.0 + Lovable/Bolt/v0/Cursor = 2025 mainstream. Bolt v2, Lovable 2.0, Cursor `/best-of-n` (10/2025) = produkují live URL v session. Wow-faktor se ztratil. |
| **„AI-mediovaná syntéza feedbacku v S2"** | ⚠️ Rapidly commoditizing | SessionLab + Miro AI + Mural konvergují k podobnému patternu. 12-18 měsíců window. |
| **„Funkční kód místo Figmy"** | ❌ Commoditizováno | Stejný důvod jako vibe-coding. Lovable produkuje live URL, Figma fasáda kritika je v 2026 oslabená. |

#### Kopírovatelné v 6-12 měsících:

- Multi-version A/B/C generování (Cursor `/best-of-n` má od 10/2025)
- Funkční prototyp v session (Bolt v2, v0, Lovable 2.0)
- Mob session formát (AWS push přes AI-DLC distribution channel)

### 3. V čem je naše unikátní?

**Pflanzer's hardest defensible position v květnu 2026:**

> **„Cross-functional AI pilot fixture s native AI Act compliance, kterou velcí
> poradci (McKinsey/BCG/Accenture) nemají out-of-the-box, AWS AI-DLC nemá
> stakeholder alignment vrstvu, a hackathon frameworks nemají audit trail."**

Konkrétně 3 pilíře, které **dohromady** v 2026 nikdo jiný nedělá:

#### Pilíř 1 — **Non-tech role v primary session** (organizational moat)
- Security + Legal/DPO + A11y + UX writer + CS proxy **v místnosti od minuty 0**.
- AI-DLC tomu říká *„mob"*, ale jeho mob je homogenní engineering.
- McKinsey to dělá v consulting engagement (multi-week), ne v single-session fixture.
- **Důsledek:** late-stage veto eliminované (security/legal flag risk surface na minutě 240, ne v sprintu 4).

#### Pilíř 2 — **Native AI Act / DORA compliance artefakt** (regulatorní moat)
- Decision log s human attribution per AI Act čl. 14 + dvoufázový AI Act protokol (Fáze A/B/C, ADR-0013).
- DORA-grade 7-letá retence audit logů.
- **Anti-Pflanzer external validation:** Martinelli, *„Why Spec-Driven Development Tools Fail in the Enterprise"* (2026) kritizuje Spec Kit/BMAD/Kiro za **chybějící stakeholder alignment + audit trail** — Pflanzer USPs jsou doslova jeho critique pointy.
- Enterprise expert: procurement-grade compliance — hardest moat proti commoditization.

#### Pilíř 3 — **Score závaznosti per role + anti-HiPPO Decider** (decision moat)
- Hierarchie závaznosti Critical/Yellow/Score s rationale field.
- AI-only feedback deflated max 0.5/1.0 (calibration tied to T+30/60/90 retrospective per Method Charter v0.3).
- Decider hlasuje poslední — zveřejnění score až po silent voting.
- **Důsledek:** přemostění propasti mezi *„líbí se mi"* (LDJ dot voting) a *„tohle commitnu"* (DS Decider binary). Žádná z metod ji jinak neřeší.

---

## Konflikt matrix (kde se experti rozcházejí)

### Konflikt #1 — Je „vibe-coding" stále Pflanzer differentiator?

| Expert | Pozice |
|--------|--------|
| Workshop methodology | NE — Sprint 2.0 + Lovable mainstream v 2026, wow-faktor se ztratil. |
| AI vibe-coding | NE — Karpathy mainstream definice „vibe coding" = individual practice, žádný workshop kontext. Sémantická divergence pokud Pflanzer používá „společně provibe-koduje". |
| Enterprise | NE — enterprise audience nečte vibe-coding literaturu; positioning jako „AI pilot fixture", ne „vibe-coding workshop". |

**Resolution:** Pflanzer **nesmí** pozicovat na vibe-codingu jako primary USP. Interní použití pro builder workflow OK; externí marketing pivot na **„cross-functional AI pilot fixture"** nebo **„14-day production AI cycle"**.

### Konflikt #2 — Eponymní pojmenování „Pflanzerova metoda"

| Expert | Pozice |
|--------|--------|
| Workshop methodology | (žádný komentář k naming) |
| AI vibe-coding | „Pflanzer" má germánskou váhu (sazba/pěstování) — etymologicky pasuje, ale brand recognition mimo CZ/DE je nula. |
| Enterprise | Eponym **enterprise procurement-hostile**. Žádný McKinsey produkt se nejmenuje „Smith Method". Doporučen rebrand (např. „Pflanzer Cycle", „14-Day Pilot Cycle"). |

**Resolution:** **Strategická otázka pro Toma.** Doporučení: dual-naming — *„Pflanzer Method (14-Day AI Pilot Cycle)"* pro consulting/procurement audience, „Pflanzer" pro community / developer audience. Případně **úplný rebrand v0.4 do enterprise-friendly názvu**.

### Konflikt #3 — Pozicovat proti AWS AI-DLC nebo s ním?

| Expert | Pozice |
|--------|--------|
| Workshop methodology | (zmiňuje AI-DLC pouze okrajově) |
| AI vibe-coding | **AI-DLC je direct competitor** (60-70 % DNA overlap). Certifikační program jako long-term moat proti AWS commoditization. |
| Enterprise | AWS jako **distribution channel**. AABG (Accenture Anthropic Business Group, 30 000 trained Claude Code lidí) jako single highest-leverage target. |

**Resolution:** **Oboje.** Public differentiation (non-tech inclusion, audit trail, AI Act compliance) **+** soukromá channel exploration (AWS partner program, Accenture AABG pitch). Není to either-or.

### Konflikt #4 — Co je Pflanzer pozice v enterprise stack?

| Expert | Pozice |
|--------|--------|
| Workshop methodology | „Workshop methodology" kategorie (Design Sprint successor + AI augmentation) |
| AI vibe-coding | „AI workshop methodology" kategorie (mezi solo vibe-coding a agent orchestration frameworks) |
| Enterprise | **„AI pilot fixture"** kategorie — operating-cadence layer mezi McKinsey strategy a Microsoft/AWS hackathon frameworks. *„14-day production AI cycle"*. |

**Resolution:** Enterprise framing wins. Pflanzer **není** „yet another workshop methodology" — to je hřbitov, ze kterého většina metod nevyšla. Pflanzer je **„operating-cadence layer pro AI Center of Excellence"** — opakovatelná, certifikovaná, procurement-ready fixture, kterou AI CoE Lead používá pro pilot portfolio.

---

## Klíčové strategic findings

### A) Pflanzer má **3 zdroje moat**, ne 1
1. **Organizational** (non-tech v místnosti — Security/Legal/DPO).
2. **Regulatorní** (AI Act čl. 14 native compliance, DORA-grade audit log).
3. **Decision-protocol** (score závaznosti + anti-HiPPO).

Ztráta vibe-coding USP **nezničila Pflanzer** — protože ten nikdy nebyl jediným moat. Marketing v0.2 ho ale prezentoval jako primary, což je nyní fragile.

### B) Pflanzer má **3 friction points** v 2026
1. **Naming** — eponym + „vibe coding" + collision s „AI Design Sprint" (Design Sprint Academy brand).
2. **Pricing/packaging** — enterprise audience nemá CFO-readable cost line; Pflanzer dnes je free/open metoda bez procurement template.
3. **Ecosystem integration** — Foundation Sprint, BMAD, Spec Kit, Kiro, AI Champions Network — Pflanzer s nimi nemá explicit interop / handoff path.

### C) Pflanzer má **3 distribution opportunities**
1. **AWS AABG channel** (Anthropic Accenture, 30 000 trained Claude Code lidí) — direct pitch.
2. **ICAgile partnership** (ICP-FAI / ICP-ENT track) — certified facilitator roster.
3. **CEE bank/telco reference** — e-shop case study formalize + 2-3 audit-grade reference v Q3 2026.

### D) Pflanzer má **1 external validation** (silent ally)
**Martinelli paper (2026)** kritizuje Spec-Driven Development tools za:
- Chybějící stakeholder alignment vrstvu
- Neformalizovanou eskalaci konfliktů
- Žádný audit trail per AI Act

**Tyto critique pointy jsou doslova Pflanzer USPs.** Pflanzer by měl Martinelli paper citovat ve své marketing materiálech / website jako *„independent validation of the gap Pflanzer addresses"*.

### E) Brand collision risk
- **„AI Design Sprint"** je Design Sprint Academy (DSA) brand. Pflanzer NESMÍ tento termín používat (ani v marketingu, ani v dokumentaci).
- Rychlá akce: grep pro „AI Design Sprint" v repo + website + případné externí reference, replace.

---

## Doporučení (P0-P3 priority)

### P0 — PR-blocking pro v0.4 (do 2 týdnů)

1. **Update `09-srovnani-existujici-metody.md`** — přidat AI-DLC, Thoughtworks AI/works, Foundation Sprint, McKinsey QuantumBlack entries. Workshop expert a AI vibe-coding expert oba potvrdili: AI-DLC chybí v current 09 = bug.
2. **Brand collision audit** — grep „AI Design Sprint" v celém repo + website; replace na neutral termín („AI-augmented workshop", „cross-fn AI session").
3. **Website hero/USPs rewrite** — replace „funkční kód místo Figmy" + „real-time AI vibe-coding" framing s actual protected USPs: „non-tech v místnosti", „AI Act native compliance", „decision protocol s human attribution".
4. **ADR-0015 — Vztah k AWS AI-DLC** (positioning + interop): „AI-DLC je adjacent direct competitor; Pflanzer se diferencuje non-tech inclusion + audit trail; potenciální channel partnership přes AWS partner program / AABG."

### P1 — v0.4 SHOULD (do 4 týdnů)

5. **ADR-0016 — Vibe coding terminologie** — Option C selective use (interní v builder workflow, externí marketing pivot na „AI pilot fixture").
6. **ADR-0017 — Foundation Sprint jako pre-step** — Pflanzer nenahrazuje Foundation Sprint, doporučuje ho jako optional foundation phase. Foundation Sprint → Pflanzer Charter handoff.
7. **4. diferenciátor:** Spec-kit-compatible handoff (BMAD-feedable, Kiro-feedable export). Charter `tool/templates/` přidat `handoff-spec-kit.md.template`.
8. **Strategic naming decision** — eponym vs „Pflanzer Cycle" vs „14-Day AI Pilot Cycle" (Tom rozhoduje). Resolution v ADR-0018 pokud potřeba.

### P2 — v0.5 (do 8 týdnů)

9. **Pricing tiers + MSA template** — DIY (free), Facilitátor €10-25k/cyklus, Audit-grade €40-80k, Bundle €80-150k. Procurement-ready MSA s outcome-based clauses.
10. **e-shop case study formalize** — datovaný, signed, public. Plus 2-3 CEE bank/telco audit-grade reference v Q3-Q4 2026.
11. **AABG channel pitch deck** — Accenture Anthropic Business Group direct pitch jako „AI workflow redesign methodology pro Digital Core Engagement".
12. **Martinelli paper citation** — website + README + 09-srovnani jako external validation.

### P3 — v1.0+ (do 6 měsíců)

13. **ICAgile partnership exploration** — ICP-FAI / ICP-ENT track s certified facilitator roster.
14. **AWS partner channel** — exploring whether AI-DLC team kolaboruje vs competuje.
15. **Pflanzer certification program** — long-term moat proti commoditization (AWS scaling AI-DLC distribution).

---

## Co tato research **NEZMĚNILA** (Pflanzer fundamentals stay)

- **Core 2-session formát s týdenním asyncem** — stále unique, žádný direct competitor.
- **Pre-flight triage 4 tracks** — žádný competitor nemá.
- **Hierarchie závaznosti (Critical/Yellow/Score)** — žádný competitor nemá.
- **Method Charter v0.3 audit-grade discipline** — ADR-0011/12/13/14 stack je v 2026 unikátní.
- **Default vs audit-grade profil rozlišení** — žádný competitor nemá tuto bifurkaci.
- **Decision log s human attribution per AI Act čl. 14** — žádný competitor nemá native.

---

## Reference

### Direct competitors

- AWS AI-DLC: [awslabs/aidlc-workflows](https://github.com/awslabs/aidlc-workflows) + AWS DevOps blog 31/7/2025 + re:Invent DVT214 12/2025
- Thoughtworks AI/works: [thoughtworks.com/insights/ai-works](https://www.thoughtworks.com/insights/ai-works) + 3-3-3 methodology Q1 2026
- McKinsey QuantumBlack: [mckinsey.com/quantumblack](https://www.mckinsey.com/quantumblack) + AI Operating Model 2024+
- BCG GAMMA + BCG X: [bcg.com/x](https://www.bcg.com/x) + DRI framework (Deploy/Reshape/Invent)
- Accenture Anthropic Business Group: 12/2025 launch + Microsoft Accenture Digital Core Q1 2026

### Adjacent / komplementární

- Foundation Sprint (Knapp/Zeratsky, kniha *Click* 2025)
- BMAD-METHOD: [bmad-code-org](https://github.com/bmad-code-org/BMAD-METHOD)
- Spec Kit: [github/spec-kit](https://github.com/github/spec-kit) (93k stars)
- Amazon Kiro: spec-driven development tool
- OpenSpec community
- AJ&Smart Sprint 2.0: [ajsmart.com](https://ajsmart.com)
- Lovable 2.0, Bolt v2, Cursor Composer + `/best-of-n`

### External validation

- Martinelli, *„Why Spec-Driven Development Tools Fail in the Enterprise"* (2026) — kritika Spec Kit/BMAD/Kiro za chybějící stakeholder alignment + audit trail. Tyto critique pointy = Pflanzer USPs.

### Vibe coding category

- Karpathy original tweet (Feb 2025) — individual practice definition
- Wikipedia, Collins Dictionary, IBM — vše consistent: solo developer + LLM
- Pflanzer „společně provibe-koduje" = sémantická divergence

### Per-expert deep dive

- `01-workshop-methodology-landscape.md` — full Workshop expert output (~580 ř.)
- `02-vibecoding-methodologies-2026.md` — full AI vibe-coding expert output (~590 ř.)
- `03-enterprise-ai-adoption-frameworks.md` — full Enterprise expert output (~530 ř.)
