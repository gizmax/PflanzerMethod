# Perspektiva: Data / Analytics

## Kdo jsem
Senior Data / Analytics Engineer + Product Analyst v korporátu, 10+ let. Vlastním event taxonomy (Snowplow + Segment), Amplitude/Mixpanel pro produktovou analytiku, Looker semantic layer, A/B testing platformu (interní wrapper nad Statsig). Denní bolesti: feature shipne v pátek bez instrumentace, v pondělí PM ptá „kolik lidí to použilo"; A/B test bez sufficient power → běží 6 týdnů, výsledek „inconclusive"; exec dashboard plný vanity metrik (DAU bez kontextu retentionu); a věčně dohledávám eventy, které měly vzniknout v sprintu N-3.

## 1. Posouzení metody z mé role

**Co mi pomáhá**
- Cross-functional místnost = poprvé jsem v Session 1, ne až post-launch při „proč to neměříme". Instrumentation se navrhne s kódem, ne proti němu.
- Klikací prototyp mezi sessions je ideální moment pro **draft event schema** — view už existuje, hooks vidím v kódu, jméno eventu vznikne dřív než jméno tlačítka v Jiře.
- Score závaznosti per oddělení = strukturovaný dataset. Můžu trackovat decision quality napříč projekty (které varianty s nízkým score nakonec uspěly / selhaly → kalibrace metody).
- Mockup → reálný kód znamená, že telemetry SDK lze zaintegrovat už v session, ne jako P2 ticket pro Q+1.

**Co mi chybí**
- **Žádný measurement plan jako povinný výstup.** Metoda končí prototypem a handoffem; success metric se nikde explicitně nedefinuje. Bez něj je celá metoda alignment bez learning loopu.
- **Žádná A/B test design fáze.** Pokud je výstupem produkční fíčura, musí mít test plan (hypotéza, MDE, sample size, primary + guardrail metrika). Pflanzer to neřeší, takže shipne jako big-bang launch.
- **Event taxonomy není vstupem.** Frontend/backend lead nese stack a conventions, ale tracking schema chybí v seznamu vstupů Session 1 → eventy vzniknou ad hoc, naming inconsistent, breaks downstream dashboards.
- **„Score závaznosti" je samo metrikou bez definice.** Co je škála? 1–5? Likert? NPS-style? Bez consistency mezi projekty nelze srovnávat ani retrospektivně analyzovat.

**Co mě v ní ohrožuje**
- Speed-bias workshopu shipne fíčuru rychle, ale bez instrumentation deadline → analytics debt narůstá, dashboardy lžou, exec ztratí důvěru v data team.
- AI-led syntéza Session 2 může produkovat „insighty", které jsou statisticky neprůkazné (n=8 stakeholderů ≠ signál o uživatelích) a stakeholdeři je odeberou jako evidence.

## 2. Must-have vstupy do Session 1

1. **Existující event taxonomy + naming convention dokument.** Bez toho nové eventy duplikují / kolidují s existujícími. Ideálně export z Avo / Iteratively / interního schema registry.
2. **Baseline metriky pro affected flow** — current funnel, conversion rates, drop-off body. Definuje, co se musí *zlepšit*, ne jen *změřit*.
3. **Hypotéza v XYZ + measurable form**: „Po změně X vzroste metrika M z baseline B na target T během N dní u segmentu S." Falsifikovatelná, ne „bude to lepší".
4. **Power analysis pre-read**: orientační traffic do flow / týden + minimal detectable effect (MDE), který sponzor považuje za smysluplný. Bez toho se A/B test nedá designovat.
5. **Privacy classification dat**, která flow generuje (PII / pseudonymized / anonymous). Triggeruje Legal a definuje, co lze trackovat v EU bez consent banneru.
6. **Existující dashboard / KPI strom**, do kterého výstup spadne. Pokud nikam nespadá, je to red flag (orphan metrika).

## 3. Must-have výstupy ze Session 1 a 2

**Po Session 1:**
- **Measurement plan v1** (1 strana): primary metric (lagging), 2–3 leading indicators, guardrail metriky (latency, error rate, churn proxy), instrumentation deadline = ship date minus 2 dny.
- **Event schema draft**: 5–15 eventů v `object_action` formátu s properties a typy (viz §5).
- **A/B test design skica**: control vs treatment, randomization unit (user/session), expected runtime ze sample size kalkulace.

**Po Session 2:**
- **Schválené event schema** registered v schema registry (Avo / Snowplow Iglu) → blokuje merge bez přidání eventů.
- **Dashboard mockup link** (Looker/Amplitude) — alespoň drátěnka, kde žije primary + leading metrics.
- **Learning agenda**: jaké otázky chceme po launchi zodpovědět, deadline pro readout (T+30, T+60, T+90).
- **Kill criteria**: kdy to vypneme. „Pokud po 14 dnech v 95 % CI nevidíme uplift > MDE, treatment killujeme."

## 4. Edge cases a rizika

1. **Low traffic feature** — flow má < 1000 users / týden, A/B test by trval měsíce. Mitigace: pre-post quasi-experiment, switchback design, nebo synthetic control. Rozhodne se v Session 1, ne později.
2. **Multi-touch attribution mess** — fíčura ovlivňuje metriku, která je downstream několika dalších změn (concurrent A/B tests). Mitigace: koordinace s experimentation platform ownerem před session, MMM pre-read.
3. **Vanity metric capture** — sponzor chce trackovat „engagement" (= scroll depth × session time), což nekoreluje s business outcome. Mitigace: PM + Analytics interlock — PM definuje OKR (lagging), já definuji measurable proxy (leading), oba podepíšeme.
4. **GDPR/consent gap** — eventy navržené v session vyžadují consent, který flow nemá. V EU = silent telemetry death. Mitigace: Legal pre-read, server-side tracking pro essential eventy, client-side jen s consent.
5. **Schema drift mezi prototypem a produkcí** — eventy v Bolt/Lovable mockupu používají demo namespace, na produkci jiný. Mitigace: dual-environment schema, prefix `proto_` v session, mapping table do prod schema při handoffu.
6. **Power < 80 %** — sponzor tlačí na rychlý launch, ale traffic neumožňuje detekovat realistic effect. Mitigace: explicitně v measurement plan napsat statistical power; pokud pod 80 %, není to A/B test ale shadow launch s observation.

## 5. Konkrétní vylepšení metody

**1. Event taxonomy template (povinný artefakt Session 1):**
```
Event name: object_action (snake_case, past tense pro state change)
  Examples: checkout_started, plan_upgraded, prototype_voted
Properties:
  - user_id (string, hashed)
  - session_id (uuid)
  - source (enum: web|ios|android|api)
  - feature_flag_variant (enum: control|treatment_a|treatment_b)
  - timestamp_client (iso8601)
  - context_* (any feature-specific)
Naming rules:
  - žádné mezery, žádné UPPERCASE, žádné CZ diakritika
  - max 40 znaků, verb v past tense
  - PII NIKDY v event name nebo property key
GA4 fallback: snake_case max 40 chars, max 25 params, reserved name check
```

**2. Leading vs lagging metric powinnost:**
- Lagging (business outcome): revenue uplift, retention D30, NPS delta. Měřitelné T+30 až T+90.
- Leading (proxy v session 1): completion rate flow, time-to-first-value, activation event count / user. Měřitelné T+7.
- **Pravidlo: každý lagging má alespoň 1 leading. Bez leadingu je metoda blind 60 dní.**

**3. A/B test sizing rule of thumb (formula card v session):**
```
n per variant ≈ 16 × σ² / Δ²   (continuous, alpha=0.05, power=0.80)
n per variant ≈ 16 × p(1-p) / Δ² (binary conversion)
Runtime = (2 × n) / (weekly_traffic × allocation_ratio)
```
Kalkulačka jako Miro embed; pokud runtime > 4 týdny → red flag, redesign experiment.

**4. Instrumentation deadline = ship date minus 2 dny.** Tvrdé pravidlo. Bez merge-blokujícího schema check eventy nikdy nevzniknou včas. Implementace: pre-commit hook na schema registry diff.

**5. Interlock s PM (formalizovaný):**
| PM definuje | Já definuji |
|---|---|
| OKR / Outcome („zvýšit retention o 5 %") | Measurable proxy + event („D7 retention computed from `session_started` event, cohort = `signup_completed` users") |
| Persona / segment | Audience definition v query layeru („`country IN (CZ,SK) AND plan = paid`") |
| Hypotéza („nový onboarding pomůže") | Falsifikovatelný test design (H0, H1, MDE, runtime, kill criteria) |
| Acceptance criteria | Validation queries — SQL, který běží v CI a fall každý PR, který schema rozbije |

**6. Score závaznosti = standardizovaná škála 1–5** s rationale field. Uložit do interní DB → po 10 projektech máme dataset pro learning loop (které role chronicky underscore-ují, kalibrace facilitátora).

## 6. Konflikty s ostatními rolemi

- **PM (#2):** klasický „outcome vs output" konflikt. PM chce ship, já chci měřitelný ship. Řešení: měření jako součást Definition of Done, ne jako P2 ticket.
- **Engineering / Backend (#5):** eventy = další kód, latency, schema migrations. Řešení: schema-first, generated SDK, ne hand-rolled tracking.
- **Security / Legal (#7, #10):** PII v eventech = veto. Řešení: hashing + pseudonymizace v session designu, ne ex post.
- **Zadavatel (#1):** chce „dashboard zítra", neuznává consent / sample size. Řešení: tvrdé pravidlo „bez measurement plan není ship", podepsáno v charteru.
- **UX (#6):** chce qualitative insighty (5 user interviews), já kvantitativní signál. Komplementární, ne konfliktní — qual pro „proč", quant pro „jestli".

## Memorabilia
Feature without measurement = feature without learning. Pflanzer bez instrumentation deadline a measurement plan vyrobí nejlépe sladěnou black box organizaci v korporátu — všichni se shodli, nikdo neví, jestli to funguje.
