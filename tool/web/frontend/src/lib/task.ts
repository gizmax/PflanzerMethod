// Úkol zástupce podle jeho role (kroku cesty) + příklad feedbacku podle role.

import { PATH_STEPS } from "./identity";
import type { ProjectDetail } from "./types";

export type RoleKey = "decider" | "bezpecnost" | "provoz" | "core" | "other";

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

export function buildTask(
  detail: ProjectDetail,
  identity: { name: string; step: string } | null,
  range: string,
  deadline: string | null,
  slug: string,
): RoleTask {
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
          `Pak okno podepište spolu s produktovým vlastníkem${detail.pm_name ? ` (${detail.pm_name})` : ""} tímto příkazem:`,
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

/** Placeholder příkladu feedbacku podle role. */
export function feedbackExample(step: string | undefined): string {
  switch (stepKey(step)) {
    case "bezpecnost":
      return "Varianta A posílá e-mail zákazníka do analytiky bez souhlasu → riziko GDPR → odeslat až po souhlasu; API klíč je v kódu → přesunout do prostředí";
    case "provoz":
      return "Varianta B nemá jak vrátit nasazení zpět ani alarm při výpadku platební brány → přidat feature flag a monitoring";
    case "design":
      return "U varianty C není jasné, co tlačítko Objednat udělá → uživatel váhá → přepsat popisek na „Zaplatit 1 290 Kč“";
    default:
      return "U varianty A jsem zkusil dokončit objednávku → po kliknutí se nic nestalo → čekal jsem potvrzení → přidat zprávu o úspěchu";
  }
}
