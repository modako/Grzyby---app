import * as fs from "fs";
import * as path from "path";

import { cellIndex, roundHalfUp } from "../ig";
import { IG_PARAMS, SPECIES, WEATHER_VARIANT } from "../params";

// Shared contract with the Python pipeline (pipeline/tests/test_ig.py reads the same file).
const contract = JSON.parse(
  fs.readFileSync(path.join(__dirname, "../../../../docs/contract/ig_cases.json"), "utf-8"),
);

describe("IG contract (docs/contract/ig_cases.json)", () => {
  for (const c of contract.cases as any[]) {
    it(c.name, () => {
      const out = cellIndex({ myc: c.input.w_myc, frost: c.input.w_frost }, c.input.h, c.input.banned, c.input.species);
      expect(out).toEqual(c.expected);
    });
  }

  it("uses the same parameters as the contract", () => {
    expect(IG_PARAMS.igBase).toBe(contract.params.ig_base);
    expect(IG_PARAMS.igHWeight).toBe(contract.params.ig_h_weight);
    expect(IG_PARAMS.greenMin).toBe(contract.params.color_green_min);
    expect(IG_PARAMS.yellowMin).toBe(contract.params.color_yellow_min);
    for (const sp of SPECIES) {
      expect(WEATHER_VARIANT[sp]).toBe(contract.params.variant[sp] ?? contract.params.variant.default);
    }
  });

  it("rounds halves up like the pipeline", () => {
    expect(roundHalfUp(34.5)).toBe(35);
    expect(roundHalfUp(0.49)).toBe(0);
  });
});
