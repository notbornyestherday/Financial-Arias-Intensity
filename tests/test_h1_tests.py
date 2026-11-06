"""The H1 test script on synthetic daily tables, and the inference helpers it adds."""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

from fai.inference import fe_ols, fe_slope, holm

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("h1", ROOT / "scripts" / "h1_tests.py")
h1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(h1)


def test_fe_ols_with_one_regressor_matches_fe_slope():
    rng = np.random.default_rng(0)
    n = 800
    g = rng.integers(0, 10, n)
    x = rng.standard_normal(n) + 0.3 * g
    y = 0.5 * x + g + rng.standard_normal(n)
    a = fe_slope(y, x, g, lag=5)
    b = fe_ols(y, {"x": x}, g, lag=5).loc["x"]
    assert np.isclose(a["slope"], b["coef"]) and np.isclose(a["se"], b["se"])


def test_fe_ols_recovers_two_coefficients_under_fixed_effects():
    rng = np.random.default_rng(1)
    n = 20000
    g = rng.integers(0, 10, n)
    x1 = rng.standard_normal(n) + 0.5 * g
    x2 = (rng.random(n) < 0.05).astype(float)
    y = 0.3 * x1 - 0.2 * x2 + 2.0 * g + 0.5 * rng.standard_normal(n)
    r = fe_ols(y, {"x1": x1, "x2": x2}, g)
    assert abs(r.loc["x1", "coef"] - 0.3) < 0.01
    assert abs(r.loc["x2", "coef"] + 0.2) < 3 * r.loc["x2", "se"]


def test_holm_by_hand():
    assert np.allclose(holm([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06])
    assert np.allclose(holm([0.5, 0.9]), [1.0, 1.0])


def _synthetic_daily(seed=2, b=0.05, fomc_shift=-0.6, d575_noise=False):
    """Business days 2009-2025; VR** = 1 + b ln W50 + noise; FOMC days have shorter W50."""
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2009-01-01", "2025-12-31")
    n = idx.size
    fomc = np.zeros(n, bool)
    fomc[::32] = True
    ln_rv = rng.standard_normal(n)
    ln_w50 = 4.0 + 0.3 * rng.standard_normal(n) - 0.2 * ln_rv + fomc_shift * fomc
    d = pd.DataFrame(index=idx)
    d["rv"] = np.exp(ln_rv)
    d["w50"] = np.exp(ln_w50)
    other = 4.5 + 0.3 * rng.standard_normal(n)
    d["d5_75"] = np.exp(other if d575_noise else ln_w50 + 0.4 + 0.05 * rng.standard_normal(n))
    d["d5_95"] = np.exp(ln_w50 + 0.8)
    noise = lambda: 0.05 * rng.standard_normal(n)  # noqa: E731
    d["vr_skip2"] = 1 + b * (ln_w50 - 4) + noise()
    for c in ["vr", "vr_skip", "vr_skip_60"]:
        d[c] = 1 + noise()
    d["fomc"] = fomc
    d["half_day"] = False
    d["in_tests"] = True
    d.iloc[100, d.columns.get_loc("in_tests")] = False
    return d


def test_sample_is_2010_to_2025_with_in_tests_and_full_sample_deciles():
    daily = _synthetic_daily()
    s = h1.test_sample(daily)
    assert s.index.min() >= pd.Timestamp("2010-01-01") and s.index.max() <= pd.Timestamp("2025-12-31")
    assert s["in_tests"].all()
    assert s["rv_decile"].nunique() == 10
    counts = s["rv_decile"].value_counts()
    assert counts.max() - counts.min() <= 1


def test_percentile_is_within_rv_decile():
    d = pd.DataFrame({"rv_decile": [0, 0, 0, 0, 1, 1], "w50": [10, 20, 30, 40, 5, 50]})
    q = h1.decile_percentile(d, "w50")
    assert list(q) == [25.0, 50.0, 75.0, 100.0, 50.0, 100.0]


def test_verdicts_on_a_planted_effect():
    res = h1.run(_synthetic_daily())
    v = res["verdicts"]
    assert v["H1b"] == "supported, and holds with D5-75"
    assert v["H1c_concentration"] == "supported, and holds with D5-75"
    assert v["H1c_dummy"].startswith("not significantly negative")
    assert v["H1c_holds"]
    assert set(v["holm_family_raw_p"]) == {"H1b", "H1c concentration"}


def test_fragile_when_d575_does_not_carry_the_effect():
    v = h1.run(_synthetic_daily(d575_noise=True))["verdicts"]
    assert v["H1b"] == "supported, but fragile (D5-75 disagrees)"


def test_no_effect_is_not_significant_and_no_fomc_shift_fails_the_control():
    v = h1.run(_synthetic_daily(seed=3, b=0.0, fomc_shift=0.0))["verdicts"]
    assert v["H1b"] in ("not significant", "opposite sign (significant)")
    assert not v["H1c_holds"]


def test_missing_named_day_raises():
    daily = _synthetic_daily()
    daily.loc[pd.Timestamp("2010-05-06"), "in_tests"] = False
    try:
        h1.run(daily)
    except ValueError as e:
        assert "2010-05-06" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_missing_vr_column_names_the_fix():
    daily = _synthetic_daily().drop(columns=["vr_skip2"])
    try:
        h1.test_sample(daily)
    except ValueError as e:
        assert "vr_skip2" in str(e) and "--stages measures" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_h1c_and_h1a_follow_the_robustness_rule():
    """D5-75 that does not carry the FOMC effect makes H1c fragile; H1a reports D5-75 too."""
    daily = _synthetic_daily(d575_noise=True)
    res = h1.run(daily)
    assert res["verdicts"]["H1c_concentration"] == "supported, but fragile (D5-75 disagrees)"
    assert {"q_d5_75", "d5_75"} <= set(res["h1a_table"].columns)
    assert "holds_with_d5_75" in res["h1a"]
