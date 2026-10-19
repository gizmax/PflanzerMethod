# 05 — Async

**Pflanzer Method | pflanzer.cz/method**

> K čemu je tento dokument: co se děje mezi Buildem a Rozhodnutím —
> sběr feedbacku zástupců na preview URL, keep/fix/kill nad diffem, pravidla
> pro mlčení a eskalace. Příkaz: `/pm feedback`. Délka okna podle stupně
> je jen v kanonické tabulce [`00-lean-pflanzer.md`](00-lean-pflanzer.md)
> § Tři stupně a v ADR-0017; tady je Lean a odchylky pro Quick a Full.

## Cíl

Dát všem zástupcům kroků cesty šanci **vidět běžící varianty ve svém
prohlížeči** a říct, co jim vadí, dřív než se u Rozhodnutí sejde Decider.
Async nahrazuje velkou místnost: místo 3 hodin přítomnosti ~15 minut
denně nad konkrétním artefaktem. Zároveň zmírňuje hlavní riziko modelu —
Decider u stavby nebyl.

## Průběh (Lean)

| Den | Co |
|-----|----|
| 1 | Builder pushne 3 větve, preview URL (se štítkem „k rozhodnutí, ne produkt") a pošle odkazy všem zástupcům; spustí se `pflanzer hub` |
| 2–3 | Zástupci klikají a komentují; technické role procházejí diff; builder zapracovává |
| 4 | `pflanzer feedback_pull`: agregace, audit debtu, top 3 spory; pre-read pro Decidera nejpozději 24 h před Rozhodnutím |

Délka okna se řídí stupněm, protože stupeň určuje, kdo musí dát feedback:
**Quick** má kratší okno (bez vetovacích rolí v místnosti), **Full**
nejdelší (async vetovací role potřebují pracovní dny). Okno se
**neprodlužuje** nad horní hranici stupně; potřeba delšího okna je signál
k upgradu stupně nebo odkladu Rozhodnutí (ADR-0017).

## Co kdo dělá v okně

- **Technické role** (vývoj, QA, provoz): projdou **PR diff** varianty
  (draft PR, `pflanzer worktree preview --slug <slug>`) a ke každému
  změněnému souboru napíšou **keep / fix / kill** jako PR komentář.
  Feedback míří přímo do kódu, ne jen do preferencí.
- **Ostatní zástupci** (byznys, produkt, design, právo): klikají na
  preview a píšou feedback v hubu.
- **Builder** zapracovává připomínky ve větvích (preview se aktualizuje),
  neprodukuje čtvrtou variantu.
- **Facilitátor/PdM** hlídá termín a pokrytí kroků cesty; chybějící hlasy
  jmenuje.

## Preview a sandbox

Preview = to, co firma už má (Vercel/Netlify preview, review apps, preview
namespace). Pravidla (kontrolována v checkpointu bezpečnost & právo):

- bez produkčních dat a bez cesty do produkční sítě, noindex, watermark,
- viditelný štítek „Varianta X — k rozhodnutí, ne produkt" + 1 věta,
  jaký problém řeší,
- URL nejsou pro externí osoby ani zákazníky (viz [`08`](08-edge-cases-a-rizika.md) § 8),
- bez skutečné URL nemá Async na co klikat — nehraj ho; zařiď preview,
  nebo pilot posuň.

## Sběr feedbacku

**Web hub** (sdílí DB s CLI): `pflanzer hub` (kolegům ve firemní síti
`--host 0.0.0.0`). **Bez hubu**, offline — kdo klikal a nezadal, zapíše
ho facilitátor za něj podle jeho slov:

```bash
pflanzer feedback add --slug <slug> --variant A --role <krok/role> \
  --severity critical|major|minor --text "<co a proč>"
pflanzer feedback list --slug <slug>
```

Minimum každého záznamu: **varianta, krok cesty/role, závažnost, text s
důvodem** (bez rationale záznam nic neříká). Závažnosti:

- **critical** — brání nasazení: bezpečnost, právo, data, rozbitý hlavní
  tok, WCAG Critical/Serious na veřejném rozhraní, breaking change bez
  konzumentů. Kdo dává critical, píše proč; critical bez důkazu se
  downgraduje.
- **major** — zásadní výhrada, nebrání nasazení; viditelné v Rozhodnutí.
- **minor** — nit, zapracuje builder.

**Otevřený critical na vítězi blokuje Go** (Iterate ho může opravit).
Řešení: opravit hned, varianta ven ze shortlistu, nebo nechat na Decidera
(override vyžaduje rationale v decision logu).

AI-only feedback (sub-agenti) se označuje a má váhu max 0,5; je to vstup,
ne hlas. V rozšířené sestavě Full se navíc používá score závaznosti per
role ([`04`](04-session-1.md) § Score závaznosti).

## Mlčení

- **Nevetovací role:** chybějící feedback po termínu = „no objection",
  zapíše se do decision logu s atribucí (kdo mlčel).
- **Vetovací role** (bezpečnost & právo, kapacita EM): ticho **není**
  souhlas. Bez jejich vyjádření je Rozhodnutí jen review, ne rozhodnutí.
  Pravidlo kvóra a postup: [`08`](08-edge-cases-a-rizika.md) § 11.
- **Připomínky** 48 h a 24 h před termínem; ve Full navíc vetovací role
  upozorni uprostřed okna.

## Audit discovery debtu

Při agregaci (`pflanzer feedback_pull`, jen pokud je feedback; prázdná data
auditovat nemá smysl) běží sub-agent `discovery-debt-detector`: kolik
tvrzení o uživateli má zdroj, kolik feedbacku je AI-only, zda existuje
uzel OST. Skóre 0–10: ≤ 2 OK · 3–6 varování (výstupy jen exploratory) ·
**≥ 7 STOP**, předřaď discovery. Je to vstup pro Decidera, ne verdikt.

## Eskalace

**Svolat Rozhodnutí dřív:** všichni dali feedback a nic není critical, nebo
Decider potřebuje Go k pevnému termínu.

**Odložit Rozhodnutí:** critical bez návrhu řešení (posun o 3–5 dní na
opravu) · nové vysoké riziko · debt ≥ 7 · Decider nedostupný (ADR-0001) ·
vetovací role bez vyjádření.

**Ukončit projekt bez Rozhodnutí:** únik L4 dat v preview (incident playbook,
ne rozhodnutí) · splněné kill kritérium ze zadání · debt ≥ 7 a Decider
odmítá discovery.

## Full — navíc

- Okno 5–7 pracovních dní, triage updates (re-klasifikace datového toku,
  STRIDE update, scany, **AI Act Fáze B** nad skutečnými variantami,
  odhad provozní stopy, SLO a runbook) odevzdat nejpozději v den 5 —
  bez nich se Rozhodnutí nesvolá ([`03`](03-pre-session-priprava.md)).
- Upgrade Limited → High-risk ve Fázi B = povinný sporný bod Rozhodnutí.
- Hub navíc ukazuje odhad T-shirt od EM a risk register.

## Výstup do Rozhodnutí (24 h předem)

Agregovaný feedback per krok a variantu · seznam critical a jejich stav ·
top 3 sporné body · veto registr · verdikt debtu · u Full triage updates.
Další krok: `/pm decide <slug>` ([`06`](06-session-2.md)) — přizvi Decidera.
