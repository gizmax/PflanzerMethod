# Pflanzerova metoda

> Univerzální corporate framework pro zrychlení agentního vývoje od nápadu po handoff
> tím, že se všechny zainteresované role sejdou v jedné místnosti s AI co-pilotem
> a společně provibekódují 1–3 funkční prototypy.

## Co řeší

V korporátu typicky cesta od nápadu k funkční fíčuře trvá měsíce: zadavatel pinká
s produktem, produkt s vývojem, schvalovací kola, security audit, atd. Metoda to
zkracuje na **jednu in-room session** (60–90 min) — tým se sejde, společně
provibe-koduje 2–3 varianty, hned se rozhodne. Žádné kolečka iterací mezi sessions.

## Quick start (in-room session, 60–90 min)

Sednete si s týmem (4–6 lidí, jeden notebook na velkém TV) a v Claude Code spustíte:

```
/pflanzer "chceme zlepšit X"
```

Wizard provede 5 kroky:

1. **HOOK** — co dnes řešíte? (1 věta)
2. **DECIDER + ROOM** — kdo má hlas? Decider single-select + 5–6 rolí multi-select.
3. **RISK PROFILE** — Throwaway proto / Pilot / Production. Jeden klik.
4. **BUILD** — AI vyplivne 2–3 copy-paste prompts pro Bolt / v0 / Cursor.
   Tým se rozdělí po dvojicích a paralelně buildí 15–30 min.
5. **VOTE + DECIDER's CALL** — silent dot voting + Decider rozhoduje shortlist.
6. **HANDOFF** — 1-page MD: kdo / co / do kdy / kill criteria. Vyhoď na TV.

Pod kapotou: Charter (ADR-0004) + 18-position role catalog + builder decision +
preference matrix s AI-only deflation + audit log s DORA 7-letou retencí.
**Sofistikovanost zachovaná, UX zjednodušeno.**

## Plný flow (pokud potřebuješ celé)

Pro audit-grade projekty (regulated SDLC, AI Act high-risk, multi-team scope):

```
/pflanzer-charter <slug>     # Plný Charter wizard (XYZ, kapacita, Decider mandate, …)
/pflanzer-roles <slug>       # Decision tree pro 18 rolí
/pflanzer-triage <slug>      # 4 paralelní triage tracks (Discovery + Security + Legal + Platform)
/pflanzer-session-1 <slug>   # Session 1 orchestrator (5–6 h)
# … mezi-session 5–7 dní (web hub) …
/pflanzer-session-2 <slug>   # Session 2 (decisional, 3 h) — TBD Slice 7
/pflanzer-handoff <slug>     # Handoff package (BE/FE/QA/Platform) — TBD Slice 8
```

## Klíčový pilíř — role catalog

Místo fixní sady stakeholderů má metoda **knihovnu 18 rolí**. Před každým
projektem si tým vybere relevantní podmnožinu (decision tree). AI panel pak
v session zapojí právě tyhle role — žádný overhead, žádné chybějící vstupy.

Detail: [`docs/methodology/02-role-catalog.md`](docs/methodology/02-role-catalog.md).

## Status

✅ **Fáze 1** — autoresearch & dokumentace metodiky (v0.2.1, ADR-0008 form-factor)
🚧 **Fáze 2** — implementace toolu (probíhá)
- Slice 1 ✅ Charter wizard
- Slice 2 ✅ Role selection
- Slice 3 ✅ Pre-flight triage (4 paralelní agents)
- Slice 4 ✅ Web hub MVP (FastAPI + React + Vite + nginx)
- Slice 5 ✅ Session 1 orchestrator (facilitator + 17 role experts)
- **`/pflanzer` quick wizard** ✅ — single-entry pro in-room session
- Slice 6 ⏳ Mezi-session feedback collection
- Slice 7 ⏳ Session 2 (decisional)
- Slice 8 ⏳ Handoff package generator

## Struktura repa

```
docs/
├── methodology/         # finální metoda v češtině (9 dokumentů)
├── research/
│   ├── baseline/        # adjacent metody, vibe-coding tools, change-mgmt
│   ├── perspectives/    # raw výstupy expertního panelu (1 .md / role)
│   └── synthesis/       # pracovní syntézy, conflict matrix, devil's advocate
└── decisions/           # ADR (Architecture Decision Records)

tool/
├── cli/                 # Python backend (charter, roles, triage, session, quick)
├── db/                  # SQLite schema + migrate
├── data/                # role_catalog.json
└── web/                 # FastAPI backend + React frontend (Hybrid form-factor)

.claude/
├── commands/            # slash commands (/pflanzer, /pflanzer-charter, …)
└── agents/              # 23 sub-agentů (1 facilitator + 17 role experts + 5 triage)
```

## Setup (lokálně)

```bash
# Inicializace DB
python3 tool/db/migrate.py

# Web hub (volitelně, pro async mezi-session feedback)
cd tool/web/backend && uvicorn main:app --reload --port 8000 &
cd tool/web/frontend && npm install && npm run dev
```

Pak stačí v Claude Code:

```
/pflanzer "tvůj problém v jedné větě"
```

## Plán fáze 2 (full)

Detailní plán: [`~/.claude/plans/recursive-cuddling-sonnet.md`](../../.claude/plans/recursive-cuddling-sonnet.md)

## Konvence

- Dokumentace metodiky: **čeština**
- Code, comments v toolu: EN, dle CLAUDE.md
- Git workflow: feature-branche + lokální merge `--no-ff` (NIKDY commit přímo na main)
- ADR formát: `docs/decisions/NNNN-short-slug.md`
