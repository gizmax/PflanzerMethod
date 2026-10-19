Pflanzer Method | pflanzer.cz/method

# Role card #7 — Security / Compliance

> Zastupuješ krok bezpečnost & právo a máš veto na varianty s kritickým rizikem — veto je veto, ne hlas mezi hlasy.

**Krok cesty:** Bezpečnost & právo · **Kde jsi:** okno — checkpoint 20 min v posledních 30 min Buildu (stačí Security nebo Legal / DPO)

Status v catalogu: **povinná při triggeru** · Kdy se zve: Pracujeme s daty uživatelů, auth, integracemi nebo platbami?

## Přines do svého okna
- Data classification L1–L4 pro projekt
- STRIDE one-pager (threat model lite): datový tok, egress limit, riziko prompt injection
- Strop tokenů / nákladů a Approved AI Tool list se sandbox spec (24h TTL)
- SSO + MFA pravidla a DORA 3rd-party checklist, pokud se týká

## Podepisuješ
- Checkpoint bezpečnost & právo: `pflanzer checkpoint --slug <slug> bezpecnost --by JMÉNO --note …` (blokace: přidej `--blocked`)
- Veto registr — veto na varianty se STRIDE Critical
- SBOM + CVE scan a secret scan před Shipem

## Kdy jsi u toho
- Quick (60–90 min) — **async**: checkpoint se odkládá — před pilotem ho doběhneš (`/pm triage`) a podepíšeš
- Lean (3 h) — **async**: checkpoint 20 min nad datovým tokem + 1-page checklist (data L1/L2)
- Full (5–6 h) — **celý běh**: senior delegát; 4 triage tracky 48–72 h předem

## Hlasuješ o
Skóruješ 4 dimenze, ale Critical riziko neřešíš hlasem: zapíšeš veto do veto registru a Build pivotuje na jinou variantu.

Preference matrix: `user_value` · `effort` · `risk` · `strategic_fit`; tvoje váha: **risk**. K tomu commitment level 0–3 pro Async okno.

## Okamžitě hlas
- Reálná PII / L4 data v promptu → přerušení Buildu, incident playbook, 72h GDPR clock
- Nástroj mimo Approved AI Tool list
- Secret nebo credential v kódu varianty

## AI proxy
**Režim 1 — Vlastnické a vetovací (vždy člověk).** ❌ Veto podepisuje člověk; AI připraví STRIDE draft a SBOM / CVE scan. Sub-agent: `.claude/agents/security-expert.md`.

---

Detail: `docs/methodology/02-role-catalog.md` § 7 · stupně: `docs/methodology/00-lean-pflanzer.md` § Tři stupně jedné metody
