// Renders og-<lang>.png (1200×630) and apple-touch-icon.png into website/dist/method/.
// Run after build.py: NODE_PATH=<dir with playwright> node website/v3/og.cjs
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const dist = path.resolve(__dirname, '..', 'dist', 'method');
const meta = JSON.parse(fs.readFileSync(path.join(dist, 'og-meta.json'), 'utf8'));
const strip = (s) => s.replace(/&nbsp;/g, ' ').replace(/<[^>]+>/g, '');

const card = (m) => `<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,300;12..96,800&family=IBM+Plex+Sans:wght@500&display=swap" rel="stylesheet">
<style>
body{margin:0;width:1200px;height:630px;background:#EDF1EA;color:#13221A;font-family:"IBM Plex Sans",Arial,sans-serif;position:relative;overflow:hidden}
.pad{position:absolute;left:72px;top:64px;right:72px}
.lock{font:800 26px "Bricolage Grotesque",Arial,sans-serif;letter-spacing:-.01em}
.lock span{font-weight:300;color:#55665B}
h1{font:800 70px/1 "Bricolage Grotesque",Arial,sans-serif;letter-spacing:-.03em;margin:44px 0 0;max-width:1000px}
h1 i{display:block;font-style:normal;font-weight:300}
.claim{position:absolute;left:72px;bottom:58px;font:500 26px "IBM Plex Sans",Arial,sans-serif;color:#1E7A46}
svg{position:absolute;right:56px;bottom:40px}
</style></head><body>
<div class="pad"><div class="lock">Pflanzer Method <span>| pflanzer.cz/method</span></div>
<h1>${strip(m.h1a)}<i>${strip(m.h1b)}</i></h1></div>
<div class="claim">${strip(m.claim)}</div>
<svg width="300" height="120" viewBox="0 0 300 120"><path d="M0 60H90M90 60C130 60 130 18 170 18M90 60H170M90 60C130 60 130 102 170 102" fill="none" stroke="#A7B5A8" stroke-width="3" stroke-linecap="round"/>
<path d="M170 60H240" stroke="#1E7A46" stroke-width="5" stroke-linecap="round"/>
<g transform="translate(262 60)" fill="#1E7A46">${[0,72,144,216,288].map(a=>`<ellipse transform="rotate(${a})" cx="0" cy="-15" rx="8" ry="14"/>`).join('')}<circle r="7" fill="#EDF1EA"/></g></svg>
</body></html>`;

(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1200, height: 630 } });
  for (const [lang, m] of Object.entries(meta)) {
    await p.setContent(card(m), { waitUntil: 'networkidle' });
    await p.screenshot({ path: path.join(dist, `og-${lang}.png`) });
  }
  const i = await b.newPage({ viewport: { width: 180, height: 180 } });
  const svg = fs.readFileSync(path.join(dist, 'favicon.svg'), 'utf8');
  await i.setContent(`<body style="margin:0">${svg.replace('<svg ', '<svg width="180" height="180" ')}</body>`);
  await i.screenshot({ path: path.join(dist, 'apple-touch-icon.png') });
  await b.close();
  fs.unlinkSync(path.join(dist, 'og-meta.json'));
  console.log('og images:', Object.keys(meta).join(', '));
})();
