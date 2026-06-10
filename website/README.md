# Pflanzer Method — Marketing website

Single-page distinctive marketing site pro Pflanzerovu metodu. Žádný build step,
žádný framework, pure HTML + CSS + jeden inline SVG diagram.

**Bilingual:** CS (default) + EN. Switcher v top-right rohu, persistuje přes
`localStorage`. URL param `?lang=en` přepíše. Implementováno přes
`.lang-cs` / `.lang-en` CSS visibility toggle — žádný build, žádná i18n knihovna.

## Aesthetic

**Editorial Botanical Brutalism** — manuscript-style typography, hard grid,
botanical line-drawings místo generic AI tropes. Pflanzer = německy „pěstitel" —
metoda vizualizovaná jako rostlina od semínka po květ.

- **Display font:** [Fraunces](https://fonts.google.com/specimen/Fraunces) (variable, WONK + SOFT osy) — editorial, lehce „nedokonalá" v italics
- **Body font:** [JetBrains Mono](https://fonts.google.com/specimen/JetBrains+Mono) — mechanická, technická
- **Palette:** bone paper (#F4EFE6) + ink (#1A2418) + moss (#2F4A2F) + punch chartreuse (#C7E84A)
- **Texture:** subtle SVG paper grain overlay

## Bold varianty (drafty k výběru)

Tři alternativní bold směry — jednoduché na pochopení, výrazné v expresi,
každá obsahuje srovnání se spec-driven vývojem. Všechny nesou brand lockup
`Pflanzer Method | pflanzer.cz/method`, jsou self-contained (žádný build),
CS-only.

| Soubor | Směr | Anchor (co si zapamatuješ) |
|--------|------|----------------------------|
| `bold-poster.html` | **Signal Poster** — švýcarský typografický plakát; papír + ink + signální červená; Archivo Black + Space Mono | Obří „SPECKA." přeškrtnutá animovaným červeným tahem fixy → „PRODUKT." |
| `bold-duel.html` | **Duel** — celá stránka je split-screen souboj: šedý svět specky vlevo, Pflanzer noc + chartreuse vpravo; Syne + IBM Plex Mono | Sticky „VS" šev uprostřed; 270 dní vs. 14 dní v hero |
| `bold-terminal.html` | **Session** — pitch jako terminálový přepis `/pm` session; fosforová zelená, CRT scanlines; JetBrains Mono | Hero terminál „odehraje" celých 14 dní; srovnání jako `git diff` (− specka / + pflanzer) |
| `bold-hybrid.html` | **Poster × Session** (favorit) — plakátový vizuál A + terminálové prvky z C; scroll-reveal animace, count-up čísla, kreslící se timeline, FAQ | Timeline 14 dní = rostoucí rostlina (semínko → květ, Pflanzer = pěstitel); hero terminál + přeškrtnutá SPECKA |

## Sekce

- `00` — Manifesto (proč metoda vznikla, handoff hell)
- `01` — Botanická vizualizace 2-session flow (semínko → výhonek → list → stonek → květ)
- `02` — 3 USPs (funkční kód, anti-HiPPO, cross-funkční místnost)
- `03` — Field notes / e-shop case study mention
- `04` — CTA + proč teď

## Deploy

### Lokální preview

```bash
cd website
python3 -m http.server 8000
# otevři http://localhost:8000
```

### Static hosting

Soubor `index.html` je self-contained (Google Fonts CDN, žádné build artefakty).
Nahraj na:

- **GitHub Pages** — povol Pages na `/website` directory v repo settings
- **Vercel / Netlify** — drag-and-drop deploy
- **Cloudflare Pages** — connect repo, root directory `website`
- **FTP na claude.gizmax.cz** — viz globální CLAUDE.md upload command

### FTP deploy (pflanzer.gizmax.cz subdomain)

```bash
curl -T website/index.html --user "claude.gizmax.cz:***REDACTED***" \
  "ftp://ftp.gizmax.cz/pflanzer/index.html"
```

(Předpokládá subdoménový mapping `pflanzer.gizmax.cz` → `/pflanzer/` na FTP.)

## Před produkčním deployem TODO

- [ ] Aktualizovat GitHub URL v `<a href="https://github.com/">` (3 výskyty)
  na skutečnou repo URL po publikaci
- [ ] Pokud nasazujeme na `*.gizmax.cz` doménu → přidat GA4 snippet
  (`G-ZN1K4G2TCZ` per global CLAUDE.md):
  ```html
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-ZN1K4G2TCZ"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', 'G-ZN1K4G2TCZ');
  </script>
  ```
- [ ] OG image + Twitter card meta (placeholder zatím chybí)
- [ ] e-shop case study — buď anonymizovat dále, nebo požádat o explicitní
  souhlas s veřejnou referencí
- [ ] Favicon (SVG sprout icon je k mání v hero punchmark)
- [ ] Případně doménová varianta `.en` pro anglickou verzi

## Performance

- Self-contained HTML (~38 KB unminified)
- 2 Google Fonts (preconnect + preload doporučeno pokud bude critical)
- 1 inline SVG (~7 KB), žádné externí obrázky
- Zero JS framework

## Lottie animace (bold-hybrid)

`bold-hybrid.html` má v CTA sekci animaci růstu rostliny
(`plant-lottie.json`, ~9 kB, generováno skillem `text-to-lottie`
z `diffusionstudio/lottie`, instalován v `.agents/skills/`).

- Přehrávač: `lottie_light.min.js` z cdnjs (~150 kB, lazy: SVG renderer)
- Spouští se přes IntersectionObserver, hraje jednou, drží poslední frame
- `prefers-reduced-motion`: skočí rovnou na rozkvetlý poslední frame
- Když CDN nejede, sekce zůstane bez animace, nic se nerozbije
- Regenerace: viz `.agents/skills/text-to-lottie/SKILL.md`, JSON se dá
  upravit i ručně (vrstvy: ground, seed, stem, 4× leaf, 5× petal, center)

## Accessibility

- Semantic HTML (`header`, `section`, `footer`, `h1`–`h3`)
- SVG má `role="img"` + `aria-label`
- Color contrast WCAG AA pro body text
- `prefers-reduced-motion` respektován
- Focus states inherent (no custom focus killer)
- Keyboard navigable

## Why this design avoids generic UI

| Generic AI/SaaS                       | Pflanzer site                                |
|---------------------------------------|----------------------------------------------|
| Inter/Roboto sans body                | JetBrains Mono — mechanical contrast         |
| Centered hero, gradient bg            | Asymmetric editorial grid, paper texture     |
| Rounded card grid (3 columns)         | Numbered manuscript sections + 12-col grid   |
| Purple/blue SaaS palette              | Bone + ink + chartreuse (botanical-industrial) |
| Stock illustrations / hero image      | Inline botanical SVG diagram of method       |
| „Get started" CTA in soft button      | Hard-edge `btn` with arrow + monospace label |
| Smooth scroll animations              | Single staggered hero entrance, rest static  |
