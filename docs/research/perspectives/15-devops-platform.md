# 15 — DevOps / Platform perspektiva

## Kdo jsem

Staff Platform / DevOps engineer v korporátu, 12+ let. Vlastním Kubernetes
landing zone, multi-cloud infra (AWS + on-prem OpenShift), CI/CD pipelines
(GitLab + GitHub Actions), observability stack (Prometheus, Grafana, Loki,
Tempo, plus Datadog pro tier-1 produkty), IaC (Terraform + Pulumi pro
glue), secret management (Vault + cloud KMS), service mesh (Istio).
Moje denní bolesti: prototyp shipnutý ručním `kubectl apply`em na shared
cluster, observability afterthought (no logs, no metrics, no tracing,
"přidáme to v sprintu 4"), nový service bez SLO, secrets v repu, IaC
"udělám to z UI rychleji". Pflanzer mě **principiálně láká** —
cross-funkční místnost znamená, že se konečně dostanu do rozhovoru
před deploy review, ne po něm.

## 1. Posouzení Pflanzerovy metody

Co mě **těší:** DevOps je v role katalogu jako trigger-based, což je
správně — neplýtvám časem na UI-only sessions. Když jsem v místnosti,
jsem tam včas (před tím, než někdo slíbí "deploy do produkce za týden").

Co mě **straší:**

1. **"Klikací prototyp" je nedefinovaný runtime.** Lokál? Bolt deploy?
   Vercel preview? Náš sandbox? Každá varianta má jinou bezpečnostní
   třídu, jiný pricing, jiný cleanup. Bez specifikace vznikne shadow-IT.
2. **Žádný deploy footprint estimate.** Mockup ukáže "dashboard s
   real-time grafem", BE řekne "OK", a já se v týdnu 6 dozvím, že
   potřebujeme Kafka cluster, Clickhouse a 3 nové services, žádný
   z nich není v capacity plánu.
3. **Observability jako afterthought.** Metoda mluví o handoffu do
   vývoje, ale nikde nepadne, že prototyp už má mít structured logging,
   metric naming convention a trace propagation. Jinak to dev tým
   "doplní později" = nikdy.
4. **Žádný IaC kontrakt.** Prototyp vznikne ad-hoc na něčí AWS subaccountu,
   pak ho nikdo neumí znovu postavit. Sandbox musí být reproducible
   z Terraformu, ne klikací artefakt.
5. **Secrets jsou klasický fail mode.** Vibe-coder vygeneruje
   `OPENAI_API_KEY=sk-...` v `.env`, demo na session 1 funguje,
   ten klíč potom žije rok v Bolt history.
6. **SLO jako koncept v metodě nefiguruje.** Bez baseline SLO nemá
   QA na čem stavět acceptance, BE neví performance budget, security
   nemá DORA resilience evidenci.
7. **Prototype-to-prod transition** = single biggest organizační bug.
   Pflanzer slibuje "hladký handoff", ale neříká, kde končí prototyp
   a začíná produkční artefakt. Bez explicitní hranice se prototyp
   shipne jak je.

Verdikt: metoda je **deployable pod podmínkou**, že nad ní postavíme
paved-road platform stack se sandbox modulem, footprint estimate
templatem a SLO baseline. Bez nich = každý workshop reinventuje
kolo a my v platformě platíme úklid.

## 2. Must-have vstupy (do charteru, před session 1)

- **Sandbox spec** — sdílený artefakt se Security perspektivou (07).
  Terraform modul `pflanzer-sandbox`: izolovaný VPC/namespace, throwaway
  Postgres + Redis, syntetický seeder, audit logging do SIEM, **24h TTL
  s auto-destroy**, cost cap $50/session. Tým si ho objedná self-service
  z internal developer portal (Backstage), přidělen do hodiny.
- **Approved runtime list** — kde smí prototyp žít: (a) interní sandbox
  K8s namespace, (b) Vercel Team account s SSO + DPA, (c) lokál + ngrok
  jen pro session, nikdy mimo. **Neschválené:** osobní AWS, Bolt deploy
  bez Pro, free Replit.
- **Deploy footprint estimate template** — sdílený s Backendem (05).
  Jednostránkový TCO sheet: predicted services, runtime (CPU/RAM/storage),
  data stores, external SaaS dependencies, est. monthly cost, infra effort
  (S/M/L/XL). Vyplní se per varianta v session 1, ne v týdnu 6.
- **Observability baseline contract.** Powered defaults pro každý prototyp:
  `OpenTelemetry SDK` zapnutý, structured JSON logs (žádné `console.log`),
  trace context propagace v HTTP klientech, metric naming `<bu>_<svc>_<metric>`.
  Generovaný builderem? Tím líp — paved-road template má to už uvnitř.
- **Secret management policy.** Vault path konvence `secret/sandbox/<session-id>/*`,
  rotace 24h, žádné `.env` v repu, `gitleaks` pre-commit hook, OIDC
  federation pro CI (žádné long-lived tokens).
- **Existující platform conventions** — naše base images, ingress patterns,
  service mesh pravidla (Istio mTLS default), GitOps repo struktura
  (ArgoCD app-of-apps).

## 3. Must-have výstupy ze session

**Session 1**
- **Deploy footprint estimate** per varianta (TCO sheet vyplněný,
  shared s BE pro contract sizing).
- **Sandbox URL + IaC commit hash** — prototyp běží reproducible,
  ne na něčím laptopu.
- **Observability hooks check** — basic dashboard (4 golden signals)
  visible při prezentaci variant. Pokud neběží, prototyp je `demo only`
  a do session 2 se nepouští real users.

**Session 2**
- **SLO baseline draft** — minimum: availability (např. 99.5% pro
  internal tooling, 99.9% pro customer-facing), p95 latence, error
  budget. Sdíleno s QA pro acceptance kritéria.
- **Runbook stub** — alert thresholds, on-call rotation owner,
  rollback procedura, dependencies graph.
- **Prod footprint commitment** — pokud se schvaluje varianta k handoffu,
  finální infra estimate s capacity asks (cluster headroom, DB tier,
  CDN, third-party SaaS registrace per DORA čl. 28).
- **Promote-to-prod gate checklist** — co všechno musí být splněno,
  než prototyp opustí sandbox: SBOM clean, secret scan clean, IaC
  v platform monorepu, observability instrumented, SLO defined,
  runbook existuje, on-call assigned, change advisory approval.

## 4. Edge cases

- **"Deployneme to na náš shared cluster, jen na jeden den"** —
  ne. Sandbox VPC nebo nic. Žádný route do prod sítě, žádné prod
  credentials, network policy default-deny.
- **Builder vyrobí Dockerfile s `latest` tagem a root userem** —
  paved-road template enforces non-root, pinned base image, distroless
  pokud jde. CI gate odmítne `latest`.
- **Prototyp běží pomalu, tým chce "škálovat to v cloudu"** — eskalace
  do platform review, ne self-service scale na shared infra.
- **AI builder generuje IaC který nikdo nečetl** (Pulumi/Terraform
  output) — povinný `terraform plan` review + OPA policy check
  (žádné public S3, žádné 0.0.0.0/0 ingress, mandatory tags).
- **Vendor outage během session** (Vercel/Bolt down) — fallback
  na interní sandbox, dokumentovaný v charteru.
- **Cost runaway** — sandbox má hard cap přes AWS Budgets / Azure
  Cost Mgmt, prototyp se vypne automaticky, ne ex-post faktura.

## 5. Vylepšení metody

1. **Krok 0 "Platform Triage"** (15 min, async, paralelně se Security
   triage z perspektivy 07). Platform engineer ověří footprint odhad,
   schválí runtime, přidělí sandbox modul. Bez podpisu se session 1
   nespouští do "deployable" módu.
2. **Paved-road prototype template jako produkt platformy.** Cookiecutter
   repo s OpenTelemetry, structured logging, healthcheck endpointem,
   Dockerfile podle conventions, GitHub Actions s SAST/SBOM/secret scan,
   ArgoCD manifests pro sandbox. Vibe-coder generuje *do tohoto templatu*,
   ne na zelené louce. Většina paved-road věcí "for free".
3. **Sandbox spec jako sdílený artefakt** se Security (07) a BE (05).
   Jeden Terraform modul, tři vlastníci: Security definuje guardrails
   (VPC, IAM, audit), Platform vlastní lifecycle (TTL, cost), BE
   contract (DB schema, seed data shape). Žádný team neownuje sám.
4. **SLO Quick-Set library.** 5 archetypů (internal tool, customer
   portal, batch job, real-time API, mobile BE) s default SLO čísly.
   Tým si v session 2 vybere archetyp místo aby SLO designoval od nuly.
5. **Deploy footprint kalkulačka jako AI sub-agent v session 1.**
   Bere mockup spec + variant description, vrací estimate (services,
   compute, data, third-party). Lidský platform engineer schvaluje async.
   Šetří moji kapacitu a dává PM/zadavateli reálné cost-aware varianty.
6. **GitOps od minuty 0.** Prototyp commitne do firemního monorepa
   (subfolder `prototypes/<session-id>/`), ArgoCD ho deployne do
   sandbox namespace. Žádné manuální `kubectl`, žádné "u mě to běží".

## 6. Konflikty s ostatními rolemi

- **vs Zadavatel / PM:** "Chceme prototyp dnes, paved-road je overhead."
  Protiargument: paved-road je rychlejší, protože sandbox máš za hodinu
  a observability hned. Ad-hoc deploy ti vezme 2 dny v týdnu 6.
- **vs Frontend / Backend lead:** "Naše service má vlastní conventions."
  Platform standard přebíjí lokální preferenci pro nový service. Existující
  service zůstává, prototyp nemá privilegia "udělat to jinak".
- **vs Security (07):** sdílená agenda, sandbox spec je společný artefakt.
  Konflikt jen pokud Security chce dlouhý review na každý footprint —
  navrhuju pre-approved templates s rychlým schválením.
- **vs Eng manager:** kapacita platform týmu na podporu sandboxů je
  reálné omezení. Self-service portal řeší 80 % případů, zbytek do
  ticketu.
- **vs QA:** SLO baseline je sdílený vstup pro acceptance kritéria.
  Konflikt minimální, jen synchronizace, kdo definuje čísla.

## Memorabilia

- **"Vibe-prototyp je deployable, jen když má sandbox spec, footprint
  estimate, observability hooks a IaC commit. Bez nich je `demo only`
  a localhost ho nikdy neopustí."** Tahle hranice musí být v charteru
  napsaná, jinak shadow-IT vyhraje.
- **"Paved-road je rychlejší než ad-hoc, ne pomalejší."** Když platform
  team vlastní cookiecutter template a Terraform sandbox modul, vibe-coder
  dostane observability, security defaults a deploy zdarma. Ad-hoc znamená
  "platím to v incident response za půl roku".
- **"SLO není luxus pro velké services, je to acceptance contract."**
  Bez čísel nemá QA na co testovat, BE nemá performance budget, on-call
  nemá kdy vstávat. Pflanzer musí session 2 zakončit jedním řádkem:
  `Availability 99.5%, p95 < 300ms, error budget 0.5%/30d` — jinak
  prototyp do produ nesmí.
