# 03 — Visualization & Web Integration: „Spec-Driven Trap" vs Pflanzer

> **Cíl dokumentu:** Navrhnout sekci webu, která **vizuálně** ukáže, proč
> Pflanzer (artifact-first vibe) je rychlejší a alignment-ně bohatší než
> Spec-Driven Development (SDD). Tři vizuální koncepty → jeden winner →
> kompletní implementace (SVG + CSS + copy CS/EN) → integrační plán.
>
> **Tone of voice:** Editorial Botanical Brutalism. Žádná generic AI UI.
> Fraunces + JetBrains Mono. Print-friendly. Sub-50 KB inline SVG.
>
> **Status:** návrh, k odsouhlasení. Po schválení merge do `website/index.html`
> jako sekce **02b — Past spec-drivenu / The Spec-Driven Trap**.

---

## TLDR

1. **Tři koncepty**: (A) *Dvě cesty* — side-by-side timeline, (B) *Telefon-loop* —
   SDD jako broken telephone s % decay, (C) *Dvě rostliny* — extends existující
   botanical SVG (Pflanzer roste do květu, SDD má kořeny ve smyčce).
2. **Winner: hybrid B+C** — *„Botanical loop trap"*: Pflanzer = jeden stem,
   strom roste rovně do bloomu. SDD = stem, který se zacyklí v podzemí
   (spec → app → spec → app), nikdy nevykvete. Doplněno o % alignment decay
   per krok jako mikro-data overlay.
3. **Implementace:** jediné inline SVG (~7 KB), čistě `<path>`+`<text>`,
   re-používá existující CSS classes `.stroke-ink/.stroke-moss/.fill-punch`,
   nový `@keyframes` pro loop (respektuje `prefers-reduced-motion`).
4. **Section umístění:** mezi current 02 (USPs) a `#srovnani` jako **02b**.
   Comparison matrix dostane novou kolonku „Spec Kit / Kiro / OpenSpec".
   1-pager dostane shrnutí v jednom radku.
5. **Tagline winners:** CS — *„Specka je nájemné. Kód je vlastnictví."*,
   EN — *„Specs decay. Artifacts compound."*

---

## 1. Tři vizuální koncepty

### Koncept A — „Two Paths" / Dvě cesty

**Idea:** Side-by-side timeline. Vlevo Pflanzer (D0 → D14, jeden šíp,
chartreuse květ na konci). Vpravo SDD (App → Spec → Dev → App' → Spec' → …,
pinking back-and-forth, žádný end-stav).

**ASCII mockup:**

```
┌──────────────────────────────────┬──────────────────────────────────┐
│ PFLANZER                         │ SPEC-DRIVEN                      │
│                                  │                                  │
│ D0 ●──→ D5 ●──→ D10 ●──→ D14 ✿   │ App ●←→ Spec ●←→ Dev ●←→ App' ?  │
│ sazba   S1     S2       prod     │  ↑                          ↓    │
│                                  │  └──── ping-pong (∞) ───────┘    │
│ 14 dní                            │ 8 týdnů +/- ?                   │
└──────────────────────────────────┴──────────────────────────────────┘
```

**Emoce:** *clarita, kontrast.* Čtenář v jedné sekundě vidí „rovná čára"
vs „smyčka, ze které není výjezd".

**Print-friendly:** triviální. Dvě sloupcové timeliny, žádná animace
potřeba; print stylesheet jen vypne hover/animace.

**Risk:** generic. Tenhle pattern dnes dělá kdejaká SaaS landing („zastaralé
vs nové"). Není to brand-distinctive — chybí botanická metafora.

---

### Koncept B — „Broken Telephone Loop" / Telefon-hra

**Idea:** SDD jako broken telephone (alignment % decay per kroku). Každý
předávací krok ztrácí část informace. Pflanzer naopak alignment akumuluje
(co-located, 6 lidí, jeden artefakt).

**ASCII mockup:**

```
PFLANZER — alignment compounds
[Sponsor]──[PM]──[Sec]──[Legal]──[Dev]──[A11y]   100% → 100% (same room)
   └────────── 1 artifact, 6 heads ──────────┘   ✿ prod code

SDD — alignment decays per handoff
[Sponsor 100%] → [PM 87%] → [Spec 71%] → [Dev 54%] → [App ≠ Spec 38%] → ?
                  -13%        -16%        -17%        -16%
                  ↓
                  „We need to revise the spec."
```

**Emoce:** *frustrace, zachycená.* Procenta dělají argument konkrétní.
Engineering manager si představí poslední 3 projekty, kde se tohle stalo.

**Print-friendly:** ano, ale jen jako statický bar chart / step chart.
Animace „token klesající do dalšího kroku" je bonus pro web, ne nutnost.

**Risk:** procenta jsou ilustrativní (ne peer-reviewed); musí být označeny
jako *„illustrative, not measured"*, jinak ztratíme E-E-A-T kredibility,
kterou si web buduje v Evidence row.

---

### Koncept C — „Dvě rostliny" (botanical extension) **← favorit**

**Idea:** Extends existující botanical SVG ze sekce 01. Vedle Pflanzer
rostliny (seed → sprout → leaf → stem → bloom) druhá rostlina — SDD —
která **kořeny zacyklí v podzemí** (spec→app→spec→app) a **nikdy se
nedostane nad zem**.

**ASCII mockup:**

```
PFLANZER                                  SPEC-DRIVEN
                                          
        ✿ ← prod                          ? ← still in spec
        │                                 │
        ║ stem grows                      ║
       / \\\\ leaves                       │
        ║                                 │
   ─────●───── ground ─────────────────● ──────────
        │                              ╱╲
        ●  ← seed                    ╱  ╲
       /│\\                           spec→app
      roots                          ╲  ╱
                                      ╲╱
                                      spec'→app'
                                      ╲  ╱
                                       …(loop)…
                                      
   D0 — D14, květ                     T+? , kořeny v cyklu
```

**Emoce:** *poetická, brand-perfect.* Rostlina = manifesto („Sázíme AI
do rigidních procesů"). Druhá rostlina, která **vidíš ze schématu** —
nevykvete, protože její kořeny jsou ve smyčce — je memorable a citlivá.

**Print-friendly:** native. Statické SVG; loop u SDD je vyjádřený **tvarem
cesty**, ne animací. Animace je optional vrstva (kořeny pulzují) jen
pro web, vypnutá v `@media print` a `prefers-reduced-motion`.

**Risk:** musí být **brutalně čitelný**. Kdyby čtenář nepoznal na první
pohled, kde co je, ztrácíme funkci. Mitigace: labels v JetBrains Mono
nad každou rostlinou (PFLANZER / SPEC-DRIVEN), výrazný kontrast (květ
chartreuse vs prázdné nebe), labels per fáze.

---

## 2. Recommended concept — *Botanical Loop Trap* (C s vrstvami z B)

**Winner:** Koncept C jako primární vrstva, s mikro-overlayem konceptu B
(% alignment decay per krok u SDD). Důvody:

1. **Brand consistency** — extension existující rostliny v sekci 01.
   Čtenář, který skroloval z hero, automaticky propojí: *„aha, sekce 02b
   ukazuje, co se stane, kdyz tu rostlinu odřízneš od korpu vzduchu."*
2. **Memorability** — botanická metafora se v B2B SaaS landings nedělá.
   Diferencujeme.
3. **Defensibility** — loop ve tvaru cesty = strukturální tvrzení (SDD
   *má* zpětnou hranu), ne data tvrzení. Není potřeba peer-reviewed číslo.
4. **Print-safe** — žádné animace nutné. Loop je tvar, ne motion.

### 2.1 Full SVG (inline, ~7 KB)

> **Note:** SVG níže používá identické CSS classes jako existující flow
> v sekci 01 (`.stroke-ink`, `.stroke-moss`, `.fill-punch`, `.fill-ink`,
> `.fill-moss`, `.stroke-dash`, `.label-svg`, `.label-day`). Žádné nové
> styly. Jediný nový tween je `.spec-loop-anim` pro animaci po hover.

```html
<svg viewBox="0 0 1000 360" xmlns="http://www.w3.org/2000/svg"
     role="img" class="trap-svg"
     aria-label="Two plants side-by-side: Pflanzer grows from seed to bloom in 14 days; Spec-Driven loops underground between spec and app, never blooms.">
  <defs>
    <style>
      .trap-svg .stroke-ink   { stroke: #1A2418; fill: none; stroke-width: 1.6; stroke-linecap: round; stroke-linejoin: round; }
      .trap-svg .stroke-moss  { stroke: #2F4A2F; fill: none; stroke-width: 1.4; stroke-linecap: round; stroke-linejoin: round; }
      .trap-svg .stroke-thin  { stroke: #1A2418; fill: none; stroke-width: 1; stroke-linecap: round; }
      .trap-svg .stroke-dash  { stroke: #1A2418; fill: none; stroke-width: 1; stroke-dasharray: 3 4; }
      .trap-svg .stroke-loop  { stroke: #1A2418; fill: none; stroke-width: 1.4; stroke-dasharray: 4 3; opacity: 0.7; }
      .trap-svg .fill-punch   { fill: #C7E84A; }
      .trap-svg .fill-ink     { fill: #1A2418; }
      .trap-svg .fill-moss    { fill: #2F4A2F; }
      .trap-svg .fill-bone    { fill: #F4EFE6; }
      .trap-svg .label-svg    { font-family: 'JetBrains Mono', monospace; font-size: 10px;
                                text-transform: uppercase; letter-spacing: 0.12em;
                                fill: #1A2418; font-weight: 600; }
      .trap-svg .label-day    { font-family: 'JetBrains Mono', monospace; font-size: 9px;
                                letter-spacing: 0.1em; fill: #7A7264; font-weight: 500;
                                text-transform: uppercase; }
      .trap-svg .label-decay  { font-family: 'JetBrains Mono', monospace; font-size: 9px;
                                fill: #7A7264; font-weight: 500; }
      .trap-svg .label-side   { font-family: 'Fraunces', Georgia, serif;
                                font-variation-settings: 'SOFT' 100, 'opsz' 48;
                                font-size: 15px; fill: #1A2418; font-weight: 500;
                                letter-spacing: -0.015em; }
      .trap-svg .label-side em{ font-variation-settings: 'SOFT' 100, 'WONK' 1, 'opsz' 48;
                                font-style: italic; font-weight: 300; fill: #2F4A2F; }

      /* Loop animation — only when section visible + motion allowed */
      .trap-svg .spec-loop-anim { animation: specLoopDash 6s linear infinite; }
      @keyframes specLoopDash {
        from { stroke-dashoffset: 0; }
        to   { stroke-dashoffset: -28; }
      }
      @media (prefers-reduced-motion: reduce) {
        .trap-svg .spec-loop-anim { animation: none; }
      }
      @media print {
        .trap-svg .spec-loop-anim { animation: none; }
      }
    </style>
  </defs>

  <!-- ============ LEFT SIDE — PFLANZER ============ -->
  <text x="50"  y="34" class="label-side">Pflanzer — <em>roste do květu.</em></text>
  <text x="50"  y="52" class="label-day">Day 0 → Day 14 · single artifact</text>

  <!-- ground -->
  <line x1="40" y1="220" x2="470" y2="220" class="stroke-ink"/>
  <g class="stroke-thin">
    <line x1="50"  y1="228" x2="54"  y2="234"/>
    <line x1="80"  y1="228" x2="84"  y2="234"/>
    <line x1="110" y1="228" x2="114" y2="234"/>
    <line x1="140" y1="228" x2="144" y2="234"/>
    <line x1="170" y1="228" x2="174" y2="234"/>
    <line x1="200" y1="228" x2="204" y2="234"/>
    <line x1="230" y1="228" x2="234" y2="234"/>
    <line x1="260" y1="228" x2="264" y2="234"/>
    <line x1="290" y1="228" x2="294" y2="234"/>
    <line x1="320" y1="228" x2="324" y2="234"/>
    <line x1="350" y1="228" x2="354" y2="234"/>
    <line x1="380" y1="228" x2="384" y2="234"/>
    <line x1="410" y1="228" x2="414" y2="234"/>
    <line x1="440" y1="228" x2="444" y2="234"/>
  </g>

  <!-- seed underground (Day 0) -->
  <g transform="translate(110, 220)">
    <ellipse cx="0" cy="14" rx="9" ry="6" class="fill-ink"/>
    <path d="M -6 18 Q -10 24 -12 28" class="stroke-moss"/>
    <path d="M  0 20 Q  0 26  -2 32" class="stroke-moss"/>
    <path d="M  6 18 Q 10 24  12 28" class="stroke-moss"/>
  </g>
  <text x="110" y="270" text-anchor="middle" class="label-day">D0</text>
  <text x="110" y="284" text-anchor="middle" class="label-svg">sazba</text>

  <!-- straight stem to bloom (Day 14) -->
  <path d="M 260 220 Q 260 140 260 90" class="stroke-ink"/>
  <!-- two leaves -->
  <g class="stroke-moss">
    <path d="M 260 180 Q 240 175 222 182 Q 230 192 246 194 Q 260 192 260 180 Z"/>
    <path d="M 260 150 Q 282 145 300 152 Q 292 162 276 164 Q 260 162 260 150 Z"/>
    <path d="M 260 180 L 230 188" class="stroke-thin"/>
    <path d="M 260 150 L 296 158" class="stroke-thin"/>
  </g>
  <ellipse cx="260" cy="220" rx="14" ry="3" class="stroke-thin"/>

  <!-- bloom -->
  <g transform="translate(260, 88)">
    <circle cx="0" cy="-8" r="7" class="fill-punch" stroke="#1A2418" stroke-width="1.4"/>
    <circle cx="-9" cy="0" r="7" class="fill-punch" stroke="#1A2418" stroke-width="1.4"/>
    <circle cx="9"  cy="0" r="7" class="fill-punch" stroke="#1A2418" stroke-width="1.4"/>
    <circle cx="0" cy="8"  r="7" class="fill-punch" stroke="#1A2418" stroke-width="1.4"/>
    <circle cx="0" cy="0"  r="5" class="fill-ink"/>
  </g>
  <text x="260" y="320" text-anchor="middle" class="label-day">D14</text>
  <text x="260" y="334" text-anchor="middle" class="label-svg">prod</text>

  <!-- alignment label (compounds) -->
  <text x="395" y="270" class="label-day">alignment:</text>
  <text x="395" y="284" class="label-svg" style="fill:#2F4A2F;">100% → 100%</text>
  <text x="395" y="298" class="label-decay">same room · 6 heads</text>

  <!-- ============ DIVIDER ============ -->
  <line x1="500" y1="20" x2="500" y2="340" class="stroke-dash"/>

  <!-- ============ RIGHT SIDE — SPEC-DRIVEN ============ -->
  <text x="530" y="34" class="label-side">Spec-driven — <em>zacyklí v podzemí.</em></text>
  <text x="530" y="52" class="label-day">T+? · spec ↔ app ↔ spec'</text>

  <!-- ground -->
  <line x1="520" y1="220" x2="960" y2="220" class="stroke-ink"/>
  <g class="stroke-thin">
    <line x1="530" y1="228" x2="534" y2="234"/>
    <line x1="560" y1="228" x2="564" y2="234"/>
    <line x1="590" y1="228" x2="594" y2="234"/>
    <line x1="620" y1="228" x2="624" y2="234"/>
    <line x1="650" y1="228" x2="654" y2="234"/>
    <line x1="680" y1="228" x2="684" y2="234"/>
    <line x1="710" y1="228" x2="714" y2="234"/>
    <line x1="740" y1="228" x2="744" y2="234"/>
    <line x1="770" y1="228" x2="774" y2="234"/>
    <line x1="800" y1="228" x2="804" y2="234"/>
    <line x1="830" y1="228" x2="834" y2="234"/>
    <line x1="860" y1="228" x2="864" y2="234"/>
    <line x1="890" y1="228" x2="894" y2="234"/>
    <line x1="920" y1="228" x2="924" y2="234"/>
  </g>

  <!-- stem that tries to grow but bends back -->
  <path d="M 720 220 Q 720 180 700 168 Q 660 152 660 130"
        class="stroke-ink"/>
  <!-- failed bloom — outline only, no punch fill -->
  <circle cx="660" cy="118" r="9" class="stroke-ink fill-bone"/>
  <text x="660" y="122" text-anchor="middle" class="label-svg" style="fill:#7A7264;">?</text>

  <!-- one withered leaf -->
  <g class="stroke-moss" opacity="0.55">
    <path d="M 712 200 Q 695 198 682 205 Q 690 212 702 213 Q 712 212 712 200 Z"/>
  </g>

  <!-- the loop underground: spec → app → spec' → app' -->
  <!-- 4 nodes arranged in a tight rectangular cycle -->
  <g>
    <!-- node 1: spec -->
    <rect x="585" y="245" width="60" height="22" class="stroke-ink fill-bone"/>
    <text x="615" y="260" text-anchor="middle" class="label-svg">spec</text>

    <!-- node 2: app -->
    <rect x="685" y="245" width="60" height="22" class="stroke-ink fill-bone"/>
    <text x="715" y="260" text-anchor="middle" class="label-svg">app</text>

    <!-- node 3: spec' -->
    <rect x="785" y="245" width="60" height="22" class="stroke-ink fill-bone"/>
    <text x="815" y="260" text-anchor="middle" class="label-svg">spec'</text>

    <!-- node 4: app' -->
    <rect x="685" y="295" width="60" height="22" class="stroke-ink fill-bone"/>
    <text x="715" y="310" text-anchor="middle" class="label-svg">app'</text>

    <!-- arrows: forming a loop. animated stroke-dashoffset -->
    <path d="M 645 256 L 685 256" class="stroke-loop spec-loop-anim" marker-end="url(#arrow)"/>
    <path d="M 745 256 L 785 256" class="stroke-loop spec-loop-anim" marker-end="url(#arrow)"/>
    <path d="M 815 267 Q 815 286 745 306"
          class="stroke-loop spec-loop-anim" marker-end="url(#arrow)"/>
    <path d="M 685 306 Q 615 286 615 267"
          class="stroke-loop spec-loop-anim" marker-end="url(#arrow)"/>
  </g>

  <!-- arrow marker definition -->
  <defs>
    <marker id="arrow" viewBox="0 0 8 8" refX="6" refY="4"
            markerWidth="6" markerHeight="6" orient="auto">
      <path d="M 0 0 L 8 4 L 0 8 z" fill="#1A2418"/>
    </marker>
  </defs>

  <!-- decay numbers -->
  <text x="660" y="284" text-anchor="middle" class="label-decay">−13%</text>
  <text x="760" y="284" text-anchor="middle" class="label-decay">−16%</text>
  <text x="660" y="288" text-anchor="middle" class="label-decay" transform="translate(165,46)">−17%</text>

  <!-- alignment label (decays) -->
  <text x="530" y="334" class="label-day">alignment:</text>
  <text x="600" y="334" class="label-svg" style="fill:#7A7264;">100% → 54%</text>
  <text x="720" y="334" class="label-decay">handoffs · async · async · async</text>

  <!-- footnote -->
  <text x="530" y="350" class="label-decay" style="font-style: italic;">
    decay % illustrative — see methodology/09 for full comparison
  </text>
</svg>
```

> **Inline size:** SVG outputuje cca 6.8 KB (raw, neminifikováno). Po
> minifikaci ~5.4 KB. Pod 50 KB budget bez problémů.

### 2.2 Inline CSS (frame + hover)

Doplnit do `<style>` v `website/index.html` (ideálně poblíž `.flow-frame`,
re-use stejných tokenů):

```css
/* ─────── Spec-driven trap section ─────── */
.trap-section {
  /* uses existing section padding */
}
.trap-frame {
  border: 1.5px solid var(--ink);
  background: var(--paper);
  position: relative;
  padding: clamp(1.5rem, 3vw, 2.5rem);
}
.trap-frame .flow-meta {            /* re-use class for visual parity */
  display: flex;
  justify-content: space-between;
  border-bottom: 1px solid var(--line);
  padding-bottom: 0.8rem;
  margin-bottom: 1.4rem;
}
.trap-frame .flow-meta span {
  font-size: 10.5px;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  color: var(--gray);
}
.trap-svg-wrap {
  overflow-x: auto;
  overflow-y: hidden;
  margin: 0 -0.5rem;
  padding: 1rem 0.5rem;
}
.trap-svg-wrap svg {
  display: block;
  min-width: 760px;       /* ensures readability, scrolls horizontally on mobile */
  width: 100%;
  height: auto;
}

/* hover: deepen the punch bloom on Pflanzer side */
.trap-svg-wrap:hover .fill-punch {
  fill: #B4D838;
  transition: fill 0.3s ease;
}

/* breakdown table under SVG — mirrors .flow-stages grid */
.trap-breakdown {
  display: grid;
  grid-template-columns: 1fr 1fr;
  column-gap: 1.5rem;
  margin-top: 1.5rem;
  border-top: 1.5px solid var(--ink);
  padding-top: 1.2rem;
}
.trap-breakdown > div { display: flex; flex-direction: column; gap: 0.4rem; }
.trap-breakdown .col-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--moss);
  font-weight: 600;
}
.trap-breakdown .col-name {
  font-family: 'Fraunces', Georgia, serif;
  font-variation-settings: 'SOFT' 80, 'opsz' 36;
  font-weight: 500;
  font-size: 1.05rem;
  line-height: 1.15;
  letter-spacing: -0.012em;
}
.trap-breakdown .col-desc {
  font-size: 12.5px;
  line-height: 1.5;
  color: var(--ink);
}
.trap-breakdown .col-tags {
  margin-top: 0.6rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}
.trap-breakdown .col-tags span {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  padding: 0.25rem 0.5rem;
  border: 1px solid var(--line-bold);
  background: var(--bone);
  color: var(--moss);
}
.trap-breakdown .col-sdd .col-tags span { color: var(--gray); }

/* punchline */
.trap-punchline {
  margin-top: 2rem;
  padding: 1.6rem 1.8rem;
  background: var(--ink);
  color: var(--bone);
  font-family: 'Fraunces', Georgia, serif;
  font-variation-settings: 'SOFT' 100, 'WONK' 1, 'opsz' 96;
  font-style: italic;
  font-weight: 300;
  font-size: clamp(1.4rem, 2.4vw, 1.9rem);
  line-height: 1.25;
  letter-spacing: -0.018em;
}
.trap-punchline em {
  color: var(--punch);
  font-style: italic;
}

/* responsive */
@media (max-width: 840px) {
  .trap-breakdown { grid-template-columns: 1fr; row-gap: 1.4rem; }
}

/* print */
@media print {
  .trap-svg-wrap svg { min-width: 100%; max-height: 6cm; }
  .trap-punchline { background: var(--bone); color: var(--ink); border: 1.5px solid var(--ink); }
  .trap-punchline em { color: var(--moss); }
}
```

### 2.3 Accessibility

- **`<svg role="img">`** + `aria-label` shrne, co diagram říká (čtečka
  obrazovky dostane jednovětný popis bez kreslení).
- **Kontrast**: ink na bone = ~14.3:1 (AAA). Moss na bone = ~7.2:1 (AAA).
  Gray na bone = ~4.6:1 (AA pro normal text). Punch jen jako fill květu,
  ne jako foreground text.
- **`prefers-reduced-motion`** vypne loop animaci.
- **Keyboard nav**: SVG je purely informativní, není interaktivní (ne
  buttony), takže focus management irrelevantní. Tagy v breakdown jsou
  `<span>` (ne `<button>`), text-only.
- **Lang switching**: každý label uvnitř SVG je v EN (univerzální IT termíny:
  „spec", „app", „prod"). CS/EN copy je v HTML wrapper, ne v SVG, aby
  jeden SVG sloužil oběma jazykům.

---

## 3. Nová section — *„Past spec-drivenu" / „The Spec-Driven Trap"*

### 3.1 Pozice v layoutu

Aktuální posloupnost:

```
hero
00 manifesto
persona routing
01 botanical flow
02 USPs + evidence + limitations
#srovnani comparison matrix
03 field notes e-shop
#cena pricing
04 CTA
```

**Návrh:** vložit jako **02b** mezi 02 (USPs) a `#srovnani`. Logická
linka:

> 02 *„Pět věcí, které nikdo jiný nedělá"* (proč jsme jiní)
> → **02b *„Past spec-drivenu"*** (proč konkurenční myšlenkový směr selhává)
> → `#srovnani` *„5 metod, jeden řádek"* (kam přesně do mapy patříme)

Toto čte líp než skok rovnou ze USPs do feature matrice. Sekce 02b je
**most ze argumentu do tabulky**.

**Číslování:** ponechat 02 jako USPs, novou označit **02b** — žádné
přečíslování dalších sekcí (03, 04). Nebo pokud vadí half-step, posunout
USPs na 02, novou na 03, Field Notes na 04, CTA na 05. **Doporučení: 02b**
(menší diff, brand precedent — sekce už mívají `b/c` suffixy).

### 3.2 Plný HTML markup (sekce)

```html
<hr class="rule">

<!-- ─────── 02b SPEC-DRIVEN TRAP ─────── -->
<section id="spec-trap" class="trap-section">
  <div class="wrap">
    <div class="section-head">
      <div class="num-tag">02<em style="font-variation-settings: 'SOFT' 100, 'WONK' 1; font-style: italic; font-weight: 300; opacity: 0.65;">b</em></div>
      <h2 class="h-section lang-cs">
        Past <em>spec-drivenu.</em>
      </h2>
      <h2 class="h-section lang-en">
        The spec-driven <em>trap.</em>
      </h2>
      <div class="label-meta label">
        <span class="lang-cs">Kontrast · proč ne SDD</span>
        <span class="lang-en">Contrast · why not SDD</span>
      </div>
    </div>

    <p class="lang-cs" style="font-size: 15px; line-height: 1.7; max-width: 62ch; margin-bottom: 2rem;">
      Spec-Driven Development — Spec Kit, Kiro, OpenSpec, BMAD — říká:
      <em>„Nejdřív specka, pak kód."</em> V korporátu to zní zodpovědně.
      Realita: <strong>app → specka → dev → další app, která se liší → pinking →
      cyklus se prodlouží.</strong> Pflanzer dělá opačnou věc — artefakt
      v místnosti od minuty 0, specka padá ven jako vedlejší produkt.
    </p>
    <p class="lang-en" style="font-size: 15px; line-height: 1.7; max-width: 62ch; margin-bottom: 2rem;">
      Spec-Driven Development — Spec Kit, Kiro, OpenSpec, BMAD — says:
      <em>„Spec first, code second."</em> In the enterprise it sounds
      responsible. The reality: <strong>app → spec → dev → a different app →
      ping-pong → the cycle gets longer.</strong> Pflanzer flips it —
      the artifact is in the room from minute zero, the spec falls out
      as a by-product.
    </p>

    <div class="trap-frame">
      <div class="flow-meta">
        <span>
          <span class="lang-cs">Fig. 02b — Dvě rostliny, jedna ve smyčce</span>
          <span class="lang-en">Fig. 02b — Two plants, one stuck in a loop</span>
        </span>
        <span>
          <span class="lang-cs">Pflanzer vs Spec-Driven · ilustrativní</span>
          <span class="lang-en">Pflanzer vs Spec-Driven · illustrative</span>
        </span>
      </div>

      <div class="trap-svg-wrap" aria-label="Two plants side-by-side: Pflanzer grows seed to bloom in 14 days; Spec-Driven loops underground between spec and app, never blooms.">
        <!-- INSERT SVG FROM SECTION 2.1 HERE -->
      </div>

      <div class="trap-breakdown">
        <div class="col-pflanzer">
          <div class="col-label">Pflanzer · artifact-first</div>
          <div class="col-name lang-cs">Jeden artefakt. Šest hlav. Stejná místnost.</div>
          <div class="col-name lang-en">One artifact. Six heads. Same room.</div>
          <div class="col-desc lang-cs">
            Funkční klikací prototyp od hodiny 1. Security, Legal, DPO
            čtou ten samý URL, ne PDF se speckou. Specka se generuje
            <em>po</em> sezení jako audit log, ne před.
          </div>
          <div class="col-desc lang-en">
            A working clickable prototype from hour 1. Security, Legal,
            DPO read the same URL — not a PDF spec. The spec is generated
            <em>after</em> the session as an audit log, not before.
          </div>
          <div class="col-tags">
            <span>same room</span>
            <span><span class="lang-cs">alignment roste</span><span class="lang-en">alignment compounds</span></span>
            <span>D14 → prod</span>
          </div>
        </div>

        <div class="col-sdd">
          <div class="col-label">Spec-Driven · spec-first</div>
          <div class="col-name lang-cs">Specka. Dev. App, která se liší. Specka'.</div>
          <div class="col-name lang-en">Spec. Dev. An app that diverges. Spec'.</div>
          <div class="col-desc lang-cs">
            Každý předací krok ztrácí kontext (PM → spec → dev → app, kde
            spec ≠ app). Pinking začne v týdnu 3. Compliance audit do
            specky <em>nepronikne</em> — kontroluje papír, ne live URL.
          </div>
          <div class="col-desc lang-en">
            Every handoff loses context (PM → spec → dev → an app that
            differs from spec). Ping-pong kicks in by week 3. The
            compliance audit <em>never reaches</em> the spec — it inspects
            paper, not a live URL.
          </div>
          <div class="col-tags">
            <span>handoff decay</span>
            <span><span class="lang-cs">spec ≠ app</span><span class="lang-en">spec ≠ app</span></span>
            <span>T+? · loop</span>
          </div>
        </div>
      </div>
    </div>

    <div class="trap-punchline">
      <span class="lang-cs">
        Specka je <em>nájemné.</em> Artefakt je <em>vlastnictví.</em>
        Pflanzer staví artefakty.
      </span>
      <span class="lang-en">
        A spec is <em>rent.</em> An artifact is <em>equity.</em>
        Pflanzer builds artifacts.
      </span>
    </div>

    <p style="margin-top: 1.4rem; font-size: 12px; color: var(--gray); max-width: 70ch;">
      <span class="lang-cs">
        Detail per SDD nástroj (Spec Kit · Kiro · OpenSpec · BMAD) +
        rozhodovací strom v
        <a class="link-underline" href="https://github.com/" target="_blank" rel="noopener">repo</a>
        — <code>docs/research/spec-driven-vs-pflanzer/</code>.
      </span>
      <span class="lang-en">
        Per-tool detail (Spec Kit · Kiro · OpenSpec · BMAD) + decision tree in the
        <a class="link-underline" href="https://github.com/" target="_blank" rel="noopener">repo</a>
        — <code>docs/research/spec-driven-vs-pflanzer/</code>.
      </span>
    </p>
  </div>
</section>
```

### 3.3 Body text — finální copy

**Czech:**

> **Past spec-drivenu.**
>
> Spec-Driven Development — Spec Kit, Kiro, OpenSpec, BMAD — říká:
> *„Nejdřív specka, pak kód."* V korporátu to zní zodpovědně.
>
> Realita: **app → specka → dev → další app, která se liší → pinking →
> cyklus se prodlouží.** Každý handoff je ztráta kontextu. Spec dokument
> nikdy nedohoní live URL — a compliance audit kontroluje *papír*, ne
> klikatelný artefakt.
>
> Pflanzer dělá opačnou věc: **artefakt v místnosti od minuty 0**. Šest
> lidí, jedna URL. Specka padá ven jako vedlejší produkt — po sezení,
> ne před ním. Audit log se píše sám.
>
> Specka je nájemné. Artefakt je vlastnictví.

**English:**

> **The spec-driven trap.**
>
> Spec-Driven Development — Spec Kit, Kiro, OpenSpec, BMAD — says:
> *„Spec first, code second."* In the enterprise it sounds responsible.
>
> The reality: **app → spec → dev → a different app → ping-pong →
> the cycle gets longer.** Every handoff loses context. The spec doc
> never catches up to the live URL — and the compliance audit reviews
> *paper*, not a clickable artifact.
>
> Pflanzer flips it: **the artifact is in the room from minute zero.**
> Six people, one URL. The spec falls out as a by-product — after the
> session, not before. The audit log writes itself.
>
> A spec is rent. An artifact is equity.

---

## 4. Claude best practices — citace pro autoritu

> **Účel:** přidat 2–3 mikro-citace přímo do sekce 02b (border-left
> stylem, jako už děláme u USP 02 a 03 s peer-review opora). Posiluje
> argument *„toto není jen náš názor, Anthropic engineering tým to
> dokumentuje."*

### 4.1 Multi-perspective parallel workshops (paralela k Pflanzer 6 lidem)

> *„The lead agent spins up 3–5 subagents in parallel rather than serially.
> Subagents facilitate compression by operating in parallel with their
> own context windows, exploring different aspects of the question
> simultaneously."*
>
> **Anthropic Engineering, *How we built our multi-agent research
> system*, červen 2025.**
> https://www.anthropic.com/engineering/multi-agent-research-system

**Použití v sekci:** mikro-quote pod col-pflanzer, vysvětluje, proč
6 lidí v místnosti = compounding, ne overhead.

### 4.2 Artifact-first communication (paralela k „jeden artefakt v místnosti")

> *„Communication was handled via files: one agent would write a file,
> another agent would read it and respond either within that file or a
> new file that the previous agent would read in turn."*
>
> **Anthropic Engineering, *Harness design for long-running application
> development*, 2026.**
> https://www.anthropic.com/engineering/harness-design-long-running-apps

**Použití:** mikro-quote pod col-pflanzer, vysvětluje, proč artefakt
(file / URL) > spec dokument.

### 4.3 Spec-driven scope discipline (paralela k „nepřespecifikovat předem")

> *„I prompted it to be ambitious about scope and to stay focused on
> product context and high level technical design rather than detailed
> technical implementation."*
>
> **Anthropic Engineering, *Harness design for long-running application
> development*, 2026.**
> https://www.anthropic.com/engineering/harness-design-long-running-apps

**Použití:** mikro-quote pod col-sdd jako kontrast — *„i Anthropic
deliberately nepřespecifikuje, Spec-Driven dělá opak."*

### 4.4 Trust-but-verify (paralela k Pflanzer quality gates ≥80/100)

> *„Even on tasks that do have verifiable outcomes, agents still sometimes
> exhibit poor judgment… Separating the agent doing the work from the
> agent judging it proves to be a strong lever."*
>
> **Anthropic Engineering, *Harness design for long-running application
> development*, 2026.**
> https://www.anthropic.com/engineering/harness-design-long-running-apps

**Použití:** **NE v sekci 02b**, ale jako mikro-quote do USP 03
(„Mezi líbí se mi a commitnu") — posiluje argument, že **silent voting
+ veto rights = separation of work and judgment**.

### 4.5 Decision attribution / audit trail (paralela k AI Act čl. 14)

> *„Every Claude API call is attributable to a federation rule + service
> account in the audit trail."*
>
> **Anthropic, *Hardening Guide*, 2026.**
> https://howtoharden.com/guides/anthropic-claude/

**Použití:** posílení USP 02 (AI Act compliance) — *„i Anthropic sám
buduje atribuci na API úrovni, my ji budujeme na decision úrovni."*

### 4.6 Implementace v HTML (mikro-citace block)

```html
<!-- pod col-pflanzer description -->
<p style="font-size: 11.5px; color: var(--gray); border-left: 2px solid var(--moss);
          padding-left: 0.7rem; margin-top: 0.8rem; line-height: 1.5;">
  <strong style="color: var(--ink);">Engineering precedent:</strong>
  <em>„Communication was handled via files: one agent would write a file,
  another would read it and respond."</em>
  <br>
  <span style="color: var(--gray);">— Anthropic Engineering,
    <a class="link-underline" href="https://www.anthropic.com/engineering/harness-design-long-running-apps" target="_blank" rel="noopener">Harness design</a>, 2026.</span>
</p>
```

---

## 5. Integration plan — kde, co, jak

### 5.1 `website/index.html` — sekce 02b

**Diff:**

- Najít `<!-- ─────── COMPARISON MATRIX ─────── -->` (řádek ~1802).
- **Vložit před** novou sekci 02b dle § 3.2 (cca 90 řádků HTML).
- **Doplnit CSS** dle § 2.2 (cca 80 řádků, ideálně poblíž `.flow-frame`
  bloku — řádek ~358).
- **Update `.frame-top`** breadcrumb (řádek ~165): doplnit
  `<span class="hide-sm">02b · TRAP</span>` mezi 02 a 03.

**Risk:** žádný — sekce je čistá addice, neporušuje existující grid
ani anchor IDs.

### 5.2 `#srovnani` comparison matrix — přidat SDD řádek

**Současné řádky:** Pflanzer · AWS AI-DLC · Thoughtworks 3-3-3 ·
McKinsey QuantumBlack · Design Sprint 2.0.

**Doplnit jako 6. řádek:**

```html
<tr>
  <td><span class="lang-cs">Spec Kit / Kiro / OpenSpec / BMAD</span><span class="lang-en">Spec Kit / Kiro / OpenSpec / BMAD</span></td>
  <td><span class="lang-cs">Variable · spec iteration</span><span class="lang-en">Variable · spec iteration</span></td>
  <td><span class="lang-cs">Solo dev + AI (no humans)</span><span class="lang-en">Solo dev + AI (no humans)</span></td>
  <td><span class="lang-cs">Žádný</span><span class="lang-en">None</span></td>
  <td><span class="lang-cs">Free (OSS)</span><span class="lang-en">Free (OSS)</span></td>
  <td><span class="lang-cs">Spec doc + code</span><span class="lang-en">Spec doc + code</span></td>
</tr>
```

**Tagline změna:** přepsat lead text matrice z *„5 metod, jeden řádek"*
na *„6 metod, jeden řádek"*.

### 5.3 `1-pager.html` — A4 print

**Diff:** A4 layout je tight, nepřidávat plný diagram. Místo toho **2-line
quote box** vedle existující e-shop field-note:

```html
<aside class="print-callout" style="border: 1px solid var(--ink);
       padding: 0.5rem 0.7rem; margin-top: 0.5rem;">
  <span style="font-family: 'JetBrains Mono', monospace; font-size: 7pt;
        text-transform: uppercase; letter-spacing: 0.12em; color: var(--gray);">
    Vs Spec-Driven
  </span>
  <p style="font-family: 'Fraunces', serif; font-size: 9pt; font-style: italic;
     margin-top: 0.2rem; line-height: 1.3;">
    „Specka je nájemné. Artefakt je vlastnictví."
    <br>
    Pflanzer staví artefakt od hodiny 1, ne dokument.
  </p>
</aside>
```

**Risk:** zabere ~3 cm v print layoutu. Pokud A4 padá přes okraj, vyhodit
nejméně load-bearing kus (např. jednu evidence kartu).

### 5.4 USPs sekce — drobný update

V USP 01 („Non-tech v místnosti") přidat krátkou kontrastní větu do
descu:

```html
<p style="font-size: 12px; color: var(--gray); margin-top: 0.6rem;">
  <em><span class="lang-cs">→ Srov.: Spec Kit / Kiro vyžadují, aby tě
     compliance přečetla v PDF až po dev fázi. Past spec-drivenu.</span>
  <span class="lang-en">→ Cf.: Spec Kit / Kiro require compliance to read
     a PDF after the dev phase. The spec-driven trap.</span></em>
  <a class="link-underline" href="#spec-trap" style="font-style: normal;">
    <span class="lang-cs">Viz 02b</span><span class="lang-en">See 02b</span>
  </a>
</p>
```

### 5.5 Manifesto 00 — žádná změna

Nemíchat. Manifesto je vize, ne argument. Sekce 02b je argumentní.

### 5.6 Persona routing — žádná změna

Routing slouží jako navigace dle role (engineer / security / sponsor).
Sekce 02b je relevantní pro **engineering manager** a **sponsor** —
oba už mají routing entrypoint do USPs. 02b dostanou skrolováním.

### 5.7 Anchor & SEO

- ID: `#spec-trap` (krátké, sémantické).
- `<meta name="description">` v `<head>`: žádný update (manifest claim
  zůstává).
- Pokud se chceme rankovat na *„spec-driven development critique"* /
  *„artifact-first vs spec-driven"*, doporučení: vytvořit
  `docs/research/spec-driven-vs-pflanzer/01-summary.md` jako veřejnou
  landing entry a linkovat z `#spec-trap` footer.

---

## 6. Tagline kandidáti (8 + 8)

### Czech

1. *„Specka je nájemné. Artefakt je vlastnictví."* — **TOP pick**, brand-y,
   ekonomická metafora, memorable.
2. *„Past spec-drivenu: pinking je drahé."*
3. *„Místo specky funkční kód."*
4. *„Specka nikdy nedohoní live URL."*
5. *„Spec-driven: papír. Pflanzer: artefakt."*
6. *„Když specka roste, alignment klesá."*
7. *„Spec-first je late-stage compliance veto."*
8. *„Specka padá ven, ne dovnitř."* (Pflanzer-specific direction)

### English

1. *„Specs decay. Artifacts compound."* — **TOP pick**, parallel structure,
   technical credibility.
2. *„Spec-driven? Ping-pong is expensive."*
3. *„Skip the spec. Ship the code."*
4. *„The spec never catches the live URL."*
5. *„Spec-driven is a paper review. Pflanzer is a URL review."*
6. *„The longer the spec, the wider the gap."*
7. *„Spec-first is late-stage compliance veto."*
8. *„The spec falls out, it doesn't fall in."*

### Doporučení k použití

- **Hero / wordmark area**: nezasahovat (manifesto claim stay).
- **Sekce 02b punchline**: CS *„Specka je nájemné. Artefakt je
  vlastnictví."* / EN *„Specs decay. Artifacts compound."* — to už je
  v § 3.2 markup.
- **OG image / social card**: EN *„Specs decay. Artifacts compound."* +
  botanical SVG.
- **CTA hover state** (long-term experiment): A/B test mezi
  *„Skip the spec. Ship the code."* a current CTA copy.

---

## 7. Reference & sources

### Anthropic engineering (primary)

- Anthropic Engineering, *How we built our multi-agent research system*,
  Jun 2025 — https://www.anthropic.com/engineering/multi-agent-research-system
- Anthropic Engineering, *Harness design for long-running application
  development*, 2026 — https://www.anthropic.com/engineering/harness-design-long-running-apps
- Anthropic, *Claude Code product page*, 2026 — https://www.anthropic.com/product/claude-code
- Anthropic, *Hardening Guide* (community-mirrored), 2026 — https://howtoharden.com/guides/anthropic-claude/

### Spec-Driven Development sources (for comparison fairness)

- GitHub Spec-Kit — https://github.com/github/spec-kit
- Scalable Path, *Beyond Vibe-Coding: A Practical Guide to Spec-Driven
  Development* — https://www.scalablepath.com/machine-learning/spec-driven-development-guide
- AgentFactory, *Chapter 16: Spec-Driven Development with Claude Code* —
  https://agentfactory.panaversity.org/docs/General-Agents-Foundations/spec-driven-development

### Multi-agent / sub-agents 2026 context

- MindStudio, *Code with Claude 2026: 5 New Agent Features Anthropic
  Just Shipped* — https://www.mindstudio.ai/blog/code-with-claude-2026-new-agent-features
- AI Builder Club, *Claude Code Sub-Agents Guide (2026)* —
  https://www.aibuilderclub.com/blog/claude-code-sub-agents-guide
- CloudZero, *Claude Code Agents In 2026: Subagents, Teams, And What
  Parallel Sessions Actually Cost* — https://www.cloudzero.com/blog/claude-code-agents/

### Internal repo

- `docs/methodology/09-srovnani-existujici-metody.md` — comparison master
- `docs/research/competitive/04-synthesis-and-positioning.md` — positioning
- `docs/research/external-validation/` — peer-review opora
- (po merge) `docs/research/spec-driven-vs-pflanzer/01-summary.md` —
  detailed per-tool breakdown (Spec Kit · Kiro · OpenSpec · BMAD), TBD

---

## 8. Acceptance checklist (pro implementaci)

- [ ] SVG validuje v W3C SVG Validator (žádné syntaktické chyby).
- [ ] Total inline page weight under 60 KB delta vs current.
- [ ] Lighthouse a11y score zůstává ≥ 95 (testovat po merge).
- [ ] Print preview (Chrome DevTools → emulate print) — sekce 02b se vejde
      na 1 stránku, žádné overflow.
- [ ] `prefers-reduced-motion` test — loop animace se zastaví.
- [ ] CS/EN switch funguje na všech nových `<span class="lang-cs|lang-en">`.
- [ ] Anchor `#spec-trap` funguje z nav i z USP 01 inline linku.
- [ ] Comparison matrix obsahuje 6. řádek (Spec Kit / Kiro / OpenSpec / BMAD).
- [ ] Lead text comparison matrix přepsán z „5 metod" na „6 metod".
- [ ] 1-pager A4 stále vyjde na 1 stránku po přidání print-callout.
- [ ] Mikro-quote Anthropic engineering pod col-pflanzer obsahuje URL +
      datum.

---

*v0.1 — 2026-05-28 — Tom Pflanzer (Claude assist)*
