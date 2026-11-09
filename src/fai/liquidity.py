"""Liquidity proxies (Section 3 of the brief) and their trailing percentiles.

Everything works on day x minute matrices (rows = session dates, columns = tau), as in
seasonality.py. Two proxies, both measures of *illiquidity* (higher = less liquid):

* Amihud (2002), per minute: |r_t| / (P_t * V_t), the price move per dollar traded.
* Corwin and Schultz (2012), per pair of consecutive minutes: a bid-ask spread estimate
  from high-low ranges. A one-minute range reflects volatility plus the spread; a
  two-minute range has twice the volatility but the same spread, so comparing the two
  separates them. Negative estimates are set to zero (as the brief specifies).
  Limitation at 1-minute SPY resolution: the spread (a fraction of a basis point) is
  small next to one minute's volatility (several basis points), so most pair estimates
  are noise, about half are floored at zero, and the average is biased upward. CS sees
  large spread blow-outs (x20 and more in simulation) but not routine variation, which
  is why Amihud is the proposed primary proxy for the weighting.

Both are averaged over a trailing 30-minute window that ends the minute *before* t, so
the proxy used at minute t never contains minute t's own return (the brief's lag rule).
The window stays inside the day: nothing carries over from the previous close.

liquidity_percentile turns either proxy into Pi_t in [0, 1], high when the market is
*more* liquid than usual, judged against the same minute of the day over the prior 60
sessions. Comparing like with like matters: volume and spreads follow their own
intraday pattern, and pooling all minutes would make Pi_t track the time of day rather
than unusual liquidity. Pi_t feeds the damping weight zeta_t (the next step, Week 3/4).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config

_K = 3.0 - 2.0 * np.sqrt(2.0)             # Corwin-Schultz constant, 3 - 2*sqrt(2)


def trailing_within_day(X: pd.DataFrame, window: int = config.AMIHUD_WINDOW_MIN,
                        lag: int = 1, min_periods: int = config.LIQ_MIN_MINUTES) -> pd.DataFrame:
    """Mean of X over minutes [t - lag - window + 1, t - lag] of the same day.

    Rolls along each row (one day), so the open never reaches back into yesterday.
    NaNs are skipped; fewer than ``min_periods`` valid minutes gives NaN.
    """
    out = X.T.rolling(window, min_periods=min_periods).mean().shift(lag).T
    return out.reindex(index=X.index, columns=X.columns)


def amihud_minute(R: pd.DataFrame, C: pd.DataFrame, V: pd.DataFrame,
                  G: pd.DataFrame | None = None) -> pd.DataFrame:
    """|r_t| / (close_t * volume_t), in units of return per million dollars traded.

    Minutes with no volume, and returns spanning more than one minute (``G`` > 1: halts,
    missing bars), are NaN: a 15-minute move set against one bar's volume is not an
    Amihud ratio.
    """
    dollar_vol = (C * V).where(V > 0)
    out = R.abs() / dollar_vol * 1e6
    if G is not None:
        out = out.where(G == 1)
    return out


def corwin_schultz_pair(H: pd.DataFrame, L: pd.DataFrame, C: pd.DataFrame,
                        G: pd.DataFrame | None = None) -> pd.DataFrame:
    """Corwin-Schultz spread from bars t-1 and t, assigned to t (fraction of price).

    Before the ranges are combined, bar t is shifted to remove any jump from close t-1
    to bar t (the paper's overnight adjustment, applied minute to minute): if bar t
    trades entirely above close t-1 its range is moved down by low_t - close_{t-1}, and
    likewise below. Pairs that are not consecutive minutes are NaN.
    """
    h, l = H.to_numpy(float), L.to_numpy(float)
    c_prev = np.full_like(h, np.nan)
    c_prev[:, 1:] = C.to_numpy(float)[:, :-1]
    up = np.where(l > c_prev, l - c_prev, 0.0)
    down = np.where(h < c_prev, c_prev - h, 0.0)
    h_adj, l_adj = h - up + down, l - up + down
    h_prev = np.full_like(h, np.nan)
    l_prev = np.full_like(h, np.nan)
    h_prev[:, 1:], l_prev[:, 1:] = h[:, :-1], l[:, :-1]
    with np.errstate(invalid="ignore", divide="ignore"):
        beta = np.log(h_adj / l_adj) ** 2 + np.log(h_prev / l_prev) ** 2
        gamma = np.log(np.fmax(h_adj, h_prev) / np.fmin(l_adj, l_prev)) ** 2
        alpha = (np.sqrt(2 * beta) - np.sqrt(beta)) / _K - np.sqrt(gamma / _K)
        s = 2 * (np.exp(alpha) - 1) / (1 + np.exp(alpha))
    s = np.where(np.isfinite(s), np.maximum(s, 0.0), np.nan)
    out = pd.DataFrame(s, index=H.index, columns=H.columns)
    if G is not None:
        out = out.where(G == 1)
    return out


def amihud(R, C, V, G=None, window: int = config.AMIHUD_WINDOW_MIN) -> pd.DataFrame:
    """Trailing 30-minute Amihud illiquidity, lagged one minute."""
    return trailing_within_day(amihud_minute(R, C, V, G), window)


def corwin_schultz(H, L, C, G=None, window: int = config.AMIHUD_WINDOW_MIN) -> pd.DataFrame:
    """Trailing 30-minute Corwin-Schultz spread, lagged one minute."""
    return trailing_within_day(corwin_schultz_pair(H, L, C, G), window)


def liquidity_percentile(X: pd.DataFrame, window_days: int = config.LIQ_PCT_WINDOW_DAYS,
                         min_days: int = config.LIQ_PCT_MIN_DAYS, exclude=None) -> pd.DataFrame:
    """Pi_t: how liquid minute t is against the same minute of the prior sessions.

    X is an illiquidity proxy (higher = less liquid). Pi_t is the share of the prior
    ``window_days`` sessions whose value at that minute was *higher* than today's (ties
    count half), so Pi_t near 1 means unusually liquid and near 0 unusually illiquid.
    Only prior days enter; days in ``exclude`` (half-days) are left out of the reference.
    Fewer than ``min_days`` valid prior values gives NaN.
    """
    x = X.to_numpy(float)
    ref = x.copy()
    if exclude is not None:
        ref[X.index.isin(pd.Index(exclude))] = np.nan
    n_days, n = x.shape
    out = np.full_like(x, np.nan)
    for d in range(1, n_days):
        past = ref[max(0, d - window_days): d]                 # prior sessions only
        valid = np.isfinite(past)
        cnt = valid.sum(axis=0)
        cur = x[d]
        with np.errstate(invalid="ignore"):
            above = np.where(valid, past > cur, False).sum(axis=0)
            tie = np.where(valid, past == cur, False).sum(axis=0)
            pi = (above + 0.5 * tie) / cnt
        out[d] = np.where((cnt >= min_days) & np.isfinite(cur), pi, np.nan)
    return pd.DataFrame(out, index=X.index, columns=X.columns)
