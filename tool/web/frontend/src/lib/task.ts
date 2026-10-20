// Úkol zástupce podle jeho role (kroku cesty) + příklad feedbacku podle role.

import { PATH_STEPS } from "./identity";
import type { ProjectDetail } from "./types";

export type RoleKey = "decider" | "bezpecnost" | "provoz" | "signer" | "core" | "other";

export type RoleTask = {
  key: RoleKey;
  /** první věta úkolu (může být prázdná) */
  lead: string;
  steps: string[];
  /** příkaz k zkopírování (zobrazí se pod kroky) */
  command?: string;
  /** Decider nemusí nic psát — „Dát feedback“ je pro něj vedlejší tlačítko */
  optionalFeedback: boolean;
};

export const firstName = (full: string | null | undefined): string =>
  (full ?? "").trim().split(/\s+/)[0] ?? "";

/** 3. pád křestního jména (Petr -> Petrovi); neznámé jméno vrátí null. */
export function dative(full: string | null | undefined): string | null {
  const f = firstName(full);
  if (!f) return null;
  if (/[aA]$/.test(f) && f.length > 2) return f.slice(0, -1) + (/[kg]a$/i.test(f) ? "ce" : /[dtn]a$/i.test(f) ? "ě" : "e");
  if (/(ek|el)$/i.test(f)) return null;
  if (/[a-záčďéěíňóřšťúůýž]$/i.test(f) && !/[eiyíý]$/i.test(f)) return f + "ovi";
  return null;
}

export function stepKey(stepLabel: string | undefined): string | null {
  return PATH_STEPS.find(([k, l]) => l === stepLabel || k === stepLabel)?.[0] ?? null;
}

export function roleKey(
  identity: { name: string; step: string } | null,
  deciderName: string | null | undefined,
): RoleKey {
  if (!identity) return "other";
  if (deciderName && identity.name === deciderName) return "decider";
  const k = stepKey(identity.step);
  if (k === "bezpecnost") return "bezpecnost";
  if (k === "provoz") return "provoz";
  if (k === "produkt" || k === "design" || k === "vyvoj") return "core";
  return "other";
}

const SIGN_WINDOWS: Record<string, { window: string; check: string }> = {
  bezpecnost: { window: "bezpecnost",
    check: "jaká data vidí, kam data posílá, žádná tajemství v kódu ani logu, osobní údaje a souhlasy" },
  provoz: { window: "provoz", check: "rollback, monitoring, on-call a náklady" },
  design: { window: "design", check: "hlavní tok, kontrasty a ovládání z klávesnice" },
};

/** Krok s AI náhradou, který tato osoba skutečně podepisuje (jméno i krok sedí). */
export function signingStep(
  detail: ProjectDetail,
  identity: { name: string; step: string } | null,
): string | null {
  const k = stepKey(identity?.step);
  if (!identity || !k || !SIGN_WINDOWS[k]) return null;
  if (!/^AI(:|\s|$)/i.test(detail.path_owners?.[k] ?? "")) return null;
  return detail.confirmers?.[k] === identity.name ? k : null;
}

export function buildTask(
  detail: ProjectDetail,
  identity: { name: string; step: string } | null,
  range: string,
  deadline: string | null,
  slug: string,
): RoleTask {
  const signKey = signingStep(detail, identity);
  if (signKey && identity) {
    const w = SIGN_WINDOWS[signKey];
    return {
      key: "signer",
      optionalFeedback: false,
      lead: "AI připravila draft tohoto kroku, podepisujete ho vy (20 min).",
      steps: [
        `U každé varianty (${range}) zkontrolujte AI draft: ${w.check}.`,
        `Pak okno podepište tímto příkazem. Podmínky, které musí splnit PR, připište jako --conditions "první; druhá".`,
      ],
      command: `pflanzer checkpoint --slug ${slug} ${w.window} --by "${identity.name}" --note "co jsem ověřil"`,
    };
  }
  const key = roleKey(identity, detail.decider_name);
  const pmDat = dative(detail.pm_name);
  const tellPm = detail.pm_name
    ? (pmDat ? `Řekněte ${pmDat}` : `Řekněte tomu, kdo vede Produkt (${detail.pm_name})`)
    : "Řekněte produktovému vlastníkovi";
  switch (key) {
    case "decider":
      return {
        key,
        optionalFeedback: true,
        lead: deadline
          ? `Rozhodnutí je ${deadline}. Do té doby nemusíte nic psát.`
          : "Do Rozhodnutí nemusíte nic psát.",
        steps: [
          `Prohlédněte si varianty ${range} (10 min).`,
          `${tellPm}, co by vás zastavilo.`,
          "Hlasujete až na Rozhodnutí, poslední.",
        ],
      };
    case "bezpecnost":
      return {
        key,
        optionalFeedback: false,
        lead: "Vaše okno: 20 min.",
        steps: [
          `U každé varianty (${range}) zkontrolujte: jaká data vidí, kam data posílá, žádná tajemství v kódu ani logu, osobní údaje a souhlasy.`,
          `Pak okno podepište tímto příkazem. Podmínky, které musí splnit PR, připište jako --conditions "první; druhá":`,
        ],
        command: `pflanzer checkpoint --slug ${slug} bezpecnost --by "${identity?.name ?? ""}" --note "co jsem ověřil"`,
      };
    case "provoz":
      return {
        key,
        optionalFeedback: false,
        lead: "Posuďte, jestli by se varianta dala provozovat.",
        steps: [
          `U každé varianty (${range}) zkontrolujte: rollback, monitoring, on-call a náklady.`,
          "Ke každé napište, co by vás v provozu zastavilo.",
        ],
      };
    case "core":
      return {
        key,
        optionalFeedback: false,
        lead: "Sbírejte feedback a opravujte.",
        steps: [
          `Otevřete varianty ${range} a vyzkoušejte hlavní tok.`,
          `Ke každé napište, co vás zastaví. ${tellPm}, co ladit.`,
        ],
      };
    default:
      return {
        key,
        optionalFeedback: false,
        lead: "",
        steps: [`Otevřete varianty ${range}.`, "Ke každé napište, co vás zastaví."],
      };
  }
}

/** Placeholder příkladu feedbacku podle role; `variant` je varianta, ke které se píše. */
export function feedbackExample(step: string | undefined, variant = "A"): string {
  switch (stepKey(step)) {
    case "bezpecnost":
      return `U varianty ${variant} se osobní údaje posílají třetí straně bez souhlasu → riziko GDPR → odeslat až po souhlasu; přístupový klíč je v kódu → přesunout do prostředí`;
    case "provoz":
      return `Varianta ${variant} nemá jak vrátit nasazení zpět ani upozornění při výpadku → přidat feature flag a monitoring`;
    case "design":
      return `U varianty ${variant} není jasné, co hlavní tlačítko udělá → uživatel váhá → přepsat popisek na konkrétní akci`;
    default:
      return `U varianty ${variant} jsem zkusil dokončit hlavní úkol → po kliknutí se nic nestalo → čekal jsem potvrzení → přidat zprávu o úspěchu`;
  }
}

/** Jak se přihlásit k náhledu (odkazy jinak vedou na přihlašovací okno prohlížeče). */
export function previewLoginText(detail: ProjectDetail): string | null {
  const l = detail.preview_login;
  if (!l) return null;
  if (l.password) return `Náhled se otevře po přihlášení: uživatel ${l.user}, heslo ${l.password}.`;
  const who = detail.pm_name ? `Heslo vám pošle ${detail.pm_name}` : "Heslo vám pošle produktový vlastník";
  return `Náhled je chráněný heslem (uživatel ${l.user}). ${who}.`;
}

const PROFILE_LINE: Record<string, string> = {
  throwaway: "Zkušební prototyp pro interní demo, nejde do produkce.",
  pilot: "Pilot s omezenou skupinou reálných uživatelů.",
  production: "Ostré nasazení pro všechny uživatele, přísnější kontroly.",
};

/** Hypotéza bez věty o rozsahu (ta je v textu zadání napevno) + rozsah podle profilu projektu. */
export function splitHypothesis(text: string, profile?: string): { text: string; scope: string | null } {
  const cleaned = text.replace(
    /\s*(?:Throwaway prototyp|Pilot s|Ostré nasazení)[^.]*\.?\s*$/i, "").trim();
  return { text: cleaned, scope: profile ? PROFILE_LINE[profile] ?? null : null };
}
