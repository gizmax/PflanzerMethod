// "Kdo jste?" — jméno a krok cesty zástupce, uložené v prohlížeči (localStorage).
// Pozor: v dev režimu hubu je to jen označení pro audit, ne přihlášení.

export type Identity = { name: string; step: string };

const KEY = "pflanzer.identity";
let memory: Identity | null = null; // záloha, když localStorage není k dispozici

export function getIdentity(): Identity | null {
  try {
    const raw = window.localStorage.getItem(KEY);
    if (raw) {
      const v = JSON.parse(raw);
      if (v && typeof v.name === "string" && v.name) return v as Identity;
    }
  } catch {
    /* privátní okno apod. */
  }
  return memory;
}

export function setIdentity(id: Identity | null): void {
  memory = id;
  try {
    if (id) window.localStorage.setItem(KEY, JSON.stringify(id));
    else window.localStorage.removeItem(KEY);
  } catch {
    /* ignorujeme */
  }
}

/** Kroky cesty: klíč v DB (path_owners_json) -> český název. */
export const PATH_STEPS: [string, string][] = [
  ["byznys", "Byznys"],
  ["produkt", "Produkt"],
  ["design", "Design"],
  ["vyvoj", "Vývoj"],
  ["bezpecnost", "Bezpečnost & právo"],
  ["provoz", "Provoz"],
];

export const stepLabel = (key: string): string =>
  PATH_STEPS.find(([k]) => k === key)?.[1] ?? key;

/** Hrubé oslovení (5. pád) pro "Díky, Evo." — jen jisté případy, jinak jméno beze změny. */
export function vocative(fullName: string): string {
  const first = fullName.trim().split(/\s+/)[0] || fullName;
  if (/[aA]$/.test(first) && first.length > 2) return first.slice(0, -1) + "o";
  const known: Record<string, string> = {
    Petr: "Petře", Martin: "Martine", Tomáš: "Tomáši", Jan: "Jane", Pavel: "Pavle",
    Ondřej: "Ondřeji", Michal: "Michale", Marek: "Marku", Karel: "Karle", Jakub: "Jakube",
  };
  return known[first] ?? first;
}
