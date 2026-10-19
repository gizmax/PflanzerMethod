// Vyrenderuje stránky SPA v headless chromiu (Playwright) a vypíše JSON na stdout.
// Použití: node render_pages.cjs <dir s node_modules> <baseUrl> <paths JSON> <timeoutMs>
const path = require("path");
const { createRequire } = require("module");

function load(dir) {
  const req = createRequire(path.join(dir, "noop.js"));
  for (const name of ["playwright", "@playwright/test", "playwright-core"]) {
    try {
      const m = req(name);
      if (m && m.chromium) return m;
    } catch (e) { /* zkus další */ }
  }
  throw new Error("Playwright v " + dir + " nenalezen");
}

(async () => {
  const [dir, base, pathsJson, tmo] = process.argv.slice(2);
  const timeout = parseInt(tmo || "30000", 10);
  const out = { ok: false, why: "", pages: [] };
  let browser;
  try {
    const pw = load(dir);
    browser = await pw.chromium.launch({ headless: true });
  } catch (e) {
    out.why = String(e && e.message ? e.message : e).split("\n")[0];
    out.browser = true;
    console.log(JSON.stringify(out));
    process.exit(0);
  }
  try {
    for (const p of JSON.parse(pathsJson)) {
      const page = await browser.newPage();
      const errors = [];
      const consoleErrors = [];
      page.on("pageerror", (e) => errors.push(String(e && e.message ? e.message : e).split("\n")[0]));
      page.on("console", (m) => { if (m.type() === "error") consoleErrors.push(m.text().split("\n")[0]); });
      let status = null;
      let note = "";
      try {
        const resp = await page.goto(base + p, { waitUntil: "networkidle", timeout });
        status = resp ? resp.status() : null;
      } catch (e) {
        note = String(e && e.message ? e.message : e).split("\n")[0];
      }
      let html = "";
      let rootEmpty = true;
      try {
        await page.waitForTimeout(300);
        html = "<!DOCTYPE html>\n" + (await page.evaluate(() => document.documentElement.outerHTML));
        rootEmpty = await page.evaluate(() => {
          const r = document.querySelector("#root, #app");
          if (r) return r.children.length === 0 && !r.textContent.trim();
          return !document.body || !document.body.innerText.trim();
        });
      } catch (e) {
        note = note || String(e && e.message ? e.message : e).split("\n")[0];
      }
      out.pages.push({ path: p, status, html, rootEmpty, errors, consoleErrors, note });
      await page.close();
    }
    out.ok = true;
  } catch (e) {
    out.why = String(e && e.message ? e.message : e).split("\n")[0];
  }
  await browser.close();
  console.log(JSON.stringify(out));
})();
