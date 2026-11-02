import numpy as np
import pandas as pd

from fai.inference import fe_slope, nw_lag


def test_registered_lag_rule():
    assert nw_lag(100) == 4
    assert nw_lag(3850) == 9          # the H1b-sized sample in D-022


def _full_dummy_regression(y, x, g, lag):
    """Slope and Newey-West SE from the regression with a dummy for every group."""
    D = pd.get_dummies(pd.Series(g)).to_numpy(float)
    X = np.column_stack([x, D])
    XtX_inv = np.linalg.inv(X.T @ X)
    beta = XtX_inv @ X.T @ y
    e = y - X @ beta
    Z = X * e[:, None]
    S = Z.T @ Z
    for k in range(1, lag + 1):
        G = Z[k:].T @ Z[:-k]
        S += (1 - k / (lag + 1)) * (G + G.T)
    V = XtX_inv @ S @ XtX_inv
    return beta[0], np.sqrt(V[0, 0])


def test_fe_slope_matches_the_dummy_regression():
    rng = np.random.default_rng(3)
    n = 600
    g = rng.integers(0, 10, n)
    x = rng.standard_normal(n) + 0.3 * g
    y = 0.5 * x + 0.2 * g + rng.standard_normal(n) * (1 + 0.5 * np.abs(x))
    for lag in (0, 4, 9):
        res = fe_slope(y, x, g, lag=lag)
        b, se = _full_dummy_regression(y, x, g, lag)
        assert np.isclose(res["slope"], b) and np.isclose(res["se"], se)
    assert fe_slope(y, x, g)["lag"] == nw_lag(n)


def test_fe_slope_drops_missing_rows():
    rng = np.random.default_rng(4)
    x = rng.standard_normal(200)
    y = x + rng.standard_normal(200)
    g = np.repeat(np.arange(10), 20)
    y2 = y.copy()
    y2[5] = np.nan
    res = fe_slope(y2, x, g, lag=2)
    keep = np.arange(200) != 5
    assert res["n"] == 199
    assert np.isclose(res["slope"], fe_slope(y[keep], x[keep], g[keep], lag=2)["slope"])
