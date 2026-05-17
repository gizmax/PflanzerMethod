# Leading indicators — operational dashboard pro Method Steward

> **Status:** v0.3 (P1-6 z `docs/research/method-falsifiability/07-recommendations.md`).
> Operacionalizuje **Method Steward early-kill veto** z ADR-0011 a leading
> indicators z autoresearch perspektivy 01 (Method Steward, bod #5).
>
> **Cíl:** Method Steward musí mít v horizontu **T+30 dní** signál, že metoda
> neperformuje — ne až za T+6 mo. Bez leading indicators jsou kill criteria
> v `method-charter.md` (N=12 / T+18 mo) **trailing-only** a veto pravomoc je
> bezzubá.

## Proč leading indicators

ADR-0011 dává Method Stewardovi pravomoc **svolat emergency review** pokud
*„2+ leading indicators porušují threshold po dobu > 60 dní"*. Method Charter
ale neudával, **které** leading indicators měřit. Tento dokument je vyplňuje.

Lagging metrics (PflanzerIndex, re-work %, blind acceptance) jsou T+30 až T+90;
do té doby je „pilot status unknown". Leading indicators dávají signál **už
v průběhu cyklu** nebo do **2 týdnů po handoff** — to je window, kdy lze
intervenovat před harm akumulací.

## 5 leading indicators

### LI-1 — Pre-flight gate rejection rate

**Co měří:** % pre-flight triage runs, které **nedostartují Session 1** kvůli
gate failure (Security blokátor, Legal blokátor, EM capacity veto, Discovery
Readiness Gate fail).

**Formula:**
```
LI-1 = (# pilot proposals s pre-flight gate fail v rolling 90-day window)
       / (# pilot proposals v rolling 90-day window)
```

**Data source:** Pflanzer tool DB (`pre_flight_runs` tabulka) — každý pre-flight
run loguje status `passed` / `failed-{security|legal|capacity|discovery}`.

**Cadence:** Method Steward dashboard refresh weekly. Rolling 90-day window.

**Thresholds:**

| Hodnota | Stav | Action |
|---------|------|--------|
| 0 — 0.10 | Healthy | None |
| 0.10 — 0.25 | Watch | Flag v T+30 dashboard, sledovat trend |
| 0.25 — 0.40 | **Warning** | Method Steward kvalitativní review: jsou fit criteria too tight, nebo Champion pipeline submituje špatné kandidáty? |
| > 0.40 | **Veto trigger** | Pokud sustained > 60 dní → emergency review. Možné root causes: Charter scope creep, Champion training gap, org change. |
| < 0.05 (sustained 60+ d) | **Rubber-stamping risk** | Sus low rejection rate = triage je theatre. Re-audit triage rigor. |

**Interpretace:** Cíl není zero rejection — některé proposals MAJÍ failovat.
Sweet spot je 0.10-0.20 (= triage works as gate, ne jako schvalovna).

### LI-2 — Session 1 → Session 2 churn

**Co měří:** % pilotů, kteří po Session 1 **nedojdou do Session 2** (Decider
abort, Champion withdrawal, sponsor zhasnutí, fit criteria mid-flight revelation).

**Formula:**
```
LI-2 = (# pilots Session 1 completed AND Session 2 never scheduled within T+30)
       / (# pilots Session 1 completed v rolling 90-day window)
```

**Data source:** Pflanzer tool DB (`sessions` tabulka, status field).

**Cadence:** Weekly dashboard. T+30 po Session 1 = trigger window.

**Thresholds:**

| Hodnota | Stav | Action |
|---------|------|--------|
| 0 — 0.10 | Healthy | None |
| 0.10 — 0.20 | Watch | Acceptable noise (one BU pivot, sponsor unavail) |
| 0.20 — 0.35 | **Warning** | Method Steward sleduje per-Champion + per-BU breakdown |
| > 0.35 | **Veto trigger** | Sustained > 60 dní → emergency review. Možné root causes: Session 1 nedělá real alignment (jen workshop theatre), Decider eskalační protokol selhává. |

**Interpretace:** Vysoký churn = **Pflanzer cycle neabsorbuje alignment ve
své core unit (cyklus Session 1 → Session 2)**. To je signál, že metoda
generuje nadšení v místnosti, ale nepřežívá první týden reality.

### LI-3 — Champion overload

**Co měří:** Průměrný počet **active concurrent pilots per Champion**.
Nadměrné = burn-out a poklesající compliance score.

**Formula:**
```
LI-3 = mean(# active pilots assigned to Champion C, for each Champion C in pool)
       computed weekly over rolling 30-day window
```

**Active pilot:** mezi Session 1 sign-off a T+90 reinforcement readout.

**Data source:** Pflanzer tool DB (`pilots.champion_id` + status).

**Cadence:** Weekly dashboard.

**Thresholds:**

| Hodnota | Stav | Action |
|---------|------|--------|
| 0.5 — 1.5 | Healthy | Normal allocation |
| 1.5 — 2.5 | Watch | Sledovat compliance score correlation (LI-5 cross-check) |
| 2.5 — 3.5 | **Warning** | Champion pipeline pod tlakem — buď hire-train víc Champions, nebo throttle Session 1 cadence |
| > 3.5 | **Veto trigger** | Champion burnout imminent. Compliance score historically degrades. Sustained > 60 dní → emergency review. |
| **Per-Champion max > 4** kdykoli | **Hard alert** | Single Champion overload = single point of failure. Method Steward immediate redistribution. |

**Interpretace:** Pflanzer kvalita závisí na Champion bandwidth. LI-3 je
proxy pro *„will Compliance Score degrade in next cohort?"*. ADR-0006
(Champion bootstrap) připomíná: Champion pipeline must scale s pilot
throughput.

### LI-4 — Decider tie-breaker frequency

**Co měří:** % Session 2 rozhodnutí, kde **Decider override-uje silent-vote
výsledek** (anti-HiPPO byl výzva, ale nebyl použit jako shared decision).

**Formula:**
```
LI-4 = (# Session 2 decisions kde Decider final pick ≠ majority silent vote)
       / (# Session 2 decisions celkem v rolling 90-day window)
```

**Data source:** Pflanzer tool DB `session_2_decisions` tabulka — silent_vote_winner
+ decider_final_pick fields. Compliance Score element #8 audit cross-check.

**Cadence:** Weekly dashboard.

**Thresholds:**

| Hodnota | Stav | Action |
|---------|------|--------|
| 0 — 0.15 | Healthy | Decider follows team alignment (anti-HiPPO works) |
| 0.15 — 0.30 | Watch | Některé override-y normální (Decider má context, který tým nemá) |
| 0.30 — 0.50 | **Warning** | Anti-HiPPO mechanism degraduje; Method Steward kvalitativní review (decision logs) |
| > 0.50 | **Veto trigger** | Silent voting je theatre — Decider rozhoduje předem a tým je co-located rubber-stamp. Sustained > 60 dní → emergency review. Charter sign-off byl naive. |
| < 0.05 (sustained 90+ d) | **Echo chamber risk** | Suspicious low — tým buď přesně předvídá Decidera (= co-optation), nebo silent vote není svobodný. Re-audit facilitation. |

**Interpretace:** Anti-HiPPO je core differentiator Pflanzeru (per `09-srovnani-...md`).
LI-4 sleduje, jestli ho organizace **operacionálně** používá, nebo jen formálně.

### LI-5 — Throwaway → Evolve slip rate

**Co měří:** % pilotů, které začaly s **`throw-away` flag** v Charteru (ADR-0005
default) a **mid-cycle pivot na `evolve`** bez formal sign-off (FE + EM + Security
+ Legal + Platform per ADR-0005).

**Formula:**
```
LI-5 = (# pilots s charter.flag = throwaway AND post-handoff prototype routed to
        production/customer-facing AND missing one or more required evolve sign-offs)
       / (# pilots celkem completed v rolling 90-day window)
```

**Data source:**
- Pflanzer tool DB `pilots.throwaway_flag` (initial) + `pilots.evolve_signoffs` array.
- Cross-check: Audit log of sandbox URL access logs (per Platform Triage spec) —
  pokud sandbox URL je accessed > 24h TTL nebo z external IP, flag.

**Cadence:** Weekly dashboard + handoff completion trigger.

**Thresholds:**

| Hodnota | Stav | Action |
|---------|------|--------|
| 0 — 0.05 | Healthy | Throw-away default is enforced |
| 0.05 — 0.15 | Watch | Sledovat per-sponsor pattern (jedna BU evade?) |
| 0.15 — 0.30 | **Warning** | Throw-away default deteriorating; Method Steward review of sponsor education |
| > 0.30 | **Veto trigger** | Charter sign-off discipline broken. Sustained > 60 dní → emergency review + **stopping-for-harm escalation** (per Method Charter § Kill criteria). Production-by-stealth risk (Útok 5 DEFERRED v0.3 — re-eskalovat na FULL FIX). |
| **Single L4 data leak event** | **Hard alert** | Immediate CISO escalation, ne čekat na threshold. Method Charter Sunset trigger candidate. |

**Interpretace:** LI-5 je **safety guardrail**. Pflanzer hodnotová proposice
*„rapid prototyping"* závisí na throw-away default. Slip do evolve bez sign-off
= organizace metodu používá pro production-by-stealth, čímž ji **zničí
governance trust** (Útok 5 vector).

## Dashboard layout

Method Steward má **single-pane weekly dashboard**:

```
┌─────────────────────────────────────────────────────────────────────┐
│  Pflanzer Method Dashboard — week of 2026-MM-DD                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  LEADING INDICATORS (rolling 90d)        STATUS    TREND   DAYS BAD  │
│  ─────────────────────────────────────   ──────    ─────   ────────  │
│  LI-1 Pre-flight rejection rate           0.18     ↗        0       │
│         [Healthy:0-0.10 Watch:-0.25 Warn:-0.40 Veto:>0.40]           │
│  LI-2 S1→S2 churn                         0.08     →        0       │
│         [Healthy:0-0.10 Watch:-0.20 Warn:-0.35 Veto:>0.35]           │
│  LI-3 Champion overload (mean active)     2.1      ↗        12      │
│         [Healthy:0.5-1.5 Watch:-2.5 Warn:-3.5 Veto:>3.5]             │
│  LI-4 Decider override rate               0.22     →        0       │
│         [Healthy:0-0.15 Watch:-0.30 Warn:-0.50 Veto:>0.50]           │
│  LI-5 Throwaway→Evolve slip               0.04     ↘        0       │
│         [Healthy:0-0.05 Watch:-0.15 Warn:-0.30 Veto:>0.30]           │
│                                                                      │
│  ACTIVE PILOTS: 7 (5 Pflanzer, 2 Pflanzer-inspired pending audit)   │
│  RECENT COMPLIANCE SCORES: 11, 12, 9*, 10, 12 (* = inspired tier)   │
│                                                                      │
│  ALERT STATE: 0 veto triggers, 1 watch (LI-3 trending up)            │
│  NEXT REVIEW: Q-end aggregation 2026-MM-DD                           │
└─────────────────────────────────────────────────────────────────────┘
```

**Dashboard implementation:** Confluence template (v0) nebo Notion DB (v0.1)
nebo Pflanzer tool view (v0.2, P2 work). MVP = manual update weekly v Confluence
table; data sourcing přes Pflanzer tool API queries.

## Veto trigger workflow

Pokud **2+ indicators** porušují threshold > 60 dní (sustained), Method Steward
**MUSÍ** do 7 dní:

1. **Publikovat 1-page alert** do Process Portfolio Review meeting agenda.
2. **Svolat emergency method-level review** (per ADR-0011) — 60-min dedicated
   meeting, Method Decider + 3 BU Champions + Method Steward.
3. **Pre-read 2-pager** s:
   - Indicator history (90-day chart).
   - Possible root causes (qualitative hypothesis).
   - Recommended action: Iterate (Charter amendment), Pause (no new pilots
     until cause addressed), Sunset (early kill).
4. **Decision log signed** v meetingu, ADR commit pokud Sunset / Iterate.

**Single „hard alert" trigger** (LI-5 L4 leak, LI-3 per-Champion > 4) =
**immediate notification** (within 24 h), ne čekat na 60-day threshold.

## Cross-cuts s ADR-0013 Compliance Score

Leading indicators jsou **process metrics** (jak metoda probíhá).
Compliance Score je **artifact metric** (co metoda vyprodukovala).
Korelace pozorovat (Method Steward T+6 analysis):

- LI-3 ↑ (Champion overload) by mělo korelovat s Compliance Score ↓ (rushed
  pilots = missed elements).
- LI-4 ↑ (Decider override) by mělo korelovat s Compliance element #8 fail
  (decider voted last not enforced).
- LI-5 ↑ (throwaway slip) by mělo korelovat s element #10 fail (throwaway/evolve
  flag missing or wrong).

Pokud korelace **chybí**, je to signál, že buď indicators nebo Compliance Score
měří špatnou věc — Method Steward T+12 review item.

## Out of scope (deferred)

- **Quantitative correlation analysis** mezi LIs a PflanzerIndex (potřebuje
  N=12+ pilotů s data) — P2 academic track.
- **Predictive model** (ML-based kill prediction) — P3, vyžaduje > 30 pilotů.
- **Per-BU dashboard slicing** — P2 (po Pflanzer tool DB schema extension).
- **Real-time alerting** (Slack / email push) — P2 tool work.

## Reference

- ADR-0011 — Method Decider profile + Default Sunset (early-kill veto authority).
- ADR-0013 — Pre-registration + Compliance Score (cross-cut).
- ADR-0005 — Throw-away vs evolve prototype (LI-5 trigger).
- ADR-0006 — Champion bootstrap (LI-3 context).
- Method Charter v0.3 § Validační loop & sunset.
- `docs/research/method-falsifiability/01-method-steward.md` bod #5 + #7.
- `docs/research/method-falsifiability/07-recommendations.md` P1-6.