Pflanzer Method | pflanzer.cz/method

# Role card #7 — Security / Compliance

> Máš veto na varianty s kritickým rizikem — veto je veto, ne hlas mezi hlasy.

Status v catalogu: **povinná při triggeru** · Kdy se zve: Pracujeme s daty uživatelů, auth, integracemi nebo platbami?

## Přines do Session 1
- Data Classification L1–L4 pro projekt
- STRIDE one-pager (threat model lite)
- Approved AI Tool list a sandbox spec (24h TTL)
- SSO + MFA pravidla a DORA 3rd-party checklist, pokud se týká

## Podepisuješ
- Veto registr — veto na varianty se STRIDE Critical
- Security triage a sandbox-to-prod gate
- SBOM + CVE scan a secret scan před Ship gate

## Kdy jsi v místnosti
- Quick (60–90 min) — **async**: triage je deferred — podepíšeš ji před pilotem (`/pm triage`)
- Lean (3 h) — **async**: 1-page checklist místo účasti (data L1/L2)
- Full (5–6 h) — **celá session**: jako senior delegát; triage 48–72 h předem

## Hlasuješ o
Skóruješ 4 dimenze, ale Critical riziko neřešíš hlasem: zapíšeš veto do veto registru a session pivotuje na jinou variantu.

Preference matrix: `user_value` · `effort` · `risk` · `strategic_fit`; tvoje váha: **risk**. K tomu commitment level 0–3 pro mezi-session práci.

## Okamžitě hlas
- Reálná PII / L4 data v promptu → přerušení session, incident playbook, 72h GDPR clock
- Nástroj mimo Approved AI Tool list
- Secret nebo credential v kódu varianty

## AI proxy
**Režim 1 — Vlastnické a vetovací (vždy člověk).** ❌ Veto podepisuje člověk; AI připraví STRIDE draft a SBOM / CVE scan. Sub-agent: `.claude/agents/security-expert.md`.

---

Detail: `docs/methodology/02-role-catalog.md` § 7 · stupně: `docs/methodology/00-lean-pflanzer.md` § Tři stupně jedné metody
