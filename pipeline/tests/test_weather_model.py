import math

import pytest

from pipeline.params import model_params
from pipeline.weather import model as wm

P = model_params()
N = 45  # days -30..+14 like the daily run


def series(precip=None, tmean=14.0, tmin=8.0, et0=1.0, sm=0.5, month=9):
    return {
        "precip": precip if precip is not None else [0.0] * N,
        "tmean": [tmean] * N if not isinstance(tmean, list) else tmean,
        "tmin": [tmin] * N if not isinstance(tmin, list) else tmin,
        "et0": [et0] * N,
        "sm_pct": [sm] * N,
        "month": [month] * N,
    }


def test_lag_kernel_nodes_from_research():
    assert wm.lag_kernel(5, P) == pytest.approx(0.3)
    assert wm.lag_kernel(8, P) == pytest.approx(0.8)
    assert wm.lag_kernel(10, P) == pytest.approx(1.0)
    assert wm.lag_kernel(14, P) == pytest.approx(0.7)
    assert wm.lag_kernel(21, P) == pytest.approx(0.2)
    assert wm.lag_kernel(1, P) == 0.0
    assert wm.lag_kernel(30, P) == 0.0


def test_trigger_peaks_about_ten_days_after_heavy_rain():
    rain = [0.0] * N
    rain[10] = 30.0  # one heavy rain day
    s = series(rain)
    values = {k: wm.trigger(s["precip"], 10 + k, P) for k in range(0, 25)}
    assert values[0] == 0.0
    assert max(values, key=values.get) == 10
    assert values[10] == pytest.approx(1.0)
    assert values[14] == pytest.approx(0.7)


def test_light_rain_does_not_trigger():
    s = series([8.0] * N)
    assert wm.trigger(s["precip"], 40, P) == 0.0


def test_antecedent_precipitation_formula():
    rain = [0.0] * N
    rain[39] = 10.0  # yesterday for i = 40
    assert wm.antecedent_precipitation(rain, 40, P) == pytest.approx(9.0)


def test_temperature_optimum_and_heat_drought_cutoff():
    assert wm.temperature([14.0] * N, [8.0] * N, [0.0] * N, 40, "myc", P) == pytest.approx(1.0)
    assert wm.temperature([19.0] * N, [12.0] * N, [0.0] * N, 40, "myc", P) == 0.0
    wet = wm.temperature([19.0] * N, [12.0] * N, [2.0] * N, 40, "myc", P)
    assert wet == pytest.approx(math.exp(-1.0))


def test_frost_penalty_differs_by_variant():
    tmin = [5.0] * N
    tmin[39] = tmin[40] = -2.0
    myc = wm.temperature([14.0] * N, tmin, [0.0] * N, 40, "myc", P)
    frost = wm.temperature([14.0] * N, tmin, [0.0] * N, 40, "frost", P)
    assert myc == pytest.approx(0.3)
    assert frost == pytest.approx(0.7)
    tmin[39] = 5.0  # only one frosty night: no penalty
    assert wm.temperature([14.0] * N, tmin, [0.0] * N, 40, "myc", P) == pytest.approx(1.0)


def test_season_outside_season_kills_w():
    s = series(month=1)
    assert wm.weather_score(s, 40, "myc", P)["W"] == 0.0


def test_w_is_bounded_and_increases_after_rain():
    dry = series()
    rain = [0.0] * N
    rain[30] = 30.0
    wet = series(rain)
    w_dry = wm.weather_score(dry, 40, "myc", P)["W"]
    w_wet = wm.weather_score(wet, 40, "myc", P)["W"]
    assert 0.0 <= w_dry < w_wet <= 100.0


def test_missing_soil_percentile_falls_back_to_median():
    s = series(sm=float("nan"))
    t = series(sm=0.5)
    assert wm.weather_score(s, 40, "myc", P)["W"] == pytest.approx(wm.weather_score(t, 40, "myc", P)["W"])
