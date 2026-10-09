"""Benchmark concentration measures (D-018)."""

import numpy as np
import pandas as pd

from fai.husid import husid_times
from fai.measures import benchmark_measures


def _frame(*rows):
    return pd.DataFrame(np.vstack(rows))


def test_single_spike_is_all_jump_and_one_effective_minute():
    a = np.zeros(390)
    a[200] = 1.0
    b = benchmark_measures(_frame(a)).iloc[0]
    assert np.isclose(b["jump_share"], 1.0) and np.isclose(b["n_eff"], 1.0)


def test_constant_volatility_is_baseline():
    rng = np.random.default_rng(0)
    z = rng.standard_normal((400, 390))
    b = benchmark_measures(pd.DataFrame(z))
    assert 0.9 < b["rq_ratio"].mean() < 1.1                 # about 1 by construction
    assert b["jump_share"].mean() < 0.1
    assert 0.45 < b["down_share"].mean() < 0.55


def test_herfindahl_identity():
    rng = np.random.default_rng(1)
    z = rng.standard_t(4, (5, 390))
    b = benchmark_measures(pd.DataFrame(z))
    shares = z ** 2 / (z ** 2).sum(axis=1, keepdims=True)
    hhi = (shares ** 2).sum(axis=1)
    assert np.allclose(b["n_eff"], 1 / hhi)


def test_order_matters_for_w50_but_not_for_rq():
    """Same minutes, different order: one 15-minute cluster vs the same values scattered.

    rq_ratio cannot tell them apart; W50 can. This is the distinction D-018 tests."""
    rng = np.random.default_rng(2)
    a = rng.standard_normal(390)
    a[200:215] *= 10.0
    scattered = a.copy()
    idx = np.r_[200:215]
    spread = np.linspace(5, 385, 15).astype(int)
    scattered[idx], scattered[spread] = a[spread], a[idx]
    b = benchmark_measures(_frame(a, scattered))
    assert np.isclose(b["rq_ratio"].iloc[0], b["rq_ratio"].iloc[1])
    w = husid_times(_frame(a, scattered))["w50"]
    assert w.iloc[0] < 20 < w.iloc[1]


def test_empty_day_is_nan():
    b = benchmark_measures(_frame(np.full(390, np.nan)))
    assert b.isna().all(axis=None)
