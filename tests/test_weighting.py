"""Liquidity weighting (fai.weighting): bounds, by-hand cases, and a simulated drop."""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

from fai.clean import clean
from fai.measures import damping_factor
from fai.seasonality import deseasonalize, seasonal_variance, to_matrix
from fai.sim import LiquidityDrop, simulate_panel
from fai.weighting import (damping_weights, floored_inverse_weights, weighted_energy,
                           weighting_measures, zeta)

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("run_all", ROOT / "scripts" / "run_all.py")
run_all = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(run_all)


def test_weights_are_bounded_like_arias_damping():
    Pi = pd.DataFrame([[0.0, 0.5, 1.0, np.nan]])
    w = damping_weights(Pi).iloc[0]
    assert np.isclose(w[0], np.pi / 2)                       # very illiquid: the most weight
    assert np.isclose(w[2], damping_factor(0.99)) and w[2] < 1.01   # capped at 0.99, near 1
    assert np.isclose(w[3], w[1])                            # missing counts as typical
    assert np.isclose(w[1], np.arccos(0.5) / np.sqrt(0.75))
    assert zeta(Pi).iloc[0, 2] == 0.99


def test_constant_liquidity_scales_fai_by_one_factor():
    rng = np.random.default_rng(0)
    Rt = pd.DataFrame(rng.standard_normal((5, 390)))
    R_m = pd.Series(390.0, index=Rt.index)
    Pi = pd.DataFrame(0.2, index=Rt.index, columns=Rt.columns)
    out = weighting_measures(Rt, R_m, {"amihud": Pi})
    f = damping_factor(0.2)
    fai = (Rt ** 2).sum(axis=1) / R_m
    assert np.allclose(out["fai_w"], f * fai)
    assert np.allclose(out["f_bar"], f)
    assert np.allclose(out["fai_c"], fai / 0.2)
    assert (out["pi_missing"] == 0).all()


def test_same_energy_counts_more_when_it_arrives_in_thin_markets():
    Rt = pd.DataFrame(np.ones((2, 390)))
    Rt.iloc[:, 100:110] = 5.0                                # the same burst on both days
    Pi = pd.DataFrame(0.5, index=Rt.index, columns=Rt.columns)
    Pi.iloc[0, 100:110] = 0.02                               # day 0: the burst is illiquid
    Pi.iloc[1, 100:110] = 0.98                               # day 1: the burst is liquid
    out = weighting_measures(Rt, pd.Series(1.0, index=Rt.index), {"amihud": Pi})
    assert out["fai_w"].iloc[0] > out["fai_w"].iloc[1]
    assert 1.0 <= out["f_bar"].min() and out["f_bar"].max() <= np.pi / 2


def test_floored_inverse_runs_from_1_to_20():
    w = floored_inverse_weights(pd.DataFrame([[0.0, 0.01, 0.5, 1.0]])).iloc[0]
    assert np.allclose(w, [20.0, 20.0, 2.0, 1.0])


def test_missing_minutes_are_counted_and_nan_returns_skipped():
    Rt = pd.DataFrame([[1.0, np.nan, 1.0, 1.0]])
    Pi = pd.DataFrame([[np.nan, 0.3, 0.3, 0.3]])
    out = weighting_measures(Rt, pd.Series([1.0]), {"amihud": Pi})
    assert np.isclose(out["pi_missing"].iloc[0], 1 / 3)
    W = damping_weights(Pi)
    assert np.isclose(weighted_energy(Rt, W).iloc[0], W.iloc[0, 0] + W.iloc[0, 2] + W.iloc[0, 3])


def _sim_weighting(specs):
    bars, sessions, _ = simulate_panel(np.random.default_rng(3), 70, specs=specs)
    minutes, _, _ = clean(bars, sessions)
    R, G = to_matrix(minutes, "r"), to_matrix(minutes, "gap")
    Rt = deseasonalize(R, G, seasonal_variance(R, G))
    out = run_all.liquidity_weighting(minutes, R, Rt, G, exclude=pd.DatetimeIndex([]))
    return out, Rt


def test_pipeline_weighting_raises_fai_w_on_a_simulated_liquidity_drop():
    """End to end, same simulated prices with and without a 30-minute drop (spread x20,
    volume x0.2) on day 65: f_bar rises that day and nowhere before it.

    Only by about 0.08: the drop holds about 30% of that day's energy and its weight is at
    most pi/2. That is about 1.5 times f_bar's day-to-day noise (sd about 0.05), so the
    bound that keeps the weighting sane also keeps it small."""
    drop = {65: {"liquidity_drops": [LiquidityDrop(200, 30, volume_mult=0.2, spread_mult=20.0)]}}
    with_drop, _ = _sim_weighting(drop)
    without, _ = _sim_weighting(None)
    assert with_drop["f_bar"].iloc[65] - without["f_bar"].iloc[65] > 0.05
    assert np.allclose(with_drop["f_bar"].iloc[:65], without["f_bar"].iloc[:65], equal_nan=True)
    assert {"fai_w", "fai_w_cs", "fai_c", "f_bar", "pi_missing"} <= set(with_drop.columns)
    # R_m needs 60 prior days of energy, more than this 70-day panel has after warm-up,
    # so fai_w is NaN here; the identity fai_w = f_bar * FAI is checked by hand above.
    assert with_drop["f_bar"].iloc[45:].notna().all()
