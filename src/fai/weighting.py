"""Liquidity weighting of FAI (brief, Section 3): zeta, the Arias damping factor, FAI_w.

In Arias (1970) the intensity of a record is scaled by f(zeta) = arccos(zeta) /
sqrt(1 - zeta^2), where zeta is the structure's damping: f(0) = pi/2 and f -> 1 as
zeta -> 1, so damping changes the intensity by a bounded amount. Here zeta_t is how
liquid minute t is (the liquidity percentile Pi_t of liquidity.py, capped at 0.99), so

    FAI_w = sum_t f(zeta_t) a_t^2 / R_m

counts energy that arrives in an unusually illiquid minute up to pi/2 (about 1.57)
times as much as the same energy in an unusually liquid one. R_m is the same trailing
normalizer as unweighted FAI, so ln FAI_w - ln FAI = ln f_bar, the energy-weighted
average damping factor of the day: how much of the day's energy arrived in thin markets.

Comparison (brief): the floored inverse, sum_t a_t^2 / (R_m max(C_t, c_min)), with C_t
the same percentile and c_min = 0.05 (about its 5th percentile, since Pi_t is close to
uniform by construction). Its weights run from 1 to 20, so it shows what an unbounded
weighting does next to the bounded one.

Minutes with no percentile (the first minutes of each day, before the trailing window
has 5 valid minutes; zero-volume minutes; the first 40 sessions) get Pi = 0.5, typical
liquidity: no information about liquidity should neither raise nor lower their weight.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config
from .measures import damping_factor

PI_MISSING = 0.5
C_MIN = config.CMIN_PERCENTILE / 100.0


def zeta(Pi: pd.DataFrame, cap: float = config.ZETA_CAP,
         missing: float = PI_MISSING) -> pd.DataFrame:
    """zeta_t = min(Pi_t, cap); missing percentiles count as typical liquidity."""
    return Pi.fillna(missing).clip(lower=0.0, upper=cap)


def damping_weights(Pi: pd.DataFrame, missing: float = PI_MISSING) -> pd.DataFrame:
    """f(zeta_t) per minute, between 1 (very liquid) and pi/2 (very illiquid)."""
    z = zeta(Pi, missing=missing)
    return pd.DataFrame(damping_factor(z.to_numpy(float)), index=Pi.index, columns=Pi.columns)


def floored_inverse_weights(Pi: pd.DataFrame, c_min: float = C_MIN,
                            missing: float = PI_MISSING) -> pd.DataFrame:
    """1 / max(C_t, c_min) with C_t = Pi_t: the brief's comparison weighting."""
    return 1.0 / Pi.fillna(missing).clip(lower=c_min)


def weighted_energy(A: pd.DataFrame, W: pd.DataFrame) -> pd.Series:
    """sum_t w_t a_t^2 per day (NaN minutes skipped, as in measures.daily_energy)."""
    return (W.reindex_like(A) * A ** 2).sum(axis=1, min_count=1)


def weighting_measures(Rt: pd.DataFrame, R_m: pd.Series, Pi: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Daily weighted measures from deseasonalized returns, the FAI normalizer and the
    liquidity percentiles of each proxy (``{"amihud": Pi_a, "cs": Pi_cs}``).

    Columns: fai_w (Amihud, primary), fai_w_cs (Corwin-Schultz, robustness), fai_c
    (floored inverse, Amihud, comparison), f_bar (energy-weighted mean f, Amihud) and
    pi_missing (share of the day's minutes with no Amihud percentile).
    """
    E = (Rt ** 2).sum(axis=1, min_count=1)
    out = pd.DataFrame(index=Rt.index)
    Wa = damping_weights(Pi["amihud"])
    Ew = weighted_energy(Rt, Wa)
    out["fai_w"] = Ew / R_m
    out["f_bar"] = Ew / E
    if "cs" in Pi:
        out["fai_w_cs"] = weighted_energy(Rt, damping_weights(Pi["cs"])) / R_m
    out["fai_c"] = weighted_energy(Rt, floored_inverse_weights(Pi["amihud"])) / R_m
    have = Rt.notna()
    out["pi_missing"] = (Pi["amihud"].reindex_like(Rt).isna() & have).sum(axis=1) / have.sum(axis=1)
    return out
