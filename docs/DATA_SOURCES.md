# Data sources: verified behaviour

Findings from real requests. Update this file whenever a service is re-checked.

## BDL WFS (verified 2026-10-05)

Endpoint: `https://wfs.bdl.lasy.gov.pl/geoserver/BDL/ows` (GeoServer, WFS 2.0.0).

Layers (20): `BDL:RDLP`, `BDL:Nadleśnictwa`, `BDL:Leśnictwa` and one stand layer per RDLP:
`BDL:RDLP_<Name>_wydzielenia` for Białystok, Gdańsk, Katowice, Kraków, Krosno, Lublin, Olsztyn,
Piła, Poznań, Radom, Szczecin, Szczecinek, Toruń, Warszawa, Wrocław, Zielona_Góra, Łódź.

Output formats include `application/json`, `SHAPE-ZIP`, `csv`, GML. `count` up to at least 2000 per page;
`resultType=hits` works. Native CRS EPSG:2180.

**Axis order quirk:** in WFS 2.0 with `urn:ogc:def:crs:EPSG::2180` the BBOX must be given as
`northing_min,easting_min,northing_max,easting_max` (i.e. y,x). With x,y order the filter silently
returns wrong results.

Occasional `Connection reset by peer`: always retry with backoff.

### Stand layer fields (`RDLP_*_wydzielenia`)

| Field | Meaning | Sample values (RDLP Piła, 2000 features) |
|---|---|---|
| `geom` | MultiPolygon, EPSG:2180 | |
| `a_i_num` | stand id (numeric) | `801042092` |
| `adr_for` | forest address (RDLP-nadl.-obręb-leśnictwo-oddział-wydzielenie) | `08-01-1-01-74 -a -00` |
| `area_type` | land type | `D-STAN` (stand) 1787, `ZRĄB` (clear-cut) 58, `BAGNO` 57, `R` 25, `DROGI L` 13, `PS`, `Ł`, `BUD INNE`, `ROWY`, … (25 values) |
| `site_type` | forest site type (uppercase) | `BMŚW`, `BŚW`, `LMŚW`, `LŚW`, `OLJ`, `LMW`, `LMB`, `OL`, `LW`, `BMB`, `BMW`, `BB`, null |
| `silvicult` | silvicultural management type | `P-Z`, `Z`, `S`, `N` |
| `forest_fun` | forest function | `GOSP`, `REZ` (reserve) |
| `stand_stru` | stand structure | `DRZEW`, `KO`, `KDO`, `2 PIĘT` |
| `rotat_age` | rotation age (years) | `100` |
| `sub_area` | area (ha) | `10.53` |
| `prot_categ` | protective category | null 1555, `OCH WOD` 193, `OCH GLEB` 129, `OCH OSTOJ` 54, `OCH BADAW` 39, `OCH MIAST` 15, `OCH CENNE` 14, `OCH NAS` 1 |
| `species_cd` | dominant tree species | `SO` 1602, `BK`, `OL`, `DB.B`, `BRZ`, `MD`, `DB.S`, `ŚW`, `JW`, `BRZ.O`, `DB`, `DB.C`, `GB` (suffix after `.` = sub-species, map by prefix) |
| `part_cd` | share of dominant species in tenths | `10` … `3` |
| `spec_age` | age of dominant species (years) | 0–171; 0 for non-stand land types |
| `a_year` | data year | `2026` |
| `nazwa` | source dataset (per forest district) | `BDL_08_01_CZLOPA_2026` |

Not available in WFS: **ownership** (layers contain only State Forests / LP), **stand height**,
**admixture species** (only the dominant species and its share).

`BDL:Nadleśnictwa` fields: `adress_forest`, `a_year`, `inspectorate_name`, `region_cd`, `inspectorate_cd`.

### Volume for łódzkie (current pilot region, 2026-10-06)

Bbox hits: Łódź 105 583, Radom 32 875, Poznań 27 269, Katowice 23 088, Warszawa 168.
107 583 stands intersect the voivodeship polygon. Full download with 5000-feature pages: ~2.5 min.

### Volume for lubuskie + wielkopolskie (original plan, bbox hits)

Piła 115 964, Poznań 166 013, Zielona Góra 186 307, Szczecin 181 667, Wrocław 113 707, Toruń 107 029,
Szczecinek 38 554, Łódź 24 202, Gdańsk 1 724, Katowice 979, i.e. ~936k features in the bounding box.
The real region polygon is smaller. Approx. 0.9 kB GeoJSON per feature.

## Other hosts

| Host | Status 2026-10-05 | Note |
|---|---|---|
| `api.open-meteo.com`, `archive-api.open-meteo.com` | OK | archive returned one transient 429 |
| `tiles.openfreemap.org` | OK | |
| `raw.githubusercontent.com`, `media.githubusercontent.com` | OK | geoBoundaries POL ADM1 (OSM-derived, ODbL, 2017 boundaries) used for the region outline |
| `sdi.gdos.gov.pl` | blocked by GDOŚ bot filter | files downloaded by hand: `data/manual/gdos/` |
| `download.geofabrik.de`, `overpass-api.de` | connection reset | OSM layers come from `.github/workflows/osm-extract.yml` (GitHub Actions) |
| `mapserver.bdl.lasy.gov.pl` (BDL WMS) | not on the allow-list | needed in stage 6 |

## OSM extract (GitHub Actions, verified 2026-10-06)

GDAL's OSM driver puts common keys (`landuse`, `natural`, `military`, …) into their own columns and the rest into
`other_tags` (hstore text). `-select` must therefore list `military` explicitly, otherwise the value is lost.
Do not use `ogr2ogr -where` on the OSM driver; filter in Python (`pipeline/sources/osm.py`).

Łódzkie: 131 military polygons (of which 40 count as no-entry: `landuse=military` or area-type `military=*`;
64 are single bunkers), 64 442 forest/wood polygons (~3 700 km²).

## Open-Meteo (verified 2026-10-06)

- Docs site `open-meteo.com` is blocked in the cloud environment; the APIs work. Call-weight formula and limits were
  taken from the website source (github.com/open-meteo/open-meteo-website: `results-preview.svelte`, `pricing`,
  `terms`): weight = `max(1, max(v/10, days/14 * v/10)) * locations`, v = variables x models; free tier 600/min,
  5 000/h, 10 000/day, non-commercial.
- Forecast `models=ecmwf_ifs`: daily `precipitation_sum`, `temperature_2m_mean`, `temperature_2m_min`,
  `et0_fao_evapotranspiration` and hourly `soil_moisture_0_to_7cm`, `soil_moisture_7_to_28cm` complete for
  `past_days=30`, `forecast_days=15`.
- Default (best_match) soil layers are 0-1, 1-3, 3-9, 9-27 cm with nulls after ~37 days of the 45-day window.
- `icon_seamless` daily data covers only 7 of 15 days; `gfs_seamless` covers 15.
- Archive `models=era5_land`: hourly soil 0-7 / 7-28 cm OK; daily `precipitation_sum` and `et0` came back null in a
  test, so the backtest takes daily weather from the default archive model (falls back to `era5`).
- From the Claude cloud IP the archive quickly answers "Daily API request limit exceeded" (shared IP). All
  production calls run on GitHub Actions.
- Measured on Actions: 5 points = 14.6 calls, 4 s, latest.json 2.1 kB; backtest incl. 5-point climatology = 200 calls.
