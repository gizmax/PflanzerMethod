# Governance — audit-grade vrstva

**Pflanzer Method | pflanzer.cz/method**

> Tato složka **není součástí běžné cesty**. Default profil
> (`docs/methodology/00-lean-pflanzer.md`) ji nepotřebuje. Sáhni sem, jen
> pokud platí některý trigger níže (per ADR-0021).

## Kdy sem sáhnout

| Trigger | Co přidat | Kde |
|---------|-----------|-----|
| AI Act High-risk (čl. 6 + Annex III) | Fáze A/B/C klasifikace, DPIA, human-oversight design | `docs/methodology/03-pre-session-priprava.md` § Legal & Privacy Triage |
| DORA scope (banky, pojišťovny EU) | prompt audit log, 7letá retence, 3rd-party register | `docs/methodology/03-pre-session-priprava.md` § Security & Data Triage |
| Public sector / zvláštní kategorie dat | DPIA full, RoPA, Privacy Notice | tamtéž |
| Rollout metody napříč organizací (3+ pilotů) | Method Steward, Method Decider + sunset, pre-registrace, Compliance Score, PflanzerIndex, leading indicators | `method-charter.md`, `leading-indicators.md`, ADR-0007/0011/0012/0013/0014 |
| Vývojáři nejsou k dispozici a platí 1 ze 4 hard triggerů | Track S — precision spec místo produktu | ADR-0020, `tool/templates/precision-spec-track-s.md.template` |

## Obsah

- `method-charter.md` — method-level Charter (success threshold, sunset,
  metriky napříč piloty).
- `leading-indicators.md` — LI-1 až LI-5 pro method-level dashboard.
- Související ADR (zůstávají v `docs/decisions/`):
  - ADR-0007 — method-level Charter
  - ADR-0011 — Method Decider profile + default sunset
  - ADR-0012 — Method Steward operational scope
  - ADR-0013 — pre-registrace + Compliance Score
  - ADR-0014 — PflanzerIndex (composite metrika)
  - ADR-0020 — Track P / Track S

## Pravidlo

Governance vrstva **přidává** artefakty a podpisy, ale **nemění** základní
model ADR-0021: malé jádro, zástupce každého kroku cesty, okna místo stálé
účasti. Regulace typicky znamená delší checkpoint bezpečnosti & práva
a víc podpisů, ne víc lidí v místnosti.
