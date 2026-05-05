# Pflanzerova metoda

> Univerzální corporate framework pro zrychlení agentního vývoje od nápadu po handoff
> tím, že se všechny zainteresované role sejdou v jedné místnosti s AI co-pilotem
> a společně provibekódují 1–3 funkční prototypy.

## Co řeší

V korporátu typicky cesta od nápadu k funkční fíčuře trvá měsíce: zadavatel pinká
s produktem, produkt s vývojem, schvalovací kola, security audit, atd. Metoda to
zkracuje na **dvě intenzivní sessions** s předem připraveným kontextem a AI panelem
expertů.

## Klíčový pilíř — role catalog

Místo fixní sady stakeholderů má metoda **knihovnu rolí** (~15 perspektiv).
Před každým projektem si tým vybere relevantní podmnožinu. AI panel pak v session
zapojí právě tyhle role — žádný overhead, žádné chybějící vstupy.

## Status

🚧 **Fáze 1 — autoresearch & dokumentace metodiky** (probíhá)
⏳ Fáze 2 — návrh & implementace toolu (po schválení fáze 1)

## Struktura repa

```
docs/
├── methodology/      # finální metoda v češtině (9 dokumentů)
├── research/
│   ├── baseline/     # adjacent metody, vibe-coding tools, change-mgmt
│   ├── perspectives/ # raw výstupy expertního panelu (1 .md / role)
│   └── synthesis/    # pracovní syntézy, conflict matrix, devil's advocate
└── decisions/        # ADR (Architecture Decision Records)
```

## Plán fáze 1

Detailní plán: [`/Users/gizmax/.claude/plans/recursive-cuddling-sonnet.md`](../../.claude/plans/recursive-cuddling-sonnet.md)

## Konvence

- Dokumentace metodiky: **čeština**
- Code, comments v toolu (fáze 2): EN, dle CLAUDE.md
- Git workflow: feature-branche + PR (NIKDY commit přímo na main mimo bootstrap)
- ADR formát: `docs/decisions/NNNN-short-slug.md`
