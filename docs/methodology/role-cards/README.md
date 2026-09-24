Pflanzer Method | pflanzer.cz/method

# Role cards — jedna strana na roli

> Generováno z `tool/data/role_catalog.json` (sekce `card`) příkazem
> `python3 tool/cli/roles.py cards --all`. **Needitovat ručně** — test
> `tests/test_role_cards.py` hlídá, že karty odpovídají generátoru.

Sponzor, Security ani UX nemusí číst celou metodiku: každá karta na jedné
straně říká, co do Session 1 přinést, co role podepisuje, kdy je v místnosti
(Quick / Lean / Full), na co hlasuje a co má okamžitě nahlásit. Detail role
je v `docs/methodology/02-role-catalog.md`.

Pro konkrétní projekt vygeneruj karty se jmény, Deciderem, termíny a stupněm:
`python3 tool/cli/roles.py cards --slug <slug>` → `data/role-cards/<slug>/`.

| # | Role | Status v catalogu | AI proxy | Karta |
|---|------|-------------------|----------|-------|
| 1 | Zadavatel / Business owner | povinná | Režim 1 — Vlastnické a vetovací (vždy člověk) | [01-zadavatel-business-owner.md](01-zadavatel-business-owner.md) |
| 2 | Produkt manažer | povinná | Režim 1 — Vlastnické a vetovací (vždy člověk) | [02-produkt-manazer.md](02-produkt-manazer.md) |
| 3 | Facilitátor (lidský + AI) | povinná | Režim 1 — Vlastnické a vetovací (vždy člověk) | [03-facilitator-lidsky-ai.md](03-facilitator-lidsky-ai.md) |
| 4 | Frontend / Vibe-coding lead | doporučená | Režim 2 — Konzultativní (AI proxy + human sign-off 24-48 h) | [04-frontend-vibe-coding-lead.md](04-frontend-vibe-coding-lead.md) |
| 5 | Backend / API lead | doporučená | Režim 2 — Konzultativní (AI proxy + human sign-off 24-48 h) | [05-backend-api-lead.md](05-backend-api-lead.md) |
| 6 | UX / Designer | doporučená | Režim 2 — Konzultativní (AI proxy + human sign-off 24-48 h) | [06-ux-designer.md](06-ux-designer.md) |
| 7 | Security / Compliance | povinná při triggeru | Režim 1 — Vlastnické a vetovací (vždy člověk) | [07-security-compliance.md](07-security-compliance.md) |
| 8 | QA / Test lead | povinná při triggeru | Režim 2 — Konzultativní (AI proxy + human sign-off 24-48 h) | [08-qa-test-lead.md](08-qa-test-lead.md) |
| 9 | Engineering manager | doporučená | Režim 1 — Vlastnické a vetovací (vždy člověk) | [09-engineering-manager.md](09-engineering-manager.md) |
| 10 | Legal / GDPR / DPO | doporučená | Režim 2 — Konzultativní (AI proxy + human sign-off 24-48 h) | [10-legal-gdpr-dpo.md](10-legal-gdpr-dpo.md) |
| 11 | Accessibility expert | doporučená (default-on) | Režim 2 — Konzultativní (AI proxy + human sign-off 24-48 h) | [11-accessibility-expert.md](11-accessibility-expert.md) |
| 12 | Data / Analytics | doporučená | Režim 2 — Konzultativní (AI proxy + human sign-off 24-48 h) | [12-data-analytics.md](12-data-analytics.md) |
| 13 | Customer support proxy | doporučená | Režim 2 — Konzultativní (AI proxy + human sign-off 24-48 h) | [13-customer-support-proxy.md](13-customer-support-proxy.md) |
| 14 | End-user proxy / User research | doporučená (default-on) | Režim 2 — Konzultativní (AI proxy + human sign-off 24-48 h) | [14-end-user-proxy-user-research.md](14-end-user-proxy-user-research.md) |
| 15 | DevOps / Platform | doporučená | Režim 2 — Konzultativní (AI proxy + human sign-off 24-48 h) | [15-devops-platform.md](15-devops-platform.md) |
| 16 | UX writer / Content designer | volitelná (trigger) | Režim 2 — Konzultativní (AI proxy + human sign-off 24-48 h) | [16-ux-writer-content-designer.md](16-ux-writer-content-designer.md) |
| 17 | Champion / Pilot lead | volitelná (trigger) | Režim 1 — Vlastnické a vetovací (vždy člověk) | [17-champion-pilot-lead.md](17-champion-pilot-lead.md) |
| 18 | Solution / Domain architect | volitelná (trigger) | Režim 2 — Konzultativní (AI proxy + human sign-off 24-48 h) | [18-solution-domain-architect.md](18-solution-domain-architect.md) |
