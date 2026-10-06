"""Backtest chart: IG line (top panel) and daily rain bars (bottom panel), shared date axis.

Two panels instead of a dual y-axis: IG (0-100) and rain (mm) have different scales.
"""

from datetime import date, timedelta

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"
IG_LINE = "#2a78d6"   # categorical slot 1
RAIN = "#1baf7a"      # categorical slot 3, its own panel
FROST = "#4a3aa7"     # categorical slot 7
ZONE_GREEN = "#e3f1e3"
ZONE_YELLOW = "#fbf1d6"
LAG_WINDOW = "#2a78d6"  # drawn translucent over the colour zones


def plot_cell(result: dict, path, params: dict) -> None:
    days = result["days"]
    x = [date.fromisoformat(d["date"]) for d in days]
    fig, (ax, axr) = plt.subplots(2, 1, figsize=(10, 5.8), sharex=True, gridspec_kw={"height_ratios": [2.2, 1]},
                                  facecolor=SURFACE)
    for a in (ax, axr):
        a.set_facecolor(SURFACE)
        for side in ("top", "right"):
            a.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            a.spines[side].set_color(GRID)
        a.tick_params(colors=INK_2, labelsize=9)
        a.grid(axis="y", color=GRID, linewidth=0.8)
        a.set_axisbelow(True)

    green, yellow = params["color_green_min"], params["color_yellow_min"]
    ax.axhspan(green, 100, color=ZONE_GREEN, zorder=0)
    ax.axhspan(yellow, green, color=ZONE_YELLOW, zorder=0)
    ax.text(x[-1] + timedelta(days=1), (green + 100) / 2, "zielony ≥60", color=INK_2, fontsize=8, va="center")
    ax.text(x[-1] + timedelta(days=1), (yellow + green) / 2, "żółty 35–59", color=INK_2, fontsize=8, va="center")

    for ev in result["rain_events"]:
        e = date.fromisoformat(ev["event"])
        ax.axvspan(e + timedelta(days=7), e + timedelta(days=14), color=LAG_WINDOW, alpha=0.09, linewidth=0, zorder=1)
        ax.axvline(e, color=RAIN, linewidth=1, linestyle=(0, (3, 2)), zorder=1)
        axr.axvline(e, color=RAIN, linewidth=1, linestyle=(0, (3, 2)), zorder=1)

    ax.plot(x, [d["ig"] for d in days], color=IG_LINE, linewidth=2, zorder=3)
    best = max(days, key=lambda d: d["ig"])
    bx = date.fromisoformat(best["date"])
    ax.scatter([bx], [best["ig"]], s=36, color=IG_LINE, edgecolor=SURFACE, linewidth=2, zorder=4)
    ax.annotate(f"max {best['ig']} ({bx.day}.{bx.month:02d})", (bx, best["ig"]), xytext=(6, 6),
                textcoords="offset points", fontsize=8.5, color=INK)

    frost = [date.fromisoformat(f) for f in result["frost_days"]]
    if frost:
        ax.scatter(frost, [3] * len(frost), marker="v", s=40, color=FROST, zorder=4)
        ax.annotate("przymrozek (Tmin < 0 °C)", (frost[0], 3), xytext=(6, 6), textcoords="offset points",
                    fontsize=8, color=INK_2)

    ax.set_ylim(0, 100)
    ax.set_ylabel("IG (wszystkie gatunki)", color=INK_2, fontsize=9)
    ax.set_title(f"{result['name']}: {result['forest']}, H_max {result['h_max']:.2f}".replace(".", ","), loc="left", fontsize=11,
                 color=INK, pad=10)

    axr.bar(x, [d["rain"] for d in days], width=0.75, color=RAIN, zorder=2)
    axr.set_ylabel("opad [mm/d]", color=INK_2, fontsize=9)
    axr.set_ylim(0, max(10, max(d["rain"] for d in days) * 1.15))
    axr.xaxis.set_major_locator(mdates.MonthLocator())
    axr.xaxis.set_minor_locator(mdates.WeekdayLocator(byweekday=0))
    axr.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))

    fig.text(0.01, 0.01, "Przerywana linia: początek opadu ≥20 mm w 3 dni; jasne pole: 7–14 dni po nim. "
             "Pogoda: ERA5/ERA5-Land (Open-Meteo), nie archiwalne prognozy.", fontsize=7.5, color=INK_2)
    fig.tight_layout(rect=(0, 0.03, 0.97, 1))
    fig.savefig(path, dpi=150, facecolor=SURFACE)
    plt.close(fig)
