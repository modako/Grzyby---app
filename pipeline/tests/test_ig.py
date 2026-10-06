import json

import pytest

from pipeline import ig
from pipeline.paths import ROOT
from pipeline.params import model_params

P = model_params()
CASES = json.loads((ROOT / "docs" / "contract" / "ig_cases.json").read_text(encoding="utf-8"))["cases"]


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_contract_cases(case):
    inp, exp = case["input"], case["expected"]
    out = ig.cell_index({"myc": inp["w_myc"], "frost": inp["w_frost"]}, inp["h"], inp["banned"], P, inp["species"])
    assert out == exp


def test_contract_params_match_model_params():
    params = json.loads((ROOT / "docs" / "contract" / "ig_cases.json").read_text(encoding="utf-8"))["params"]
    assert params["ig_base"] == P["ig_base"]
    assert params["ig_h_weight"] == P["ig_h_weight"]
    assert params["color_green_min"] == P["color_green_min"]
    assert params["color_yellow_min"] == P["color_yellow_min"]
    for sp, variant in P["weather_variant"].items():
        assert params["variant"].get(sp, params["variant"]["default"]) == variant


def test_round_half_up_matches_js_math_round():
    assert ig.round_half_up(34.5) == 35
    assert ig.round_half_up(0.49) == 0
