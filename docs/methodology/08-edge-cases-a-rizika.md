# 08 — Edge cases a rizika

**Pflanzer Method | pflanzer.cz/method**

> K čemu je tento dokument: co dělat, když metoda narazí na realitu. Každý
> případ má strukturu **situace → co dělat → kdo rozhoduje**. Číslování
> je stabilní (odkazují na něj ADR-0001 a ADR-0017: § 11 kvórum, § 12
> Decider). Default je malá skupina (max 5 naráz, ADR-0021); případy
> o víc lidech platí pro rozšířenou sestavu Full.

## 1. Zástupce kroku nebo Decider nepřijde

**Situace.** Den před oknem je Decider, nebo zástupce bezpečnosti & práva
nebo provozu, nedostupný.

**Co dělat.**
- **Decider:** nedelegovatelný — Kickoff/Rozhodnutí se **odkládá**, nepřesouvá
  na delegáta bez mandátu. Backup Decider jen předem určený v Kickoffu.
- **Bezpečnost & právo / provoz:** okno se přesune; **krok bez jména se
  nesvolává**. Pomáhá předem určený zástupce s mandátem (deputy). Build
  může proběhnout, ale Ship bez podepsaného okna neprojde.
- Senior delegát u vetovací role: junior bez mandátu = okno se odkládá.

**Kdo rozhoduje.** Facilitátor + PdM; právo zrušit okno bez kvóra.

## 2. Veto bezpečnosti v Buildu

**Situace.** Bezpečnost označí variantu jako Kritickou (token v URL, PII
v event property, únik mezi tenanty, reálná PII v promptu).

**Co dělat.**
1. Zastav stavbu na dotčené variantě.
2. 5 min: veto přečteno nahlas, ostatní mlčí.
3. 15 min: existuje varianta A' s technickou mitigací (tokenizace,
   server-side tracking, pseudonymizace)? Ano → pokračuj na A'; ne →
   varianta ven, soutěží zbylé.
4. Zapiš do **veto registru** s rationale a mitigací.
5. Reálná PII/L4 v promptu = okamžité přerušení, incident playbook,
   72h GDPR hodiny.

**Kdo rozhoduje.** Bezpečnost (lidský podpis); facilitátor moderuje
proces, ne rozhodnutí. Veto nepřebíjí hlas, jen mitigace nebo výslovný
override Decidera s rationale. **Prevence:** data classification a threat
model v checkpointu a v `CONSTITUTION.md`.

## 3. HiPPO přebije skóre

**Situace.** Zadavatel po prezentaci: „já to cítím jinak, jdeme s variantou
A", i když B vede.

**Co dělat.** Silent voting předem, **Decider hlasuje poslední**, skóre se
zveřejní až po hlasování. Přebije-li přesto, zapiš do decision logu
**člověka a rationale** („Decider override: A přes nižší skóre, protože…"),
žádné anonymní „tým rozhodl". Častý override (> 30 % rozhodnutí) je signál
ke kalibraci metody.

**Kdo rozhoduje.** Decider (informed dictatorship), s povinným rationale.
Critical od bezpečnosti/práva/přístupnosti se nepřebíjí hlasem.

## 4. Scope creep

**Situace.** „Když už jsme tady, přidáme export do PDF / SSO / multi-tenant."

**Co dělat.** Parking lot okamžitě, bez diskuse; PdM ho vlastní (každý bod:
vlastník, termín, rozhodnutí in-scope / další zadání / nikdy). Po třetím
opakování facilitátor zastaví a připomene zadání. Nová věc = kandidát na
další Kickoff, ne na tento Build.

**Kdo rozhoduje.** PdM + facilitátor (PdM scope, design flow).

## 5. AI vygeneruje halucinaci

**Situace.** Neexistující UX pattern, vymyšlený API endpoint, vymyšlené
právní tvrzení v textu („GDPR-certified").

**Co dělat.** Žádný AI výstup bez lidského podpisu příslušné role. Detektory:

| Typ | Detektor | Zachytí |
|-----|----------|---------|
| UX pattern | pattern allowlist v `INTEGRATION_GUIDE` | vývojář FE + design |
| API endpoint | OpenAPI diff proti registru | vývojář BE |
| Právní/marketingové tvrzení | firemní šablona, nikdy generovaný text | právo / UX writer |
| Komponenta | component manifest | vývojář FE |
| Přístupnost | axe-core + ruční klávesnicový test | A11y |

**Kdo rozhoduje.** Vždy člověk příslušné expertízy. AI vede jen rychlé,
kontextově lehké úkoly (Režim 3, [`02`](02-role-catalog.md)).

## 6. Discovery debt odhalen během Buildu

**Situace.** V průběhu vyjde najevo, že persona je stará slideshow a JTBD/OST
neexistují; Debt Detector dává ≥ 7.

**Co dělat.** Facilitátor stavbu zastaví („metoda řeší alignment, ne
discovery"). Předřaď discovery ([`03`](03-pre-session-priprava.md) § Krok
0): rozhovory nebo jejich ekvivalent, JTBD, OST v0. Kickoff/Build po něm
znovu. Náklady jdou na projekt, ne na metodu.

**Kdo rozhoduje.** Facilitátor (zastavit) + PdM (discovery) + design (persona).

## 7. Zadání přes víc týmů

**Situace.** V místnosti je víc než 5 lidí ze 3+ týmů; každý tým má vlastní
backend, design system a release cyklus.

**Co dělat.** Scope zúžit na jeden bounded context, nebo **federovat**:
mini-Build per tým (každý svoji buňku ≤ 5 lidí), architekt (#18) vlastní
integration map, společné Rozhodnutí se 2 zástupci z týmu jen o integraci.
Mezi buňkami synchronizuj OpenAPI a breaking-change registr.

**Kdo rozhoduje.** EM + architekt. Bez architekta je multi-team zadání
chaos; v takovém případě projekt nespouštěj.

## 8. Preview jde ostře bez Ship

**Situace.** Sponzor vidí preview, pošle ho zákazníkovi a ten ji používá na
ostro. Vítěz je sice určen pro produkci (evolve), ale **neprošel Ship**:
gates, checkpointy, review.

**Co dělat.**
1. **Okamžitě stáhni preview** (bezpečnost + provoz mají právo).
2. Blame-free retro do 48 h: selhal technický enforcement (preview mělo
   být bez prod dat a sítě), sociální (zadání), nebo komunikace?
3. Sponzor zákazníkovi vysvětlí a dá termín: stejný kód projde Ship
   (gates 80/85 + checkpointy) a nasadí se správnou cestou; **nic se
   nepřepisuje**.
4. Do zadání: preview před Ship se externě nesdílí a nepoužívá s reálnými
   daty. U throw-away platí absolutně — do produkce nejde nikdy.

**Kdo rozhoduje.** Bezpečnost + provoz (takedown); EM + sponzor
(komunikace); o urychlení Ship rozhoduje Decider s EM — gate se nesnižuje,
jen priorizuje. „Production by stealth" je organizační chyba, ne technická;
štítek „k rozhodnutí, ne produkt" a izolace preview ji jen zmírňují.

## 9. Hodnocení se stane politickým nástrojem

**Situace.** Oddělení dá variantě nejnižší skóre / Kritické, aby se zbavilo
práce, nebo naopak nafoukne skóre kvůli agendě.

**Co dělat.** Rationale povinné (záznam bez něj je neplatný); Kritické bez
důkazu (STRIDE, a11y, kapacita, právo) facilitátor sníží na varování;
hlasy jsou v decision logu s jmény; chronicky podezřelý vzorec ukaž jako
samostatný bod Rozhodnutí.

**Kdo rozhoduje.** Facilitátor (downgrade bez rationale); dlouhodobou
kalibraci drží Champion/komunita.

## 10. Champion nebo klíčový zástupce odejde

**Situace.** Po týdnech odejde člověk, který vlastnil měření T+30/60/90
nebo handoff.

**Co dělat.** Předem určený **buddy** (druhý senior ze stejné jednotky)
převezme: 30min recap (hotové milníky, otevřená rizika), videoprůchod
SHIP.md, přečtení decision logu (do 5 pracovních dní). Odchod zaznamenej
jako signál udržitelnosti.

**Kdo rozhoduje.** EM (přidělení buddy) + PdM.

## 11. Zástupci nestíhají Sběr feedbacku (Async)

**Situace.** V okně jsou někteří zástupci na dovolené, v uzávěrce nebo mimo
dosah.

**Co dělat.**
1. Sběr feedbacku (Async) je výchozí: hub nebo offline `pflanzer feedback add`, hlasování
   do termínu; krátké video preview (≤ 10 min) pro nepřítomné.
2. **Kvórum:** pokud do termínu odpoví méně než 60 % povinných zástupců,
   Rozhodnutí se posune o nejvýš 5 dní. Při ≥ 60 % a chybějící **nevetovací**
   roli se rozhoduje a její mlčení se zapíše jako „no objection" (ADR-0017).
3. **Vetovací role** (bezpečnost & právo, kapacita EM) bez vyjádření:
   Rozhodnutí je jen review, ne rozhodnutí.
4. Okno se neprodlužuje nad strop stupně; nestíhá-li vetovací role,
   upgrade stupně nebo odklad.

**Kdo rozhoduje.** Facilitátor + PdM (PdM hlídá kalendář; ověř dovolené při
bookování oken).

## 12. Rozhodnutí skončí bez rozhodnutí

**Situace.** Decider: „potřebuji to ještě promyslet, dejte mi týden."

**Co dělat.** Použij **kanonický eskalační protokol v
[`ADR-0001`](../decisions/0001-decider-model.md)** (scénáře A: Decider chybí ·
B: „potřebuji čas" · C: Iterate vyčerpán). Text se sem nekopíruje — tři
rozcházející se kopie byly původní chyba. Orientačně: písemné rozhodnutí do
decision logu do 48 h, pak eskalace na sponzora, mlčení nevede k tichému
zániku (Iterate), Iterate max 1× a poté Go nebo Kill. Prevence: mandát
Deciderova a eskalační kontakt jsou už v zadání z Kickoffu.

## 13. Selhání facilitátora

Facilitátor je nejčastější bod selhání. Šest vzorců:

| Vzorec | Příznak | Protijed |
|--------|---------|----------|
| Captured by tool | 40 % času debugováním builderu | AI v sub-roli, záložní builder, facilitátor bez IDE |
| Captured by HiPPO | podvědomé nadržování sponzorovi | silent voting, Decider poslední; u high-stakes druhý facilitátor |
| Conflict avoidance | „vyřešíme potom" | konflikt pojmenovat v 5. minutě výskytu |
| Energy blindness | tlačí agendu, tým mrtvý | pauza každých 90 min, pulz 1–5 prstů, strop délky |
| AI as authority | „AI navrhla" jako argument | každý AI insight má lidský override; log atribuuje člověka |
| Charter creep | 30 vstupů pro 12 perspektiv | MoSCoW vstupů, právo „tohle teď ne" |

**Kdo rozhoduje.** Facilitátor sám sebe nehodnotí — pozorování po třetím
Buildu dělá spolufacilitátor nebo Champion; po 10 Buildech kalibrace
v komunitě praxe. Facilitátor je architekt odpovědnosti: rozhoduje, kdy AI
mluví, kdy člověk mlčí a kdy se konflikt eskaluje.
