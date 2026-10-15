"""The D-019 selection rule and the half-day normalizer."""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

from fai.measures import normalizer

ROOT = Path(__file__).resolve().parents[1]


def _script():
    spec = importlib.util.spec_from_file_location("cs", ROOT / "scripts" / "choose_seasonality.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_qlike_is_lowest_at_the_true_variance():
    cs = _script()
    rng = np.random.default_rng(0)
    R = pd.DataFrame(rng.standard_normal((300, 390)) * 2.0)      # true variance 4
    mask = pd.DataFrame(True, index=R.index, columns=R.columns)
    losses = {s2: cs.daily_qlike(R, pd.DataFrame(s2, index=R.index, columns=R.columns),
                                 mask).mean() for s2 in (2.0, 3.0, 4.0, 5.0, 8.0)}
    assert min(losses, key=losses.get) == 4.0


def test_qlike_handles_zero_returns():
    cs = _script()
    R = pd.DataFrame(np.zeros((2, 5)))
    S2 = pd.DataFrame(np.ones((2, 5)))
    mask = pd.DataFrame(True, index=R.index, columns=R.columns)
    assert np.isfinite(cs.daily_qlike(R, S2, mask)).all()


def _daily(gap, n=1500, seed=1):
    rng = np.random.default_rng(seed)
    base = rng.normal(0, 1, n)
    names = [c[0] for c in _script().CANDIDATES]
    df = pd.DataFrame({names[0]: base + rng.normal(0, 0.05, n)})
    df[names[1]] = base + rng.normal(0, 0.05, n) + 0.02
    df[names[2]] = base + rng.normal(0, 0.05, n) - gap
    df[names[3]] = base + rng.normal(0, 0.05, n) + 0.03
    return df


def test_clearly_better_candidate_wins():
    cs = _script()
    winner, table = cs.pick(_daily(gap=0.05))
    assert winner == cs.CANDIDATES[2][0]
    assert table["winner"].sum() == 1


def test_tie_goes_to_the_simpler_candidate():
    cs = _script()
    winner, _ = cs.pick(_daily(gap=0.0))
    assert winner == cs.CANDIDATES[0][0]                         # registered default


def test_newey_west_matches_iid_formula_at_lag_zero():
    cs = _script()
    x = np.random.default_rng(3).standard_normal(5000)
    assert np.isclose(cs.newey_west_se(x, 0), x.std() / np.sqrt(x.size), rtol=1e-6)


def test_evaluate_runs_on_simulated_data():
    from fai.clean import clean
    from fai.seasonality import to_matrix
    from fai.sim import simulate_panel
    cs = _script()
    bars, sessions, _ = simulate_panel(np.random.default_rng(4), 130, start="2015-01-05")
    minutes, _, _ = clean(bars, sessions)
    R, G = to_matrix(minutes, "r"), to_matrix(minutes, "gap")
    winner, table, info = cs.evaluate(R, G, [], start="2015-01-01", end="2015-12-31")
    assert winner in table["candidate"].tolist()
    assert np.isfinite(table["mean_qlike"]).all()
    assert info["days"] >= 60 and info["minutes"] > 60 * 380


def test_normalizer_skips_half_days():
    idx = pd.bdate_range("2015-01-05", periods=100)
    E = pd.Series(10.0, index=idx)
    E.iloc[50] = 1.0                                             # a short day
    with_it = normalizer(E, window=20, min_days=10)
    without = normalizer(E, window=20, min_days=10, exclude=[idx[50]])
    assert with_it.iloc[60] < 10.0
    assert np.isclose(without.iloc[60], 10.0)
