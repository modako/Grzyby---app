/** IG series for cells (all days), the "best day" and green windows. */
import { cellIndex, colorOf, roundHalfUp, IgColor } from "./ig";
import { IG_PARAMS, Species } from "./params";
import type { CellProps, Daily, PointWeather } from "./types";

export interface DayIndex {
  ig: number;
  color: IgColor;
  species: Species;
  /** Range for uncertain days (+8..+14), otherwise equal to ig. */
  low: number;
  high: number;
}

/** Shift of the frost variant when the myc band is applied (the band is published for W_myc only). */
function bandVariant(w: PointWeather, d: number, bound: number): { myc: number; frost: number } {
  return { myc: bound, frost: Math.max(0, w.w_frost[d] + (bound - w.w_myc[d])) };
}

export function cellSeries(cell: CellProps, daily: Daily, species: Species | null): DayIndex[] | null {
  const w = daily.points[cell.pt];
  if (!w) return null;
  return w.w_myc.map((_, d) => {
    const main = cellIndex({ myc: w.w_myc[d], frost: w.w_frost[d] }, cell.h, cell.banned, species);
    if (d < daily.uncertain_from_day) return { ...main, low: main.ig, high: main.ig };
    const low = cellIndex(bandVariant(w, d, w.w_low[d]), cell.h, cell.banned, species).ig;
    const high = cellIndex(bandVariant(w, d, w.w_high[d]), cell.h, cell.banned, species).ig;
    return { ...main, low: Math.min(low, main.ig), high: Math.max(high, main.ig) };
  });
}

/** Rounded IG per day only (fast path for the map layer); -1 when the cell has no weather point. */
export function igArray(cell: CellProps, daily: Daily, species: Species | null): number[] {
  const series = cellSeries(cell, daily, species);
  return series ? series.map((s) => s.ig) : daily.dates.map(() => -1);
}

export function bestDay(series: DayIndex[]): number {
  let best = 0;
  series.forEach((s, d) => {
    if (s.ig > series[best].ig) best = d;
  });
  return best;
}

/** Runs of consecutive days with IG >= green threshold, as [first, last] day indices. */
export function greenWindows(series: DayIndex[]): [number, number][] {
  const out: [number, number][] = [];
  let start = -1;
  series.forEach((s, d) => {
    const green = s.ig >= IG_PARAMS.greenMin;
    if (green && start < 0) start = d;
    if (!green && start >= 0) {
      out.push([start, d - 1]);
      start = -1;
    }
  });
  if (start >= 0) out.push([start, series.length - 1]);
  return out;
}

export { colorOf, roundHalfUp };
