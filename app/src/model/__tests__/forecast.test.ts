import { bestDay, cellSeries, greenWindows, igArray } from "../forecast";
import { SPECIES } from "../params";
import type { CellProps, Daily } from "../types";

const h = Object.fromEntries(SPECIES.map((s) => [s, 0])) as CellProps["h"];
const cell: CellProps = {
  id: "c1", pt: "51.6_20.1", h: { ...h, borowik: 1, opienka: 0.5 }, h_max: 1, banned: false, ban_share: 0,
  ban_reasons: [], private_maybe: false, non_lp_share: 0, forest_ha: 50, trees: "So 100%", age: 70, habitat: "BŚW",
};
const n = 15;
const daily: Daily = {
  generated_at: "2026-10-06T04:00:00Z", params_version: "0.2.0", uncertain_from_day: 8,
  dates: Array.from({ length: n }, (_, i) => `2026-10-${String(6 + i).padStart(2, "0")}`),
  points: {
    "51.6_20.1": {
      w_myc: [10, 20, 30, 40, 50, 60, 70, 80, 70, 60, 50, 40, 30, 20, 10],
      w_frost: [10, 20, 30, 40, 50, 60, 70, 80, 70, 60, 50, 40, 30, 20, 10],
      w_low: [10, 20, 30, 40, 50, 60, 70, 80, 50, 40, 30, 20, 10, 5, 0],
      w_high: [10, 20, 30, 40, 50, 60, 70, 80, 90, 80, 70, 60, 50, 40, 30],
      rain: Array(n).fill(0), tmean: Array(n).fill(10),
    },
  },
};

test("all-species series uses the best species and the contract rounding", () => {
  const s = cellSeries(cell, daily, null)!;
  expect(s.map((x) => x.ig)).toEqual([10, 20, 30, 40, 50, 60, 70, 80, 70, 60, 50, 40, 30, 20, 10]);
  expect(s[7]).toMatchObject({ color: "green", species: "borowik" });
});

test("uncertain days carry a low-high range, certain days do not", () => {
  const s = cellSeries(cell, daily, "borowik")!;
  expect(s[3]).toMatchObject({ low: 40, high: 40 });
  expect(s[8]).toMatchObject({ ig: 70, low: 50, high: 90 });
});

test("best day and green windows", () => {
  const s = cellSeries(cell, daily, null)!;
  expect(bestDay(s)).toBe(7);
  expect(greenWindows(s)).toEqual([[5, 9]]);
});

test("banned cells are grey whatever the weather; missing weather gives -1", () => {
  const s = cellSeries({ ...cell, banned: true }, daily, null)!;
  expect(s.every((x) => x.color === "grey")).toBe(true);
  expect(igArray({ ...cell, pt: "nope" }, daily, null)).toEqual(Array(n).fill(-1));
});
