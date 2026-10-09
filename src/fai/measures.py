"""Daily measures: RV (benchmark), normalised energy (FAI), Husid timing, VR,
and the D-018 benchmark concentration measures."""

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


def benchmark_measures(A: pd.DataFrame) -> pd.DataFrame:
    """Existing high-frequency measures of uneven variation, for comparison with W50 (D-018).

    Computed on the same deseasonalised returns as W50 so that only the functional differs.

    * jump_share = max(RV - BV, 0) / RV, with bipower variation
      BV = (pi/2) * sum |a_t| |a_{t-1}| (Barndorff-Nielsen and Shephard 2004). Near 1 when
      one isolated minute dominates; near 0 when large moves come in runs or not at all.
    * rq_ratio = n * sum a^4 / (3 * (sum a^2)^2): realized quarticity scaled so that it is
      about 1 under constant volatility (Bollerslev, Patton and Quaedvlieg 2016). It is the
      Herfindahl index of the minutes' energy shares times n/3, so n_eff = n / (3 * rq_ratio)
      reads as the effective number of active minutes.
    * down_share = sum a^2 [a < 0] / sum a^2: downside semivariance share (Patton and
      Sheppard 2015).

    rq_ratio and jump_share do not depend on the order of the minutes (jump_share only
    through adjacent pairs); W50 does. "W50 beyond rq_ratio" is therefore the test of
    whether timing matters beyond unevenness.
    """
    x = A.to_numpy(float)
    n = np.isfinite(x).sum(axis=1)
    z = np.nan_to_num(x, nan=0.0)
    rv = (z ** 2).sum(axis=1)
    bv = (np.pi / 2) * (np.abs(z[:, 1:]) * np.abs(z[:, :-1])).sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        jump = np.clip(rv - bv, 0.0, None) / rv
        rq = n * (z ** 4).sum(axis=1) / (3.0 * rv ** 2)
        down = (np.where(z < 0, z, 0.0) ** 2).sum(axis=1) / rv
    out = pd.DataFrame({"bv": bv, "jump_share": jump, "rq_ratio": rq, "down_share": down},
                       index=A.index)
    out["n_eff"] = n / (3.0 * out["rq_ratio"])
    out.loc[~(rv > 0)] = np.nan                     # no energy: nothing to measure
    return out


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
    out = out.join(benchmark_measures(Rt))
    out["n_obs"] = Rt.notna().sum(axis=1)
    return out
