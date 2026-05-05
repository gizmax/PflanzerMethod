# Perspektiva: Produkt manažer

## Kdo jsem
Senior PM v B2B SaaS korporátu, 10+ let v oboru. Cagan a Torres na noční stolek, ale kalendář mi denně rozbíjejí sales escalations a HiPPO porady. Design Sprint mi jednou zachránil čtvrtletí, podruhé spolehlivě nedoručil — proto jsem k „2-day workshop solves everything" zdravě skeptický, ale vidím tam páku.

## 1. Posouzení metody z mé role

**Co mi pomáhá**
- Stakeholdery dostane do místnosti den 1 — končí rok pinkání mezi mnou, sales a engineeringem.
- Funkční mockup místo Figma fasády snižuje riziko, že se v PI planning ukáže „aha, tohle nejde".
- Score závaznosti je elegantní — poprvé dostávám nástroj, jak rozlišit „mně se to nelíbí" od „tohle commitnu do release".
- Programátoři spolutvoří → handoff přestává být můj druhý fulltime job.

**Co mi chybí**
- Žádný explicit product discovery layer před Session 1. Metoda startuje řešením (mockup), ne problémem. Bez OST / JTBD validace stavím feature factory s AI uprostřed.
- Žádná vazba na success metric / outcome. Co měříme po launchi? Kdo to definuje?
- Chybí prioritizační framework mezi „1–3 mockupy". Preferuje se dle čeho — chuti, ROI, effortu, strategic fitu?
- Žádná zmínka o roadmap impactu. Pflanzer session vyrobí prototyp pro 1 fíčuru, ale co dělá s ostatními 8 v backlogu?

**Co mě v ní ohrožuje**
- AI-led syntéza v Session 2 tiše vytlačí PM z role „překladatele business". Dostávám se do exekutivní role bez vlivu na rámec.
- Zadavatel + AI + dev v místnosti = riziko, že se PM stane sekretářkou (sumarizace, action items) místo ownerem produktu.
- „Výstup = preferovaná varianta" může být legitimizace HiPPO rozhodnutí — zadavatel řekne, dev kývne, security mlčí, a PM má držet linku v PRD ex post.

## 2. Must-have vstupy do Session 1

1. **Problem statement v JTBD formátu** — „When [situation], I want to [job], so I can [outcome]". Jedna věta. Schválená sponzorem.
2. **Persona / segment** — kdo, primary + secondary, s kontextem použití. Pokud nemáme research, použít proxy persona z support ticketů.
3. **OST kostra** (Torres) — desired outcome → 2–3 opportunities → solutions. Vyplněná do 60 % před session, dotvoří se v prvních 30 min.
4. **Success metric + leading indicator** — co měříme za 30/60/90 dní. Bez toho je „preferovaná varianta" subjektivní soutěž krásy.
5. **Konkurenční / status-quo screenshot deck** — 5–8 snímků jak to dělá konkurence + jak to děláme dnes. Anti-NIH, anti-„vymyslíme to od nuly".
6. **OKR / strategic alignment řádek** — k jakému company outcome to patří. Pokud nepatří, zastavit Session 1.
7. **Constraints sheet** — budget, time-to-market, deal-breakery (regulatorika, integrace, contracts).
8. **Hypotéza v XYZ formátu** (Savoia) — „Alespoň X % z Y udělá Z" jako falsifikovatelný předpoklad pro mockup.

## 3. Must-have výstupy ze Session 1 a 2

**Po Session 1 (PM odnáší):**
- Preference matrix: 1–3 mockupy × dimenze (user value, effort, risk, strategic fit) s hlasy per role.
- Decision log s rationale + dissenting opinions (kdo nesouhlasil a proč) — kritické pro audit a follow-up.
- Updated OST: které opportunity branch jsme zvolili, které park.

**Po Session 2 (PM odnáší):**
- Scored feedback aggregát per role × per varianta s commitment levelem.
- Open questions backlog s ownerem a deadline.
- Draft akceptačních kritérií navázaných na success metric.
- Definition of Done pro discovery → handoff (PRD lite, ne 30stránkový spec).
- Measurement plan: jaké eventy, jaký dashboard, kdo sleduje.

## 4. Edge cases a rizika

1. **Scope creep během Session 1** — „když už tu jsme, přidejme ještě…". Mitigace: facilitátor + PM mají právo říct „parking lot" a vrátit do JTBD. Časový budget na varianty fixní.
2. **HiPPO přebije persony** — zadavatel/exec si v reálném čase prosadí variantu, kterou data nepodporují. Mitigace: silent dot voting před verbální diskusí (Liberating Structures 1-2-4-All), score závaznosti zveřejněno až po hlasování.
3. **AI mockup ≠ technická realita** — vibe-coding vyrobí variantu, kterou v existujícím stacku nepostavíte za méně než 3 sprinty. Mitigace: tech feasibility check inline, ne až post-session.
4. **Discovery debt** — metoda předpokládá známou personu/problém. Pokud není, Session 1 generuje řešení k neexistujícímu problému. Mitigace: pre-flight gate „máme JTBD a evidenci?" → pokud ne, předřadit Continuous Discovery sprint (2 týdny user interviews).
5. **Závaznost score se stane politickým nástrojem** — oddělení dá nízký score, aby se zbavilo práce. Mitigace: score má rationale field + facilitátor flaguje pattern „chronický blocker".

## 5. Konkrétní vylepšení metody

1. **Přidat Session 0 (90 min, async OK)** — discovery alignment: JTBD, persona, OST, success metric, konkurenční scan. Bez výstupu Session 0 se Session 1 nespouští. Řeší prázdnotu před „Hlavní přípravy".
2. **Preference matrix místo „preference variant"** — strukturovaný scoring (4 dimenze × role), ne hlasování chuti. Šablona v Miro/FigJam, agreguje AI co-pilot.
3. **Outcome-based sukces kritéria, ne feature checklist** — výstup Session 2 musí obsahovat „za 60 dní změříme metric X o Y %, jinak iterujeme/killneme". Jinak je to feature factory s drahým prototypem.
4. **Pre-mortem ve 30. minutě Session 1** (Atlassian Play) — „je 6 měsíců po launchi, fíčura selhala, proč?". Kondenzát v 15 min. Generuje rizika dřív, než tým zamiluje variantu.
5. **PRD-lite template napojený na výstup** — 1stránka: JTBD, persona, success metric, scope in/out, akceptační kritéria, otevřené otázky. Generuje AI ze session artefaktů, PM jen edituje. Šetří mi 1–2 dny po každé session.

## 6. Konflikty s ostatními rolemi

- **Zadavatel (#1):** klasický HiPPO konflikt — on chce variantu, která mu sedí; já potřebuji variantu, kterou kupují personas. Score závaznosti + silent voting jsou moje páka.
- **Engineering manager (#9):** přetahování o kapacitu a timeline. Já chci ship za 2 sprinty, on říká 4. Musíme sdílet odhad effortu inline v Session 1, ne ex post.
- **UX / Designer (#6):** kdo vlastní persona/JTBD? Klasický PM vs. UX battle. Doporučuji shared ownership s PM jako tie-breakerem na scope, UX na flow.
- **Security (#7):** veto právo může zabít variantu, do které jsem investoval session. Řešení: security pre-read charteru + on-call slot, ne až final reaction.
- **Customer support proxy (#13):** často vidí real pain líp než já — konflikt v interpretaci „co uživatelé chtějí". Vítám to, ale potřebuji strukturu: jejich data jako vstup, ne jejich názor jako rozhodnutí.

## Memorabilia
Pflanzer řeší alignment, ne discovery. Pokud mu nepředřadím JTBD a success metric, vyrobí mi nejhladší feature factory v korporátu — s AI uprostřed.
