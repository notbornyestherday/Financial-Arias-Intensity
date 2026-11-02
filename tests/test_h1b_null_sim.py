"""Checks on the D-022 simulation itself: bounce mechanics and scenario spreads."""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

from fai.measures import variance_ratio

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("sim_null", ROOT / "scripts" / "sim_h1b_null_pipeline.py")
sim = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sim)


def _panel(n_days=200, seed=0):
    rng = np.random.default_rng(seed)
    eff, vol, burst = sim.efficient_panel(rng, n_days)
    q = rng.choice([-1.0, 1.0], size=eff.shape)
    q_open = rng.choice([-1.0, 1.0], size=n_days)
    return eff, vol, burst, q, q_open


def test_bounce_telescopes_within_the_day():
    """Summed over a day, only the opening and closing prints' bounce is left."""
    eff, vol, burst, q, q_open = _panel()
    h = sim.half_spread("A", vol, burst)
    r = sim.observed_returns(eff, h, q, q_open)
    left = r.sum(axis=1) - eff.sum(axis=1)
    assert np.allclose(left, sim.HALF_SPREAD * (q[:, -1] - q_open))


def test_bounce_creates_negative_autocorrelation():
    """Roll (1984): with no true reversal, the bounce alone makes successive returns
    negatively correlated, by -h^2 over the return variance."""
    rng = np.random.default_rng(1)
    eff = np.zeros((50, 390))                         # no efficient moves at all
    h = np.full(eff.shape, 1e-4)
    q = rng.choice([-1.0, 1.0], size=eff.shape)
    r = sim.observed_returns(eff, h, q, rng.choice([-1.0, 1.0], size=50))
    rho = np.corrcoef(r[:, 1:].ravel(), r[:, :-1].ravel())[0, 1]
    assert abs(rho - (-0.5)) < 0.02                   # pure bounce: exactly -1/2


def test_scenario_spreads():
    eff, vol, burst, q, q_open = _panel()
    assert np.all(sim.half_spread("A", vol, burst) == sim.HALF_SPREAD)
    b1 = sim.half_spread("B1", vol, burst)
    assert np.allclose(b1 / vol, b1.flat[0] / vol.flat[0])          # proportional
    b2 = sim.half_spread("B2", vol, burst)
    assert np.all(b2[burst] == sim.HALF_SPREAD * sim.B2_MULT)
    assert np.all(b2[~burst] == sim.HALF_SPREAD)
    assert burst.any(axis=1).mean() > 0.5                            # most days have a burst


def test_wide_spreads_in_bursts_lower_vr_on_burst_days_only():
    """The mechanism B2 tests: extra bounce inside bursts pulls VR down on burst days."""
    eff, vol, burst, q, q_open = _panel(n_days=400, seed=2)
    true_s = sim.SIGMA * sim.u_shape(390)
    vr = {}
    for sc in ("A", "B2"):
        r = sim.observed_returns(eff, sim.half_spread(sc, vol, burst), q, q_open)
        vr[sc] = variance_ratio(pd.DataFrame(r / true_s)).to_numpy()
    has_burst = burst.any(axis=1)
    drop = vr["A"] - vr["B2"]
    assert np.allclose(drop[~has_burst], 0.0)
    assert drop[has_burst].mean() > 0.0


def test_one_rep_runs_every_scenario():
    rows = sim.one_rep((0, 120))
    assert {r["scenario"] for r in rows} == set(sim.SCENARIOS)
    assert {r["measure"] for r in rows} == set(sim.MEASURES)
    assert all(np.isfinite(r["slope"]) and np.isfinite(r["se"]) for r in rows)
