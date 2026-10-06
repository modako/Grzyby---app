/** IG = W * (0.4 + 0.6 * H): the same contract as pipeline/ig.py (docs/SPEC.md chapter 5). */
import { IG_PARAMS, SPECIES, Species, WEATHER_VARIANT } from "./params";

export type IgColor = "grey" | "green" | "yellow" | "red";

/** Same as Python floor(x + 0.5) and JS Math.round for non-negative values. */
export function roundHalfUp(x: number): number {
  return Math.floor(x + 0.5);
}

export function ig(w: number, h: number): number {
  return w * (IG_PARAMS.igBase + IG_PARAMS.igHWeight * h);
}

export function colorOf(igRounded: number, banned: boolean): IgColor {
  if (banned) return "grey";
  if (igRounded >= IG_PARAMS.greenMin) return "green";
  if (igRounded >= IG_PARAMS.yellowMin) return "yellow";
  return "red";
}

export interface CellIndex {
  ig: number;
  color: IgColor;
  species: Species;
}

/** IG for one cell and day: one species, or the best species when `species` is null. */
export function cellIndex(
  w: { myc: number; frost: number },
  h: Record<Species, number>,
  banned: boolean,
  species: Species | null,
): CellIndex {
  const names: readonly Species[] = species ? [species] : SPECIES;
  let best: Species = names[0];
  let bestValue = -Infinity;
  for (const sp of names) {
    const value = ig(w[WEATHER_VARIANT[sp]], h[sp] ?? 0);
    if (value > bestValue) {
      bestValue = value;
      best = sp;
    }
  }
  const rounded = roundHalfUp(bestValue);
  return { ig: rounded, color: colorOf(rounded, banned), species: best };
}
