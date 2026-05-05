# 03 — Korporátní change-mgmt & cross-functional facilitation

Rešerše baseline pro Pflanzerovu metodu: jak v korporátu reálně dostat 6–10 lidí z různých oddělení do jedné místnosti na vibe-coding session a jak metodu zavést, aniž by ji vytlačily existující procesy. Datum: 2026-05-05.

---

## Cross-functional discovery

**Atlassian Team Playbook** je nejhutnější veřejná knihovna „plays“ pro cross-functional týmy. Relevantní pro Pflanzera:
- **Inception / Kick-off** — sjednocení cílů, scope, in/out, rizik.
- **Pre-Mortem** — tým si představí, že projekt selhal, a brainstormuje proč; výstup = top rizika s ownerem. Atlassian doporučuje pouštět ji i v polovině projektu, ne jen na startu.
- **Cross-Functional Product Team** play — strukturovaný posun z „pohledu vlastní role“ (dev, tester, designer) do pohledu zákazníka. Přesně to, co Pflanzer potřebuje udělat v prvních 60–90 min.

**GV Design Sprint (5 dní)** je nejbližší veřejný precedent — 5–7 lidí z různých rolí, jedna místnost, Map → Sketch → Decide → Prototype → Test. Používali Google, Uber, Slack, NYT, Dropbox. Klíčový rozdíl: Sprint končí fasádovým prototypem pro user test. Pflanzer s vibe-codingem (Cursor / Claude Code) může den 4 posunout od fasády k reálně běžícímu kódu.

**Marty Cagan — Inspired → Empowered → Transformed (2024)** definuje Product Operating Model: empowered teams dostávají problémy, ne featury; outcomes nad output; principles over process; trust over control. Hlavní bariéra adopce = **trust**: exekutiva se musí vzdát kontroly. Pro Pflanzera: workshop má smysl jen tam, kde stakeholder akceptuje, že výstup je „bet on the team“, ne „delivery na podpis“.

**Teresa Torres — Continuous Discovery + Opportunity Solution Tree (OST)**: discovery jako weekly rhythm, ne jednorázová událost. OST mapuje desired outcome → opportunities → solutions → experiments. V Pflanzeru použitelné jako warm-up artefakt: OST naplněný v prvních 60 min ukotví problém a omezí scope-creep během dne.

**Spotify model (Squads/Tribes/Chapters/Guilds)** je nejkopírovanější a nejvíc nepochopený model dekády. Autoři (Kniberg, Ivarsson) opakovaně říkají, že šlo o snapshot Spotify z r. 2012, ne blueprint. Kritika 2024–2025: **20 % struktura, 80 % kultura**; tribes přerostly 150-osobní limit a staly se silami; guildy ztratily efektivitu (kdo je nejvíc potřeboval, neměl čas). Modernější alternativa = **Team Topologies** (Skelton/Pais) se 4 typy týmů a kognitivní zátěží jako designovým principem.

**ING agile transformation** je nejcitovanější CEE/EU bankovní case: ~350 squadů × 9 lidí ve 13 tribes, co-located. Výsledky (McKinsey/ING): NPS Business Platform z -30 na +30 za rok, cykly z 18 měsíců na 3–6 (malé projekty 4–6 týdnů), engagement až 93 %, NL net result +54 % (2017 vs. 2015). Klíčové: **co-locace zlepšila komunikaci od prvního dne** — Pflanzer to institucionalizuje na úrovni dne, ne reorganizace.

---

## Change-mgmt modely

**Kotter 8-step (1996, rev. 2014)** — Urgency → Guiding coalition → Vision → Communicate → Empower → Short-term wins → Consolidate → Anchor. Kritika 2024: žádná empirická validace; top-down, omezuje participaci; lineární, předpokládá one-time event (Kotter 2014 přiznal paralelní běh kroků); ignoruje emoce a change-fatigue; první krok („urgency“) má status-quo bias a může derailovat (Tandfonline 2022). Pro Pflanzera: použitelné jako rétorický rámec pro sponzora („quick wins = krok 6“), ne jako návod k zavádění.

**ADKAR (Prosci)** — Awareness → Desire → Knowledge → Ability → Reinforcement. Individual-level model: organizace se nezmění bez změny jednotlivců. Doplněno PCT trojúhelníkem (success / sponsorship / project mgmt / change mgmt) a 3-fázovým procesem (Prepare → Manage → Sustain). Adoptováno v Microsoftu, Avnetu, Colorado govt. Pro Pflanzera nejpřímější fit — workshop = „A+D+K“ v jednom dni; **reinforcement (R) se typicky podcení** a tím adopce zhasne.

**Toyota Kata (Mike Rother)** — Improvement Kata + Coaching Kata. Mini-experimenty (PDCA), coach klade otázky a nedává odpovědi, učí „myslet jako vědec“. Pro Pflanzera silný framing: vibe-coding den = jeden experiment Improvement Kata; facilitátor = coach kata; výstup není „dodávka“ ale „learning + next experiment“. Snižuje politický tlak na úspěch.

**Innersource / Champion model** — adopce přes interní champions šířící praxi ne-direktivně (Capital One, SAP, FINOS). Princip: paralelně **top-down structuring** (program office, standardy) + **bottom-up voluntary collaboration**. Pro Pflanzera nejrealističtější vzorec: 2–3 champions v různých BUs, každý spustí pilot, learnings se sdílejí v internal CoP.

---

## Korporátní omezení (EU/CEE)

**Security gating před prototypem.** V regulovaných sektorech (banky, pojišťovny, telco) bývá architecture/security review checkpoint **před** psaním kódu. Workshop stojí a padá s typem dat:
- **synthetic / dummy data** → většinou stačí lehký review po workshopu;
- **anonymizovaný snapshot prod dat** → DPIA per GDPR čl. 35 + legal sign-off;
- **live prod systém** → plný security review, pen test, threat model — sem workshop nepatří.

Pravidlo: **prototype-only data + sandbox + throwaway DB** zruší 80 % security gates ex-ante. Definovat v charteru.

**GDPR + DORA + NIS2.** DORA platí od 17. 1. 2025 pro finanční entity v EU: ICT risk mgmt s board accountability, incident reporting do 4 h, TLPT každé 3 roky pro významné entity, registr ICT third-party providerů (first submission 30. 4. 2025), pokuty až 2 % global turnover. NIS2 (transpozice 10/2024) rozšiřuje cyber povinnosti na essential + important entities. GDPR řeší data, NIS2/DORA resilience — překryv v incident response a third-party riziku. Pokud výstup workshopu zůstane v sandboxu a neměnní production, žádný z režimů se dne přímo netýká. Triggery (production API, real PII, deploy do prod) musí být **explicitně out-of-scope** v charteru.

**SAFe PI Planning.** V CEE bankách běžné. Rytmus 8–12 týdnů s **Innovation & Planning (IP) iterací** na konci, která explicitně obsahuje hackathons, výzkum, technical spikes, učení. Pflanzer je ideální fit do IP iterace — neporušuje sprint commitment, využívá „structured window for free investigation“. Sponzor argumentuje SAFe definicí IP iterace, ne tlakem nového procesu vedle.

**Legal/compliance bez kapacity.** Realistický pattern: legal/compliance člověk na celý den nepřijde. Mitigace:
- **async pre-review** charteru 2–3 dny předem (10 min jejich času);
- **on-call slot** uprostřed dne (30–45 min) pro 1–2 otázky;
- **post-workshop sign-off** prototypu před jakýmkoliv krokem ven ze sandboxu;
- **delegovaný přítomný** (junior z compliance se senior sponsorshipem) — zaplní seat, eskaluje.

---

## AI-facilitation tools

**Miro AI Sidekicks & Flows (2025)** — konverzační agenti na canvasu, čtou sticky notes, diagramy, dokumenty. Personas (beta léto 2025): Challenger, Synthesizer, Optimist, Historian. Praktická hodnota: cluster + theme-naming sticky notes během sekund (úspora 15–30 min facilitace), Agile Coach Sidekick navrhuje akce z retro.

**Mural AI** — facilitator-first, silnější template knihovna a guided facilitation. Vhodné pro workshopy s předem definovaným flow.

**Otter.ai / Read.ai** — meeting transcription + summaries + action items. V korporátu schválení nutné (data residency, recording disclosure per GDPR čl. 13). Hodnota: facilitátor nepíše zápis, je 100 % v místnosti; po workshopu auto-decision log.

**Použití v Pflanzeru:** (1) **Prep** — Sidekick sumarizuje problem space z materiálů, tým startuje 30 min napřed. (2) **Run** — Otter/Read zachytí decisions + rationale. (3) **Post** — Miro AI clustruje výstupy, generuje draft retro a follow-up. Pozor: AI summaries v regulovaných doménách potřebují review člověkem před distribucí (halucinace + compliance log).

---

## Implikace pro Pflanzera

1. **Pozicovat metodu jako „IP iteration play“, ne nový proces.** V SAFe korporátech tím obejdeš odpor („další framework nepotřebujeme“). Mimo SAFe pozicovat jako Atlassian Play / GV Design Sprint variantu — známé referenční rámce, žádné nové buzzwordy.

2. **Charter s pevnými security rails.** Default scope = synthetic data + sandbox + throwaway artifact. To zruší většinu DORA/GDPR/NIS2 friction ex-ante. Cokoliv mimo scope (live data, prod API) explicitně out-of-scope a vyžaduje samostatný security review track. Charter podepisuje sponzor + security delegát před workshopem.

3. **Champion model + Coaching Kata, ne Kotter top-down.** Pflanzera nezavádět direktivně. 2–3 dobrovolní champions napříč BUs, každý udělá 1 pilot, učí se z něj (Improvement Kata: target → obstacle → next experiment). Sdílení v internal CoP měsíčně. Po 3–4 pilotech vznikne playbook — pak teprve scale.

4. **Async-friendly stakeholder model pro legal/compliance.** Nepředpokládat fyzickou přítomnost po celý den. Pre-read (10 min), on-call slot (30–45 min uprostřed), post-workshop sign-off. Delegovaný přítomný z compliance teamu. To je nejčastější reálný blocker — vyřeš ho v designu metody, ne ad hoc.

5. **AI-facilitation stack jako default, ne nadstavba.** Miro AI + Otter/Read od první session. Facilitátor je v místnosti pro lidi, ne pro zápis. Output dne = funkční prototyp + AI-generated decision log + action items, vše do 30 min po skončení. To je rozdíl mezi „hezký den“ a „artefakt, který přežije pondělí“.

---

## Zdroje

- Atlassian — Cross-Functional Product Team play: https://www.atlassian.com/team-playbook/examples/cross-functional-product-team
- Atlassian — Pre-Mortem play: https://www.atlassian.com/team-playbook/plays/pre-mortem
- GV — The Design Sprint: https://www.gv.com/sprint/
- SVPG (Marty Cagan) — Empowered Product Teams: https://www.svpg.com/empowered-product-teams/
- Teresa Torres — Opportunity Solution Trees: https://www.producttalk.org/opportunity-solution-trees/
- SI Labs — Spotify Model critique: https://www.si-labs.com/en/articles/spotify-model/
- McKinsey — ING agile transformation: https://www.mckinsey.com/industries/financial-services/our-insights/ings-agile-transformation
- Tandfonline — Kotter critique (status quo bias): https://www.tandfonline.com/doi/full/10.1080/14697017.2022.2137835
- Whatfix — Kotter 8-step advantages & disadvantages: https://whatfix.com/blog/kotters-8-step-change-model/
- Prosci — ADKAR Model: https://www.prosci.com/methodology/adkar
- NIST — Toyota Kata continuous improvement: https://www.nist.gov/mep/toyota-kata-helps-create-continuous-improvement-mindset
- Capital One — Innersourcing for Enterprise Applications: https://www.capitalone.com/tech/open-source/innersourcing-enterprise-applications/
- Mayer Brown — DORA takes effect (2025): https://www.mayerbrown.com/en/insights/publications/2025/01/cybersecurity-in-the-financial-sector-eus-digital-operational-resilience-act-takes-effect
- Conformance — NIS2 + GDPR overlaps: https://www.conformance.dk/understanding-nis2-and-its-overlaps-with-gdpr-a-practical-guide/
- Scaled Agile Framework — Innovation and Planning Iteration: https://framework.scaledagile.com/innovation-and-planning-iteration
- Voltage Control — AI Teaming on Miro Canvas: https://voltagecontrol.com/blog/ai-teaming-comes-alive-on-the-miro-canvas/
- Miro — AI Workshop guide: https://miro.com/ai/ai-workshop/
