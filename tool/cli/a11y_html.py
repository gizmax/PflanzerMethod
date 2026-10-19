"""Lehká statická a11y kontrola HTML stránek (jen stdlib `html.parser`).

Není to náhrada axe-core: hlídá jen to, co jde spolehlivě poznat z markupu
(lang, title, viewport, alt, popisky formulářových prvků, text tlačítek a odkazů,
struktura nadpisů, autocomplete). Používá ji brána `a11y` nad stránkami běžící aplikace.
"""
from __future__ import annotations

from html.parser import HTMLParser
from urllib.parse import urldefrag, urljoin, urlsplit

FAIL = "fail"
WARN = "warn"

_NO_LABEL_INPUTS = {"hidden", "submit", "button", "reset", "image"}
_VOID = {"img", "input", "meta", "br", "hr", "link", "area", "base", "col", "source", "wbr"}
_SKIP_EXT = (".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".pdf", ".zip",
             ".txt", ".xml", ".json", ".woff", ".woff2", ".webp", ".mp4", ".mp3")
_NAME_HINTS = ("name", "jmeno", "prijmeni", "fullname", "first", "last")


def _blank(v: str | None) -> bool:
    return v is None or not v.strip()


class _Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.lang: str | None = None
        self.has_html = False
        self.title = ""
        self._in_title = False
        self.viewport = False
        self.imgs_no_alt = 0
        self.headings: list[int] = []
        self.links: list[str] = []
        self.label_for: set[str] = set()
        self.controls: list[dict] = []   # {id, labelled, kind}
        self.nameless: dict[str, int] = {"tlačítko": 0, "odkaz": 0}
        self.no_autocomplete: set[str] = set()
        self._label_depth = 0
        self._skip = 0
        self._acc: list[dict] = []        # otevřená tlačítka / odkazy

    # -- pomocné
    def _text_into_acc(self, text: str, named: bool = False) -> None:
        for a in self._acc:
            if named or text.strip():
                a["named"] = True

    def handle_starttag(self, tag: str, attrs: list) -> None:  # noqa: C901
        a = {k: (v if v is not None else "") for k, v in attrs}
        if tag == "html":
            self.has_html = True
            self.lang = a.get("lang")
        elif tag == "title":
            self._in_title = True
        elif tag in ("script", "style"):
            self._skip += 1
        elif tag == "meta" and a.get("name", "").lower() == "viewport":
            self.viewport = True
        elif tag == "img":
            if "alt" not in a:
                self.imgs_no_alt += 1
            elif a["alt"].strip():
                self._text_into_acc("", named=True)
            if a.get("aria-label", "").strip():
                self._text_into_acc("", named=True)
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.headings.append(int(tag[1]))
        elif tag == "label":
            self._label_depth += 1
            if a.get("for"):
                self.label_for.add(a["for"])
        elif tag in ("input", "select", "textarea"):
            self._control(tag, a)
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
        if tag in ("a", "button") and (tag == "button" or "href" in a):
            named = (not _blank(a.get("aria-label")) or not _blank(a.get("aria-labelledby"))
                     or not _blank(a.get("title")))
            self._acc.append({"tag": tag, "named": named})
        if tag == "svg" and a.get("aria-label", "").strip():
            self._text_into_acc("", named=True)

    def _control(self, tag: str, a: dict) -> None:
        typ = a.get("type", "text").lower() if tag == "input" else tag
        if tag == "input" and typ in _NO_LABEL_INPUTS:
            return
        labelled = (self._label_depth > 0 or not _blank(a.get("aria-label"))
                    or not _blank(a.get("aria-labelledby")) or not _blank(a.get("title")))
        self.controls.append({"id": a.get("id"), "labelled": labelled, "kind": typ})
        if tag == "input":
            ident = f'{a.get("name", "")} {a.get("id", "")}'.lower()
            wants = typ in ("tel", "email") or (typ == "text" and any(h in ident for h in _NAME_HINTS))
            if wants and _blank(a.get("autocomplete")):
                self.no_autocomplete.add(typ if typ in ("tel", "email") else "name")

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        elif tag in ("script", "style"):
            self._skip = max(0, self._skip - 1)
        elif tag == "label":
            self._label_depth = max(0, self._label_depth - 1)
        elif tag in ("a", "button"):
            for i in range(len(self._acc) - 1, -1, -1):
                if self._acc[i]["tag"] == tag:
                    item = self._acc.pop(i)
                    if not item["named"]:
                        self.nameless["tlačítko" if tag == "button" else "odkaz"] += 1
                    break

    def handle_data(self, data: str) -> None:
        if self._skip:
            return
        if self._in_title:
            self.title += data
        self._text_into_acc(data)


def analyze(html: str) -> list[tuple[str, str]]:
    """Vrátí [(závažnost, lidský popis)] pro jednu stránku."""
    p = _Page()
    try:
        p.feed(html)
        p.close()
    except Exception:  # noqa: BLE001 — rozbitý markup nesmí shodit bránu
        pass
    out: list[tuple[str, str]] = []
    if _blank(p.lang):
        out.append((FAIL, "chybí <html lang> (čtečky nepoznají jazyk)"))
    if _blank(p.title):
        out.append((FAIL, "chybí nebo je prázdný <title>"))
    if not p.viewport:
        out.append((WARN, "chybí meta viewport (špatné zobrazení na mobilu)"))
    if p.imgs_no_alt:
        out.append((FAIL, f"{p.imgs_no_alt}× obrázek bez atributu alt"))
    unl = [c for c in p.controls if not c["labelled"] and c["id"] not in p.label_for]
    if unl:
        kinds = ", ".join(sorted({c["kind"] for c in unl}))
        out.append((FAIL, f"{len(unl)}× pole formuláře bez popisku ({kinds})"))
    for what, n in p.nameless.items():
        if n:
            out.append((FAIL, f"{n}× {what} bez přístupného textu"))
    h = p.headings
    if h.count(1) > 1:
        out.append((WARN, f"{h.count(1)}× <h1>, má být jen jeden"))
    elif h and 1 not in h:
        out.append((WARN, "chybí <h1>"))
    skipped = [(a, b) for a, b in zip(h, h[1:]) if b > a + 1]
    if skipped:
        a, b = skipped[0]
        out.append((WARN, f"přeskočená úroveň nadpisu (h{a} → h{b})"))
    if p.no_autocomplete:
        out.append((WARN, "chybí autocomplete u polí " + "/".join(sorted(p.no_autocomplete))))
    return out


def same_host_links(html: str, base_url: str, limit: int = 20) -> list[str]:
    """Cesty odkazů na stejném hostu (bez fragmentu, bez souborů typu css/png)."""
    p = _Page()
    try:
        p.feed(html)
    except Exception:  # noqa: BLE001
        return []
    host = urlsplit(base_url).netloc
    paths: list[str] = []
    for href in p.links:
        if href.startswith(("mailto:", "tel:", "javascript:", "#")):
            continue
        u = urlsplit(urldefrag(urljoin(base_url, href))[0])
        if u.scheme not in ("http", "https") or u.netloc != host:
            continue
        if u.path.lower().endswith(_SKIP_EXT):
            continue
        path = (u.path or "/") + (f"?{u.query}" if u.query else "")
        if path not in paths:
            paths.append(path)
        if len(paths) >= limit:
            break
    return paths


def summarize(findings: list[tuple[str, str, str]], pages: int, max_items: int = 6) -> str:
    """Lidský výpis nálezů (path, závažnost, text); nejdřív závažné."""
    ordered = sorted(findings, key=lambda f: 0 if f[1] == FAIL else 1)
    lines = [f"{'závažné' if sev == FAIL else 'doporučení'} · {path}: {msg}"
             for path, sev, msg in ordered[:max_items]]
    if len(ordered) > max_items:
        lines.append(f"… a {len(ordered) - max_items} dalších")
    return f"a11y: {pages} stránek zkontrolováno staticky\n" + "\n".join(lines)
