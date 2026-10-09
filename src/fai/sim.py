"""Synthetic minute bars with known ground truth.

The point is to check that the pipeline recovers what was injected before it is
trusted on real data: a burst with known timing (so D5-95 is known), a slow grind
with the same total energy, liquidity drops (wider spread, lower volume; used from
Week 3), Roll-style bid-ask bounce (so the differenced signal in H3 has something
to amplify), a U-shaped intraday profile, and overnight gaps that must not leak in.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import config
from .husid import significant_times
from .ingest import CANON
from .sessions import synthetic_sessions

MINUTE = pd.Timedelta(minutes=1)


@dataclass(frozen=True)
class Burst:
    start: int        # first minute (tau) of the burst
    length: int       # minutes
    mult: float       # volatility multiplier inside the window


@dataclass(frozen=True)
class LiquidityDrop:
    start: int
    length: int
    volume_mult: float = 0.2
    spread_mult: float = 5.0


@dataclass
class DayTruth:
    """Two kinds of truth.

    expected_*: Husid times of the injected variance profile (what the day looks like
        on average over realisations).
    oracle_*: Husid times of this realisation's efficient returns divided by the true
        sigma * season, i.e. what a perfect deseasonaliser with no bid-ask bounce would
        measure. The pipeline should match the oracle closely; the gap between oracle
        and expected is sampling noise in D5-95 itself, which is worth knowing.
    """
    vol: np.ndarray                # true per-minute SD of efficient log returns
    profile: np.ndarray            # expected deseasonalised energy per minute
    expected_t5: float
    expected_t95: float
    expected_d5_95: float
    oracle_z: np.ndarray           # deseasonalised efficient returns
    oracle_t5: float
    oracle_t95: float
    oracle_d5_95: float
    liquidity_drops: tuple = field(default_factory=tuple)


def u_shape(n: int = config.FULL_DAY_MINUTES, open_amp: float = 2.0, open_decay: float = 20.0,
            close_amp: float = 0.7, close_decay: float = 15.0) -> np.ndarray:
    """Multiplicative intraday volatility profile: high at the open, smaller rise at the close."""
    tau = np.arange(n)
    return 1 + open_amp * np.exp(-tau / open_decay) + close_amp * np.exp(-(n - 1 - tau) / close_decay)


def simulate_day(rng: np.random.Generator, n: int = config.FULL_DAY_MINUTES,
                 sigma: float = 4e-4, p0: float = 300.0, season: np.ndarray | None = None,
                 grind: float = 1.0, bursts=(), liquidity_drops=(),
                 half_spread: float = 1.5e-5, substeps: int = 10,
                 base_volume: float = 2e5) -> tuple[pd.DataFrame, DayTruth]:
    season = u_shape(n) if season is None else np.asarray(season, float)
    mult = np.full(n, float(grind))
    for b in bursts:
        mult[b.start: b.start + b.length] *= b.mult
    vol = sigma * season * mult

    spread = np.full(n, half_spread)
    volf = np.ones(n)
    for d in liquidity_drops:
        spread[d.start: d.start + d.length] *= d.spread_mult
        volf[d.start: d.start + d.length] *= d.volume_mult

    inc = rng.standard_normal((n, substeps)) * (vol / np.sqrt(substeps))[:, None]
    logp = np.log(p0) + np.cumsum(inc.ravel()).reshape(n, substeps)
    bounce = rng.choice([-1.0, 1.0], size=(n, substeps))
    obs = np.exp(logp) * (1.0 + spread[:, None] * bounce)

    bars = pd.DataFrame({
        "tau": np.arange(n),
        "open": obs[:, 0],
        "high": obs.max(axis=1),
        "low": obs.min(axis=1),
        "close": obs[:, -1],
        "volume": np.round(base_volume * season * volf * rng.lognormal(0.0, 0.3, n)),
    })
    profile = mult ** 2
    e_t5, e_t95, e_d = significant_times(profile)
    # Efficient returns on the same definitions as clean.py (first bar: open -> close)
    eff = np.diff(logp[:, -1], prepend=logp[0, 0])
    first_scale = np.sqrt((substeps - 1) / substeps)
    z = eff / (sigma * season)
    z[0] /= first_scale
    o_t5, o_t95, o_d = significant_times(z ** 2)
    truth = DayTruth(vol, profile, e_t5, e_t95, e_d, z, o_t5, o_t95, o_d,
                     tuple(liquidity_drops))
    return bars, truth


def simulate_panel(rng: np.random.Generator, n_days: int, start: str = "2015-01-05",
                   specs: dict | None = None, overnight_sd: float = 0.008,
                   p0: float = 200.0, **day_kwargs):
    """Many days of bars. ``specs`` maps a day index (int) to simulate_day overrides.

    Returns (bars in canonical schema, sessions, {date: DayTruth}).
    """
    specs = specs or {}
    dates = pd.bdate_range(start, periods=n_days)
    sessions = synthetic_sessions(dates)
    frames, truths, p = [], {}, p0
    for i, d in enumerate(dates):
        kw = {**day_kwargs, **specs.get(i, {})}
        p_open = p * np.exp(overnight_sd * rng.standard_normal())
        bars, truth = simulate_day(rng, p0=p_open, **kw)
        bars["ts"] = sessions.at[d, "open"] + bars["tau"] * MINUTE
        frames.append(bars[CANON])
        truths[d] = truth
        p = float(bars["close"].iloc[-1])
    return pd.concat(frames, ignore_index=True), sessions, truths


def matched_energy_pair(rng: np.random.Generator, n: int = config.FULL_DAY_MINUTES,
                        burst: Burst = Burst(200, 15, 15.0)) -> tuple[np.ndarray, np.ndarray]:
    """Two deseasonalised-return days with identical total energy (identical RV):
    one with a burst, one a uniform grind. The core of H1 as a unit test."""
    z_burst = rng.standard_normal(n)
    z_burst[burst.start: burst.start + burst.length] *= burst.mult
    z_grind = rng.standard_normal(n)
    z_grind *= np.sqrt((z_burst ** 2).sum() / (z_grind ** 2).sum())
    return z_burst, z_grind
