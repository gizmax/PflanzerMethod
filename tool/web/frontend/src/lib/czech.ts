// České skloňování křestních jmen (jen jisté případy; neznámé jméno vrací null).

export const firstName = (full: string | null | undefined): string =>
  (full ?? "").trim().split(/\s+/)[0] ?? "";

// Mužská jména na -a skloňují jako podstatná jména „ženského“ typu, ale jsou mužská.
const MALE_A = new Set(["honza", "jirka", "franta", "standa", "pepa", "kuba", "olda", "vláďa", "láďa",
  "sáva", "jura", "toma", "tonda", "lojza", "fanda", "ríša", "míša", "mirek"]);

const VOCATIVE: Record<string, string> = {
  petr: "Petře", jiří: "Jiří", zdeněk: "Zdeňku", vojtěch: "Vojtěchu", ivo: "Ivo", bohumil: "Bohumile",
  josef: "Josefe", ladislav: "Ladislave", štěpán: "Štěpáne", lukáš: "Lukáši", tomáš: "Tomáši",
  ondřej: "Ondřeji", matěj: "Matěji", daniel: "Danieli", samuel: "Samueli", michael: "Michaeli",
  alois: "Aloisi", luboš: "Luboši", miloš: "Miloši", radek: "Radku", marek: "Marku", hynek: "Hynku",
  jaromír: "Jaromíre", vladimír: "Vladimíre", miroslav: "Miroslave",
};

const HARD_END = /[bdfmnpstvzlrxwqk]$/i;

/** 5. pád (oslovení): Petr -> Petře, Jana -> Jano, Karel -> Karle; neznámé jméno vrátí null. */
export function vocativeName(full: string | null | undefined): string | null {
  const f = firstName(full);
  if (!f) return null;
  const lc = f.toLowerCase();
  if (VOCATIVE[lc]) return VOCATIVE[lc];
  if (/(ie|e|í)$/i.test(f)) return f; // Lucie, Marie, Jiří: oslovení = základní tvar
  if (/a$/i.test(f)) return f.length > 2 ? f.slice(0, -1) + "o" : null; // Jana -> Jano, Honza -> Honzo
  if (/ek$/i.test(f)) return f.slice(0, -2) + "ku"; // Marek -> Marku
  if (/iel$/i.test(f)) return f + "i";
  if (/el$/i.test(f)) return f.slice(0, -2) + "le"; // Karel -> Karle, Pavel -> Pavle
  if (/[bcdfghjklmnpqrstvwxz]r$/i.test(f)) return f.slice(0, -1) + "ře"; // Alexandr -> Alexandře
  if (/(ch|h|g|k)$/i.test(f)) return f + "u";
  if (/[šžčřjďťňc]$/i.test(f)) return f + "i";
  if (HARD_END.test(f)) return f + "e"; // Jan -> Jane, Martin -> Martine, Jakub -> Jakube
  return null;
}

/** 3. pád (komu): Petr -> Petrovi, Jana -> Janě, Karel -> Karlovi, Lucie -> Lucii; neznámé null. */
export function dative(full: string | null | undefined): string | null {
  const f = firstName(full);
  if (!f) return null;
  const lc = f.toLowerCase();
  if (lc === "jiří") return "Jiřímu";
  if (/ie$/i.test(f)) return f.slice(0, -1) + "i"; // Lucie -> Lucii
  if (/a$/i.test(f)) {
    if (f.length <= 2) return null;
    if (MALE_A.has(lc)) return f.slice(0, -1) + "ovi"; // Honza -> Honzovi
    const stem = f.slice(0, -1);
    if (/ka$/i.test(f)) return stem.slice(0, -1) + "ce"; // Lenka -> Lence
    if (/ga$/i.test(f)) return stem.slice(0, -1) + "ze"; // Olga -> Olze
    if (/cha$/i.test(f)) return stem.slice(0, -2) + "še";
    if (/ha$/i.test(f)) return stem.slice(0, -1) + "ze";
    if (/ra$/i.test(f)) return stem.slice(0, -1) + "ře"; // Petra -> Petře, Klára -> Kláře
    if (/[dtnbpmv]a$/i.test(f)) return stem + "ě"; // Jana -> Janě, Eva -> Evě
    if (/[lszc]a$/i.test(f)) return stem + "e"; // Adéla -> Adéle
    return null;
  }
  if (/ek$/i.test(f)) return f.slice(0, -2) + "kovi"; // Marek -> Markovi
  if (/iel$/i.test(f)) return f + "ovi";
  if (/el$/i.test(f)) return f.slice(0, -2) + "lovi"; // Karel -> Karlovi, Pavel -> Pavlovi
  if (/[a-záčďéěíňóřšťúůýž]$/i.test(f) && !/[eiyíýo]$/i.test(f)) return f + "ovi";
  return null;
}

/** Oslovení do věty „Díky, X.“ — když si tvarem nejsme jistí, použije jméno beze změny. */
export const vocative = (full: string): string =>
  vocativeName(full) ?? (firstName(full) || full);
