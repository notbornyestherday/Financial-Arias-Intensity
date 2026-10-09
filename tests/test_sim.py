import numpy as np
import pandas as pd

from fai.clean import clean
from fai.husid import husid_times, significant_times
from fai.measures import daily_measures
from fai.seasonality import deseasonalize, seasonal_variance, to_matrix
from fai.sim import Burst, matched_energy_pair, simulate_panel


def test_same_rv_different_concentration():
    """H1 in one test: identical total energy, very different D5-95."""
    rng = np.random.default_rng(1)
    zb, zg = matched_energy_pair(rng)
    assert np.isclose((zb ** 2).sum(), (zg ** 2).sum())
    _, _, d_burst = significant_times(zb ** 2)
    _, _, d_grind = significant_times(zg ** 2)
    assert d_burst < 60
    assert 320 < d_grind < 375


def _pipeline(n_days=170, specs=None, seed=2, **kw):
    rng = np.random.default_rng(seed)
    bars, sessions, truth = simulate_panel(rng, n_days, specs=specs, **kw)
    minutes, dq, _ = clean(bars, sessions)
    R, G = to_matrix(minutes, "r"), to_matrix(minutes, "gap")
    S2 = seasonal_variance(R, G, exclude=sessions.index[sessions["half_day"]])
    Rt = deseasonalize(R, G, S2)
    return daily_measures(R, Rt), truth, sessions, Rt, S2, dq


def test_end_to_end_recovers_injected_burst_and_grind():
    """Pipeline (estimated seasonality, bid-ask bounce) vs. a perfect-knowledge oracle."""
    burst = Burst(start=200, length=15, mult=12.0)
    grind = float(np.sqrt((375 + 15 * 144) / 390))     # same expected energy
    for seed in (2, 5, 7):
        specs = {160: {"bursts": [burst]}, 161: {"grind": grind}}
        daily, truth, sessions, *_ = _pipeline(specs=specs, seed=seed)
        d_burst, d_grind = sessions.index[160], sessions.index[161]
        for d in (d_burst, d_grind):
            oracle = husid_times(pd.DataFrame([truth[d].oracle_z])).iloc[0]
            assert abs(daily.at[d, "d5_95"] - oracle["d5_95"]) < 12
            assert abs(daily.at[d, "w50"] - oracle["w50"]) < 8
            oracle_energy = (truth[d].oracle_z ** 2).sum()
            assert 0.8 < daily.at[d, "energy"] / oracle_energy < 1.25
        assert daily.at[d_burst, "w50"] < 20 and daily.at[d_grind, "w50"] > 150
        calm = daily["fai"].iloc[110:155]
        assert 0.8 < calm.mean() < 1.2


def test_overnight_gaps_do_not_leak_into_first_minute():
    _, _, _, Rt, _, _ = _pipeline(n_days=120, overnight_sd=0.03)
    first_minute_energy = (Rt[0].iloc[60:] ** 2).mean()
    assert 0.5 < first_minute_energy < 2.0


def test_seasonality_recovers_u_shape():
    from fai.sim import u_shape
    _, _, _, _, S2, _ = _pipeline(n_days=120)
    s = np.sqrt(S2.iloc[100])
    true = u_shape()
    est_ratio = (s[5:30] / s[150:250].mean()).to_numpy()
    true_ratio = true[5:30] / true[150:250].mean()
    assert np.allclose(est_ratio, true_ratio, rtol=0.35)
    assert np.isclose(est_ratio.mean(), true_ratio.mean(), rtol=0.1)
