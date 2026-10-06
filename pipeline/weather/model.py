"""Weather component W of the mushroom index (docs/SPEC.md, chapter 4).

Pure functions over daily series. Index i is the target day; the series must start at least
`api_window_days` days before the first target day. All numbers come from `params`.
"""

import math
from collections.abc import Sequence

from pipeline.suitability import interp_nodes


def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def antecedent_precipitation(precip: Sequence[float], i: int, params: dict) -> float:
    """API_d = sum_{k=1..30} P_{d-k} * 0.9^k."""
    decay = params["api_decay"]
    return sum(precip[i - k] * decay ** k for k in range(1, params["api_window_days"] + 1) if i - k >= 0)


def water_balance(precip: Sequence[float], et0: Sequence[float], i: int, params: dict) -> float:
    """Bilans14_d = sum_{k=1..14} (P_{d-k} - ET0_{d-k})."""
    return sum(precip[i - k] - et0[i - k] for k in range(1, params["balance_window_days"] + 1) if i - k >= 0)


def moisture(precip, et0, sm_pct: float | None, i: int, params: dict) -> float:
    """M in [0, 1]. Missing soil-moisture percentile falls back to the median (0.5)."""
    w = params["m_weights"]
    api = antecedent_precipitation(precip, i, params)
    bal = water_balance(precip, et0, i, params)
    pct = 0.5 if sm_pct is None or math.isnan(sm_pct) else sm_pct
    return (w["api"] * sigmoid((api - params["api_center_mm"]) / params["api_scale_mm"])
            + w["balance"] * sigmoid(bal / params["balance_scale_mm"])
            + w["sm"] * pct)


def lag_kernel(k: int, params: dict) -> float:
    return interp_nodes(k, params["lag_kernel_nodes"])


def trigger(precip: Sequence[float], i: int, params: dict) -> float:
    """L in [0, 1]: rain days >= 10 mm contribute with a delay kernel peaking ~10 days later."""
    total = 0.0
    for k in range(1, params["lag_max_days"] + 1):
        if i - k < 0:
            break
        p = precip[i - k]
        if p >= params["trigger_min_mm"]:
            total += min(1.0, p / params["trigger_sat_mm"]) * lag_kernel(k, params)
    return min(1.0, total)


def temperature(tmean: Sequence[float], tmin: Sequence[float], precip: Sequence[float], i: int,
                variant: str, params: dict) -> float:
    """T in [0, 1] with the heat-and-drought cut-off and the frost penalty of the given variant."""
    n = params["t_window_days"]
    window = range(max(0, i - n + 1), i + 1)
    t5 = sum(tmean[j] for j in window) / len(window)
    p5 = sum(precip[j] for j in window) / len(window)
    t = math.exp(-(((t5 - params["t_opt"]) / params["t_width"]) ** 2))
    if t5 > params["heat_dry_t5"] and p5 < params["heat_dry_p5_mm"]:
        t = 0.0
    nights = range(max(0, i - params["frost_nights_window"] + 1), i + 1)
    if sum(1 for j in nights if tmin[j] < params["frost_tmin"]) >= params["frost_nights_min"]:
        t *= params["frost_mult"][variant]
    return t


def season(month: int, params: dict) -> float:
    return float(params["season_s"][month])


def weather_score(series: dict, i: int, variant: str, params: dict) -> dict:
    """W for target day i. `series` holds lists: precip, tmean, tmin, et0, sm_pct, month."""
    m = moisture(series["precip"], series["et0"], series["sm_pct"][i], i, params)
    lag = trigger(series["precip"], i, params)
    t = temperature(series["tmean"], series["tmin"], series["precip"], i, variant, params)
    s = season(series["month"][i], params)
    w = params["w_weights"]
    return {"M": m, "L": lag, "T": t, "S": s, "W": 100.0 * s * t * (w["m"] * m + w["l"] * lag)}
