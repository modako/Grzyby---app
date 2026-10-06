"""Daily weather component W per weather grid point: python -m pipeline.build_daily

Reads the weather points from data/static/cells_meta.json, downloads days -30..+14 from
Open-Meteo (ECMWF IFS, plus GFS and ECMWF AIFS for the uncertainty band of days +8..+14),
computes W_myc / W_frost (docs/SPEC.md, chapter 4) and writes data/daily/latest.json and a
dated copy. Prints the number of API calls used.
"""

import argparse
import json
import logging
import math
import time
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from pipeline.ig import round_half_up
from pipeline.params import model_params
from pipeline.paths import DATA_DIR, STATIC_DIR
from pipeline.weather import climatology
from pipeline.weather.model import weather_score
from pipeline.weather.openmeteo import FORECAST_URL, Client, batches, call_weight, coord_params

log = logging.getLogger("build_daily")

TZ = "Europe/Warsaw"
MAIN_MODEL = "ecmwf_ifs"  # same soil layers (0-7, 7-28 cm) as the ERA5-Land climatology
BAND_MODELS = ["gfs_seamless", "ecmwf_aifs025_single"]
DAILY_VARS = ["precipitation_sum", "temperature_2m_mean", "temperature_2m_min", "et0_fao_evapotranspiration"]
SERIES_KEYS = {"precipitation_sum": "precip", "temperature_2m_mean": "tmean", "temperature_2m_min": "tmin",
               "et0_fao_evapotranspiration": "et0"}
BATCH = 20
DAILY_DIR = DATA_DIR / "daily"


def estimate_calls(n_points: int, params: dict) -> dict:
    past, fut = params["api_window_days"], params["forecast_days"] + 1
    main = call_weight(len(DAILY_VARS) + len(climatology.VARIABLES), past + fut, n_points)
    band = call_weight(len(DAILY_VARS), fut, n_points, n_models=len(BAND_MODELS))
    return {"main": round(main, 1), "band": round(band, 1), "total": round(main + band, 1)}


def fetch_main(points: dict, client: Client, params: dict) -> dict:
    past, fut = params["api_window_days"], params["forecast_days"] + 1
    out = {}
    for chunk in batches(list(points), BATCH):
        query = {**coord_params([points[p] for p in chunk]), "daily": ",".join(DAILY_VARS),
                 "hourly": ",".join(climatology.VARIABLES), "models": MAIN_MODEL, "past_days": past,
                 "forecast_days": fut, "timezone": TZ}
        weight = call_weight(len(DAILY_VARS) + len(climatology.VARIABLES), past + fut, len(chunk))
        for pid, loc in zip(chunk, client.get(FORECAST_URL, query, weight)):
            out[pid] = loc
        log.info("Main model: %d/%d points", len(out), len(points))
    return out


def fetch_band(points: dict, client: Client, params: dict) -> dict:
    fut = params["forecast_days"] + 1
    out = {}
    for chunk in batches(list(points), BATCH):
        query = {**coord_params([points[p] for p in chunk]), "daily": ",".join(DAILY_VARS),
                 "models": ",".join(BAND_MODELS), "forecast_days": fut, "timezone": TZ}
        weight = call_weight(len(DAILY_VARS), fut, len(chunk), n_models=len(BAND_MODELS))
        for pid, loc in zip(chunk, client.get(FORECAST_URL, query, weight)):
            out[pid] = loc
        log.info("Band models: %d/%d points", len(out), len(points))
    return out


def _fill(values: list, default: float) -> tuple[list[float], int]:
    """Replace missing values: precipitation with 0, others with the previous value."""
    out, missing, last = [], 0, default
    for v in values:
        if v is None:
            missing += 1
            v = last
        out.append(float(v))
        last = v
    return out, missing


def build_series(loc: dict, quantiles: dict | None, pid: str) -> tuple[dict, list[date], int]:
    daily = loc["daily"]
    dates = [date.fromisoformat(d) for d in daily["time"]]
    series, missing = {}, 0
    for var, key in SERIES_KEYS.items():
        values, n = _fill(daily[var], 0.0 if key == "precip" else (next((v for v in daily[var] if v is not None), 0.0)))
        series[key] = values
        missing += n
    sm = climatology.daily_sm_0_28(loc["hourly"])
    series["sm_pct"] = [climatology.percentile(quantiles, pid, d.month, v) for d, v in zip(dates, sm)]
    series["month"] = [d.month for d in dates]
    return series, dates, missing


def band_series(base: dict, loc: dict, model: str, first: int) -> dict | None:
    """Base series with forecast days replaced by another model's values (where available)."""
    daily = loc["daily"]
    out = {k: list(v) for k, v in base.items()}
    n_used = 0
    for var, key in SERIES_KEYS.items():
        values = daily.get(f"{var}_{model}")
        if values is None:
            continue
        for j, v in enumerate(values):
            if v is not None and first + j < len(out[key]):
                out[key][first + j] = float(v)
                n_used += 1
    return out if n_used else None


def compute_point(pid: str, main: dict, band: dict | None, quantiles: dict | None, params: dict) -> dict:
    series, dates, missing = build_series(main, quantiles, pid)
    first = params["api_window_days"]  # index of today
    days = range(first, first + params["forecast_days"] + 1)
    w_myc = [weather_score(series, i, "myc", params)["W"] for i in days]
    w_frost = [weather_score(series, i, "frost", params)["W"] for i in days]
    low, high = list(w_myc), list(w_myc)
    if band is not None:
        start = first + params["uncertain_from_day"]
        for model in BAND_MODELS:
            alt = band_series(series, band, model, first)
            if alt is None:
                continue
            for i in range(start, first + params["forecast_days"] + 1):
                w = weather_score(alt, i, "myc", params)["W"]
                low[i - first] = min(low[i - first], w)
                high[i - first] = max(high[i - first], w)
    return {
        "dates": [d.isoformat() for d in dates[first:first + params["forecast_days"] + 1]],
        "w_myc": [round_half_up(v) for v in w_myc],
        "w_frost": [round_half_up(v) for v in w_frost],
        "w_low": [round_half_up(v) for v in low],
        "w_high": [round_half_up(v) for v in high],
        "rain": [round(series["precip"][i], 1) for i in days],
        "tmean": [round(series["tmean"][i], 1) for i in days],
        "_missing": missing,
        "_sm_clim": not all(math.isnan(series["sm_pct"][i]) for i in days),
    }


def load_points(path) -> dict:
    meta = json.loads(path.read_text(encoding="utf-8"))
    return {pid: tuple(latlon) for pid, latlon in meta["points"].items()}


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--meta", default=str(STATIC_DIR / "cells_meta.json"))
    ap.add_argument("--limit", type=int, default=0, help="only the first N points (test runs)")
    ap.add_argument("--out", default=str(DAILY_DIR))
    ap.add_argument("--estimate-only", action="store_true")
    ap.add_argument("--backtest-points", action="store_true", help="use the backtest cells' points (test runs)")
    args = ap.parse_args()

    from pathlib import Path
    params = model_params()
    if args.backtest_points:
        import yaml
        from pipeline.paths import CONFIG_DIR
        cfg = yaml.safe_load((CONFIG_DIR / "backtest.yaml").read_text(encoding="utf-8"))
        points = {c["point"]: tuple(float(x) for x in c["point"].split("_")) for c in cfg["cells"]}
    else:
        points = load_points(Path(args.meta))
    if args.limit:
        points = dict(list(points.items())[:args.limit])
    est = estimate_calls(len(points), params)
    log.info("Weather points: %d, estimated API calls: %s", len(points), est)
    if args.estimate_only:
        return

    t0 = time.time()
    client = Client(budget=3000)
    main_data = fetch_main(points, client, params)
    band_data = fetch_band(points, client, params)
    quantiles = climatology.load_quantiles()

    result, missing, with_clim = {}, 0, 0
    for pid in points:
        r = compute_point(pid, main_data[pid], band_data.get(pid), quantiles, params)
        missing += r.pop("_missing")
        with_clim += r.pop("_sm_clim")
        dates = r.pop("dates")
        result[pid] = r

    now = datetime.now(timezone.utc)
    local_day = now.astimezone(ZoneInfo(TZ)).date()
    out = {
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "params_version": params["params_version"],
        "dates": dates,
        "uncertain_from_day": params["uncertain_from_day"],
        "models": {"main": MAIN_MODEL, "band": BAND_MODELS},
        "sm_climatology_points": with_clim,
        "attribution": "Dane pogodowe: Open-Meteo.com (CC BY 4.0), ECMWF, NOAA GFS",
        "points": result,
    }
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    text = json.dumps(out, separators=(",", ":"))
    (out_dir / "latest.json").write_text(text, encoding="utf-8")
    (out_dir / f"{local_day.isoformat()}.json").write_text(text, encoding="utf-8")
    log.info("Done: %d points, %.1f API calls, %.0f s, latest.json %.1f kB, missing values filled: %d, "
             "points with soil climatology: %d", len(result), client.calls, time.time() - t0, len(text) / 1024,
             missing, with_clim)
    summary = {"points": len(result), "api_calls": round(client.calls, 1), "seconds": round(time.time() - t0),
               "latest_kb": round(len(text) / 1024, 1), "sm_climatology_points": with_clim, "date": local_day.isoformat()}
    (out_dir / "run_summary.json").write_text(json.dumps(summary), encoding="utf-8")


if __name__ == "__main__":
    main()
