"""The H2 test script on synthetic data with a known answer."""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

from fai import vix

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("h2", ROOT / "scripts" / "h2_tests.py")
h2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(h2)


def _synthetic(seed=0, b_w50=0.0, b_fbar=0.0, kappa=0.0, fai_tracks_vix=False):
    """Business days 2009-06 to 2025-12. ln VIX follows

        ln V_{t+1} - ln V_t = -kappa (ln V_t - mu) + b_w50 (ln W50_t - 4)
                              + b_fbar (ln f_bar_t - 0.2) + 0.06 e_{t+1},

    so the true next-day effects are b_w50 and b_fbar. With ``fai_tracks_vix``, ln FAI is
    minus today's ln VIX gap plus noise: the trailing-normalization channel of D-027.
    """
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2009-06-01", "2025-12-31")
    n = idx.size
    ln_rv = -9 + 0.8 * rng.standard_normal(n)
    ln_w50 = 4 + 0.4 * rng.standard_normal(n)
    ln_fbar = np.clip(0.2 + 0.09 * rng.standard_normal(n), 0, np.log(np.pi / 2))
    mu = np.log(18.0)
    lv = np.empty(n)
    lv[0] = mu
    for t in range(n - 1):
        lv[t + 1] = (lv[t] - kappa * (lv[t] - mu) + b_w50 * (ln_w50[t] - 4)
                     + b_fbar * (ln_fbar[t] - 0.2) + 0.06 * rng.standard_normal())
    if fai_tracks_vix:
        ln_fai = -(lv - mu) + 0.1 * rng.standard_normal(n)
    else:
        ln_fai = 0.5 * (ln_rv + 9) + 0.5 * rng.standard_normal(n)
    d = pd.DataFrame(index=idx)
    d["rv"] = np.exp(ln_rv)
    d["fai"] = np.exp(ln_fai)
    d["f_bar"] = np.exp(ln_fbar)
    d["fai_w"] = d["fai"] * d["f_bar"]
    d["fai_w_cs"] = d["fai"] * np.exp(0.2 + 0.05 * rng.standard_normal(n))
    d["fai_c"] = d["fai"] * np.exp(0.5 * rng.standard_normal(n))
    d["w50"] = np.exp(ln_w50)
    d["d5_75"] = np.exp(ln_w50 + 0.4 + 0.05 * rng.standard_normal(n))
    d["fomc"] = False
    d["half_day"] = False
    d["in_tests"] = True
    d.iloc[[300, 2000], d.columns.get_loc("in_tests")] = False
    close = pd.Series(100 * np.exp(np.cumsum(0.01 * rng.standard_normal(n))), index=idx)
    vix_close = pd.Series(np.exp(lv), index=idx)
    div = pd.Series([0.5, 0.6], index=idx[[400, 3000]])
    return d, close, vix_close, div


def test_sample_is_test_days_2010_to_2025_complete():
    d, close, vix_close, div = _synthetic()
    s = h2.test_sample(vix.h2_frame(d, close, vix_close, div))
    assert s.index.min() >= pd.Timestamp("2010-01-01")
    assert s.index.max() <= pd.Timestamp("2025-12-31")
    assert s["in_tests"].all() and s[h2.REQUIRED].notna().all().all()
    ins, oos = h2.periods(s)
    assert ins.sum() > 2000 and oos.sum() > 1700 and not (ins & oos).any()


def test_no_effect_gives_no_significant_h2():
    """One draw with no effect anywhere. Any single draw has about a 5% chance of a false
    alarm per test (seed 1 gives one, out of sample: p 0.045); the rejection rates
    themselves are checked in test_vix.test_clark_west_size_and_power."""
    res = h2.run(*_synthetic(seed=6))
    v = res["verdicts"]
    assert v["H2a (i)"]["verdict"] == "not significant"
    assert v["H2a (ii)"]["verdict"] == "not significant"
    assert v["H2b"]["verdict"] == "not significant"
    assert not v["H2a out of sample"]["passes"] and not v["H2b out of sample"]["passes"]


def test_concentration_effect_is_found_in_and_out_of_sample_and_holds_with_d5_75():
    res = h2.run(*_synthetic(seed=2, b_w50=-0.02))
    v = res["verdicts"]
    assert v["H2b"]["verdict"] == "b != 0 (b < 0), and holds with D5-75"
    assert v["H2b out of sample"]["passes"]
    assert v["H2b out of sample"]["with_d5_75"] == "passes"
    assert v["H2a (i)"]["verdict"] == "not significant"


def test_h2a_ii_is_the_coefficient_on_ln_f_bar():
    """ln FAI_w = ln FAI + ln f_bar, so with ln FAI in the regression the coefficient on
    ln FAI_w is exactly the coefficient on ln f_bar."""
    d, close, vix_close, div = _synthetic(seed=3, b_fbar=0.3)
    s = h2.test_sample(vix.h2_frame(d, close, vix_close, div))
    ins, _ = h2.periods(s)
    a = vix.nw_ols(s.loc[ins], h2.Y, ["ln_fai_w", "ln_fai", *vix.CONTROLS])
    b = vix.nw_ols(s.loc[ins], h2.Y, ["ln_f_bar", "ln_fai", *vix.CONTROLS])
    assert np.isclose(a.loc["ln_fai_w", "coef"], b.loc["ln_f_bar", "coef"])
    assert np.isclose(a.loc["ln_fai_w", "se"], b.loc["ln_f_bar", "se"])
    res = h2.run(d, close, vix_close, div)
    assert res["verdicts"]["H2a (ii)"]["verdict"] == "b != 0 (b > 0)"


def test_a_pass_that_comes_only_from_vix_mean_reversion_is_a_fail():
    """D-027: if FAI carries today's VIX level, the registered regression finds an
    'effect' that is VIX mean reversion; with ln VIX_d in, it goes away."""
    res = h2.run(*_synthetic(seed=4, kappa=0.03, fai_tracks_vix=True))
    ins = res["in_sample"]
    reg = h2._pick(ins, test="H2a (i)", x="ln_fai_w", spec="registered", role="primary")
    main = h2._pick(ins, test="H2a (i)", x="ln_fai_w", spec="D-027", role="primary")
    assert abs(reg["t"]) > 3 and abs(main["t"]) < 1.96
    v = res["verdicts"]["H2a (i)"]
    assert v["verdict"].startswith("fails: significant only without the VIX-level control")
    assert not v["passes"]


def test_holm_family_has_the_seven_d029_tests(tmp_path):
    rows = [
        {"test": "H1b", "p": 0.58, "primary": True, "run": h2.PRIMARY_RUN},
        {"test": "H1b", "p": 0.31, "primary": False, "run": h2.PRIMARY_RUN},
        {"test": "H1c concentration", "p": 1e-40, "primary": True, "run": h2.PRIMARY_RUN},
        {"test": "H1c dummy", "p": 0.17, "primary": True, "run": h2.PRIMARY_RUN},
        {"test": "H1b", "p": 0.99, "primary": True, "run": "Flagged prints kept"},
    ]
    csv = tmp_path / "h1_results.csv"
    pd.DataFrame(rows).to_csv(csv, index=False)
    res = h2.run(*_synthetic(seed=2, b_w50=-0.02))
    t = h2.holm_family(res["verdicts"], csv)
    assert list(t["test"]) == ["H1b", "H1c concentration", "H2a (i)", "H2a (ii)", "H2b",
                               "H2a out of sample", "H2b out of sample"]
    assert np.isclose(t.loc[t["test"] == "H1b", "p_raw"].iloc[0], 0.58)
    assert (t["p_holm"] >= t["p_raw"] - 1e-12).all()
    assert h2.holm_family(res["verdicts"], tmp_path / "missing.csv") is None


def test_report_renders():
    res = h2.run(*_synthetic(seed=2, b_w50=-0.02))
    text = "\n".join(h2.section("Primary: flagged prints removed", res, None))
    assert "### Verdicts" in text and "Clark-West" in text and "jump logit" in text
    assert "2 ex-dividend days" in text


def test_leave_one_year_out_keeps_a_spread_effect_and_flags_a_one_year_result():
    """A real effect in every year survives each refit. A result planted in one year (nine
    very concentrated 2018 days, each followed by a VIX jump of 80%) is significant in the
    full sample, collapses when 2018 is left out, and 2018 is named as the most influential
    year. (A single planted day is not enough: the Newey-West standard error grows with it.)"""
    res = h2.run(*_synthetic(seed=2, b_w50=-0.02))
    s = res["loyo_summary"].set_index("x")
    assert len(res["loyo"]) == 4 * 9
    assert s.loc["ln_w50", "sig_same_sign"] == 9

    d, close, vix_close, div = _synthetic(seed=6)
    for day in d.index[d.index.year == 2018][20:200:22]:
        d.loc[day, "w50"] = np.exp(2.5)                    # W50 about 12 minutes
        nxt = vix_close.index[vix_close.index.get_loc(day) + 1]
        vix_close.loc[nxt] *= 1.8                          # next close 80% higher, that day only
    res = h2.run(d, close, vix_close, div)
    s = res["loyo_summary"].set_index("x")
    assert s.loc["ln_w50", "year_most_influential"] == 2018
    assert abs(s.loc["ln_w50", "t_without_it"]) < 1.96 < abs(s.loc["ln_w50", "t_full"])


def test_unadjusted_version_uses_the_same_days_and_differs_only_through_r():
    """Dividends not added back (D-034): same days, same verdict-free tests; with no
    ex-dividend days in the test span the two versions are identical."""
    d, close, vix_close, div = _synthetic(seed=2, b_w50=-0.02)
    res = h2.run(d, close, vix_close, div)
    ua = res["unadjusted"]["in_sample"]
    assert set(ua["spec"]) == {"D-027"} and len(ua) == 4
    assert (ua["n"] == h2._pick(res["in_sample"], test="H2b", x="ln_w50", spec="D-027",
                                role="primary")["n"]).all()
    none = h2.run(d, close, vix_close, div.iloc[:0])
    m = h2._pick(none["in_sample"], test="H2b", x="ln_w50", spec="D-027", role="primary")
    u = h2._pick(none["unadjusted"]["in_sample"], test="H2b", x="ln_w50", spec="D-027",
                 role="primary")
    assert np.isclose(m["coef"], u["coef"]) and np.isclose(m["t"], u["t"])
    text = "\n".join(h2.section("Primary: flagged prints removed", res, None))
    assert "### Dividends not added back" in text
