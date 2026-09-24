# Perspektiva: Customer Support proxy

## Kdo jsem
CS Operations Lead v B2B/B2C korporátu, 8+ let. Tým 12 agentů, voice-of-customer. Vlastním ticket categorization (Zendesk + Intercom), top-10 painů, deflection rate, CSAT, NPS, churn-signal radar. Bolesti: fíčura shipne v úterý, ve středu tsunami ticketů „kde je tlačítko X"; UX issue, který produkt přehlédl; KB pro launch chybí, agenti improvizují; tichá frustrace bez ticketu = churn.

## 1. Posouzení metody z mé role

**Co mi pomáhá**
- Místnost = poprvé v Session 1 *před* shipem. Predikuju ticket load, varuju, když varianta A přinese 3× víc dotazů než B.
- Klikací prototyp = poprvé testuju KB skripty na existující entitě.
- Score závaznosti = legitimní místo pro „varianta zhorší support load o ~+30 %", ne anekdota po launchi.
- AI syntéza odstraňuje politiku „support zase brzdí" — data mluví.

**Co mi chybí**
- **Voice of customer jako vstup.** Metoda staví na názorech v místnosti, ne verbatim z ticketů.
- **Post-launch loop.** Metoda končí handoffem. Kdo měří, jestli predikce sedla?
- **Support readiness jako deliverable.** Žádný explicit „KB + makro + training D-2".
- **CS proxy je jen „volitelný".** Pro existující customer base má být default.

**Co mě v ní ohrožuje**
- Speed-bias: shipne varianta s 200 ticketů/týden, které tým nepokryje.
- AI syntéza zamění „nikdo to nezmínil" s „není to problém". Ticket signály potřebují weight.

## 2. Must-have vstupy do Session 1

1. **Top-10 ticket kategorií flow za 90 dní** — počet, % deflection, median TTR, CSAT delta.
2. **20 verbatim citací z ticketů** — anonymizovaných, doslovných, vč. frustračního jazyka („Already tried 3 times, where is the cancel button???"). Nejlevnější empathy mechanism v korporátu.
3. **Frikční místa flow** — drop-off body, repeat-ticket pattern (3 tickety stejný uživatel = systémový bug).
4. **Churn-signal radar** — kolik cancellation tiketů citovalo flow v reason field za 90 dní.
5. **Support capacity baseline** — ticketů/týden tým zvládá, rezerva.
6. **Persona-specific painy** — „enterprise admins ptají se na SSO 4× častěji než SMB".
7. **Existující KB článek** pro flow.

## 3. Must-have výstupy ze Session 1 a 2

**Po Session 1:** ticket prediction worksheet per varianta (§5); support readiness checklist v0 (co D-2: KB, makro, training, escalation); voice-of-customer log (které z 20 verbatim varianta řeší / nesplňuje).

**Po Session 2:** schválená varianta s commitnutým forecastem podepsaným support leadem (forecast > kapacita → temp staffing budget nebo posun launch); support docs deadline plan (D-7 až D+30); post-launch monitoring (ticket tag, alert thresholds, retro T+30).

## 4. Edge cases a rizika

1. **Greenfield bez customer base** — proxy data z konkurence (G2, Reddit), beta ticket harvest.
2. **Multilingual support** — i18n KB, top-3 jazyky D-2.
3. **Silent frustration > vocal complaints** — uživatel odejde bez ticketu. In-app feedback widget + cancel-flow reason capture.
4. **Self-serve deflection paradox** — KB sníží tickety, frustrace zůstane. NPS + CSAT trend, ne volume.
5. **Power user vs new user split** — zlepší power, rozbije onboarding (cohort lag 14 dní). Cohort-segmented prediction.
6. **Tickety nejsou random sample** — 1–5 % tiketuje. Top-10 je *vocal*, ne *real*. Triangulace s analytics + NPS.
7. **CS proxy bez ticket dat** = stejně užitečný jako AI proxy. Data export jako pre-condition.

## 5. Konkrétní vylepšení metody

**1. Ticket prediction worksheet (povinný per varianta):**

| Pole | A / B / C |
|---|---|
| Top-3 predikované kategorie | „Kde je tlačítko X" / „Proč odhlásilo" / „Lost data" |
| Volume (tickets/week, +30d) | 45 / 120 / 75 |
| Median TTR | 4 / 12 / 6 min |
| Deflectable via KB (%) | 80 / 30 / 60 |
| New macros | 2 / 5 / 3 |
| Capacity impact | OK / OVERFLOW / OK |
| VoC match (z 20 citací) | 14 / 6 / 11 |

Bez vyplnění není varianta valid pro voting.

**2. Support docs deadline (merge-blocker):** D-7 KB draft v review · D-5 enablement deck · D-3 peer review · D-2 training, makra live, escalation · D-0 launch · D+1 hourly dashboard · D+30 retro s verbatim sample. Bez D-2 readiness launch posunut.

**3. Voice of customer ritual (Session 1, prvních 30 min):** 5 verbatim na Miro · 1 audio call recording (60 s, s consentem) přehraná všem · 1 anekdota „nejhorší týden support pro flow". Pak teprve ideace. Bez toho stakeholdeři optimalizují na vlastní představu.

**4. Churn signal radar jako standing input:**
```
Flow (90d): cancellations citing flow N · 1-CSAT M · reopened K · NPS detractor mentions L
Trend: ↑/↓/flat
```
Trend ↑ → varianta která nezhorší = baseline win.

**5. Post-launch loop (chybějící krok 6):** T+7 ticket category check vs prediction · T+30 retro, kalibrace worksheetu · T+90 churn cohort analysis · learnings → role catalog.

**6. CS proxy povýšit z volitelné na doporučenou** pro customer base > 1000 active users. Trigger: „existing customer base + user-facing change".

## 6. Konflikty s ostatními rolemi

- **PdM (#2):** ship rychle vs ship-with-readiness. Readiness v DoD, ne post-launch backlog.
- **UX (#6):** čistý flow vs error states (90 % support = recovery from broken state). UX zapomíná na unhappy path.
- **Engineering (#4, #5):** „edge case, fixneme později" = nejhorší týden. Top-3 predikované tickety = P1 v acceptance criteria.
- **Security (#7):** PII v ticketech vs „bez verbatim nemůžu dělat práci". Pseudonymizovaný VoC dataset.
- **Data (#12):** komplementární. Já qualitative, oni quantitative. Metric + forecast = leading + lagging.
- **Zadavatel (#1):** „support to vyřeší" = nejhorší email. Support cost jako line item v business case, ne externalita.

## Memorabilia
Feature shipne v úterý, ve středu v 9:00 mám 47 ticketů se stejným dotazem — protože nikdo v session 1 neřekl „takhle to uživatel pochopí špatně". Máme 48 hodin po shipu, aby uživatel fíčuru pochopil — KB a makro musí existovat *před* launchem, ne *jako reakce* na tsunami. Bez CS proxy v session 1 jsme reaktivní; cenu platí support tým a uživatelé v tichém churnu. Buď prediktivní v Session 1, nebo reaktivní po launchi. Třetí možnost není.
