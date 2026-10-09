"""Daily measures: RV (benchmark), normalised energy (FAI), Husid timing, VR."""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config
from .husid import husid_times


def signal(Rt: pd.DataFrame, kind: str = "returns") -> pd.DataFrame:
    """a_t: deseasonalised returns (primary) or their first difference (comparison, H3)."""
    if kind == "returns":
        return Rt
    if kind == "diff":
        return Rt - Rt.shift(1, axis=1)
    raise ValueError(kind)


def daily_energy(A: pd.DataFrame) -> pd.Series:
    return (A ** 2).sum(axis=1, min_count=1)


def normalizer(E: pd.Series, window: int = config.RM_WINDOW_DAYS,
               min_days: int = config.RM_MIN_DAYS) -> pd.Series:
    """R_m: mean daily energy over the prior ``window`` days (excludes today)."""
    return E.rolling(window, min_periods=min_days).mean().shift(1)


def damping_factor(zeta) -> np.ndarray:
    """Arias (1970) damping factor f(zeta) = arccos(zeta) / sqrt(1 - zeta^2).

    f(0) = pi/2, f -> 1 as zeta -> 1, so damping has a bounded effect. zeta is
    capped at config.ZETA_CAP.
    """
    z = np.clip(np.asarray(zeta, float), 0.0, config.ZETA_CAP)
    return np.arccos(z) / np.sqrt(1.0 - z ** 2)


def variance_ratio(A: pd.DataFrame, base: int = config.VR_BASE_MIN,
                   long: int = config.VR_LONG_MIN) -> pd.Series:
    """Intraday VR(long/base) = sum of squared long-block sums / sum of squared base-block sums.

    Built from base-minute blocks so 1-minute bid-ask bounce mostly cancels inside a
    block. Under independent increments E[VR] = 1 whatever the timing of volatility,
    so concentration alone does not move it; VR < 1 means intraday reversal.
    """
    x = np.nan_to_num(A.to_numpy(float), nan=0.0)
    n_days, n = x.shape
    nb = n // base
    b = x[:, : nb * base].reshape(n_days, nb, base).sum(axis=2)
    m = long // base
    nl = nb // m
    b = b[:, : nl * m]
    L = b.reshape(n_days, nl, m).sum(axis=2)
    with np.errstate(invalid="ignore", divide="ignore"):
        vr = (L ** 2).sum(axis=1) / (b ** 2).sum(axis=1)
    return pd.Series(vr, index=A.index, name="vr")


def daily_measures(R: pd.DataFrame, Rt: pd.DataFrame) -> pd.DataFrame:
    """All per-day measures from raw (R) and deseasonalised (Rt) minute matrices."""
    out = pd.DataFrame(index=R.index)
    out["rv"] = (R ** 2).sum(axis=1, min_count=1)          # benchmark, raw returns
    out["ret_oc"] = R.sum(axis=1, min_count=1)              # open-to-close log return
    for kind, sfx in [("returns", ""), ("diff", "_diff")]:
        A = signal(Rt, kind)
        E = daily_energy(A)
        out[f"energy{sfx}"] = E
        out[f"fai{sfx}"] = E / normalizer(E)
        out[f"max_share{sfx}"] = (A ** 2).max(axis=1) / E
        out = out.join(husid_times(A).add_suffix(sfx))
    out["vr"] = variance_ratio(Rt)
    out["n_obs"] = Rt.notna().sum(axis=1)
    return out
