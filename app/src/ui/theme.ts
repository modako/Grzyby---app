/** High-contrast light theme: the app is used outdoors, often in sunlight. */
export const colors = {
  bg: "#ffffff",
  surface: "#f3f5f1",
  ink: "#111a14",
  ink2: "#46524a",
  line: "#d5dbd2",
  accent: "#1f6b3e",
  // IG classes (docs/SPEC.md chapter 5)
  green: "#1e9a4a",
  yellow: "#f2c11d",
  red: "#d6453d",
  grey: "#8d918e",
  noData: "#d9dcd9",
  private: "#8a5a1c",
  rain: "#2a78d6",
} as const;

export const igColor = { green: colors.green, yellow: colors.yellow, red: colors.red, grey: colors.grey };

export const space = { xs: 4, s: 8, m: 12, l: 16, xl: 24 } as const;
export const font = { s: 14, m: 16, l: 19, xl: 24 } as const;
/** Minimum touch target (gloves, sun, moving). */
export const touch = 52;
