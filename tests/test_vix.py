"""fai.vix: VIX alignment, the close-to-close return, Clark-West and the jump logit."""

import math

import numpy as np
import pandas as pd
import pytest

from fai import vix
from fai.inference import nw_mean


def test_vix_changes_by_hand():
    idx = pd.to_datetime(["2020-01-02", "2020-01-03", "2020-01-06"])
    v = vix.vix_changes(pd.Series([20.0, 22.0, 11.0], index=idx))
    assert np.isclose(v.loc["2020-01-03", "dlnvix"], math.log(22 / 20))
    assert np.isclose(v.loc["2020-01-03", "dlnvix_next"], math.log(11 / 22))
    assert np.isnan(v.loc["2020-01-02", "dlnvix"]) and np.isnan(v.loc["2020-01-06", "dlnvix_next"])


def test_target_is_tomorrows_change_not_todays():
    """No look-ahead the wrong way round: day d's target starts at d's own close."""
    spy = pd.bdate_range("2020-01-06", periods=5)
    vix_close = pd.Series([10.0, 20.0, 40.0, 20.0, 10.0], index=spy)
    daily = pd.DataFrame({"rv": 1e-4, "in_tests": True}, index=spy)
    close = pd.Series(100.0, index=spy)
    f = vix.h2_frame(daily, close, vix_close)
    assert np.isclose(f.loc[spy[1], "dlnvix"], math.log(2))        # 10 -> 20, today
    assert np.isclose(f.loc[spy[1], "dlnvix_next"], math.log(2))   # 20 -> 40, tomorrow
    assert np.isclose(f.loc[spy[2], "dlnvix_next"], -math.log(2))
    assert np.isclose(f.loc[spy[1], "ln_vix"], math.log(20))


def test_missing_vix_day_runs_on_vixs_own_calendar():
    spy = pd.bdate_range("2020-01-06", periods=5)                  # Mon-Fri
    vix_close = pd.Series([10.0, 12.0, 15.0, 20.0], index=spy.delete(2))   # no Wednesday
    daily = pd.DataFrame({"rv": 1e-4, "in_tests": True}, index=spy)
    f = vix.h2_frame(daily, pd.Series(100.0, index=spy), vix_close)
    assert np.isclose(f.loc[spy[1], "dlnvix_next"], math.log(15 / 12))   # Tue -> Thu
    assert f.loc[spy[2], ["ln_vix", "dlnvix", "dlnvix_next"]].isna().all()
    assert vix.alignment(spy, vix_close)["spy_days_without_vix"] == [str(spy[2].date())]


def test_dividend_is_added_back_on_the_ex_date():
    idx = pd.bdate_range("2021-03-17", periods=3)
    close = pd.Series([100.0, 101.0, 100.5], index=idx)
    div = pd.Series([0.6], index=[idx[2]])
    r = vix.close_to_close(close, div)
    assert np.isnan(r.iloc[0])
    assert np.isclose(r.iloc[1], math.log(101 / 100))
    assert np.isclose(r.iloc[2], math.log(101.1 / 101.0))          # not ln(100.5 / 101)
    assert np.isclose(vix.close_to_close(close).iloc[2], math.log(100.5 / 101))


def test_ex_date_that_is_not_a_session_is_an_error_and_outside_dates_are_ignored():
    idx = pd.bdate_range("2021-03-15", periods=10)                # through Fri 2021-03-26
    close = pd.Series(100.0, index=idx)
    with pytest.raises(ValueError, match="2021-03-20"):           # a Saturday
        vix.close_to_close(close, pd.Series([0.5], index=pd.to_datetime(["2021-03-20"])))
    far = pd.Series([0.5, 0.5], index=pd.to_datetime(["2008-03-20", "2026-03-20"]))
    assert np.allclose(vix.close_to_close(close, far).iloc[1:], 0.0)


def test_last_close_is_the_last_regular_hours_bar_including_half_days():
    minutes = pd.DataFrame({
        "date": pd.to_datetime(["2021-11-26"] * 3 + ["2021-11-29"] * 2),
        "tau": [0, 209, 1, 389, 0],                                 # out of order on purpose
        "close": [10.0, 12.0, 11.0, 21.0, 20.0]})
    c = vix.last_close(minutes)
    assert c.loc["2021-11-26"] == 12.0 and c.loc["2021-11-29"] == 21.0


def test_nw_ols_slopes_match_least_squares_with_a_constant():
    rng = np.random.default_rng(3)
    n = 500
    f = pd.DataFrame({"x1": rng.standard_normal(n), "x2": rng.standard_normal(n)})
    f["y"] = 0.7 + 0.3 * f["x1"] - 0.1 * f["x2"] + rng.standard_normal(n)
    r = vix.nw_ols(f, "y", ["x1", "x2"])
    c = vix.ols_fit(f, "y", ["x1", "x2"])
    assert np.allclose(r["coef"].to_numpy(), c[["x1", "x2"]].to_numpy())
    assert np.isclose(c["const"], 0.7, atol=0.15)


def test_nw_mean_with_lag_zero_is_the_classical_standard_error():
    rng = np.random.default_rng(4)
    v = rng.standard_normal(400) + 2.0
    m = nw_mean(v, lag=0)
    assert np.isclose(m["se"], v.std(ddof=0) / math.sqrt(v.size))
    assert np.isclose(m["mean"], v.mean())


def test_clark_west_is_zero_for_identical_forecasts():
    y = np.array([1.0, -1.0, 0.5, 0.2, -0.3])
    a = np.array([0.1, 0.0, 0.2, 0.1, 0.0])
    res = vix.clark_west(y, a, a, lag=0)
    assert np.isclose(res["cw_mean"], 0.0) and np.isclose(res["r2_os"], 0.0)


def _nested_sample(rng, n_fit, n_test, beta):
    n = n_fit + n_test
    f = pd.DataFrame({"c": rng.standard_normal(n), "x": rng.standard_normal(n)})
    f["y"] = 0.5 * f["c"] + beta * f["x"] + rng.standard_normal(n)
    fit = np.r_[np.ones(n_fit, bool), np.zeros(n_test, bool)]
    return f, fit, ~fit


def test_clark_west_size_and_power():
    """X has no effect: about 5% one-sided rejections (Clark-West is if anything slightly
    undersized). X has a small real effect: rejects most of the time."""
    rng = np.random.default_rng(5)
    rej_null = rej_alt = 0
    reps = 300
    for _ in range(reps):
        f, fit, test = _nested_sample(rng, 2000, 1700, 0.0)
        rej_null += vix.out_of_sample(f, "y", "x", ["c"], fit, test)["p"] < 0.05
        f, fit, test = _nested_sample(rng, 2000, 1700, 0.08)
        rej_alt += vix.out_of_sample(f, "y", "x", ["c"], fit, test)["p"] < 0.05
    assert 0.01 <= rej_null / reps <= 0.09
    assert rej_alt / reps > 0.8


def test_clark_west_can_reject_with_a_higher_sample_mse():
    """Why both numbers are reported: the adjustment adds back estimation noise."""
    rng = np.random.default_rng(6)
    seen = 0
    for _ in range(400):
        f, fit, test = _nested_sample(rng, 200, 1500, 0.04)
        res = vix.out_of_sample(f, "y", "x", ["c"], fit, test)
        seen += (res["p"] < 0.05) and (res["r2_os"] < 0)
    assert seen > 0


def test_logit_recovers_coefficients_and_counts_events():
    rng = np.random.default_rng(7)
    n = 20000
    f = pd.DataFrame({"x": rng.standard_normal(n)})
    p = 1 / (1 + np.exp(-(-3.0 + 0.8 * f["x"])))
    f["y"] = (rng.random(n) < p).astype(float)
    r = vix.logit_hac(f, "y", ["x"])
    assert r["converged"].all()
    assert abs(r.loc["x", "coef"] - 0.8) < 3 * r.loc["x", "se"]
    assert abs(r.loc["const", "coef"] + 3.0) < 3 * r.loc["const", "se"]
    assert r.loc["x", "events"] == int(f["y"].sum())


def test_logit_with_no_events_or_separation_reports_not_converged_instead_of_crashing():
    f = pd.DataFrame({"x": np.arange(50.0)})
    f["y"] = 0.0
    r = vix.logit_hac(f, "y", ["x"])
    assert not r["converged"].any() and r["se"].isna().all()
    f["y"] = (f["x"] > 40).astype(float)                           # perfectly separated
    r = vix.logit_hac(f, "y", ["x"])
    assert not r["converged"].any() and r["se"].isna().all()
