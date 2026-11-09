#!/usr/bin/env python
"""Figure: the intraday volatility profile (the "U-shape") that deseasonalizing removes.

The line is the typical seasonal standard deviation s(tau) at each minute of the day, in
basis points per minute: the profile the pipeline actually divides by (RMS over the prior
60 sessions with 5-minute smoothing, D-019/D-020), taken as the median over the test
days 2010-2025. The band runs from the 10th to the 90th percentile across days, so it
shows how much the profile itself moves with the volatility regime.

Needs the clean stage (``python scripts/run_all.py``). Writes
``paper/figures/intraday_profile.png`` and prints the open, midday and close levels and
the minutes that stand out from their neighbours, to decide on annotations after looking.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fai import config  # noqa: E402
from fai.seasonality import seasonal_variance, to_matrix  # noqa: E402

TEST_YEARS = ("2010-01-01", "2025-12-31")
INK, INK_2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS, SURFACE = "#e1e0d9", "#c3c2b7", "#fcfcfb"
C_LINE = "#2a78d6"
# Labels chosen after looking at the first render (2026-11-08): (minute after the open,
# text, label offset in minutes, horizontal alignment). Each points at the highest
# median within a few minutes of the event.
ANNOTATIONS = [(30, "10:00 data releases", 0, "center"),
               (270, "2:00 Fed statements and minutes", 0, "center"),
               (389, "the close", -22, "right")]


def profile(S2: pd.DataFrame, days) -> pd.DataFrame:
    """Median and 10th/90th percentiles of s(tau) in basis points, across ``days``."""
    s_bp = np.sqrt(S2.loc[S2.index.isin(days)]) * 1e4
    return pd.DataFrame({"median": s_bp.median(), "p10": s_bp.quantile(0.10),
                         "p90": s_bp.quantile(0.90)})


def standouts(med: pd.Series, k: int = 6) -> pd.Series:
    """Minutes most above the average of the two minutes on either side (ratio)."""
    nb = pd.concat([med.shift(i) for i in (-2, -1, 1, 2)], axis=1).mean(axis=1)
    return (med / nb).iloc[2:-2].nlargest(k)


def clock(tau: int) -> str:
    m = 30 + int(tau)
    return f"{9 + m // 60}:{m % 60:02d}"


def draw(p: pd.DataFrame, out: Path) -> Path:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.size": 9, "axes.edgecolor": AXIS, "axes.labelcolor": INK_2,
                         "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK,
                         "axes.titlesize": 9.5, "axes.titleweight": "bold",
                         "axes.titlelocation": "left"})
    fig, ax = plt.subplots(figsize=(7.2, 3.4), facecolor=SURFACE)
    x = p.index.to_numpy() + 0.5
    ax.fill_between(x, p["p10"], p["p90"], color=C_LINE, alpha=0.14, linewidth=0)
    ax.plot(x, p["median"], color=C_LINE, linewidth=1.6)
    med = p["median"]
    for tau, text, dx, ha in ANNOTATIONS:
        near = med.iloc[max(0, tau - 2): min(len(med), tau + 8)]
        t, y = near.idxmax(), near.max()
        ax.annotate(text, xy=(t + 0.5, y), xytext=(t + 0.5 + dx, y + 1.1), ha=ha, va="bottom",
                    fontsize=8, color=INK_2,
                    arrowprops={"arrowstyle": "-", "color": MUTED, "linewidth": 0.7,
                                "shrinkA": 1, "shrinkB": 2})
    ticks = np.arange(0, 391, 60)
    ax.set_xticks(ticks, [clock(t) for t in ticks])
    ax.set_xlim(0, 390)
    ax.set_ylim(0, None)
    ax.set_ylabel("s(τ), basis points per minute")
    ax.set_title("Typical one-minute volatility by time of day, SPY 2010-2025", color=INK)
    ax.text(0.99, 0.97, "line: median across days; band: 10th-90th percentile",
            transform=ax.transAxes, ha="right", va="top", fontsize=8, color=INK_2)
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    ax.set_facecolor(SURFACE)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
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
    S2 = seasonal_variance(R, G, exclude=half_days)
    d = daily.sort_index().loc[TEST_YEARS[0]:TEST_YEARS[1]]
    p = profile(S2, d.index[d["in_tests"].astype(bool)])
    out = draw(p, config.ROOT / "paper" / "figures" / "intraday_profile.png")
    med = p["median"]
    print(f"open (9:30) {med.iloc[0]:.2f} bp, 9:31 {med.iloc[1]:.2f}, midday (12:30) "
          f"{med.iloc[180]:.2f}, 15:59 {med.iloc[389]:.2f}; open/midday {med.iloc[0] / med.iloc[180]:.1f}x")
    print("minutes standing out from their neighbours (ratio):")
    for tau, r in standouts(med).items():
        print(f"  {clock(tau)}  {r:.2f}x")
    print(f"wrote {out}")


if __name__ == "__main__":
    main(*sys.argv[1:])
