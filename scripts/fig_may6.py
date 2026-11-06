#!/usr/bin/env python
"""Figure: May 6, 2010 against a calm day chosen by rule (D-025).

Top two panels: each day's deseasonalized one-minute returns, on the same scale.
Bottom panel: both days' Husid curves (cumulative share of the day's energy), each with
its W50 window (the shortest stretch holding half the day's energy) shaded.

The calm day is picked by the D-025 rule, never by hand: among Thursdays from 2010-04-01
to 2010-05-31 other than May 6 that are not FOMC days, ISM release days or half-days and
have no missing minutes, the day whose RV is closest to the median RV of that set
(ties: the earlier day).

Needs the clean and measures stages (``python scripts/run_all.py``). Writes
``paper/figures/may6_vs_calm.png`` and prints the chosen day and both days' W50.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fai import config  # noqa: E402
from fai.husid import husid_curve  # noqa: E402
from fai.seasonality import deseasonalize, seasonal_variance, to_matrix  # noqa: E402

EVENT_DAY = pd.Timestamp("2010-05-06")
CALM_WINDOW = (pd.Timestamp("2010-04-01"), pd.Timestamp("2010-05-31"))

# Colours: reference categorical slots 1-2 and chart chrome (dataviz palette), light mode.
INK, INK_2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS, SURFACE = "#e1e0d9", "#c3c2b7", "#fcfcfb"
C_EVENT, C_CALM = "#2a78d6", "#eb6834"


def pick_calm_day(daily: pd.DataFrame) -> pd.Timestamp:
    """The D-025 rule. ``daily`` needs rv, half_day, n_missing_unexplained, fomc,
    macro_release, indexed by session date."""
    d = daily.loc[CALM_WINDOW[0]:CALM_WINDOW[1]]
    ok = ((d.index.dayofweek == 3) & (d.index != EVENT_DAY) & ~d["fomc"].astype(bool)
          & ~d["macro_release"].astype(bool) & ~d["half_day"].astype(bool)
          & (d["n_missing_unexplained"] == 0) & d["rv"].notna())
    cand = d.loc[ok, "rv"]
    if cand.empty:
        raise ValueError("no day satisfies the D-025 calm-day rule")
    dist = (cand - cand.median()).abs()
    return dist[dist == dist.min()].index.min()


def w50_window(a2: np.ndarray, frac: float = config.W_FRAC) -> tuple[float, float]:
    """(start, end) in minutes after the open of the shortest window holding ``frac`` of
    the energy; same convention as husid.shortest_window (integer starts, interpolated
    ends)."""
    H = husid_curve(a2)
    best = (np.nan, np.nan)
    for i in range(H.size - 1):
        target = H[i] + frac
        if target > H[-1] + 1e-12:
            break
        end = _first_reach(H, target)
        if np.isnan(best[0]) or end - i < best[1] - best[0]:
            best = (float(i), end)
    return best


def _first_reach(H: np.ndarray, target: float) -> float:
    """Smallest u with H(u) = target on the piecewise-linear curve (flat stretches allowed)."""
    j = int(np.searchsorted(H, target - 1e-15, side="left"))
    if j == 0:
        return 0.0
    lo, hi = H[j - 1], H[j]
    return float(j - 1 + (target - lo) / (hi - lo)) if hi > lo else float(j)


def clock_ticks(n: int):
    ticks = np.arange(0, n + 1, 60)
    labels = [f"{9 + (30 + t) // 60}:{(30 + t) % 60:02d}" for t in ticks]
    return ticks, labels


def draw(rt: dict[pd.Timestamp, np.ndarray], w50: dict, out: Path, labels: dict) -> Path:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.size": 9, "axes.edgecolor": AXIS, "axes.labelcolor": INK_2,
                         "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK,
                         "axes.titlesize": 9.5, "axes.titleweight": "bold",
                         "axes.titlelocation": "left"})
    days = list(rt)
    colors = {days[0]: C_EVENT, days[1]: C_CALM}
    fig = plt.figure(figsize=(7.2, 6.4), facecolor=SURFACE)
    gs = fig.add_gridspec(3, 1, height_ratios=[1, 1, 2.1], hspace=0.45)
    lim = max(np.nanmax(np.abs(v)) for v in rt.values()) * 1.05
    n = max(v.size for v in rt.values())
    ticks, ticklabels = clock_ticks(n)

    for k, d in enumerate(days):
        ax = fig.add_subplot(gs[k])
        x = np.arange(rt[d].size) + 0.5
        ax.vlines(x, 0, rt[d], color=colors[d], linewidth=0.8)
        ax.axhline(0, color=AXIS, linewidth=0.8)
        ax.set_ylim(-lim, lim)
        ax.set_xlim(0, n)
        ax.set_xticks(ticks, [])
        ax.set_title(f"{labels[d]}: one-minute returns (deseasonalized)", color=INK)
        ax.grid(axis="y", color=GRID, linewidth=0.6)
        ax.set_facecolor(SURFACE)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.set_ylabel("r̃ (sd units)")

    ax = fig.add_subplot(gs[2])
    for d in days:
        H = husid_curve(rt[d] ** 2)
        a, b = w50[d]
        ax.axvspan(a, b, color=colors[d], alpha=0.14, linewidth=0)
        ax.plot(np.arange(H.size), H, color=colors[d], linewidth=1.8,
                label=f"{labels[d]}  (W50 = {b - a:.0f} min)")
    ax.set_xlim(0, n)
    ax.set_ylim(0, 1.02)
    ax.set_xticks(ticks, ticklabels)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0], ["0", "25%", "50%", "75%", "100%"])
    ax.set_ylabel("share of the day's energy")
    ax.set_title("Husid curves, with each day's W50 window shaded", color=INK)
    ax.grid(color=GRID, linewidth=0.6)
    ax.set_facecolor(SURFACE)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(loc="lower right", frameon=False, fontsize=8)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200, facecolor=SURFACE, bbox_inches="tight")
    plt.close(fig)
    return out


def main(symbol: str = "SPY") -> None:
    minutes = pd.read_parquet(config.PROCESSED / f"{symbol}_minutes.parquet")
    sessions = pd.read_parquet(config.PROCESSED / "sessions.parquet")
    daily = pd.read_parquet(config.PROCESSED / f"{symbol}_daily.parquet")
    R, G = to_matrix(minutes, "r"), to_matrix(minutes, "gap")
    half_days = sessions.index[sessions["half_day"]]
    Rt = deseasonalize(R, G, seasonal_variance(R, G, exclude=half_days))
    calm = pick_calm_day(daily)
    days = [EVENT_DAY, calm]
    rt = {d: Rt.loc[d].to_numpy(float) for d in days}
    w50 = {d: w50_window(rt[d] ** 2) for d in days}
    labels = {EVENT_DAY: "May 6, 2010", calm: calm.strftime("%b %-d, %Y") if sys.platform != "win32"
              else calm.strftime("%b %#d, %Y")}
    out = draw(rt, w50, config.ROOT / "paper" / "figures" / "may6_vs_calm.png", labels)
    print(f"calm day (D-025 rule): {calm.date()}")
    for d in days:
        print(f"  {d.date()}: RV {daily.at[d, 'rv']:.3g}, W50 {w50[d][1] - w50[d][0]:.1f} min "
              f"(stored w50 {daily.at[d, 'w50']:.1f})")
    print(f"wrote {out}")


if __name__ == "__main__":
    main(*sys.argv[1:])
