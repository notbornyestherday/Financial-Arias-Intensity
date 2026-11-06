"""VR** (D-024): products of blocks one and two apart removed; the D-024 simulation."""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

from fai.measures import variance_ratio_skip

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("d024", ROOT / "scripts" / "sim_h1b_null_d024.py")
d024 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(d024)


def test_skip2_matches_the_formula_on_one_small_day():
    rng = np.random.default_rng(0)
    a = rng.standard_normal((1, 60))
    b = a.reshape(12, 5).sum(axis=1)
    L = b.reshape(2, 6).sum(axis=1)
    near = sum(b[j * 6 + i] * b[j * 6 + i + k]
               for j in range(2) for k in (1, 2) for i in range(6 - k))
    expected = (np.sum(L ** 2) - 2 * near) / np.sum(b ** 2)
    assert np.isclose(variance_ratio_skip(pd.DataFrame(a), 5, 30, skip=2).iloc[0], expected)
    assert np.isclose(variance_ratio_skip(pd.DataFrame(a), skip=1).iloc[0],
                      variance_ratio_skip(pd.DataFrame(a)).iloc[0])


def test_skip2_removes_the_echo_of_persistent_bounce():
    """Persistent bid/ask runs and wide spreads: VR* stays below 1, VR** much closer to 1."""
    rng = np.random.default_rng(1)
    n_days, n = 3000, 390
    eff = rng.standard_normal((n_days, n))
    q, q_open = d024.d023.persistent_signs(rng, n_days, n, p_same=0.9)
    r = pd.DataFrame(d024.d022.observed_returns(eff, np.full(eff.shape, 1.5), q, q_open))
    gap_star = 1 - variance_ratio_skip(r).mean()
    gap_star2 = 1 - variance_ratio_skip(r, skip=2).mean()
    assert gap_star > 0.01
    assert abs(gap_star2) < gap_star / 3


def test_same_samples_as_the_d023_run():
    rows23 = d024.d023.one_rep((0, 120))
    rows24 = d024.one_rep((0, 120))
    for sc in ("A", "D"):
        a23 = {r["measure"]: r["slope"] for r in rows23 if r["scenario"] == sc and r["estimator"] == "vr_skip"}
        a24 = {r["measure"]: r["slope"] for r in rows24 if r["scenario"] == sc and r["estimator"] == "vr_skip"}
        assert all(np.isclose(a23[m], a24[m]) for m in a23)
    assert {r["scenario"] for r in rows24} == set(d024.SCENARIOS)
    assert {r["estimator"] for r in rows24} == set(d024.ESTIMATORS)
