# Web hub — autentizace (dev vs. OIDC)

**Pflanzer Method | [pflanzer.cz/method](https://pflanzer.cz/method)**

Feedback z mezi-session okna musí mít auditovatelnou atribuci hodnotitele
(SSO ID, ne anonym) — AI Act čl. 14 (lidský dohled) a DORA (audit trail).
Backend proto identitu nikdy nebere z formuláře, ale z hlaviček, které
nastaví reverse proxy po přihlášení přes firemní IdP.

## Módy (`PFLANZER_HUB_AUTH_MODE`)

| Mód | Kdy | Identita | Bez identity |
|---|---|---|---|
| `oidc` (default) | nasazení ve firmě | `X-Forwarded-Email` → `X-Forwarded-User` z oauth2-proxy | HTTP 401 |
| `dev` | `run-local.sh`, `docker compose up` bez `.env` | navíc `X-User` z klienta | `anonymous@web-hub` |

`/api/health` je vždy bez autentizace. Neznámá hodnota módu = `oidc` (fail closed).
`dev` mód nikdy nepouštěj mimo localhost — `X-User` si klient napíše sám.

## Nasazení ve firmě (OIDC)

1. V IdP zaregistruj OIDC aplikaci (confidential client, scope `openid email profile`),
   redirect URI `https://<host>/oauth2/callback`.
2. `cp .env.example .env` a vyplň hodnoty. Issuer URL podle IdP:
   - **Entra ID:** `https://login.microsoftonline.com/<tenant-id>/v2.0`
   - **Okta:** `https://<org>.okta.com/oauth2/default`
   - **Keycloak:** `https://<host>/realms/<realm>`
3. `docker compose --profile oidc up -d` — `.env` přepne backend na `oidc`,
   nginx na `nginx/pflanzer.oidc.conf` a spustí `oauth2-proxy`.
4. Ověř: `curl -i https://<host>/method/api/projects` bez cookie → 401;
   v prohlížeči → přesměrování na přihlášení IdP.

Nginx volá `auth_request /oauth2/auth`, e-mail/uživatele z odpovědi
oauth2-proxy předá backendu jako `X-Forwarded-Email`/`X-Forwarded-User`
a klientskou hlavičku `X-User` zahodí. Backend nesmí být dostupný jinak než
přes nginx (v compose je jen `expose`, ne `ports`) — jinak lze hlavičky podvrhnout.

## Audit stopa

- `feedback.submitted_by` = e-mail z SSO (`X-Forwarded-Email`).
- `audit_log.actor` = totéž, u každého `feedback.create` / zápisu varianty,
  s DORA retencí 7 let (`audit.py`).
- V `dev` módu jsou tyto hodnoty neověřené — data z dev běhu nepoužívej jako
  důkaz pro Go/Iterate/Kill.
