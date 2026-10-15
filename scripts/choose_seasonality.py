#!/usr/bin/env python
"""Choose the intraday seasonality estimator by the rule fixed in D-019.

Each candidate's s^2(tau) for day d (built from the 60 days before d) is a forecast of
that day's squared one-minute returns. Forecasts are scored with QLIKE,

    loss = log(s^2) + r^2 / s^2,

the standard loss for comparing variance forecasts when the "truth" is a noisy proxy
such as a single squared return (Patton 2011). Lower is better. Written this way it
handles minutes with a zero return, and a difference in average loss between two
candidates does not depend on the units of the returns.

Scored on full trading days 2010-2018 only; 2019-2025 stay untouched. Only
single-minute returns are scored, and every candidate is scored on exactly the same
minutes. Each day's losses are averaged first, so each day counts once.

Rule: the candidate with the lowest average loss is the best. Any simpler candidate
whose loss is not significantly worse than the best's (one-sided Diebold-Mariano test
on the daily average losses, Newey-West standard errors, 5%) is preferred, and the
simplest such candidate wins. Simplicity order = the order of CANDIDATES below; the
first is the registered default.

    python scripts/choose_seasonality.py          # writes reports/seasonality_choice.md
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

CANDIDATES = [  # simplest first; the first is the registered default
    ("RMS, unsmoothed", "rms", 0),
    ("Median, unsmoothed", "median", 0),
    ("RMS, 5-minute smoothing", "rms", 5),
    ("Median, 5-minute smoothing", "median", 5),
]
EVAL_START, EVAL_END = "2010-01-01", "2018-12-31"
ONE_SIDED_5PCT = 1.6448536269514722


def nw_lag(t: int) -> int:
    """Newey-West lag floor(4 (T/100)^(2/9)), the rule registered in HYPOTHESES.md."""
    return int(np.floor(4 * (t / 100) ** (2 / 9)))


def newey_west_se(x: np.ndarray, lag: int) -> float:
    """Standard error of the mean of x with Bartlett-weighted autocovariances."""
    x = np.asarray(x, float) - np.mean(x)
    t = x.size
    v = x @ x / t
    for k in range(1, lag + 1):
        v += 2 * (1 - k / (lag + 1)) * (x[k:] @ x[:-k]) / t
    return float(np.sqrt(v / t))


def daily_qlike(R: pd.DataFrame, S2: pd.DataFrame, mask: pd.DataFrame) -> pd.Series:
    """Average QLIKE per day over the minutes in ``mask``."""
    with np.errstate(divide="ignore", invalid="ignore"):
        loss = np.log(S2) + R ** 2 / S2
    return loss.where(mask).mean(axis=1)


def pick(daily: pd.DataFrame) -> tuple[str, pd.DataFrame]:
    """Apply the D-019 rule to a days x candidates table of daily average losses.

    Returns the winner's name and a summary table in simplicity order.
    """
    mean = daily.mean()
    best = mean.idxmin()
    lag = nw_lag(len(daily))
    rows = []
    for name in daily.columns:
        d = (daily[name] - daily[best]).to_numpy()
        if name == best:
            t = 0.0
        else:
            se = newey_west_se(d, lag)
            t = float(d.mean() / se) if se > 0 else 0.0
        rows.append({"candidate": name, "mean_qlike": mean[name],
                     "vs_default": mean[name] - mean.iloc[0],
                     "dm_t_vs_best": t, "not_worse_than_best": t <= ONE_SIDED_5PCT})
    table = pd.DataFrame(rows)
    winner = table.loc[table["not_worse_than_best"], "candidate"].iloc[0]
    table["winner"] = table["candidate"] == winner
    return winner, table


def evaluate(R: pd.DataFrame, G: pd.DataFrame, half_days,
             start: str = EVAL_START, end: str = EVAL_END) -> tuple[str, pd.DataFrame, dict]:
    estimates = {name: seasonal_variance(R, G, exclude=half_days, method=m, smooth=w)
                 for name, m, w in CANDIDATES}
    in_window = (R.index >= pd.Timestamp(start)) & (R.index <= pd.Timestamp(end))
    full_day = ~R.index.isin(pd.DatetimeIndex(half_days))
    mask = (G == 1) & R.notna()
    mask = mask.where(pd.Series(in_window & full_day, index=R.index), False, axis=0)
    for S2 in estimates.values():                       # identical minutes for all
        mask &= S2.notna() & (S2 > 0)
    daily = pd.DataFrame({name: daily_qlike(R, S2, mask) for name, S2 in estimates.items()})
    daily = daily.dropna()
    winner, table = pick(daily)
    info = {"days": len(daily), "minutes": int(mask.to_numpy().sum()),
            "first": daily.index.min().date(), "last": daily.index.max().date(),
            "nw_lag": nw_lag(len(daily))}
    return winner, table, info


def report(winner: str, table: pd.DataFrame, info: dict, symbol: str) -> str:
    lines = [
        f"# Seasonality estimator choice ({symbol}, D-019)",
        "",
        f"Scored on {info['days']:,} full trading days ({info['first']} to {info['last']}), "
        f"{info['minutes']:,} one-minute returns. Loss: QLIKE, lower is better. "
        f"Diebold-Mariano t-statistics use Newey-West standard errors, lag {info['nw_lag']}; "
        f"a candidate is significantly worse than the best if t > {ONE_SIDED_5PCT:.3f}.",
        "",
        "| Candidate | Mean QLIKE | Difference vs registered default | DM t vs best | "
        "Not significantly worse | Winner |",
        "|---|---|---|---|---|---|",
    ]
    for r in table.itertuples():
        lines.append(f"| {r.candidate} | {r.mean_qlike:.5f} | {r.vs_default:+.5f} | "
                     f"{r.dm_t_vs_best:.2f} | {'yes' if r.not_worse_than_best else 'no'} | "
                     f"{'**yes**' if r.winner else ''} |")
    lines += ["", f"**Winner: {winner}.** Set `SEAS_METHOD` and `SEAS_SMOOTH_MIN` in "
              "`src/fai/config.py` to match and log the result as the next decision.", ""]
    return "\n".join(lines)


def main() -> None:
    symbol = sys.argv[1] if len(sys.argv) > 1 else "SPY"
    minutes = pd.read_parquet(config.PROCESSED / f"{symbol}_minutes.parquet")
    sessions = pd.read_parquet(config.PROCESSED / "sessions.parquet")
    R, G = to_matrix(minutes, "r"), to_matrix(minutes, "gap")
    winner, table, info = evaluate(R, G, sessions.index[sessions["half_day"]])
    text = report(winner, table, info, symbol)
    config.REPORTS.mkdir(parents=True, exist_ok=True)
    (config.REPORTS / "seasonality_choice.md").write_text(text)
    table.to_csv(config.REPORTS / "seasonality_choice.csv", index=False)
    print(text)


if __name__ == "__main__":
    main()
