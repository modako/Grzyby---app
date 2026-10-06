const WEEKDAYS = ["nd", "pn", "wt", "śr", "cz", "pt", "sb"];

export function dayLabel(iso: string, index: number): string {
  if (index === 0) return "dziś";
  if (index === 1) return "jutro";
  const d = new Date(`${iso}T12:00:00`);
  return `${WEEKDAYS[d.getDay()]} ${d.getDate()}.${String(d.getMonth() + 1).padStart(2, "0")}`;
}

export function shortDate(iso: string): string {
  const d = new Date(`${iso}T12:00:00`);
  return `${d.getDate()}.${String(d.getMonth() + 1).padStart(2, "0")}`;
}

export function dateTime(ms: number | string): string {
  const d = new Date(ms);
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getDate()}.${p(d.getMonth() + 1)}.${d.getFullYear()}, ${p(d.getHours())}:${p(d.getMinutes())}`;
}

const TREES: Record<string, string> = {
  So: "sosna", "Św": "świerk", Jd: "jodła", Md: "modrzew", Bk: "buk", Db: "dąb", Brz: "brzoza", Gb: "grab",
  Os: "osika", Tp: "topola", Ol: "olsza", inne: "inne",
};
const HABITATS: Record<string, string> = {
  BS: "bór suchy", "BŚW": "bór świeży", BW: "bór wilgotny", BB: "bór bagienny", "BMŚW": "bór mieszany świeży",
  BMW: "bór mieszany wilgotny", BMB: "bór mieszany bagienny", "LMŚW": "las mieszany świeży",
  LMW: "las mieszany wilgotny", LMB: "las mieszany bagienny", "LŚW": "las świeży", LW: "las wilgotny",
  OL: "ols", OLJ: "ols jesionowy", "LŁ": "las łęgowy",
};

/** "So 78%, Db 12%" -> "sosna 78%, dąb 12%" */
export function treesText(trees: string | null): string | null {
  if (!trees) return null;
  return trees.replace(/([A-Za-zŚśŁł]+) (\d+%)/g, (_, t: string, s: string) => `${TREES[t] ?? t} ${s}`);
}

export function mainTree(trees: string | null): string | null {
  const m = trees?.match(/^([A-Za-zŚśŁł]+)/);
  return m ? (TREES[m[1]] ?? m[1]) : null;
}

export function habitatText(code: string | null): string | null {
  return code ? (HABITATS[code] ?? code) : null;
}
