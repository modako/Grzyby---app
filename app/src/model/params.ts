/**
 * IG contract parameters (docs/SPEC.md chapter 5, docs/contract/ig_cases.json).
 * Mirrors pipeline/config/model_params.yaml; a test checks them against the contract file.
 */
export const IG_PARAMS = {
  igBase: 0.4,
  igHWeight: 0.6,
  greenMin: 60,
  yellowMin: 35,
  uncertainFromDay: 8,
} as const;

export const SPECIES = [
  "borowik",
  "podgrzybek",
  "kozlarz",
  "maslak",
  "kurka",
  "rydz",
  "kania",
  "opienka",
  "gaska",
] as const;
export type Species = (typeof SPECIES)[number];

/** Weather variant per species: opieńka and gąska tolerate frost better. */
export const WEATHER_VARIANT: Record<Species, "myc" | "frost"> = {
  borowik: "myc",
  podgrzybek: "myc",
  kozlarz: "myc",
  maslak: "myc",
  kurka: "myc",
  rydz: "myc",
  kania: "myc",
  opienka: "frost",
  gaska: "frost",
};

export const SPECIES_LABEL: Record<Species, string> = {
  borowik: "Borowik",
  podgrzybek: "Podgrzybek",
  kozlarz: "Koźlarz",
  maslak: "Maślak",
  kurka: "Kurka",
  rydz: "Rydz",
  kania: "Kania",
  opienka: "Opieńka",
  gaska: "Gąska",
};
