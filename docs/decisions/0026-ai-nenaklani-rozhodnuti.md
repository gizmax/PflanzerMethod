# ADR-0026 — AI nesmí naklánět Rozhodnutí

**Pflanzer Method | pflanzer.cz/method**

**Status:** Accepted · 2026-11-25 (navrženo 2026-11-22)
**Související:** ADR-0001 (Decider, anti-HiPPO), ADR-0023 (AI náhrada
chybějící role: AI nikdy není podpis), ADR-0021,
[`../research/vylepseni-2026-11.md`](../research/vylepseni-2026-11.md) § 2

## Kontext

Tiché hlasování a pravidlo „Decider hlasuje poslední“ chrání Rozhodnutí
před vlivem nejvýše postaveného člověka. Proti vlivu AI metoda ochranu
nemá. Studie Anthropic z 27. 10. 2026 (50 analytiků, jeden úkol, sklon
agenta záměrně zesílený) uvádí, že analytici šli za skrytým sklonem agenta
v 86 % voleb a jen 15 % ho uvedlo jako zdroj svých argumentů.

V metodě AI do Rozhodnutí vstupuje třikrát: `pflanzer decide prep` dává
souhrn feedbacku před hlasováním, ve stupni Full AI píše první draft
konvergence a AI smí v omezené míře zastoupit chybějící role. Formulace
„AI fakta neutrálně, bez interpretace“ je záměr, ne kontrola: výběr
a pořadí faktů je už interpretace.

## Varianty

| Varianta | Pro | Proti |
|----------|-----|-------|
| A. Stav dnes (AI souhrn před hlasováním, „neutrálně“) | Žádná změna | Neutralitu nikdo neověřuje; pořadí umožňuje ukotvení |
| B. AI z Rozhodnutí úplně vyřadit | Nejčistší | Agregace desítek komentářů ručně je drahá a lidé ji taky zkreslí |
| **C. Lidé hlasují dřív, než AI souhrn uvidí; AI píše argumenty pro každou variantu i proti; zápis toho, co AI navrhla** | Odpovídá mitigacím, které navrhují autoři studie; drží přínos agregace | Blok Rozhodnutí je o pár minut delší; víc textu ke čtení |

## Rozhodnutí

Varianta **C** v lehčí podobě: druhé kolo hlasování jen ve stupni Full.

1. **Pořadí v Rozhodnutí:** demo → tiché hlasování jádra (nad vlastní
   zkušeností z Asyncu, výsledek se zatím nezveřejní) → teprve pak AI
   souhrn, Kritické a spory → Decider poslední. Kdo chce po sporech hlas
   změnit, řekne to nahlas a zapíše se to. **Druhé tiché kolo má jen stupeň
   Full**; u Quick a Lean by Rozhodnutí zbytečně protahovalo.
2. **AI nikdy nedoporučuje vítěze** a neřadí varianty. `decide prep`
   pro každou variantu vypíše nejsilnější argument pro a nejsilnější proti,
   ve stejném rozsahu, v pořadí A, B, C.
3. **Decision log dostane pole „AI vstup“:** co AI do Rozhodnutí dodala
   (souhrn, draft konvergence, zastoupená role) a jednou větou, kde se
   Decider odchýlil nebo proč souhlasí.
4. **Draft konvergence ve stupni Full** vzniká až po prvním hlasování;
   rozdíl mezi prvním a druhým kolem je vidět v zápisu.
5. Rozšiřuje ADR-0023: AI není podpis **ani doporučení**.

## Důsledky

- Agenda v `06-session-2.md` se přeskládá; délka 60–90 min zůstává cílem.
- `pflanzer decide prep` mění výstup (pro a proti ke každé variantě, bez
  doporučení vítěze). Dvě kola hlasů se ukládají jen u Full.
- Studie má úzký záběr (jeden úkol, jeden obor, zesílený sklon). Pravidlo
  je levná pojistka, ne změřený přínos; proto jen jeho levné části.
- **Stav implementace (2026-11-25):** `decide prep` bez doporučení, pro
  a proti, pořadí bloků a „AI vstup“ v decision logu jsou v nástroji.
  Ukládání dvou kol hlasů u Full zatím není: chce změnu databáze a hubu.
  Do té doby se druhé kolo u Full zapisuje ručně do rationale.
