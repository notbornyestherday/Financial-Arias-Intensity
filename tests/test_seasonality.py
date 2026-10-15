import numpy as np
import pandas as pd

from fai.seasonality import deseasonalize, seasonal_variance


def _matrices(n_days=80, n=390, seed=3):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2016-01-04", periods=n_days)
    R = pd.DataFrame(rng.standard_normal((n_days, n)) * 1e-4, index=idx)
    G = pd.DataFrame(np.ones((n_days, n)), index=idx)
    return R, G


def test_no_look_ahead():
    R, G = _matrices()
    S2 = seasonal_variance(R, G)
    k = 60
    R2 = R.copy()
    R2.iloc[k] *= 100.0
    S2b = seasonal_variance(R2, G)
    pd.testing.assert_frame_equal(S2.iloc[: k + 1], S2b.iloc[: k + 1])
    assert not np.allclose(S2.iloc[k + 1], S2b.iloc[k + 1])


def test_warm_up_is_nan():
    R, G = _matrices()
    S2 = seasonal_variance(R, G, min_days=40)
    assert S2.iloc[:40].isna().all(axis=None)
    assert S2.iloc[40].notna().all()


def test_gap_return_uses_summed_variance():
    R, G = _matrices(n_days=1)
    S2 = pd.DataFrame(np.full(R.shape, 4.0), index=R.index)
    R.iloc[0, 100] = np.sqrt(15 * 4.0)      # a 15-minute return of typical size
    G.iloc[0, 100] = 15
    R.iloc[0, 86:100] = np.nan              # the minutes it spans have no bar
    Rt = deseasonalize(R, G, S2)
    assert np.isclose(Rt.iloc[0, 100], 1.0)


def test_excluded_days_do_not_enter_estimate():
    R, G = _matrices()
    R2 = R.copy()
    R2.iloc[50] *= 100.0
    S2 = seasonal_variance(R, G, exclude=[R.index[50]])
    S2b = seasonal_variance(R2, G, exclude=[R.index[50]])
    pd.testing.assert_frame_equal(S2, S2b)


def test_smoothing_spreads_a_spike_but_spares_open_and_close():
    from fai.seasonality import smooth_profile
    S2 = pd.DataFrame(np.ones((2, 390)))
    S2.iloc[:, 0] = 50.0                       # opening minute
    S2.iloc[:, 389] = 20.0                     # closing minute
    S2.iloc[:, 100] = 6.0                      # one noisy minute
    out = smooth_profile(S2, 5)
    assert (out.iloc[:, 0] == 50.0).all() and (out.iloc[:, 389] == 20.0).all()
    assert np.allclose(out.iloc[0, 98:103], 2.0)     # (6 + 4 x 1) / 5
    assert np.isclose(out.iloc[0, 1], 1.0)           # the open is not a neighbour
    assert np.isclose(out.iloc[0, 388], 1.0)         # nor is the close
    assert np.isclose(out.iloc[0, 1:389].sum(), S2.iloc[0, 1:389].sum())


def test_smoothing_width_one_is_identity():
    from fai.seasonality import smooth_profile
    S2 = pd.DataFrame(np.random.default_rng(7).random((3, 390)))
    pd.testing.assert_frame_equal(smooth_profile(S2, 0), S2)
