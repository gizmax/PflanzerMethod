# 06 — UX / Designer perspektiva na Pflanzerovu metodu

## Kdo jsem

Senior UX Designer / Design Lead v korporátu, 12+ let praxe (Adobe → in-house → agency → in-house). Posedlost: jasné mentální modely, výzkumem ověřené persony, JTBD framing, accessibility jako default ne addon. Denní bolesti: design system drift, spor o ownership persony s PM, "Figma vs kód jako source of truth", a teď i vibe-coding tooly, které generují krásnou kosmetiku přes špatný flow.

## 1. Posouzení (pomáhá / chybí / ohrožuje)

**Pomáhá.** PM řeší přesně to, co mě na Design Sprintu štve — Figma fasáda, kterou pak vývoj rozbije. Funkční mockup s programátorem v místnosti = handoff bez retranslace. "Together alone" princip a silent ideation z LDJ jsou pro UX zlato (HiPPO mě v korporátu zabíjí). Score závaznosti per oddělení konečně řeší, že "líbí se mi" není commitment. AI proxy pro user research je elegantní úhybný manévr, kde reálná persona není po ruce.

**Chybí.** (a) **Persona ownership** není nikde definovaný — kdo přinese personu do session 1? PM ji typicky vlastní, ale UX má research insight. Bez tohohle vznikne "persona-by-committee" během dne, což je kosmetická fikce. (b) **JTBD framing** úplně absentuje — bez něj AI generuje řešení na vágní problém ("dashboard pro manažery") místo na job ("when I prep for board meeting, I want to spot anomalies, so I avoid surprise"). (c) **Design system jako vstup** chybí v původním popisu úplně. (d) **Accessibility checklist** není v Session 1 inputs, jen jako volitelná role 11 — to je v EU 2026 (EAA platí) malus. (e) **Flow integrity** napříč variantami: 3 mockupy mohou řešit 3 různé jobs — a nikdo to nezkontroluje. (f) **Source of truth po session 2** — vibe-coded artefakt nebo Figma file? Bez rozhodnutí vznikne drift.

**Ohrožuje.** AI vygeneruje přesvědčivé UI nad nejasnou personou a tým ho potvrdí, protože "vypadá hezky". Rapid prototyping bez research guardrails = design theatre s lepší produkční hodnotou. Druhé riziko: Frontend lead u stolu povede UI rozhodnutí přes implementační pohodlí (shadcn defaults), ne přes user need. Třetí: skóre závaznosti odměňuje hlasité role (security, eng) a podhodnocuje "měkká" UX rizika, která se projeví až v produkci.

## 2. Must-have vstupy do Session 1

Bez těchto artefaktů Session 1 odkládám:

1. **Persona doc (1–3 primárních)** — JTBD věta, top 3 frustrace, kontext použití, accessibility needs. Vlastník: PM, contributor: UX.
2. **Current-state journey map** s pain points (pokud brownfield) nebo **assumption journey** (greenfield) s explicitními hypotézami.
3. **Design tokens manifest** (colors, type scale, spacing, radii, motion) export z design systému + link na živou komponentní knihovnu (Storybook nebo Figma library URL).
4. **Component inventory** — co reusneme (Button v3, DataTable v2…) a co je legitimně nové.
5. **Accessibility minimum** — WCAG 2.2 AA checklist filtrovaný na komponenty, kterých se to týká (kontrast, focus order, keyboard, ARIA roles, target size).
6. **JTBD card** pro řešený scope — `Když [situace], chci [motivace], abych [outcome]`.
7. **Brand guideline excerpt** — voice & tone, do/don't pro ilustrace a microcopy.
8. **Existing analytics** — top 5 events relevantních pro flow + drop-off místa (od Data role, pokud je u stolu).

## 3. Must-have výstupy

Ze Session 1: (a) **3 anotované mockupy** s explicitním mapováním na JTBD card a personu, (b) **flow diagram** každé varianty (ne jen screen), (c) **list odchylek od design systému** s důvodem (každá odchylka má vlastníka rozhodnutí), (d) **accessibility self-check** per varianta — quick pass/fail na 8 položek, (e) **otevřené UX otázky** pro mezi-session prototyp.

Z mezi-session fáze: **scored feedback agregovaný per varianta i per role** s rozdělením na *task success* (testovatelné) vs *preference* (subjektivní). Bez tohoto rozlišení se míchá jablka s hruškami.

Po Session 2: **rozhodnutí o source of truth** (Figma file ↔ kódový repo se vztahem who-leads-whom), **handoff package** (final mockup + tokens diff + new components RFC + accessibility annotations + microcopy final).

## 4. Edge cases

1. **AI vygeneruje variantu, která porušuje design system, ale "vypadá lépe".** Tým ji preferuje. Bez gate vznikne drift. Mitigace: pravidlo "deviation only with named owner + ticket do DS backlogu".
2. **Persona se během dne posune.** Zadavatel řekne v 10:00 "primárně pro power usery", v 15:00 "vlastně i pro nováčky". Mitigace: persona lock po prvních 60 min, změna jen explicit re-vote.
3. **Accessibility expert chybí, AI proxy ho zastoupí, prototyp projde.** V produkci spadne audit. Mitigace: pre-launch human review nepodmíněně, AI proxy ne pro final sign-off.
4. **Flow integrity collapse** — 3 varianty řeší 3 různé jobs. Tým hlasuje "best of each" a vznikne Frankenstein. Mitigace: každá varianta MUSÍ adresovat stejnou JTBD card; rozhodnutí na úrovni flow, ne komponent.
5. **Microcopy as afterthought** — AI doplní lorem ipsum nebo "Submit". Mitigace: copywriting/UX writer slot v Session 1 last hour, nebo content design checklist v inputs.

## 5. Vylepšení

1. **Přidej UX writera / content designera** jako trigger-volitelnou roli #16 (trigger: user-facing copy, error states, empty states). Microcopy je 30 % UX a v PM zatím nikde.
2. **JTBD warm-up** prvních 30 min Session 1 — facilitátor + AI vygenerují 3 JTBD karty, tým vybere jednu. To ukotví scope a brání persona drift.
3. **Design system gate v in-session toolu** — vibe-coding tool (Bolt/Lovable) musí dostat design tokens jako MCP context; každá deviation se loguje. Implementace: generovat `tokens.json` z DS a injektovat ho jako system prompt.
4. **Dual-track artefakt po session 2** — Figma file zůstává *source of truth pro design rationale a anotace* (persona, JTBD, accessibility notes), kódový repo *source of truth pro implementaci*. Vztah: Figma odkazuje na commit hash, kód odkazuje na Figma node ID. Žádný "Figma vs kód" konflikt, jen jasné vrstvy.
5. **Accessibility 8-point quickscan** povinný před koncem Session 1: kontrast, focus visible, keyboard nav, target size 24px+, alt text strategy, error identification, heading order, motion-reduce respect. AI tool to umí ověřit nad živým mockupem za 2 min.

## 6. Konflikty

- **PM vs UX o persona ownership.** Pflanzer to nezná — defaultně to PM "ukradne". Návrh: persona je *shared artefakt*, PM ji prioritizuje, UX ji validuje researchem; v PM kontextu vyžadovat **podpis obou** na persona doc před session.
- **Frontend lead vs UX o komponentní rozhodnutí.** FE tlačí na shadcn default, UX na DS variantu. Bez explicit DS authority v místnosti vyhraje rychlost. Návrh: design system steward (může být UX nebo dedicated) má **veto na nové komponenty**, podobně jako security na critical risk.
- **Eng manager kapacita vs UX kvalita.** "Tahle varianta je 2× delší, vezmeme tu jednodušší." Skóre závaznosti to neřeší, protože UX nemá vetovací sloupec. Návrh: UX dostává *yellow flag* (ne veto, ale viditelný warning v rozhodovací matici) pro varianty s known usability debt.

## Memorabilia

> **"Vibe-coding bez persony je krásná chyba v rekordním čase."**
>
> AI generátor je výtah pro design system, ne náhrada researche. Pflanzer dává UX šanci přestat být gatekeeper a stát se editorem v reálném čase — pod podmínkou, že persona, JTBD a accessibility přijdou do místnosti **dřív než první mockup**, ne po něm.
