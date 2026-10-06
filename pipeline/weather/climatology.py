"""Soil moisture climatology (ERA5-Land, 0-28 cm) for the percentile in M (docs/SPEC.md 4.1).

Raw daily values are stored per year in data/climatology/raw/<year>.json (committed, so the
download can be resumed across GitHub Actions runs within the free API quota). Quantiles per
point and calendar month go to data/climatology/sm_quantiles.json.
"""

import json
import logging
import time
from datetime import date, timedelta

import numpy as np

from pipeline.paths import DATA_DIR
from pipeline.weather.openmeteo import ARCHIVE_URL, Client, LimitExceeded, batches, call_weight, coord_params

log = logging.getLogger(__name__)

CLIM_DIR = DATA_DIR / "climatology"
RAW_DIR = CLIM_DIR / "raw"
QUANTILES_FILE = CLIM_DIR / "sm_quantiles.json"
VARIABLES = ["soil_moisture_0_to_7cm", "soil_moisture_7_to_28cm"]
LAYER_WEIGHTS = [7.0, 21.0]  # layer thickness in cm -> mean over 0-28 cm
SEASON = ((4, 1), (11, 30))  # months with S > 0 (April-November)
BATCH = 10
QUANTILE_LEVELS = list(range(0, 101, 5))


def season_dates(year: int) -> list[date]:
    start, end = date(year, *SEASON[0]), date(year, *SEASON[1])
    return [start + timedelta(days=i) for i in range((end - start).days + 1)]


def daily_sm_0_28(hourly: dict) -> list[float | None]:
    """Hourly 0-7 and 7-28 cm values -> daily thickness-weighted mean over 0-28 cm."""
    a, b = hourly[VARIABLES[0]], hourly[VARIABLES[1]]
    out = []
    for d in range(len(a) // 24):
        vals = [(x * LAYER_WEIGHTS[0] + y * LAYER_WEIGHTS[1]) / sum(LAYER_WEIGHTS)
                for x, y in zip(a[d * 24:(d + 1) * 24], b[d * 24:(d + 1) * 24]) if x is not None and y is not None]
        out.append(round(sum(vals) / len(vals), 4) if vals else None)
    return out


def load_raw(year: int) -> dict:
    path = RAW_DIR / f"{year}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"year": year, "source": "Open-Meteo Archive API, models=era5_land, timezone Europe/Warsaw",
            "variable": "soil moisture 0-28 cm (m3/m3), thickness-weighted mean of 0-7 and 7-28 cm, daily mean",
            "start": season_dates(year)[0].isoformat(), "points": {}}


def save_raw(year: int, data: dict) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    data["points"] = dict(sorted(data["points"].items()))
    (RAW_DIR / f"{year}.json").write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")


def fetch(points: dict[str, tuple[float, float]], years: list[int], client: Client, budget: float,
          max_seconds: float | None = None) -> dict:
    """Download missing point-years until done, the call budget or the time limit is reached.

    Progress is saved after every batch, so an interrupted run loses at most one batch."""
    started = time.monotonic()
    todo = [(y, pid) for y in years for pid in points if pid not in load_raw(y)["points"]]
    total_before = len(todo)
    spent_at_start = client.calls
    for year in years:
        raw = load_raw(year)
        missing = [pid for pid in points if pid not in raw["points"]]
        days = season_dates(year)
        for chunk in batches(missing, BATCH):
            weight = call_weight(len(VARIABLES), len(days), len(chunk))
            if client.calls - spent_at_start + weight > budget:
                return _progress(points, years, total_before, client.calls - spent_at_start, "budget reached")
            if max_seconds is not None and time.monotonic() - started > max_seconds:
                return _progress(points, years, total_before, client.calls - spent_at_start, "time limit reached")
            params = {**coord_params([points[p] for p in chunk]), "start_date": days[0].isoformat(),
                      "end_date": days[-1].isoformat(), "hourly": ",".join(VARIABLES), "models": "era5_land",
                      "timezone": "Europe/Warsaw"}
            try:
                result = client.get(ARCHIVE_URL, params, weight)
            except LimitExceeded as exc:
                return _progress(points, years, total_before, client.calls - spent_at_start, f"API limit: {exc}")
            for pid, loc in zip(chunk, result):
                raw["points"][pid] = daily_sm_0_28(loc["hourly"])
            save_raw(year, raw)
            log.info("Climatology %d: %d/%d points", year, len(raw["points"]), len(points))
    return _progress(points, years, total_before, client.calls - spent_at_start, "complete")


def _progress(points, years, before, spent, status) -> dict:
    left = sum(1 for y in years for pid in points if pid not in load_raw(y)["points"])
    return {"status": status, "point_years_missing_before": before, "point_years_missing_now": left,
            "calls_used": round(spent, 1)}


def build_quantiles(years: list[int]) -> dict:
    """Quantiles of daily SM per point and month, from all stored years."""
    by_point: dict[str, dict[int, list[float]]] = {}
    years_used: dict[str, int] = {}
    for year in years:
        raw = load_raw(year)
        days = season_dates(year)
        for pid, values in raw["points"].items():
            years_used[pid] = years_used.get(pid, 0) + 1
            months = by_point.setdefault(pid, {})
            for d, v in zip(days, values):
                if v is not None:
                    months.setdefault(d.month, []).append(v)
    out = {"levels": QUANTILE_LEVELS, "years": years, "points": {}}
    for pid, months in sorted(by_point.items()):
        out["points"][pid] = {"years": years_used[pid], "months": {
            str(m): [round(float(q), 4) for q in np.percentile(v, QUANTILE_LEVELS)] for m, v in sorted(months.items())}}
    CLIM_DIR.mkdir(parents=True, exist_ok=True)
    QUANTILES_FILE.write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
    return out


def load_quantiles() -> dict | None:
    if not QUANTILES_FILE.exists():
        return None
    return json.loads(QUANTILES_FILE.read_text(encoding="utf-8"))


def percentile(quantiles: dict | None, pid: str, month: int, value: float | None, min_years: int = 5) -> float:
    """Percentile (0-1) of a soil moisture value against the point's climatology for that month.

    NaN when the point has no (or too short) climatology; outside April-November the nearest
    season month is used (S = 0 there anyway)."""
    if quantiles is None or value is None or pid not in quantiles["points"]:
        return float("nan")
    entry = quantiles["points"][pid]
    if entry["years"] < min_years:
        return float("nan")
    m = str(min(max(month, SEASON[0][0]), SEASON[1][0]))
    q = entry["months"].get(m)
    if not q:
        return float("nan")
    return float(np.interp(value, q, np.array(quantiles["levels"]) / 100.0))


def main() -> None:
    """python -m pipeline.weather.climatology --meta site/static/cells_meta.json --budget 4500"""
    import argparse
    from pathlib import Path

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--meta", required=True)
    ap.add_argument("--budget", type=float, default=4500)
    ap.add_argument("--max-minutes", type=float, default=40, help="stop in time to commit before the job timeout")
    ap.add_argument("--first-year", type=int, default=2016)
    ap.add_argument("--last-year", type=int, default=2025)
    args = ap.parse_args()
    meta = json.loads(Path(args.meta).read_text(encoding="utf-8"))
    points = {pid: tuple(v) for pid, v in meta["points"].items()}
    years = list(range(args.first_year, args.last_year + 1))
    total = sum(call_weight(len(VARIABLES), len(season_dates(y)), len(points)) for y in years)
    log.info("Climatology for %d points x %d years: %.0f API calls in total (one-off)", len(points), len(years), total)
    progress = fetch(points, years, Client(), args.budget, max_seconds=args.max_minutes * 60)
    log.info("Progress: %s", progress)
    build_quantiles(years)
    (CLIM_DIR / "progress.json").write_text(json.dumps({**progress, "points": len(points), "years": years,
                                                        "total_calls_estimate": round(total)}), encoding="utf-8")


if __name__ == "__main__":
    main()
