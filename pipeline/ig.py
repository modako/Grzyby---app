"""Mushroom index IG: the contract shared by the pipeline and the app (docs/SPEC.md, chapter 5)."""

import math

GREY, GREEN, YELLOW, RED = "grey", "green", "yellow", "red"


def round_half_up(x: float) -> int:
    """Same as JavaScript Math.round for the non-negative values used here."""
    return math.floor(x + 0.5)


def ig(w: float, h: float, params: dict) -> float:
    """IG = W * (0.4 + 0.6 * H), unrounded."""
    return w * (params["ig_base"] + params["ig_h_weight"] * h)


def color(ig_rounded: int, banned: bool, params: dict) -> str:
    if banned:
        return GREY
    if ig_rounded >= params["color_green_min"]:
        return GREEN
    if ig_rounded >= params["color_yellow_min"]:
        return YELLOW
    return RED


def cell_index(w_by_variant: dict[str, float], h_by_species: dict[str, float], banned: bool,
               params: dict, species: str | None = None) -> dict:
    """IG for one cell and day: one species, or all species (max over species) when species is None."""
    names = [species] if species else params["species"]
    values = {sp: ig(w_by_variant[params["weather_variant"][sp]], h_by_species[sp], params) for sp in names}
    best = max(values, key=values.get)
    value = round_half_up(values[best])
    return {"ig": value, "color": color(value, banned, params), "species": best}
