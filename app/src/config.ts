/** The one place with addresses and app-wide settings. */

/** GitHub Pages address of the published data (stage 2). */
export const DATA_BASE_URL = "https://modako.github.io/Grzyby---app";
export const DAILY_URL = `${DATA_BASE_URL}/daily/latest.json`;
export const CELLS_URL = `${DATA_BASE_URL}/static/cells.geojson`;

/** Refresh weather at start-up when the cached copy is older than this. */
export const DAILY_STALE_HOURS = 12;
/** The forest layer changes rarely (monthly rebuild). */
export const CELLS_STALE_HOURS = 24 * 7;

/** Free vector basemap without an API key. */
export const BASEMAP_STYLE_URL = "https://tiles.openfreemap.org/styles/liberty";

/** Start view: łódzkie voivodeship [west, south, east, north]. */
export const REGION_BOUNDS: [number, number, number, number] = [18.07, 50.84, 20.66, 52.4];
