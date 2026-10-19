Pflanzer Method | pflanzer.cz/method

# Role card #7 — Security / Compliance

> Za 20 minut potvrdíš tři věci: (1) jaká data AI vidí, (2) kam smí síť, (3) kolik smí AI stát. Podpis: `pflanzer checkpoint --slug <slug> bezpecnost --by <jméno> --note …`.

**Krok cesty:** Bezpečnost & právo · **Kde jsi:** okno — checkpoint 20 min v posledních 30 min Buildu (stačí Security nebo Legal / DPO)

Status v catalogu: **povinná při triggeru** · Kdy se zve: Pracujeme s daty uživatelů, auth, integracemi nebo platbami?

## Přines do svého okna
- Jaká data AI vidí: žádná produkční data a osobní údaje v preview, promptech ani repu
- Kam smí síť: co smí agent a preview volat ven (default nic mimo povolený seznam)
- Kolik smí AI stát: strop tokenů / nákladů a kdo ho hlídá
- Pro hlubší kontrolu (stupeň Full): STRIDE one-pager, třídy dat L1–L4, Approved AI Tool list a sandbox spec, SSO + MFA, DORA 3rd-party checklist

## Podepisuješ
- Checkpoint bezpečnost & právo: `pflanzer checkpoint --slug <slug> bezpecnost --by <jméno> --note …` (blokace: přidej `--blocked`)
- Veto na variantu s kritickým rizikem (zapíše se do veto registru)
- Pro hlubší kontrolu (stupeň Full): SBOM + CVE scan a secret scan před Shipem

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
**Režim 1 — Vlastnické a vetovací (vždy člověk).** Může tě nahradit AI? **Jen jako předkontrola** (ADR-0023): `pflanzer checkpoint … --ai --agent security-expert` zapíše návrh. U throwaway stačí, u pilotu a produkce podepíše člověk do 48 h, jinak Ship blokuje. Veto je vždy člověk. Sub-agent: `.claude/agents/security-expert.md`.

---

Detail: `docs/methodology/02-role-catalog.md` § 7 · stupně: `docs/methodology/00-lean-pflanzer.md` § Tři stupně jedné metody
