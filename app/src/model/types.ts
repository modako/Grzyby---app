import type { Species } from "./params";

/** Properties of one forest cell in static/cells.geojson (stage 1). */
export interface CellProps {
  id: string;
  pt: string;
  h: Record<Species, number>;
  h_max: number;
  banned: boolean;
  ban_share: number;
  ban_reasons: string[];
  private_maybe: boolean;
  non_lp_share: number;
  forest_ha: number;
  trees: string | null;
  age: number | null;
  habitat: string | null;
}

export interface Cell extends CellProps {
  /** Polygon ring [lng, lat][] */
  ring: [number, number][];
  center: [number, number];
}

/** One weather point in daily/latest.json (stage 2). */
export interface PointWeather {
  w_myc: number[];
  w_frost: number[];
  w_low: number[];
  w_high: number[];
  rain: number[];
  tmean: number[];
}

export interface Daily {
  generated_at: string;
  params_version: string;
  dates: string[];
  uncertain_from_day: number;
  points: Record<string, PointWeather>;
}
