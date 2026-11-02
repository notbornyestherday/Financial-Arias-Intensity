"""Regression inference shared by the H1/H2 tests and their simulation checks.

Standard errors are Newey-West with the lag rule registered in HYPOTHESES.md. Keeping
this in one place means the D-022 null check exercises exactly the inference the real
H1b regression will use.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def nw_lag(t: int) -> int:
    """Newey-West lag floor(4 (T/100)^(2/9)), the rule registered in HYPOTHESES.md."""
    return int(np.floor(4 * (t / 100) ** (2 / 9)))


def _demean_within(v: np.ndarray, groups: np.ndarray) -> np.ndarray:
    return v - pd.Series(v).groupby(groups).transform("mean").to_numpy()


def fe_slope(y, x, groups, lag: int | None = None) -> dict:
    """Slope of y on x with group fixed effects, and its Newey-West standard error.

    The fixed effects are removed by demeaning y and x within each group
    (Frisch-Waugh-Lovell): the slope, the residuals and the HAC standard error of the
    slope are the same as in the regression with a dummy for every group. Rows must be
    in time order, because the Newey-West weights use it. Rows with a missing y, x or
    group are dropped. ``lag`` defaults to the registered rule for the rows used.
    """
    y = np.asarray(y, float)
    x = np.asarray(x, float)
    g = pd.Series(groups).to_numpy()
    ok = np.isfinite(y) & np.isfinite(x) & pd.notna(g)
    y, x, g = y[ok], x[ok], g[ok]
    yt, xt = _demean_within(y, g), _demean_within(x, g)
    sxx = xt @ xt
    b = (xt @ yt) / sxx
    u = xt * (yt - b * xt)                  # score of the slope
    n = u.size
    L = nw_lag(n) if lag is None else int(lag)
    s = u @ u
    for k in range(1, L + 1):
        s += 2 * (1 - k / (L + 1)) * (u[k:] @ u[:-k])
    se = np.sqrt(s) / sxx
    return {"slope": b, "se": se, "t": b / se, "n": n, "lag": L}
