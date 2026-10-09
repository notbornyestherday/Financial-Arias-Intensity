"""Intraday seasonality s(tau) and deseasonalised returns.

Work in day x minute matrices (rows = session dates, columns = tau 0..389).
s^2(tau) on day d uses only days strictly before d (no look-ahead).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config

CHI2_1_MEDIAN = 0.454936423119572  # median of chi-square(1), rescales median(r^2)


def to_matrix(minutes: pd.DataFrame, col: str,
              n_minutes: int = config.FULL_DAY_MINUTES) -> pd.DataFrame:
    m = minutes.pivot(index="date", columns="tau", values=col)
    return m.reindex(columns=range(n_minutes)).sort_index()


def seasonal_variance(R: pd.DataFrame, G: pd.DataFrame, exclude=None,
                      window: int = config.SEAS_WINDOW_DAYS,
                      min_days: int = config.SEAS_MIN_DAYS,
                      method: str = config.SEAS_METHOD) -> pd.DataFrame:
    """Trailing per-minute variance s^2(tau) from prior days only.

    Only single-minute returns (gap == 1) enter the estimate. Rows whose index is
    in ``exclude`` (e.g. half-days) are skipped. ``method="median"`` is a robust
    alternative: one crash day otherwise inflates s(tau) at that minute for 60 days.
    Open question (DECISIONS.md): smoothing across neighbouring minutes, since each
    estimate rests on ~60 observations.
    """
    X = R.where(G == 1) ** 2
    if exclude is not None:
        X.loc[X.index.isin(pd.DatetimeIndex(exclude))] = np.nan
    roll = X.rolling(window, min_periods=min_days)
    if method == "rms":
        S2 = roll.mean()
    elif method == "median":
        S2 = roll.median() / CHI2_1_MEDIAN
    else:
        raise ValueError(f"unknown method {method!r}")
    return S2.shift(1)


def deseasonalize(R: pd.DataFrame, G: pd.DataFrame, S2: pd.DataFrame) -> pd.DataFrame:
    """r_tilde = r / s(tau); a return spanning k minutes uses sqrt(sum of s^2 over them).

    The multi-minute rule keeps energy conserved across halts and missing bars:
    a 15-minute return is compared with 15 minutes' worth of typical variance.
    """
    r = R.to_numpy(float)
    g = G.to_numpy(float)
    s2 = S2.reindex(index=R.index, columns=R.columns).to_numpy(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        out = r / np.sqrt(s2)
    rows, cols = np.nonzero(np.nan_to_num(g, nan=0) > 1)
    for i, j in zip(rows, cols):
        k = int(g[i, j])
        seg = s2[i, j - k + 1: j + 1]
        ok = seg.size == k and np.isfinite(seg).all() and seg.sum() > 0
        out[i, j] = r[i, j] / np.sqrt(seg.sum()) if ok else np.nan
    return pd.DataFrame(out, index=R.index, columns=R.columns)
