---
description: Kickoff (/pm start, 15 min) — zadání na 1 stránku + jména zástupců 6 kroků cesty. Jediná cesta založení projektu.
---

# Kickoff (`/pm start`) — 15 minut

> **Cesty:** soubory `docs/…` a `tool/…` zmíněné níže leží v kořeni metody
> (`pflanzer root`), ne v target repu. Tool spouštěj vždy přes `pflanzer <cmd>`
> (funguje z libovolného adresáře).

**Pflanzer Method | pflanzer.cz/method** — brand line vždy na prvním řádku výstupu.

> **Argumenty:** `<slug>` = **první slovo** z `$ARGUMENTS` (zbytek je kontext od uživatele —
> rozhodnutí, jména, poznámky). Bez slugu: `pflanzer status`. Do příkazů dosazuj jen `<slug>`.
> **Zápisy dělá výhradně tool** (`pflanzer …`) — decision log, checkpointy ani DB nikdy needituj ručně.

Argumenty: `$ARGUMENTS` = volitelně problém v 1 větě. Kickoff vede Decider
+ jádro (ADR-0021). Cíl: **zadání na 1 stránku + jména pro všech 6 kroků
cesty + zabookovaná okna**. Žádný dlouhý wizard.

## Krok 0 — Readiness

```bash
pflanzer doctor
```

Ukaž lidský výstup a jeho Doporučení. Pokud „připraveno ke Kickoffu: ne" →
vypiš, co chybí (origin, vyplněný `INTEGRATION_GUIDE` — vývojář v Claude Code
napíše „vyplň docs/INTEGRATION_GUIDE.md podle tohoto repa“ a zkontroluje,
`CONSTITUTION`, test/lint/build, CI, preview deploy, pushnutý init:
`git add -A docs .pflanzer tests .gitignore .claude && git commit -m "chore(pflanzer): init" && git push -u origin HEAD`), a zeptej se přes AskUserQuestion:
*Opravit teď / Pokračovat vědomě (uveď riziko) / Zastavit.* Bez preview
deploye Build proběhne, ale Async nemá na co klikat — řekni to nahlas.

## Krok 1 — Sběr (AskUserQuestion, max 3 bloky)

1. **Zadání:** problém v 1 větě · **slug** (navrhni sám krátký, 2–4 slova
   bez diakritiky, např. `opusteny-kosik`; ve specu `slug`) · jedna metrika úspěchu (číslo + termín,
   např. „10 z 15 obchodníků otevře přehled 3× týdně do 30 dnů“, ne „budou
   to používat“) · kill kritérium („kdy to zabalíme“; ve specu `metric`,
   `kill_criteria`).
2. **Lidé:** Decider (jméno + mandát říct Go i Kill) · **ke každému ze
   6 kroků cesty** — byznys, produkt, design, vývoj, bezpečnost & právo,
   provoz — jedna otázka přes AskUserQuestion s možnostmi:
   - **[jméno]** (volný text),
   - **[stejný člověk jako X]** (nabídni konkrétní jména z už zadaných kroků),
   - **[AI náhrada]** — **jen tam, kde ADR-0023 dovolí** (viz tabulka níže).
   Pak které z lidí je **jádro** (3–4, celou dobu) a které **okno**.
3. **Rámec:** risk profile `throwaway | pilot | production` · **stupeň**
   `quick | lean | full` (default **Lean**: Build 3 h, Async 3–5 dní;
   Quick = `/pm live`; Full = regulované, okno 5–7 dní — tabulka v
   `docs/methodology/00-lean-pflanzer.md` § Tři stupně) · zabookovaná okna
   (Build 3 h, checkpoint B&P 20 min, Rozhodnutí 60–90 min, checkpoint
   provozu 20 min). Okna (kdy je Build, checkpointy, Rozhodnutí) jdou do specu
   jako `windows` — tool je uloží a ukáže ve `status`; nezapisuj je jen do
   odpovědi. **Režim stavby:** `session_mode` `parallel` (výchozí, 3 varianty
   A/B/C) nebo `mob` (jedna společná varianta u jednoho monitoru, max 5 lidí,
   ADR-0016). Zeptej se jednou větou, jen když to Decider nebo jádro zmínilo;
   tool po zápisu ukáže doporučení režimu (jen doporučení, nevynucuje).

**AI náhrada (ADR-0023) — nabízej jen podle tabulky:**

| Krok | Nabídka [AI náhrada] | Kdo podepíše místo chybějícího |
|------|---------------------|--------------------------------|
| byznys | **nikdy** | bez Decidera se Kickoff nesvolává |
| vývoj | **nikdy** | u klávesnice sedí vývojář |
| produkt | jen `quick` / `throwaway` | Decider (zadání) |
| design | ano (`AI:ux-expert`) | PdM; u zákaznického produktu v produkci člověk |
| bezpečnost & právo | jen předkontrola (`AI:security-expert`) | throwaway: stačí AI; pilot/production: člověk do 48 h, jinak Ship blokuje (pořadí podpisu viz níže) |
| provoz | jen předkontrola (`AI:devops-platform-expert`) | throwaway: AI; pilot: vývojář z jádra; production: člověk z provozu |

**Throwaway:** AI předkontrola bezpečnosti/provozu stačí — na podepisujícího se
**neptej** a nehlas to jako otevřený bod (ADR-0023). Jen ji po Buildu zapiš:
`pflanzer checkpoint --slug <slug> bezpecnost --ai --agent security-expert --note "…"`.

U pilotu/production se u kroku s AI náhradou zeptej **hned i na člověka, který to podepíše**,
a řekni, že AI náhrada platí jen pro tento projekt (příště sehnat člověka).
**Když tým podepisujícího určí, MUSÍŠ ho předat ve specu v `ai_signers`**
(`{"bezpecnost": "Pavel Šnek"}`) — jinak `pflanzer status` dál hlásí „čeká na
podpis: určete kdo“. Zkráceně jde i přímo v `path_owners`:
`"bezpecnost": "AI:security-expert / Pavel Šnek"` (oddělovač ` / ` nebo `|`).
Autor kódu (Vývoj) nemá podepisovat bezpečnost u osobních dat — tool varuje.

**Kdo podepíše bezpečnost & právo, když security není** — nabízej v tomto
pořadí, **nikdy ne autora kódu jako default**:
a. někdo z firmy s mandátem (DPO, IT security, compliance — stačí 20 min),
b. Decider vědomě převezme riziko (`pflanzer session_3 --slug S
   --override-triage --rationale "…"`, v decision logu je jeho jméno) —
   u pilotu bez osobních dat,
c. autor kódu až jako poslední možnost, u interního nástroje bez osobních
   dat; nástroj to označí varováním a právo tím pokryté není.

**Design s AI náhradou:** potvrzuje ho PdM (jméno vezmi z projektu) příkazem
`pflanzer checkpoint --slug S design --by <PdM> --note "…"` při Buildu —
řekni to hned při Kickoffu: potvrďte před Rozhodnutím; u pilotu Ship neblokuje,
u production ano.

Pravidla (vynucuj):
- **Krok bez jména a bez povolené AI náhrady → STOP.** Nabídni, kdo ho může
  zastoupit (jeden člověk smí krýt víc kroků; kdo — viz
  `docs/methodology/02-role-catalog.md`). Bez toho projekt nezakládej.
- **Jádro > 5** (nebo kdokoli naráz > 5) → navrhni zúžit scope nebo přesunout
  někoho na okno.
- Zástupce bez mandátu rozhodnout v okně není zástupce.
- `pilot`/`production`: repo musí mít origin (`doctor`); `target_repo_url`
  se čte z `.pflanzer/project.toml`, neptej se na něj znovu.
- `quick` nejde s audit-grade (ten je vždy Full).
- `throwaway` (kód se po Rozhodnutí zahodí) = explicitní opt-in s důvodem:
  discovery-only pilot · důkaz oddělený od produkce (audit) · certifikovaná
  regulovaná produkce (ADR-0005). Jinak platí, že vítěz jde do produkce.
- Zákaz pokračovat při datech L4 nebo AI Act „unacceptable“ — zapiš
  do decision logu a zastav. Regulované projekty: `docs/governance/`.

## Krok 2 — Založení (jediná cesta)

Spec zapiš nástrojem **Write** do `.pflanzer/specs/<slug>-kickoff.json`
v target repu (necommituje se, složka je v `.gitignore` z `init`) a pak:

```bash
pflanzer quick_session bootstrap --spec .pflanzer/specs/<slug>-kickoff.json
```

Obsah souboru (heredoc `--spec - <<'EOF'` je jen záložní varianta —
v omezených oprávněních ho blokuje bezpečnostní heuristika Bashe):

```json
{
  "slug": "<krátký-slug>",
  "title": "<krátký název projektu, ≤ 50 znaků>",
  "hook": "<problém v 1 větě>",
  "decider_name": "<jméno>",
  "room_role_idx": [1, 2, 6, 4, 7, 15],
  "risk_profile": "pilot",
  "tier": "lean",
  "role_owners": {"1": "Honza", "2": "Petra"},
  "metric": "<metrika>",
  "kill_criteria": "<kdy zabalit>",
  "path_owners": {"byznys": "Honza", "produkt": "Petra", "design": "AI:ux-expert", "vyvoj": "Jan", "bezpecnost": "AI:security-expert", "provoz": "Jan"},
  "ai_signers": {"bezpecnost": "Pavel Šnek", "design": "Petra"},
  "core": ["Petra", "Jan", "Eva"],
  "session_mode": "parallel",
  "windows": {"Build": "st 21.10. 9:00-12:00", "Rozhodnutí": "pá 30.10. 10:00"}
}
```

`title` (≤ 50 znaků): zeptej se Decidera na krátký název projektu, nebo ho
navrhni sám (např. „Online objednávka“) a nech potvrdit. Bez něj se odvodí z
hooku (první věta/klauzule). Používá ho status, reporty a PR title.

`path_owners`: jméno, `AI` nebo `AI:<agent>` (jen kde to tabulka dovolí).
`ai_signers` (nepovinné): krok s AI náhradou (`bezpecnost|provoz|design|produkt`) →
jméno člověka, který AI draft podepíše; vyplň vždy, když to tým řekl.
Víc repozitářů (FE + BE, monorepo): místo `target_repo_url` dej
`"target_repos"` — text `fe=https://…/web, be=https://…/api#develop` nebo
pole `[{"role": "fe", "url": "…", "branch": "main", "workspace": "apps/web"}]`.
Chyba „krok bez jména“, nepovolená AI náhrada nebo warning „jádro > 5“ →
vrať se ke Kroku 1, nic neobcházej. Potřebuješ-li z výstupu pole `slug`,
přidej `--json`.

## Krok 3 — Výstup a Doporučení

Ukaž lidský výstup toolu (s brand line) a předej jeho **Doporučení**; doplň:

- **Zadání na 1 stránku:** problém · metrika · kill kritérium · Decider.
- Tabulka: krok cesty → jméno (nebo „AI (agent), podepisuje X“) → jádro/okno
  → termín okna.
- Rizika z `doctor` (pokud jsme pokračovali vědomě) — **vždy s vlastníkem
  a termínem**, ne anonymně: preview / CI → zástupce **provozu**, lockfile /
  testy → zástupce **vývoje** (jména z kroků cesty v projektu), termín
  „před Buildem“. Např. „⚠ preview chybí — Tomáš (provoz), před Buildem.“

### Commit po Kickoffu

Připomeň commit i s tím, co Kickoff vytvořil: `.pflanzer/decisions/`
a `tests/acceptance/` (vedle `docs`, `.pflanzer`, `tests`):
`git add -A docs .pflanzer tests .gitignore .claude && git commit -m "chore(pflanzer): kickoff" && git push -u origin HEAD`.
Specy v `.pflanzer/specs/` se necommitují.

### Pozvánky pro okna (napiš rovnou, nečekej na další pokyn)

Po Kickoffu **hned vygeneruj** krátké texty (3–4 řádky) pro každého
zástupce okna, se skutečnými jmény a termíny z projektu. Podle jeho role
card (`docs/methodology/role-cards/`, pro projekt
`pflanzer roles cards --slug <slug>`):

- **kdy** (termín okna) a **na jak dlouho** (Decider 15 + 90 min,
  bezpečnost & právo 20 min, provoz 20 min),
- **co přinést / co uvidí:**
  - bezpečnost & právo: „co aplikace čte, kam píše, jestli vidí reálná
    data“ (3 věty ti pošle PdM předem), plus strop nákladů AI,
  - provoz: rollback, kdo je na telefonu, první hodina po nasazení,
  - Decider: že na Rozhodnutí uvidí varianty běžet, rozhodne Go / Iterate /
    Kill a jeho rozhodnutí se zapíše pod jeho jménem,
  - člověk podepisující AI náhradu: co přesně potvrzuje a do kdy (48 h),
- **co udělá na konci** (podpis `pflanzer checkpoint …` nebo Go/Kill).

Posílá je člověk; ty jen napíšeš text.

### Co je dalším krokem

**Právě jeden**, a není to automaticky `/pm build`:

1. chybí jméno podepisujícího (AI náhrada bez určeného člověka) → dalším
   krokem je sehnat ho (konkrétně: koho z pořadí výše oslovit a do kdy),
2. nejsou zabookovaná okna → zabookovat je (kdo, kdy),
3. chybí preview URL → navrhni konkrétního člověka (zástupce provozu
   z projektu) a termín, ne „domluvte s provozem“,
4. jinak `/pm build`.

Nikdy dvě otázky najednou. Žargon (Async, Decider, checkpoint, stupeň Lean)
vysvětli při prvním použití jednou větou; „připraveno ke Kickoffu“ z doctoru
neopakuj, jen otevřené výhrady jednou větou.

Na konci **jeden** další krok:

> Další krok (jen když nic z výše chybí): `/pm build <slug>` — jádro, 3 h
> (Decider u stavby není; chce-li vidět, nabídni 10min screencast a demo
> na Rozhodnutí).

## Co NEDĚLAT

- Neptej se na víc než výše a nenabízej AI náhradu byznysu ani vývoji — detail (triage, roles, plný Charter) je
  volitelný a patří do regulovaných projektů (`/pm roles`, `/pm triage`).
- Nezaváděj Sessions, Slices ani jiné výrazy; terminologie: Kickoff, Build,
  Async, Rozhodnutí, Ship.
- Nezakládej projekt mimo `pflanzer quick_session bootstrap`.

## Reference

- `docs/decisions/0021-mala-skupina-cela-cesta.md`
- `docs/decisions/0022-inspirace-z-trhu.md`
- `docs/zacni.md` § Je repo připravené?
