"""Build the static forest layer: python -m pipeline.build_static

Outputs (data/static/):
  cells.geojson     H3 forest cells with H per species, legal flags and stand description
  cells_meta.json   cell centres and their weather grid point (input for stage 2)
  attribution.json  data sources, licences and download dates
and a preview map in data/preview/preview.html.
"""

import json
import logging
import time
from datetime import datetime, timezone

import geopandas as gpd
import h3
import pandas as pd
from shapely.geometry import Polygon

from pipeline import cells as cells_mod
from pipeline.params import model_params, region_config
from pipeline.paths import PREVIEW_DIR, STATIC_DIR
from pipeline.preview import write_preview
from pipeline.sources import bdl, boundaries, gdos, osm

log = logging.getLogger("build_static")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    t0 = time.time()
    params, region_cfg = model_params(), region_config()
    species = params["species"]

    region = boundaries.region_polygon(region_cfg["voivodeships"])
    log.info("Region %s: %.0f km2", region_cfg["name"], region.area.iloc[0] / 1e6)

    stands, bdl_source = bdl.fetch_stands(region)
    log.info("BDL stands in region: %d", len(stands))
    protected = gdos.protected_areas(region)
    military = osm.military(region)
    mask = gpd.GeoDataFrame(pd.concat([protected, military], ignore_index=True), crs=2180)
    log.info("Mask polygons: %s", mask["kind"].value_counts().to_dict())

    units = pd.concat([cells_mod.lp_units(stands, params),
                       cells_mod.non_lp_units(osm.forests(region), stands, params)], ignore_index=True)
    units = gpd.GeoDataFrame(units, crs=2180)
    log.info("Forest units: %s", units["source"].value_counts().to_dict())

    cells = cells_mod.build_cells(units, mask, region, params)
    centres = [h3.cell_to_latlng(c) for c in cells["cell"]]
    cells["lat"] = [c[0] for c in centres]
    cells["lon"] = [c[1] for c in centres]
    cells["point_id"] = [cells_mod.weather_point(la, lo, params["weather_grid_deg"]) for la, lo in centres]

    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    geojson = cells_geojson(cells, species, params, generated)
    (STATIC_DIR / "cells.geojson").write_text(json.dumps(geojson, ensure_ascii=False, separators=(",", ":"), allow_nan=False),
                                              encoding="utf-8")
    meta = {
        "params_version": params["params_version"],
        "generated_at": generated,
        "region": region_cfg["name"],
        "weather_grid_deg": params["weather_grid_deg"],
        "cells": {c: [round(la, 5), round(lo, 5), p] for c, la, lo, p in
                  zip(cells["cell"], cells["lat"], cells["lon"], cells["point_id"])},
        # Weather points needed by the daily run: only those with at least one non-banned cell.
        "points": {p: [float(p.split("_")[0]), float(p.split("_")[1])]
                   for p in sorted(set(cells.loc[~cells["banned"], "point_id"]))},
    }
    (STATIC_DIR / "cells_meta.json").write_text(json.dumps(meta, separators=(",", ":")), encoding="utf-8")
    (STATIC_DIR / "attribution.json").write_text(
        json.dumps(attribution(bdl_source, generated), ensure_ascii=False, indent=2), encoding="utf-8")

    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    write_preview(geojson, region, control_places(cells, region_cfg.get("control_places", [])), region_stats(cells),
                  {"bdl": bdl_source["downloaded"], "gdos": gdos.DOWNLOADED}, PREVIEW_DIR / "preview.html")

    summary(cells, species)
    for f in ["cells.geojson", "cells_meta.json", "attribution.json"]:
        log.info("%-18s %8.1f kB", f, (STATIC_DIR / f).stat().st_size / 1024)
    log.info("preview.html       %8.1f kB", (PREVIEW_DIR / "preview.html").stat().st_size / 1024)
    log.info("Done in %.0f s", time.time() - t0)


def cells_geojson(cells: pd.DataFrame, species: list[str], params: dict, generated: str) -> dict:
    features = []
    for row in cells.itertuples(index=False):
        ring = [[round(lng, 5), round(lat, 5)] for lat, lng in h3.cell_to_boundary(row.cell)]
        ring.append(ring[0])
        props = {
            "id": row.cell,
            "pt": row.point_id,
            "h": {sp: round(getattr(row, f"h_{sp}"), 2) for sp in species},
            "h_max": round(row.h_max, 2),
            "banned": bool(row.banned),
            "ban_share": round(row.ban_share, 2),
            "ban_reasons": row.ban_reasons,
            "private_maybe": bool(row.private_maybe),
            "non_lp_share": round(row.non_lp_share, 2),
            "forest_ha": round(row.forest_ha, 1),
            "trees": _str_or_none(row.trees),
            "age": None if row.age_mean is None or pd.isna(row.age_mean) else round(row.age_mean),
            "habitat": _str_or_none(row.habitat),
        }
        features.append({"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [ring]},
                         "properties": props})
    return {"type": "FeatureCollection", "params_version": params["params_version"], "generated_at": generated,
            "features": features}


def _str_or_none(value) -> str | None:
    return value if isinstance(value, str) and value else None


def attribution(bdl_source: dict, generated: str) -> dict:
    return {
        "generated_at": generated,
        "sources": [
            {"name": bdl_source["name"], "url": bdl_source["url"], "layers": bdl_source["layers"],
             "data_years": bdl_source["data_years"], "downloaded": bdl_source["downloaded"],
             "text": f"Dane o drzewostanach: Bank Danych o Lasach, Lasy Państwowe (pobrano {bdl_source['downloaded']})"},
            {"name": "Generalna Dyrekcja Ochrony Środowiska", "url": "https://www.gov.pl/web/gdos/dostep-do-danych-geoprzestrzennych",
             "layers": ["GDOS:ParkiNarodowe", "GDOS:Rezerwaty"], "downloaded": gdos.DOWNLOADED,
             "text": gdos.ATTRIBUTION},
            {"name": "OpenStreetMap", "url": "https://www.openstreetmap.org/copyright", "license": "ODbL 1.0",
             "data_timestamp": osm.data_timestamp(), "text": osm.ATTRIBUTION},
            {"name": "geoBoundaries POL ADM1", "url": boundaries.ADM1_URL, "license": "ODbL 1.0",
             "text": boundaries.ATTRIBUTION},
            {"name": "H3", "url": "https://h3geo.org", "license": "Apache 2.0", "text": "Siatka heksagonalna H3 (Uber)"},
        ],
    }


def region_stats(cells: pd.DataFrame) -> dict:
    free = cells[~cells["banned"]]
    return {
        "Komórki z lasem": f"{len(cells):,}".replace(",", " "),
        "Las razem": f"{cells['forest_ha'].sum() / 100:,.0f} km²".replace(",", " "),
        "Zakazane (szare)": f"{int(cells['banned'].sum())}",
        "Głównie poza LP": f"{int(cells['private_maybe'].sum())}",
        "H_max ≥ 0,6": f"{int((free['h_max'] >= 0.6).sum())}",
        "Średnie H_max": f"{free['h_max'].mean():.2f}".replace(".", ","),
    }


def control_places(cells: pd.DataFrame, named: list[dict]) -> list[dict]:
    """Cells the owner can check by hand: named places, best forest, a reserve, a military area, a non-LP forest."""
    picks = []
    for place in named:
        dist = (cells["lat"] - place["lat"]) ** 2 + ((cells["lon"] - place["lon"]) * 0.62) ** 2
        row = cells.loc[dist.idxmin()]
        picks.append((row, place["name"], _describe(row)))
    full = cells[(cells["forest_ha"] >= 60) & ~cells["banned"] & ~cells["private_maybe"]]
    if not full.empty:
        best = full.sort_values(["h_max", "forest_ha"], ascending=False).iloc[0]
        picks.append((best, "Najwyższy potencjał", _describe(best)))
    for label, reason in [("Rezerwat przyrody", "rezerwat przyrody"), ("Teren wojskowy", "teren wojskowy"),
                          ("Uprawa leśna", "uprawa leśna (młodnik do ok. 4 m)")]:
        sel = cells[cells["banned"] & cells["ban_reasons"].map(lambda r, reason=reason: bool(r) and r[0] == reason)]
        if not sel.empty:
            row = sel.sort_values(["ban_share", "forest_ha"], ascending=False).iloc[0]
            picks.append((row, label, _describe(row)))
    priv = cells[cells["private_maybe"] & ~cells["banned"]]
    if not priv.empty:
        row = priv.sort_values("forest_ha", ascending=False).iloc[0]
        picks.append((row, "Las poza Lasami Państwowymi", _describe(row)))
    return [{"id": r.cell, "lat": round(r.lat, 5), "lon": round(r.lon, 5), "label": label, "why": why}
            for r, label, why in picks]


def _describe(row) -> str:
    if row.banned:
        return f"szara: {row.ban_share:.0%} lasu w masce".replace("%", " %")
    text = f"H_max {row.h_max:.2f}".replace(".", ",")
    if _str_or_none(row.trees):
        text += f", {row.trees}"
    if row.private_maybe:
        text += f", {row.non_lp_share:.0%} lasu spoza LP".replace("%", " %")
    return text


def summary(cells: pd.DataFrame, species: list[str]) -> None:
    log.info("Cells: %d, banned: %d, possibly private (>=50%% non-LP forest): %d",
             len(cells), int(cells["banned"].sum()), int(cells["private_maybe"].sum()))
    free = cells[~cells["banned"]]
    bins = pd.cut(free["h_max"], [0, 0.2, 0.4, 0.6, 0.8, 1.0001], right=False)
    log.info("H_max distribution (non-banned): %s", bins.value_counts().sort_index().to_dict())
    log.info("Mean H per species (non-banned): %s",
             {sp: round(free[f"h_{sp}"].mean(), 2) for sp in species})


if __name__ == "__main__":
    main()
