"""VR* (D-023): bounce-robust variance ratio, and the D-023 simulation's own pieces."""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

from fai.measures import variance_ratio, variance_ratio_skip

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("d023", ROOT / "scripts" / "sim_h1b_null_d023.py")
d023 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(d023)


def _roll(eff, h, rng):
    q = rng.choice([-1.0, 1.0], size=eff.shape)
    q_open = rng.choice([-1.0, 1.0], size=eff.shape[0])
    return d023.d022.observed_returns(eff, h, q, q_open)


def test_matches_the_formula_on_one_small_day():
    rng = np.random.default_rng(0)
    a = rng.standard_normal((1, 60))                       # two 30-minute blocks
    b = a.reshape(12, 5).sum(axis=1)                       # twelve 5-minute blocks
    L = b.reshape(2, 6).sum(axis=1)
    nb = sum(b[j * 6 + i] * b[j * 6 + i + 1] for j in range(2) for i in range(5))
    expected = (np.sum(L ** 2) - 2 * nb) / np.sum(b ** 2)
    assert np.isclose(variance_ratio_skip(pd.DataFrame(a), 5, 30).iloc[0], expected)


def test_bounce_alone_leaves_vr_skip_at_one():
    """Roll bounce of any size drags VR(30/5) down but leaves VR* at 1 on average."""
    rng = np.random.default_rng(1)
    eff = rng.standard_normal((3000, 390))
    for h, vr_expected_below in ((0.0, 1.01), (0.5, 0.95), (2.0, 0.6)):
        r = pd.DataFrame(_roll(eff, np.full(eff.shape, h), rng))
        assert variance_ratio(r).mean() < vr_expected_below
        assert abs(variance_ratio_skip(r).mean() - 1.0) < 0.01


def test_spreads_that_jump_inside_bursts_do_not_move_vr_skip():
    """The B2 mechanism: wide spreads in one stretch of the day."""
    rng = np.random.default_rng(2)
    eff = rng.standard_normal((3000, 390))
    h = np.full(eff.shape, 0.2)
    h[:, 150:180] = 3.0
    r = pd.DataFrame(_roll(eff, h, rng))
    assert variance_ratio(r).mean() < 0.9
    assert abs(variance_ratio_skip(r).mean() - 1.0) < 0.015


def test_real_reversal_still_lowers_vr_skip():
    """A transient deviation that decays over about 10 minutes is still seen."""
    rng = np.random.default_rng(3)
    n_days, n = 3000, 390
    shock = np.zeros((n_days, n))
    shock[:, 100:130] = 3.0 * rng.standard_normal((n_days, 30))
    phi = 2 ** (-1 / 10)
    tau = np.zeros_like(shock)
    for t in range(n):
        tau[:, t] = (phi * tau[:, t - 1] if t else 0.0) + shock[:, t]
    r = pd.DataFrame(rng.standard_normal((n_days, n)) + np.diff(tau, axis=1, prepend=0.0))
    assert variance_ratio_skip(r).mean() < 0.97


def test_persistent_signs_have_the_stated_autocorrelation():
    rng = np.random.default_rng(4)
    q, q_open = d023.persistent_signs(rng, 2000, 390, p_same=0.9)
    assert set(np.unique(q)) == {-1.0, 1.0}
    assert set(np.unique(q_open)) == {-1.0, 1.0}
    assert np.all(q[:, 0] * q_open != 0)                   # the chain starts at the open
    for k, target in ((1, 0.8), (5, 0.8 ** 5)):
        rho = np.corrcoef(q[:, k:].ravel(), q[:, :-k].ravel())[0, 1]
        assert abs(rho - target) < 0.02


def test_same_samples_as_the_d022_run():
    """Scenario A in the D-023 run is the D-022 sample, so VR(30/5) results coincide."""
    rows22 = d023.d022.one_rep((0, 120))
    rows23 = d023.one_rep((0, 120))
    a22 = {r["measure"]: r["slope"] for r in rows22 if r["scenario"] == "A"}
    a23 = {r["measure"]: r["slope"] for r in rows23 if r["scenario"] == "A" and r["estimator"] == "vr"}
    assert a22.keys() == a23.keys()
    assert all(np.isclose(a22[m], a23[m]) for m in a22)
    assert {r["scenario"] for r in rows23} == set(d023.SCENARIOS)
    assert {r["estimator"] for r in rows23} == set(d023.ESTIMATORS)
