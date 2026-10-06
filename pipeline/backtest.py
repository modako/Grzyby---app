"""Backtest of the mushroom index on past weather: python -m pipeline.backtest

For the cells in pipeline/config/backtest.yaml the index is computed day by day from
ERA5/ERA5-Land reanalysis (observed weather, not archived forecasts), i.e. what the app
would have shown as "today" on each day. Writes PNG charts and backtest.json to docs/backtest/.
"""

import json
import logging
import re
import unicodedata
from datetime import date, timedelta

import yaml

from pipeline.ig import cell_index
from pipeline.params import model_params
from pipeline.paths import CONFIG_DIR, ROOT
from pipeline.weather import climatology
from pipeline.weather.model import weather_score
from pipeline.weather.openmeteo import ARCHIVE_URL, Client, call_weight

log = logging.getLogger("backtest")

OUT_DIR = ROOT / "docs" / "backtest"
CLIM_YEARS = list(range(2016, 2026))
DAILY_VARS = ["precipitation_sum", "temperature_2m_mean", "temperature_2m_min", "et0_fao_evapotranspiration"]
KEYS = {"precipitation_sum": "precip", "temperature_2m_mean": "tmean", "temperature_2m_min": "tmin",
        "et0_fao_evapotranspiration": "et0"}


def slug(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.replace("ł", "l").replace("Ł", "L")).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def fetch_weather(client: Client, lat: float, lon: float, start: date, end: date) -> dict:
    days = (end - start).days + 1
    base = {"latitude": lat, "longitude": lon, "start_date": start.isoformat(), "end_date": end.isoformat(),
            "timezone": "Europe/Warsaw"}
    daily = None
    for model in (None, "era5"):
        query = {**base, "daily": ",".join(DAILY_VARS)}
        if model:
            query["models"] = model
        loc = client.get(ARCHIVE_URL, query, call_weight(len(DAILY_VARS), days))[0]
        if all(any(v is not None for v in loc["daily"][var]) for var in DAILY_VARS):
            daily = loc["daily"]
            log.info("Daily weather from archive model %s", model or "best_match")
            break
        log.warning("Archive model %s returned empty variables, trying the next one", model or "best_match")
    if daily is None:
        raise RuntimeError("No complete daily weather in the archive")
    soil = client.get(ARCHIVE_URL, {**base, "hourly": ",".join(climatology.VARIABLES), "models": "era5_land"},
                      call_weight(len(climatology.VARIABLES), days))[0]
    return {"daily": daily, "sm": climatology.daily_sm_0_28(soil["hourly"])}


def rain_events(dates, precip, threshold=20.0, window=3) -> list[date]:
    """First days of rain episodes with >= threshold mm within `window` days."""
    events, i = [], 0
    while i < len(precip):
        if sum(precip[i:i + window]) >= threshold and precip[i] > 0:
            events.append(dates[i])
            i += window + 2
        else:
            i += 1
    return events


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    params = model_params()
    cfg = yaml.safe_load((CONFIG_DIR / "backtest.yaml").read_text(encoding="utf-8"))
    start, end = date.fromisoformat(cfg["period"]["start"]), date.fromisoformat(cfg["period"]["end"])
    lead = params["api_window_days"] + 1
    fetch_start = start - timedelta(days=lead)
    points = {c["point"]: tuple(float(x) for x in c["point"].split("_")) for c in cfg["cells"]}

    client = Client(budget=1500)
    progress = climatology.fetch(points, CLIM_YEARS, client, budget=800)
    log.info("Climatology: %s", progress)
    quantiles = climatology.build_quantiles(CLIM_YEARS)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    for cell in cfg["cells"]:
        lat, lon = points[cell["point"]]
        wx = fetch_weather(client, lat, lon, fetch_start, end)
        dates = [date.fromisoformat(d) for d in wx["daily"]["time"]]
        series = {key: [float(v) if v is not None else 0.0 for v in wx["daily"][var]] for var, key in KEYS.items()}
        series["sm_pct"] = [climatology.percentile(quantiles, cell["point"], d.month, v) for d, v in zip(dates, wx["sm"])]
        series["month"] = [d.month for d in dates]
        days = []
        for i, d in enumerate(dates):
            if d < start:
                continue
            myc = weather_score(series, i, "myc", params)
            frost = weather_score(series, i, "frost", params)
            idx = cell_index({"myc": myc["W"], "frost": frost["W"]}, cell["h"], False, params)
            days.append({"date": d.isoformat(), "rain": round(series["precip"][i], 1),
                         "tmean": round(series["tmean"][i], 1), "tmin": round(series["tmin"][i], 1),
                         "sm_pct": None if series["sm_pct"][i] != series["sm_pct"][i] else round(series["sm_pct"][i], 2),
                         "M": round(myc["M"], 3), "L": round(myc["L"], 3), "T": round(myc["T"], 3), "S": myc["S"],
                         "w_myc": round(myc["W"], 1), "w_frost": round(frost["W"], 1),
                         "ig": idx["ig"], "ig_species": idx["species"], "color": idx["color"]})
        in_period = [x for x in days]
        events = rain_events([date.fromisoformat(x["date"]) for x in in_period], [x["rain"] for x in in_period])
        lags = []
        for ev in events:
            window = [x for x in in_period if 0 <= (date.fromisoformat(x["date"]) - ev).days <= 21]
            if window:
                peak = max(window, key=lambda x: x["ig"])
                lags.append({"event": ev.isoformat(), "rain_3d": round(sum(x["rain"] for x in in_period
                             if 0 <= (date.fromisoformat(x["date"]) - ev).days < 3), 1),
                             "peak_date": peak["date"], "peak_ig": peak["ig"],
                             "lag_days": (date.fromisoformat(peak["date"]) - ev).days,
                             "ig_at_event": next(x["ig"] for x in in_period if x["date"] == ev.isoformat())})
        frost_days = [x["date"] for x in in_period if x["tmin"] < 0]
        result = {**{k: cell[k] for k in ("name", "id", "point", "forest")}, "h_max": max(cell["h"].values()),
                  "rain_events": lags, "frost_days": frost_days,
                  "days_green": sum(1 for x in in_period if x["color"] == "green"),
                  "days_yellow": sum(1 for x in in_period if x["color"] == "yellow"),
                  "max_ig": max(x["ig"] for x in in_period), "days": in_period,
                  "png": f"{slug(cell['name'])}.png"}
        from pipeline.backtest_plot import plot_cell
        plot_cell(result, OUT_DIR / result["png"], params)
        results.append(result)
        log.info("%s: max IG %d, green days %d, rain events %s", cell["name"], result["max_ig"],
                 result["days_green"], [(e["event"], e["lag_days"]) for e in lags])

    summary = {"period": cfg["period"], "params_version": params["params_version"],
               "weather_source": "Open-Meteo Archive API: ERA5 / ERA5-Land reanalysis (observed weather, not forecasts)",
               "api_calls": round(client.calls, 1), "climatology": progress, "cells": results}
    (OUT_DIR / "backtest.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    log.info("Backtest done, %.1f API calls", client.calls)


if __name__ == "__main__":
    main()
