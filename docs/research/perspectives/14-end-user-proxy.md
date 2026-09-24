# 14 — End-user proxy / User Researcher

> Perspektiva: Senior User Researcher / End-user proxy v korporátu, 10+ let.
> Generative + evaluative research, JTBD, Continuous Discovery (Torres),
> Opportunity Solution Tree, persona freshness.

## Kde Pflanzerova metoda dělá radost

PdM staví stakeholdery do jedné místnosti, vyrábí tangible artefakt a má score
závaznosti — to je víc, než zvládne 90 % discovery workshopů, na kterých jsem
seděl. Cross-functional alignment v jeden den řeší reálnou bolest („pinkací
smyčky“). Mockup jako shared object of reference je výrazně lepší než MVP
Canvas, protože eliminuje *imaginární souhlas* — situaci, kdy všichni říkají
„ano“ na text, ale představují si jiný produkt.

## Kde Pflanzerova metoda v současné podobě selhává

**1. Discovery debt jako default state.** PdM v kroku „hlavní přípravy“ neřeší,
jestli vůbec víme, *čí* problém řešíme. Riziko: zadavatel donese nápad, panel
ho zoptimalizuje napříč rolemi, vznikne perfektně sladěný produkt, který nikdo
nepotřebuje. *Cross-functional alignment na špatný problém je drahý fail.*
Role-catalog má User Research jako VOLITELNOU s triggerem „nejasné persony“ —
to je obrácený gradient. Default by měl být *opt-out* (s důkazem fresh
evidence), ne *opt-in*.

**2. Žádný persona freshness check.** Catalog předpokládá, že „dostupné
persony“ jsou validní. V korporátu typicky nejsou: persony jsou 18+ měsíců
staré PowerPoint slidy, které nikdo nedrží live. Bez freshness checku tým
vibekóduje pro fiktivní personu z roku 2024.

**3. AI proxy persona má v catalogu ✅ bez disclaimeru.** Toto je nejdražší
bod celého dokumentu. AI persona je archetype interpolation z tréninkových dat
plus brief — umí střední statistiku, neumí *novel insight*, *contrarian
behavior* ani *edge case, který by produkt zabil v reálu*. Bez disclaimeru
panel uvěří, že má pokrytou perspektivu uživatele.

**4. JTBD framing chybí jako vstup.** Bez Job-to-be-Done struktury („when
[situation], I want to [motivation], so I can [outcome]“) panel ideuje
*features*, ne *outcomes*. Mockup pak řeší solution-space problémy, aniž by
kotvil v problem-space.

**5. Žádný link na Continuous Discovery (Torres) ani OST.** Baseline 03 to
zmiňuje, ale role-catalog ani metoda samotná neabsorbovaly. PdM je discrete
event; discovery je rhythm. Jeden bez druhého = decision theatre.

## Návrhy vylepšení (priority order)

### A. Pre-flight: Discovery Readiness Gate (POVINNÝ)

Před session 1 musí být splněny tři podmínky. Pokud kterákoli chybí, sessionu
se předřazují **2 týdny continuous discovery** (Torres rhythm: 3 zákaznické
rozhovory týdně, OST update weekly).

**Discovery Readiness checklist:**
1. **Persona freshness ≤ 6 měsíců** — minimálně 5 nedávných rozhovorů
   s reprezentativními uživateli (interní nebo externí) za posledních 6 měsíců,
   transcripty existují, klíčové JTBD jsou pojmenované.
2. **JTBD statement** pro core problém formulovaný a podepsaný PdM.
3. **Opportunity Solution Tree** v0 — desired outcome → 2–3 opportunities →
   uvažované solutions. Mockupy v session 1 musí mapovat na konkrétní
   opportunity v OST, ne se vznášet ve vzduchu.

**Pokud chybí:** Discovery Readiness = NO → 2-week Discovery Sprint
(15 rozhovorů, OST, persona refresh) → teprve pak session 1.

**Pokud je v korporátu nemožné získat externí uživatele** (B2B s NDA,
internal tooling): nahradit *internal user research* — shadowing, support
ticket review, sales call recordings. Ne přeskočit.

### B. Persona Expiration Policy

Persona má **expiry date**. Defaulty:
- **B2C consumer:** 6 měsíců.
- **B2B SaaS:** 9 měsíců.
- **Internal tooling:** 12 měsíců (ale s povinným re-shadowingem).
- **Po pivotu / org change / market shift:** auto-expire bez ohledu na věk.

**Trigger pro re-validation:** ≥ 2 z následujícího — nový segment, změna
v top-3 support tickets, NPS shift > 10 bodů, konkurenční disrupce, regulační
změna dotýkající se UX. Pokud expired persona vstupuje do PdM session bez
refreshe = **discovery debt flag**. Score závaznosti připomínek zaměřených na
„user need“ se v session 2 váží sníženě, pokud persona není fresh — explicit
distrust signal.

### C. AI proxy persona — kde má hranice (jasně)

**Co AI persona ZVLÁDNE:**
- Archetype check — „odpovídá mockup obecnému profilu segmentu?“ (heuristic
  level, ne usability test).
- Stručný JTBD reality check oproti briefu („řeší tento mockup deklarovaný
  job?“).
- Generování *hypotéz k otestování* na reálných uživatelích.
- Sumarizace existujícího research corpusu (transcripty, NPS komentáře).
- Identifikace zjevných usability porušení (heuristics à la Nielsen).

**Co AI persona NEZVLÁDNE — nikdy:**
- *Novel insight* — neřekne ti, co tě překvapí. Tréninková data konvergují
  k mediánu.
- *Edge case behavior* — power user, accessibility extremity, low-literacy
  uživatel, uživatel v krizi, uživatel s nesouladnými cíli (jeho cíl ≠ cíl
  zaměstnavatele) — všechny tyto skupiny jsou v tréninkových datech
  underrepresented, AI je smaže.
- *Cultural / regional specifics* — CEE B2B uživatel má jiné mentální modely
  než SF startup uživatel; AI default je SF.
- *Contradiction between stated and actual behavior* — UX research zlato je
  „say-do gap“. AI ti řekne stated, ne do.
- *Emotional arc* (frustrace, abandonment, trust building) — AI to popíše
  konceptuálně, neprožije.

**Pravidlo:** AI persona je **vstup do session, ne výstup ze session.**
Generuje hypotézy → člověk je validuje → výsledek vstupuje do mockup
preference. AI persona nikdy nemá poslední slovo na variantu.

**Score deflation:** AI-only persona feedback v session 2 má **score
závaznosti maximálně 0.5** (z 1.0). Distinguishuje od „real user said this“.

### D. OST jako mandatory input artefakt

Mockup v session 1 musí mít na sobě tag → konkrétní node v OST. Pokud nemá,
facilitátor (nebo AI co-pilot) musí položit otázku: *„Která opportunity tohle
adresuje? Jak víme, že tato opportunity je real?“* Pokud tým neumí odpovědět
za 60 sekund, mockup se odkládá do parking lotu.

To brání nejčastějšímu PdM failure módu: **vibekódíme cool feature, která
neřeší žádnou validovanou opportunity.**

### E. Discovery Debt Detector jako AI co-pilot skill

Nový skill v AI panelu (volá se před session 1 a v session 2):

**Discovery Debt Detector audit:**
- Kolik tvrzení o uživateli v briefu/mockupu má zdroj (research artefakt,
  citace transcriptu, support ticket ID)?
- Kolik je *assumption-stated-as-fact*?
- Kdy proběhl poslední user contact pro tuto cílovou skupinu?
- Existuje OST node pro každý mockup?

**Output:** Discovery Debt skóre 0–10. ≥7 = STOP, předřaď discovery sprint.
3–6 = WARNING, omez závaznost session výstupů na *exploratory*. ≤2 = OK.

## Změna role-catalogu

**Posunout End-user proxy z VOLITELNÉ na DOPORUČENOU s default-on.**
Trigger pro povinnost: customer-facing flow nebo nový segment. Volitelná pouze
pokud Discovery Readiness Gate prošel s persona freshness ≤ 3 měsíce.

## Memorabilia

> **AI persona je dobrý *archetype check* — neumí ti říct, co tě překvapí.
> Použij ji k validaci, že mockup *neporušuje* obecný profil uživatele.
> Nepoužívej ji k objevu, *co uživatel skutečně potřebuje*. Když nemáš čas na
> reálné uživatele a nahradíš je AI proxy, neděláš user research — vedeš
> sofistikovaný monolog a jen jsi přidal echo chamber s hlasem, který zní
> empaticky. Pflanzer bez fresh evidence z reálných uživatelů je
> alignment-driven feature factory, ne discovery.**

## Otevřené otázky pro syntézu

1. Kdo vlastní persona freshness governance napříč BUs?
2. Jak v interních / regulovaných projektech získat fresh user contact, když
   uživatel je interní zaměstnanec s šéfem v room?
3. Má Pflanzer mít „discovery sprint“ jako oficiální pre-step, nebo to
   nechat outside scope a jen flagovat readiness?
4. Score závaznosti AI-persona feedbacku — fixní deflation, nebo
   per-session kalibrace?
