# Pohled Accessibility Specialist / Inclusive Design Lead

> **Role:** Senior A11y / Inclusive Design Lead, 10+ let v korporátu.
> **Optika:** WCAG 2.2 AA, EAA (28. 6. 2025), ARIA, NVDA / JAWS / VoiceOver,
> keyboard nav, cognitive a11y. Denní bolest: a11y jako afterthought v handoffu;
> AI-vygenerované UI co vypadá hezky a rozbije semantický HTML; post-launch audit
> co vyplivne 200 issue.

## Co Pflanzerova metoda dělá dobře

- **Stakeholdeři u stolu od minuty 0** — pokud je accessibility expert v role
  catalogu, nejsem dotaz tří měsíců po designu, ale partner při výběru varianty.
  Tohle samo o sobě ušetří 80 % retrofit nákladů.
- **Funkční prototyp místo Figma fasády** — můžu reálně zapnout NVDA na deploy
  URL a slyšet, jak to čte. Z Figmy to nevyzkouším.
- **Score závaznosti** — pokud ten score zahrnuje WCAG severity (Critical /
  Serious / Moderate / Minor dle Deque klasifikace), a11y má váhu a není to
  „někdy doplníme".

## Slepá místa, která mě bolí

1. **Accessibility je v role catalogu „VOLITELNÁ (trigger)".** To je v roce 2026
   zastaralé. **EAA platí od 28. 6. 2025** pro e-commerce, banky, dopravu,
   telco, e-knihy, ATM/kiosky a B2C služby v EU. Trigger by měl být obrácený:
   **a11y POVINNÁ, pokud projekt nepadá do úzké výjimky** (interní tooling pro
   <10 lidí bez plánu externalizace, microenterprise <10 zaměstnanců + <2M EUR
   obrat). Stávající formulace pozve a11y experta jen do public-facing
   projektů — přitom interní HR systém v korporátu nad 250 zaměstnanců spadá pod
   reasonable accommodation povinnost dle EU directive 2000/78/EC.

2. **AI-vygenerovaný kód je a11y minové pole.** v0 / Bolt / Lovable produkují
   `<div onClick>` místo `<button>`, ikony bez `aria-label`, modaly bez focus
   trap, `<div role="button">` bez keyboard handleru, contrast 4.4:1 na
   placeholder textu. Metoda to dnes nezachytí — vibe-coding session 1 končí
   mockupem, který vypadá pixel-perfect, ale screen reader z něj uslyší
   „button button button button".

3. **Demo data nejsou inclusive.** „Lorem ipsum + Jan Novák" personas neodhalí,
   že form nezvládne diakritiku ve screen readeru, dlouhá jména v RTL jazycích,
   nebo uživatele co používá pouze klávesnici a switch device.

4. **Session 2 výklad připomínek vede AI.** Pokud AI nemá explicitně a11y lens,
   dropne moje připomínky jako „minor" („contrast 4.3:1 vs 4.5:1, kosmetika").
   V realitě je to WCAG 1.4.3 fail = právní expozice v EAA.

## Konkrétní vylepšení metody

### Quickscan checklist pro Session 1 (8–10 položek, 5–10 min na konci sessionu)

1. **Sémantický HTML** — `<button>` pro akce, `<a href>` pro navigaci, ne
   `<div onClick>`. Ověř view-source, ne render.
2. **Keyboard-only průchod** — odpoj myš, projdi celý flow přes Tab / Shift+Tab /
   Enter / Space / Esc. Focus indikátor viditelný (WCAG 2.4.7, 2.4.11).
3. **Focus management** — modal, drawer, toast: focus se přesune dovnitř, trap,
   po close vrátí na trigger element.
4. **Form labels** — každý input má `<label for>` nebo `aria-labelledby`.
   Placeholder není label.
5. **Error messages** — `aria-describedby` na input, `role="alert"` pro live
   region, error popisuje **co** je špatně a **jak to opravit**.
6. **Contrast** — text 4.5:1 (normal) / 3:1 (large/bold ≥18pt). Ověř na hover,
   focus, disabled, dark mode.
7. **Headings hierarchy** — `<h1>` jen jedna, žádné skoky `h2 → h4`. Screen
   reader podle toho dělá rotor.
8. **Images / icons** — informační má `alt`, dekorativní `alt=""` nebo
   `aria-hidden`. Icon-only button má `aria-label`.
9. **Touch targets** — min 24×24 CSS px (WCAG 2.5.8 AA), preferuj 44×44
   (AAA / mobile best practice).
10. **Cognitive load** — error messages plain language (B1/B2), ne corporate
    jargon. Žádné časové limity bez extend / disable (WCAG 2.2.1).

Pokud quickscan najde >2 issue v kategorii Critical/Serious, varianta jde do
session 2 s flagem „a11y rework needed", ne do dev handoff.

### Automated tools — povinný stack

- **axe DevTools** (Deque) — browser extension, najde ~30–40 % WCAG issue
  automaticky. Run na každém deploy URL před session 2.
- **Pa11y CI** — headless audit, integrace do feedback wrapperu (Next.js stránka
  s iframe varianty + scoring). Output JSON → AI v session 2 dostává
  strojový a11y report jako vstup.
- **Lighthouse a11y score** — kontextové, ne autoritativní (skóre 100 ≠ WCAG AA),
  ale rychlý baseline.
- **Color Contrast Analyser (TPGi)** — pro design system review předem.

### Manual checks — co AI nikdy nezvládne

- **Screen reader UX** (NVDA na Win, VoiceOver na Mac/iOS, TalkBack Android) —
  poslechni 10-min flow. AI nezachytí, že stejné tlačítko se 4× po sobě čte
  jako „button" bez kontextu, nebo že modal se otevře, ale screen reader
  zůstane na původním elementu.
- **Keyboard nav v dynamických komponentách** — combobox, autocomplete,
  date picker, tree view. ARIA Authoring Practices Guide patterns.
- **Cognitive walkthrough** — udělej úkol pod simulovaným časovým stresem,
  s vypnutými animacemi, s 200% zoomem. Reflow (WCAG 1.4.10) láme 80 % AI
  layoutů.
- **Reduced motion** — `prefers-reduced-motion` respektován? Vibe-coded UI to
  defaultně ignoruje.

### Persona inclusivity — rozšíř persona set

V session 1 vstupy přidat **alespoň 2 disability persony**:
- **Petr (54), low vision + screen magnifier 200%** — testuje reflow, contrast,
  text-spacing.
- **Eva (38), motor impairment, switch control / voice control** — testuje
  keyboard nav, target size, time limits.
- **Volitelně Marek (29), cognitive disability / dyslexie** — plain language,
  consistent navigation, error prevention.

Personas nesmí být tokenistické — musí mít **journey + frikce**, ne jen foto +
demografika.

## AI proxy — co zvládne a co ne

| Zvládne (AI accessibility proxy) | Nezvládne |
|---|---|
| Static mockup audit (axe/Pa11y rules) | Screen reader UX flow (timing, kontext, polotekst) |
| Contrast check, target size, alt text presence | Cognitive load v reálném úkolu pod stresem |
| Sémantický HTML lint, ARIA attribute validity | Dynamic focus management ve SPA transitions |
| Generování persona briefů s disability lens | Switch / voice control reálné usability |
| Score WCAG 2.2 SC mapping pro připomínky | Empatii s frustracelí uživatele po 5. failu |

**Pravidlo:** AI proxy v session 1 OK pro mockup audit. **Pre-launch (před
handoffem do prod) povinný human a11y review.** EAA non-compliance v EU =
pokuta až 20 000 EUR + nucené stažení produktu z trhu (per členský stát,
ČR transposice 6/2025). AI podpis na compliance attestation neexistuje.

## Memorabilia

> **A11y v session 1 stojí 5 minut. Post-launch 5 týdnů a soudní spor.**
> Quickscan checklist na konci session 1 zachytí 70 % issue. Retrofit po
> dev handoffu znamená přepsat semantiku, refactor focus management, předělat
> design system tokens — a vysvětlovat zadavateli, proč EAA pokuta není
> „IT problém". V Pflanzerově metodě je a11y nejlevnější moment kariéry.

## Otevřené otázky pro syntézu

- Měl by být quickscan checklist součástí AI-facilitator skriptu (auto-run
  axe na deploy URL před session ukončí)?
- Jak reflektovat EAA v decision tree — **default ON** pro B2C a B2B nad
  250 zaměstnanců, opt-out s justifikací?
- Score závaznosti: WCAG Critical / Serious by měly mít stejnou váhu jako
  Security veto (blokující), ne jako „nice to have".
