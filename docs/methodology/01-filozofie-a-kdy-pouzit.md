# Filozofie a kdy Pflanzer Method použít

**Pflanzer Method | pflanzer.cz/method**

> K čemu je tento dokument: pomůže rozhodnout, jestli konkrétní zadání
> do metody patří, a vysvětlí, proč metoda vypadá tak, jak vypadá.
> Praktický postup je v [`00-lean-pflanzer.md`](00-lean-pflanzer.md),
> seznam „kdy NEpoužít" je shodný s [`../zacni.md`](../zacni.md).

## Filozofie

Většina zpoždění nové funkce není v psaní kódu, ale v **sériovém
předávání**: byznys → produkt → vývoj → bezpečnost → právo → provoz.
Každé předání přidá výklad „co řeklo které oddělení" a pozdní veto.
Workshopy to řeší tím, že lidi posadí do místnosti, ale jejich výstupem
je dokument, mockup nebo seznam úkolů — a alignment na slidech se při
implementaci ukáže jako alignment na představách.

Pflanzer Method posouvá rozhodování o krok dál: **rozhoduje se nad
běžícím kódem, ne nad mockupem**. AI přesunula úzké hrdlo z psaní kódu
na rozhodování; to potřebuje mandát a jména, ne počet lidí. Proto:

- **Malá skupina, celá cesta** (ADR-0021): jádro 3–4 lidé celou dobu,
  zástupci bezpečnosti & práva a provozu na 20minutová okna nad
  konkrétním artefaktem, Decider na Kickoff a Rozhodnutí. Nikdy víc než
  5 lidí naráz.
- **3 soutěžní varianty** místo jednoho návrhu: rozhoduje se mezi
  skutečnými možnostmi, ne o jedné „správné".
- **Anti-HiPPO**: silent voting, Decider hlasuje poslední (ADR-0001).
- **Automat místo lidí v místnosti**: sandbox, lint, testy, secret scan
  a quality gates pokryjí, co jde zkontrolovat strojem; lidé řeší zbytek.
- **Vítěz jde do produkce** přes běžný PR (default evolve, ADR-0005);
  zahodit kód je výslovná výjimka.

Metoda je **kompilace, ne nová filozofie**: z Design Sprintu bere Decidera
a time-boxing, z Lightning Decision Jam silent voting, z Liberating
Structures 1-2-4-All a pre-mortem, z AI-DLC princip „AI navrhuje, lidé
validují". Diferenciátor je spojení celého cyklu — soutěžní varianty na
reálném repu, async feedback, formální rozhodnutí a cesta do produkce
(srovnání: [`09`](09-srovnani-existujici-metody.md)). Důkazy o její
účinnosti zatím neexistují; proto tool měří piloty (čas Kickoff → merge,
gate score, kola Iterate, přežití kódu, `/pm retro`).

## Kdy použít

Metoda sedí, když platí většina z toho:

1. **Rozhodnutí blokuje víc oddělení** a sériové předávání už selhalo
   nebo selže.
2. **Funkční varianta je potřeba k rozhodnutí** — nad mockupem se
   zástupci neshodnou.
3. **Je jedna věc a jedna metrika** a problém je dost ověřený (viz
   [`03`](03-pre-session-priprava.md) § Krok 0 — metoda discovery
   nenahrazuje).
4. **Existuje repo**, do kterého má kód jít, a firemní preview prostředí
   (`pflanzer doctor`).
5. **Je Decider s mandátem** říct Go i Kill a **vývojář v jádru**.
6. Scope vejde do ~6–8 PD (jinak rozděl).

## Kdy NEpoužít

Pokud platí **kterékoli**, jdi standardním SDLC / PRD-first (shodné se
[`zacni.md`](../zacni.md) § Kdy metodu NEpoužít):

- **compliance-citlivé věci** — AI Act High-risk, banky v DORA scope,
  public sector — bez vrstvy [`governance/`](../governance/README.md);
- **platby a platební flow** (PSD2 SCA);
- **silné externí závislosti** (partner, legacy systém, schvalovaný
  kontrakt), které nejdou nasimulovat — typicky i legacy migrace
  s fixním scope, kde alignment už je a problém je provedení;
- **nativní mobilní aplikace** s release cyklem přes store;
- **nejednoznačná strategie a chybí Decider** s mandátem říct Go i Kill;
- **chybí vývojář**: bez něj je to workshop s obrázky. Track S (spec
  místo produktu) je nouzová cesta jen při jednom ze čtyř triggerů
  (ADR-0020, [`governance/`](../governance/README.md));
- **drobnost na jeden sprint** — režie převýší práci; stačí backlog.

Na první pilot vyber něco jiného.

## Co metoda nedělá

- **Nenahrazuje user research ani discovery.** Persona, JTBD a OST jsou
  vstup. AI persona je kontrola archetypu, ne nový poznatek.
- **Nenahrazuje architecture review** u zadání přes víc týmů (přidej
  zástupce #18, nebo scope rozděl; viz [`08`](08-edge-cases-a-rizika.md) § 7).
- **Nenahrazuje pen test, change advisory ani go-to-market.** Končí
  mergem vítěze a měřením outcome.
- **Není jednorázové demo.** Bez měření (`/pm retro`, T+7/30/60/90) se
  metoda nedá zlepšovat.

## Vztah k okolí

- **Continuous discovery** je předpoklad, ne konkurence; metoda řeší
  prostor řešení nad už ověřeným problémem.
- **Governance** (AI Act, DORA, Method Steward, pre-registrace) se přidává
  jako vrstva a nemění model účasti — víc podpisů, ne víc lidí
  v místnosti.
- **Champion** (#17) je páka adopce při druhém a dalším pilotu v jednotce.
