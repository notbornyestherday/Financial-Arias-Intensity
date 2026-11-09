"""Liquidity proxies: Amihud, Corwin-Schultz, trailing windows and percentiles."""

import numpy as np
import pandas as pd

from fai.clean import clean
from fai.liquidity import (amihud, amihud_minute, corwin_schultz, corwin_schultz_pair,
                           liquidity_percentile, trailing_within_day)
from fai.seasonality import to_matrix
from fai.sim import LiquidityDrop, simulate_panel


def test_trailing_window_is_lagged_and_stays_inside_the_day():
    X = pd.DataFrame([[1.0, 2.0, 3.0, 4.0, 5.0], [100.0, 200.0, 300.0, 400.0, 500.0]])
    out = trailing_within_day(X, window=2, lag=1, min_periods=1)
    assert np.isnan(out.iloc[0, 0]) and np.isnan(out.iloc[1, 0])    # nothing before the open
    assert out.iloc[0, 1] == 1.0                                     # minute 1 sees only minute 0
    assert out.iloc[0, 3] == 2.5                                     # minutes 1-2, not 3 itself
    assert out.iloc[1, 1] == 100.0                                   # no carry-over from day 0


def test_amihud_by_hand_and_bad_minutes():
    R = pd.DataFrame([[0.001, -0.002, 0.003]])
    C = pd.DataFrame([[100.0, 100.0, 100.0]])
    V = pd.DataFrame([[1000.0, 0.0, 500.0]])
    G = pd.DataFrame([[1, 1, 3]])
    a = amihud_minute(R, C, V, G)
    assert np.isclose(a.iloc[0, 0], 0.001 / 1e5 * 1e6)              # per $1m traded
    assert np.isnan(a.iloc[0, 1])                                    # no volume
    assert np.isnan(a.iloc[0, 2])                                    # spans a gap


def test_corwin_schultz_recovers_a_pure_spread():
    """With no volatility and every bar touching bid and ask, CS returns the spread."""
    bid, ask = 99.95, 100.05
    n = 10
    H = pd.DataFrame([[ask] * n])
    L = pd.DataFrame([[bid] * n])
    C = pd.DataFrame([[ask if i % 2 else bid for i in range(n)]])
    s = corwin_schultz_pair(H, L, C)
    true = 2 * (ask - bid) / (ask + bid)
    assert np.isnan(s.iloc[0, 0])                                    # needs a previous bar
    assert np.allclose(s.iloc[0, 1:], true, rtol=1e-3)


def test_corwin_schultz_negatives_are_zero_and_gaps_removed():
    rng = np.random.default_rng(0)
    p = 100 * np.exp(np.cumsum(rng.normal(0, 1e-3, (1, 200)), axis=1))
    H, L, C = (pd.DataFrame(p * f) for f in (1.0005, 0.9995, 1.0))
    s = corwin_schultz_pair(H, L, C)
    assert (s.iloc[0, 1:] >= 0).all()
    G = pd.DataFrame(np.ones((1, 200)))
    G.iloc[0, 50] = 2
    assert np.isnan(corwin_schultz_pair(H, L, C, G).iloc[0, 50])


def _sim_matrices(drop_day=None, seed=3, n_days=70, spread_mult=20.0):
    specs = {drop_day: {"liquidity_drops": [LiquidityDrop(200, 30, volume_mult=0.2,
                                                          spread_mult=spread_mult)]}} if drop_day else None
    bars, sessions, _ = simulate_panel(np.random.default_rng(seed), n_days, specs=specs)
    minutes, _, _ = clean(bars, sessions)
    return {c: to_matrix(minutes, c) for c in ("r", "gap", "high", "low", "close", "volume")}


def test_both_proxies_rise_in_a_simulated_liquidity_drop():
    """Spread x20 and volume x0.2 from minute 200 to 229 (fai.sim's LiquidityDrop)."""
    m = _sim_matrices(drop_day=65)
    ami = amihud(m["r"], m["close"], m["volume"], m["gap"])
    cs = corwin_schultz(m["high"], m["low"], m["close"], m["gap"])
    for proxy in (ami, cs):
        day = proxy.iloc[65]
        before, during = day[170:200].mean(), day[225:231].mean()   # window fully inside
        assert during > 2 * before
        assert during > 2 * proxy.iloc[40:60, 225:231].mean().mean()  # vs other days


def test_percentile_uses_prior_days_and_the_same_minute():
    rng = np.random.default_rng(5)
    X = pd.DataFrame(rng.lognormal(size=(80, 3)))
    X[1] *= 10                                                       # a minute that is always worse
    P = liquidity_percentile(X, window_days=60, min_days=40)
    assert P.iloc[:40].isna().all().all()                            # warm-up
    assert P.iloc[40:].notna().all().all()
    assert abs(P.iloc[40:, 1].mean() - 0.5) < 0.1                    # judged against its own minute
    # Changing a day leaves its own and earlier percentiles' references untouched...
    Y = X.copy()
    Y.iloc[70] *= 1e6
    Q = liquidity_percentile(Y, window_days=60, min_days=40)
    assert np.allclose(P.iloc[:70], Q.iloc[:70], equal_nan=True)
    assert (Q.iloc[70] == 0).all()                                   # ...and makes that day illiquid
    # Half-days excluded from the reference distribution
    R = liquidity_percentile(X, window_days=60, min_days=40, exclude=X.index[10:20])
    assert not np.allclose(P.iloc[45], R.iloc[45])


def test_illiquid_minutes_get_low_percentiles_in_the_drop():
    m = _sim_matrices(drop_day=65)
    P = liquidity_percentile(amihud(m["r"], m["close"], m["volume"], m["gap"]),
                             min_days=40)
    assert P.iloc[65, 225:231].max() < 0.1
    assert 0.35 < np.nanmean(P.iloc[45:65].to_numpy()) < 0.65


def test_corwin_schultz_cannot_see_routine_spreads_at_one_minute():
    """A documented limitation: when the spread is tiny next to one minute's volatility
    (as in SPY), CS is mostly noise. About half the pair estimates are floored at zero,
    the average sits well above the true spread, and a x5 widening goes unnoticed."""
    m = _sim_matrices(drop_day=65, spread_mult=5.0)
    s = corwin_schultz_pair(m["high"], m["low"], m["close"], m["gap"])
    true_full_spread = 2 * 1.5e-5                                    # fai.sim default
    normal = s.iloc[:60].to_numpy()
    assert 0.3 < np.mean(normal == 0) < 0.7
    assert np.nanmean(normal) > 2 * true_full_spread
    assert np.nanmean(s.iloc[65, 200:230]) < 1.5 * np.nanmean(normal)
