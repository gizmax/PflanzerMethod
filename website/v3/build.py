"""Build the multilingual Pflanzer Method site into website/dist/method/.

Each website/v3/<lang>.html is a full page with two placeholders:
<!--ALT-->   → canonical, hreflang alternates, og:url/locale/image, icons
<!--LANGS--> → language switcher
Output: dist/method/index.html (cs) and dist/method/<lang>/index.html, plus sitemap.xml,
favicon.svg and og-<lang>.png / apple-touch-icon.png (rendered by og.cjs).
"""
from __future__ import annotations

import json
import re
import shutil
from datetime import date
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIST = HERE.parent / "dist" / "method"
BASE = "https://pflanzer.cz/method/"
LANGS = ["cs", "en", "de", "es", "fr", "it", "pl"]
X_DEFAULT = "en"
LOCALE = {"cs": "cs_CZ", "en": "en_US", "de": "de_DE", "es": "es_ES", "fr": "fr_FR",
          "it": "it_IT", "pl": "pl_PL"}
NATIVE = {"cs": "Čeština", "en": "English", "de": "Deutsch", "es": "Español", "fr": "Français",
          "it": "Italiano", "pl": "Polski"}
UPDATED = {"cs": "Aktualizováno", "en": "Updated", "de": "Aktualisiert", "es": "Actualizado",
           "fr": "Mis à jour le", "it": "Aggiornato il", "pl": "Zaktualizowano"}
CS_DOCS = {"cs": "", "en": " (CS)", "de": " (CS)", "es": " (CS)", "fr": " (CS)", "it": " (CS)", "pl": " (CS)"}
AUTHOR = {"@type": "Person", "@id": "https://pflanzer.cz/#tomas-pflanzer", "name": "Tomáš Pflanzer",
          "url": "https://pflanzer.cz/", "jobTitle": "CEO",
          "worksFor": {"@type": "Organization", "@id": "https://wiseguys.co/#org", "name": "Wiseguys",
                       "url": "https://wiseguys.co"}}
REPO = "https://github.com/gizmax/PflanzerMethod"
SWITCH_LABEL = {"cs": "Jazyk", "en": "Language", "de": "Sprache", "es": "Idioma",
                "fr": "Langue", "it": "Lingua", "pl": "Język"}


def url(lang: str) -> str:
    return BASE if lang == "cs" else f"{BASE}{lang}/"


def head_block(lang: str, og_alt: str) -> str:
    lines = [f'<link rel="canonical" href="{url(lang)}">']
    lines += [f'<link rel="alternate" hreflang="{code}" href="{url(code)}">' for code in LANGS]
    lines.append(f'<link rel="alternate" hreflang="x-default" href="{url(X_DEFAULT)}">')
    lines += [
        f'<meta property="og:url" content="{url(lang)}">',
        f'<meta property="og:locale" content="{LOCALE[lang]}">',
        *[f'<meta property="og:locale:alternate" content="{LOCALE[c]}">' for c in LANGS if c != lang],
        f'<meta property="og:image" content="{BASE}og-{lang}.png">',
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        f'<meta property="og:image:alt" content="{escape(og_alt, quote=True)}">',
        f'<meta name="twitter:image" content="{BASE}og-{lang}.png">',
        f'<meta name="twitter:image:alt" content="{escape(og_alt, quote=True)}">',
        '<meta name="author" content="Tomáš Pflanzer">',
        '<meta name="robots" content="index, follow, max-image-preview:large">',
        '<meta name="theme-color" media="(prefers-color-scheme: dark)" content="#0E1712">',
        f'<link rel="icon" href="{BASE}favicon.svg" type="image/svg+xml">',
        f'<link rel="apple-touch-icon" href="{BASE}apple-touch-icon.png">',
    ]
    return "\n".join(lines)


def switcher(lang: str) -> str:
    links = "".join(
        f'<a href="{url(c)}" hreflang="{c}" lang="{c}" title="{NATIVE[c]}"'
        + (' aria-current="page"' if c == lang else "") + f">{c.upper()}</a>"
        for c in LANGS)
    return f'<nav class="langs" aria-label="{SWITCH_LABEL[lang]}">{links}</nav>'


def text_of(pattern: str, html: str) -> str:
    m = re.search(pattern, html, re.S)
    if not m:
        raise SystemExit(f"pattern not found: {pattern}")
    return re.sub(r"<[^>]+>", "", m.group(1)).replace("&nbsp;", " ").strip()


FONTS = HERE / "fonts"


def self_host_fonts(html: str) -> str:
    """Replace Google Fonts with self-hosted woff2 (latin + latin-ext): faster, no third party."""
    html = re.sub(r'<link rel="preconnect" href="https://fonts\.g[^"]+"[^>]*>\n', "", html)
    html = re.sub(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com[^"]+">\n', "", html)
    html = html.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', "")
    pre = "".join(
        f'<link rel="preload" href="/method/fonts/{f.name}" as="font" type="font/woff2" crossorigin>\n'
        for f in sorted(FONTS.glob("*-latin-*.woff2"))
        if f.name.startswith(("bricolage-grotesque-latin-", "ibm-plex-sans-latin-")) and "-ext-" not in f.name)
    css = (FONTS / "fonts.css").read_text(encoding="utf-8")
    return html.replace("<style>", pre + "<style>\n" + css, 1)


def plain(fragment: str) -> str:
    text = re.sub(r"<[^>]+>", "", fragment).replace("&nbsp;", " ").replace("&amp;", "&")
    return " ".join(text.split())


def fix_jsonld(html: str, lang: str) -> str:
    today = date.today().isoformat()
    page = url(lang)
    faq = [{"@type": "Question", "name": plain(q),
            "acceptedAnswer": {"@type": "Answer", "text": plain(a)}}
           for q, a in re.findall(r"<details><summary>(.*?)</summary><p>(.*?)</p></details>", html, re.S)]
    m = re.search(r'<script type="application/ld\+json">\s*(\{.*?\})\s*</script>', html, re.S)
    old = json.loads(m.group(1))
    app_old = next(n for n in old["@graph"] if n.get("@type") == "SoftwareApplication")
    graph = [
        {"@type": "WebSite", "@id": f"{page}#web", "url": page, "name": "Pflanzer Method",
         "inLanguage": lang, "publisher": {"@id": AUTHOR["@id"]}},
        {"@type": "WebPage", "@id": f"{page}#page", "url": page, "inLanguage": lang,
         "name": plain(re.search(r"<title>(.*?)</title>", html, re.S).group(1)),
         "description": re.search(r'name="description" content="(.*?)"', html).group(1).replace("&nbsp;", " "),
         "isPartOf": {"@id": f"{page}#web"}, "about": {"@id": f"{BASE}#software"},
         "primaryImageOfPage": f"{BASE}og-{lang}.png", "dateModified": today,
         "author": {"@id": AUTHOR["@id"]}},
        {"@type": "SoftwareApplication", "@id": f"{BASE}#software", "name": "Pflanzer Method",
         "applicationCategory": "DeveloperApplication", "description": app_old["description"],
         "softwareVersion": "0.6", "license": "https://opensource.org/licenses/MIT",
         "isAccessibleForFree": True, "codeRepository": REPO, "sameAs": [REPO],
         "image": f"{BASE}og-{lang}.png", "url": page, "inLanguage": lang, "dateModified": today,
         "offers": {"@type": "Offer", "price": "0", "priceCurrency": "EUR"},
         "author": AUTHOR},
        {"@type": "FAQPage", "@id": f"{page}#faq", "inLanguage": lang, "mainEntity": faq},
    ]
    block = ('<script type="application/ld+json">\n'
             + json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, indent=2)
             + "\n</script>")
    return html[:m.start()] + block + html[m.end():]


def localize(html: str, lang: str) -> str:
    """Updated date in the footer, (CS) on links to Czech docs, FAQ questions as headings."""
    d = date.today()
    shown = f"{d.day}. {d.month}. {d.year}" if lang in ("cs", "de", "pl") else (
        d.strftime("%-d %b %Y") if lang == "en" else f"{d.day}/{d.month}/{d.year}")
    html = html.replace("</footer>", f'  <span>{UPDATED[lang]} <time datetime="{d.isoformat()}">{shown}</time></span>\n</footer>', 1)
    if CS_DOCS[lang]:
        html = re.sub(r'(<a [^>]*href="https://github\.com/gizmax/PflanzerMethod/blob/main/docs/[^"]+"[^>]*>)(.*?)</a>',
                      lambda m: m.group(1).replace("<a ", '<a hreflang="cs" ', 1) + m.group(2) + CS_DOCS[lang] + "</a>",
                      html, flags=re.S)
    html = re.sub(r"<details><summary>(.*?)</summary>", r'<details><summary><h3 class="fq">\1</h3></summary>', html)
    html = html.replace(".faq summary::-webkit-details-marker{display:none}",
                        ".faq summary::-webkit-details-marker{display:none}\n.faq .fq{font:inherit;letter-spacing:inherit;margin:0}")
    return html


def build() -> dict[str, dict[str, str]]:
    meta: dict[str, dict[str, str]] = {}
    for lang in LANGS:
        src = (HERE / f"{lang}.html").read_text(encoding="utf-8")
        assert "<!--ALT-->" in src and "<!--LANGS-->" in src, lang
        h1 = re.findall(r'<span class="ln"><span>(.*?)</span></span>', src, re.S)
        claim = text_of(r'<span class="claim">(.*?)</span>', src)
        meta[lang] = {"h1a": h1[0], "h1b": h1[1], "claim": claim}
        out = src.replace('<html lang="cs">', f'<html lang="{lang}">', 1)
        out = out.replace("<!--ALT-->", head_block(lang, claim))
        out = out.replace("<!--LANGS-->", switcher(lang))
        out = fix_jsonld(out, lang)
        out = localize(out, lang)
        out = self_host_fonts(out)
        target = DIST / ("index.html" if lang == "cs" else f"{lang}/index.html")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(out, encoding="utf-8")
    shutil.copytree(FONTS, DIST / "fonts", dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("fonts.css"))
    today = date.today().isoformat()
    alts = "".join(f'\n    <xhtml:link rel="alternate" hreflang="{c}" href="{url(c)}"/>' for c in LANGS)
    alts += f'\n    <xhtml:link rel="alternate" hreflang="x-default" href="{url(X_DEFAULT)}"/>'
    urls = "".join(f"\n  <url>\n    <loc>{url(c)}</loc>\n    <lastmod>{today}</lastmod>{alts}\n  </url>"
                   for c in LANGS)
    (DIST / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:xhtml="http://www.w3.org/1999/xhtml">' + urls + "\n</urlset>\n", encoding="utf-8")
    (DIST / "favicon.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" '
        'rx="7" fill="#13221A"/><path d="M4 16h8M12 16c4 0 4-8 9-8M12 16h9M12 16c4 0 4 8 9 8" '
        'fill="none" stroke="#EDF1EA" stroke-width="2.2" stroke-linecap="round"/>'
        '<circle cx="25" cy="16" r="3.4" fill="#4DC481"/></svg>\n', encoding="utf-8")
    (DIST / "og-meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta


if __name__ == "__main__":
    m = build()
    print("built", ", ".join(m), "→", DIST)
