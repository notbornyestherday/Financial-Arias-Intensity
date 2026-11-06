"""Regression inference shared by the H1/H2 tests and their simulation checks.

Standard errors are Newey-West with the lag rule registered in HYPOTHESES.md. Keeping
this in one place means the D-022 null check exercises exactly the inference the real
H1b regression will use.
"""

from __future__ import annotations

import math

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


def fe_ols(y, X: dict, groups, lag: int | None = None) -> pd.DataFrame:
    """Several regressors with group fixed effects and Newey-West standard errors.

    ``X`` maps a name to a column. Same conventions as ``fe_slope`` (within-group
    demeaning, rows in time order, incomplete rows dropped, registered lag by default);
    with one regressor the two give the same slope and standard error. Returns one row
    per regressor: coef, se, t, p (two-sided, normal), n, lag.
    """
    names = list(X)
    y = np.asarray(y, float)
    Z = np.column_stack([np.asarray(X[k], float) for k in names])
    g = pd.Series(groups).to_numpy()
    ok = np.isfinite(y) & np.isfinite(Z).all(axis=1) & pd.notna(g)
    y, Z, g = y[ok], Z[ok], g[ok]
    yt = _demean_within(y, g)
    Zt = np.column_stack([_demean_within(Z[:, j], g) for j in range(Z.shape[1])])
    A = Zt.T @ Zt
    beta = np.linalg.solve(A, Zt.T @ yt)
    U = Zt * (yt - Zt @ beta)[:, None]      # scores, one column per regressor
    n = U.shape[0]
    L = nw_lag(n) if lag is None else int(lag)
    S = U.T @ U
    for k in range(1, L + 1):
        G = U[k:].T @ U[:-k]
        S += (1 - k / (L + 1)) * (G + G.T)
    Ainv = np.linalg.inv(A)
    se = np.sqrt(np.diag(Ainv @ S @ Ainv))
    t = beta / se
    return pd.DataFrame({"coef": beta, "se": se, "t": t, "p": [p_two_sided(v) for v in t],
                         "n": n, "lag": L}, index=names)


def p_two_sided(t: float) -> float:
    """Two-sided p-value of a t statistic under the normal approximation."""
    return math.erfc(abs(float(t)) / math.sqrt(2.0))


def holm(p) -> np.ndarray:
    """Holm-adjusted p-values (HYPOTHESES.md reports them alongside raw ones), same order."""
    p = np.asarray(p, float)
    order = np.argsort(p)
    m = p.size
    adj = np.empty(m)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * p[i]))
        adj[i] = running
    return adj
