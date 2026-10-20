---
description: Spustí 4 paralelní pre-flight triage sub-agents (Discovery + Security + Legal + Platform) a aggregeguje gate decision.
---

> **Pokročilé / volitelné.** Není součást hlavní cesty (`/pm` + 5 kroků + 3 pravidla). Použij u regulovaných nebo větších projektů; pro běžný pilot stačí jména zástupců na Kickoffu (`/pm start`).

# Triage — pre-flight (pokročilé)

> **Cesty:** soubory `docs/…` a `tool/…` zmíněné níže leží v kořeni metody
> (`pflanzer root`), ne v target repu. Tool spouštěj vždy přes `pflanzer <cmd>`
> (funguje z libovolného adresáře), DB je na `pflanzer db`.

Argumenty: `$ARGUMENTS` = projekt slug. Předpokládá `projects.status='charter'`
(= proběhl Kickoff (`/pm start`)) a alespoň 1 row v `roles` (= proběhl
`/pm roles`).

## Co tento command dělá

Aplikuje **Krok 0 + 0a** z `docs/methodology/03-pre-session-priprava.md`:
1. **Krok 0** — Discovery Readiness Gate (sub-agent `discovery-readiness`).
2. **Krok 0a** — 3 paralelní triage tracks (Security / Legal / Platform).

Pokud kterýkoliv track = `blocked` → Session 1 nestartuje, vrátí důvod.
Pokud všechny `ok` nebo `deferred` → status projektu posune na `triage`.
Track, který AI subagent vrátil jako `ok` bez lidského `signed_by`, se zapíše jako
`pending` (čeká na podpis <jméno>) — výstup i `_summary.md` to ukážou; Build smí běžet,
Ship ale bez podpisu (`pflanzer checkpoint …`) neprojde.

## Jak postupuj

1. **Validuj**: slug + projekt existuje + status='charter' + roles count > 0.
   Pokud chybí, instruuj uživatele co spustit nejdřív.

2. **Spusť 4 paralelní sub-agents** v JEDNÉ zprávě s 4 Agent tool calls:

```
Agent(subagent_type="discovery-readiness", prompt="Run Discovery Readiness Gate for slug=<slug>. Read $(pflanzer data)/charters/<slug>.md. Return JSON per agent definition.")
Agent(subagent_type="security-triage", prompt="Run Security & Data Triage for slug=<slug>. Return JSON.")
Agent(subagent_type="legal-triage", prompt="Run Legal & Privacy Triage for slug=<slug>. Return JSON.")
Agent(subagent_type="platform-triage", prompt="Run Platform Triage for slug=<slug>. Return JSON.")
```

   Každý sub-agent vrátí JSON s polem `track`, `status`, `artefact_md`,
   `signed_by`, `rationale` + track-specific fields.

3. **Sestav JSON spec** s 4 výsledky a předej do `tool/cli/triage.py`:

```bash
pflanzer triage --spec /tmp/<slug>-triage-spec.json
```

JSON spec format:
```json
{
  "slug": "demo-widget",
  "results": [
    {"track": "discovery", "status": "ok", "artefact_md": "...", "signed_by": "...", "rationale": "..."},
    {"track": "security", "status": "ok", "data_class": "L2", "ai_act_tier": "minimal", ...},
    {"track": "legal", "status": "ok", "ai_act_tier": "minimal", "dpia_required": false, ...},
    {"track": "platform", "status": "ok", "sandbox_url": "...", ...}
  ]
}
```

   **Podmínky a blokace.** Každý track vrací podmínky se stabilním ID (`conditions`:
   `[{"id": "K1", "text": "…"}]`, v `artefact_md` řádky `- [K1] text` pod `## Podmínky`;
   Security `K`, Legal `D`, Platform `PROD-B`, Discovery `C`). Nástroj je uloží, podpis okna
   (`pflanzer checkpoint …`) je převezme do podmínek okna (podepisující je tím potvrzuje;
   vědomé odpuštění: `--waive K3 --rationale "proč"`), SHIP.md, PR checklist a `compliance.md`
   je ukážou a `pflanzer prompts` je přidá builderům jako „Omezení z triage“
   (security/legal/platform). Po triage `pflanzer status` řekne, že triage změnila zadání —
   zvaž úpravu Charteru.

   **Opt-out z Discovery.** Výsledek `discovery` s `status: "deferred"`, `signed_by` = jméno
   Decidera, `rationale: "opt-out: <důvod>"`. Opt-out jako `ok`, bez důvodu nebo se špatným
   `discovery_debt_score` (číslo 0–10) CLI odmítne s českou chybou a příkladem.

4. **Verifikuj output**:
   - Read `data/triage/<slug>/_summary.md`.
   - Pokud overall='blocked', shrň důvody uživateli a navrhni nápravu.
   - Pokud overall='pending', vypiš, kdo má které okno podepsat (warnings v `_summary.md`).
   - Pokud discovery vrátilo opt-out, ukaž ho a zdůvodnění (zapsáno do audit logu).
   - Pokud overall='ok', připomeň pre-flight checklist
     (`docs/methodology/03-pre-session-priprava.md` § Checklist před Kickoffem).

5. **Sjednoť AI Act tier + Data class** s Charterem:
   - Security a Legal triage vrátí AI Act tier — pokud se liší od Charteru,
     update projects.ai_act_tier (Legal má precedence).
   - Security vrátí data_class — pokud se liší od Charteru (z slice 1),
     update projects.data_class (Security má precedence).

6. **Souhrn pro uživatele**:
   - Tabulka 4 tracks × status.
   - Blockers + warnings.
   - Next krok: `/pm build <slug>` (jen pokud ok).

## Co NEDĚLAT

- Nepřeskakuj žádný ze 4 tracks — všechny POVINNÉ.
- Pokud Discovery debt skóre ≥ 7 → návrh 2-week Discovery Sprint, neforce
  pokračování.
- Pokud Legal DPIA ≥ 2 triggery → block, ne deferred.
- Pokud Security data_class = L4 → block (session se nekoná).

## Reference

- `docs/decisions/0002-pre-flight-triage-tracks.md`
- `docs/methodology/03-pre-session-priprava.md` § Krok 0 + Krok 0a
- `.claude/agents/{discovery-readiness,security-triage,legal-triage,platform-triage}.md`
