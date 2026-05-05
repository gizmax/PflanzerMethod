# Vibe-coding & rapid-prototype tooling 2026

Rešerše pro Pflanzerovu metodu — cross-functional workshop s AI co-pilotem,
výstupem 1–3 prototypy, mezi-session scored feedback od stakeholderů.
Cílem je posoudit, zda existující nástroj pokrývá use-case, nebo bude potřeba
vlastní orchestrace.

Pflanzer má tři klíčové požadavky, které žádný z níže uvedených toolů
nepokrývá nativně v plném rozsahu:

1. **Multi-version A/B/C** generace ze stejného briefu, side-by-side compare.
2. **Shareable preview link** pro stakeholdery bez accountu.
3. **Inline scored feedback** (rating + comment) s agregací napříč variantami.

---

## Nástroje — srovnávací matice

| Tool | Fullstack? | Multi-version compare | Public share link | Inline feedback | Code export | Stack |
|---|---|---|---|---|---|---|
| **v0.app** (Vercel) | Ano (Feb 2026: Git, DB, agentic) | Forky šablon, `versions` v chatu, žádný side-by-side UI | Ano (deployed URL) | Ne (komentáře jen v Vercel Toolbar přes Vercel hosting) | Ano (Next/React/Tailwind/shadcn) | Next.js, React, Tailwind, shadcn |
| **Bolt.new** (StackBlitz) | Ano (Bolt Cloud: DB, auth, storage, edge fns) | Ne (token-based linear iterace) | Ano (1-click deploy URL) | Ne nativně | Ano (download/GitHub) | React, Vue, Next, Astro, Svelte, Remix, Supabase |
| **Lovable** | Ano (Supabase + Stripe nativně) | Ne (lineární; Visual Edits klik-edit) | Ano (preview URL bez loginu) | Komentáře v paid Workspace | Ano (GitHub sync) | React/Vite + Supabase |
| **Figma Make** | Hybrid (interaktivní prototypy, ne deploy backend) | Make produkuje varianty; lze postavit do Slides/Design vedle sebe | Ano (Figma share, paid pro restricted) | **Nativní comments + reactions** v Figmě | Ano (HTML/React přes export, MCP do Cursor/VS Code) | React/HTML + Make Kits |
| **Google Stitch** | Jen UI (export do Firebase Studio pro deploy) | Ano — 5-screen canvas, generuje varianty side-by-side | Ano (Share Project, public remix) | Ne (jen voice canvas critique) | Ano (HTML/CSS, Tailwind, Vue, Angular, Flutter, SwiftUI) | Multi-framework export |
| **Claude Artifacts** | Ne (single-file SPA, KV store) | Ne nativně, ale lze paralelně otevřít víc Artifactů v Projects | Ano (Publish, viewer bez accountu) | Ne (jen remix/fork) | Manual copy-paste; Code-grade artifact | React + Tailwind (sandbox) |
| **Cursor Composer 2** | Ano (full IDE, agent mode) | **Ano — `/best-of-n` spustí stejný task přes víc modelů, každý ve worktree** | Ne (lokální IDE) | Ne | Plný kód (je to IDE) | Anything |
| **Replit Agent 3** | Ano (DB, auth, deploy, monitoring) | Ne (effort-based checkpoints, lineární) | Ano (deployed URL) | Collaborators (5 v Core / 50 viewers v Pro) | Ano (download/GitHub) | Anything (Python/Node/React) |
| **GitHub Spark** | Ano (KV store na Cosmos, auth, AI features) | Ne | Ano (deploy + share + remix) | Ne nativně | Ano (TS/React, GitHub repo) | TypeScript + React |
| **Tempo Labs** | Ano (React-only, MCP App Store integrace) | Drag-drop visual + chat — žádné A/B side-by-side | Ano (preview deploy) | Visual collaboration v editoru | Ano (full React export) | React |
| **Builder.io Visual Copilot / Fusion** | Hybrid (mapuje na vaše komponenty/repo) | Ne (Figma → kód workflow) | Ano (preview) | Komentáře v Builder | Ano (React/Vue/Svelte/Angular/Qwik/Solid/HTML) | Multi-framework |

---

## Pricing — krátce (2026)

| Tool | Free | Paid entry | Pro/Team |
|---|---|---|---|
| v0.app | $5 kreditů | Premium $20/m | Team $30/seat, Business $100/seat |
| Bolt.new | Limit free | Hobby $20/m | Pro $50/m |
| Lovable | 5 daily / 30 mo | Starter $25/m | Workspace + Enterprise |
| Figma Make | součást Figma Starter (500 kr.) | Pro $15/seat (3000 kr.) | Org $55, Ent $90 |
| Google Stitch | **Free** (350+200 gen/měs) | — | — |
| Claude Artifacts | součást Claude.ai Free | Pro $20/m | Team/Enterprise |
| Cursor | Hobby free | Pro $20/m | Pro+ $60, Ultra $200, Teams $40/seat |
| Replit | Starter free | Core $17/m | Pro $100/m (15 builders) |
| GitHub Spark | Tech preview free | **Pro+ $39/m** povinné | Enterprise $39/seat |
| Tempo | Free (limited) | Pro ~$30/m | Agent+ $4500/m |
| Builder.io VC | Free trial | Custom | Enterprise |

---

## Strengths / weaknesses pro corporate workshop

**v0.app** — Production-grade Next.js + shadcn, Snowflake/AWS DB konektory pro enterprise apps. Žádná stakeholder-friendly preview vrstva, comments jen přes Vercel Toolbar (vyžaduje účet). Multi-version je jen forking.

**Bolt.new** — Nejširší stack support (Vue/Astro/Svelte), agentic V2 fixuje chyby sám, 1-click deploy URL. Token náklady při debug-loop nepředvídatelné, žádný feedback layer.

**Lovable** — Workspace + Visual Edits = nejblíž "Figma-style" PM/dev/designer co-tvorbě. Public preview bez účtu, GitHub sync. Single-version flow, backend pro složitější systémy stále křehký, kreditní fluktuace.

**Figma Make** — **Jediný tool s nativními inline comments + reactions** v Figmě (kritické pro Pflanzer). Variants koncept + Make Kits = side-by-side prototypy. Embed do Slides/FigJam. Backend prototypy slabší, restricted prototype links jen na paid tieru.

**Google Stitch** — **5-screen canvas = nativní side-by-side variant generation**, nejlepší match pro Pflanzer multi-version. Free, public share, remix bez účtu, voice canvas. DESIGN.md export do Cursoru. Jen UI (backend přes Firebase Studio), žádný feedback layer.

**Claude Artifacts** — Nejnižší tření: 3 chaty = 3 varianty, public link bez účtu, remix. Live Artifacts s connect na Gmail/Shopify. Single-file SPA, ne plný fullstack. Žádné comments ani compare UI.

**Cursor Composer 2** — **`/best-of-n` je nejblíž Pflanzer multi-version philosophy** — stejný brief proti N modelům, každý ve worktree. Agents Window pro paralelní specialisty. IDE nástroj — stakeholder se nepřipojí, žádný share link.

**Replit Agent 3** — All-in-one (DB, auth, deploy, monitoring, autonomous bug-fix). Collaborators in workspace (5 v Core / 50 viewers v Pro). Effort-based pricing nepředvídatelné, žádné multi-version, žádné scored feedback.

**GitHub Spark** — Integrace s GitHub (workshop output = repo), auth + KV store out-of-the-box, free deploy. Pouze TS+React lock-in. Vyžaduje Pro+ $39/m, žádné multi-version, žádné comments.

**Tempo Labs** — React-only code-first (drag-drop + chat + GitHub), MCP App Store pro enterprise integrace. Cenový skok ($30/m → $4500/m), žádný multi-version flow, žádný feedback.

**Builder.io Visual Copilot / Fusion** — Pixel-perfect Figma→kód s mapováním na vaše komponenty, multi-framework (i Qwik/Solid). Není generative-from-prompt, je to Figma bridge — pro Pflanzer "vibekódujeme od nuly" workflow suboptimální.

---

## Doporučení pro Pflanzer

**Žádný jeden tool nepokrývá všechny tři pilíře (multi-version + public share + scored feedback).** Trh 2026 je rozštěpený: AI app buildery (Bolt/Lovable/v0/Replit) řeší generaci, ale ignorují stakeholder loop; Figma má feedback ale slabou backend generaci; Cursor má `/best-of-n` ale je IDE-only; Google Stitch má 5-screen multi-version ale jen UI.

**Doporučená kombinace pro pilot Pflanzeru:**

1. **In-session generation: Bolt.new nebo Lovable** (paralelně 1–3 instance v různých tabech, každá pro jinou variantu — manuálně orchestrované facilitátorem). Bolt pro full-stack komplexitu, Lovable když je workshop víc PM-driven a chcete Visual Edits live.
2. **Alternativa pro UI-heavy sessions: Google Stitch** — 5-screen canvas dává side-by-side zdarma, public share funguje pro stakeholdery bez účtu. Pro UI-only workshopy je to nejlepší match.
3. **Power-user variant: Cursor Composer 2 s `/best-of-n`** — pokud v místnosti sedí dev a chcete generovat A/B/C ze stejného briefu deterministicky a zachovat git historii. Chybí ale share-out.
4. **Feedback layer = build-vlastní.** Žádný tool nemá scored cross-prototype feedback. Mezi-session UI musíte postavit sami: tenký wrapper (např. Next.js stránka s iframe na 3 deploy URLs + scoring formulář + Supabase pro agregaci). 1–2 dny práce, řeší core diferenciátor Pflanzeru.
5. **Security pillar:** Žádný z toolů nemá nativní security review. V Pflanzer session pravděpodobně doplníte Claude Code / Cursor s `security-review` skillem nad výstupem builderu.

**Závěr: stavte tenkou Pflanzer-orchestration vrstvu nad 2–3 buildery (Bolt/Lovable/Stitch). Vlastní fullstack vibekoder nestavte — comoditizovaný trh.** Diferenciátor je v procesu (cross-functional facilitation + scored feedback loop), ne v generátoru kódu.

---

## Zdroje

- [v0 by Vercel: Complete Guide 2026 (NxCode)](https://www.nxcode.io/resources/news/v0-by-vercel-complete-guide-2026)
- [Vercel v0 Pricing 2026 (UI Bakery)](https://uibakery.io/blog/vercel-v0-pricing-explained-what-you-get-and-how-it-compares)
- [Bolt.new Pricing](https://bolt.new/pricing)
- [Bolt.new Review 2026 (vibecoding.app)](https://vibecoding.app/blog/bolt-new-review)
- [Lovable Pricing](https://lovable.dev/pricing)
- [Lovable AI Review 2026 (StartDesigns)](https://www.startdesigns.com/blog/lovable-ai-app-builder-review/)
- [Figma Make Review 2026 (NoCode MBA)](https://www.nocode.mba/articles/figma-make-ai-review)
- [Figma Plans & Pricing](https://www.figma.com/pricing/)
- [Google Stitch March 2026 Update (UXPin)](https://www.uxpin.com/studio/blog/google-stitch-ai-design-tool-updates-ui-ux/)
- [Google Stitch: Vibe Design and 5-Screen Canvas](https://tech-insider.org/google-stitch-ai-design-tool-march-2026-update/)
- [Claude Artifacts Publishing & Sharing](https://support.claude.com/en/articles/9547008-publishing-and-sharing-artifacts)
- [Claude Live Artifacts 2026 (Eigent)](https://www.eigent.ai/blog/claude-live-artifacts-guide)
- [Cursor Composer 2 Review 2026 (Toolworthy)](https://www.toolworthy.ai/tool/cursor-composer)
- [Cursor Models & Pricing Docs](https://cursor.com/docs/models-and-pricing)
- [Replit Effort-Based Pricing](https://blog.replit.com/effort-based-pricing)
- [Replit Pricing 2026 (NoCode MBA)](https://www.nocode.mba/articles/replit-pricing)
- [GitHub Spark Features](https://github.com/features/spark)
- [GitHub Spark Billing Docs](https://docs.github.com/en/billing/concepts/product-billing/github-spark)
- [Tempo Review 2026 (vibecoding.app)](https://vibecoding.app/blog/tempo-review)
- [Builder.io Visual Copilot CLI](https://www.builder.io/blog/visual-copilot-cli)
- [Lovable vs Bolt vs V0 (Lovable)](https://lovable.dev/guides/lovable-vs-bolt-vs-v0)
- [Choosing your AI prototyping stack (Anna Arteeva, Medium)](https://annaarteeva.medium.com/choosing-your-ai-prototyping-stack-lovable-v0-bolt-replit-cursor-magic-patterns-compared-9a5194f163e9)
- [Best Vibe-Coding Tools 2026 (CrewScale)](https://www.crewscale.com/blog/best-vibe-coding-tools-2026)
