"""The robustness script on synthetic data with a known answer (D-018, H3, D-025 a)."""

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
_spec = importlib.util.spec_from_file_location("rob", ROOT / "scripts" / "robustness.py")
rob = importlib.util.module_from_spec(_spec)
sys.modules["rob"] = rob
_spec.loader.exec_module(rob)


def _synthetic(seed=0, vix_on="none", vr_on_w50_diff=0.0):
    """Business days 2009-06 to 2025-12 with every column the H1 and H2 scripts read.

    ln RQ ratio (unevenness) is drawn first; ln W50 is correlated with it (corr about
    -0.7: an uneven day also has a short W50). Next-day d ln VIX responds to ``vix_on``:
    "rq" (unevenness only), "w50" (W50 beyond unevenness) or "none". VR** responds by
    ``vr_on_w50_diff`` to the part of the differenced-signal W50 that r~'s W50 does not share,
    so with it r~ fails and the differenced signal passes; nothing else moves VR**.
    """
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2009-06-01", "2025-12-31")
    n = idx.size
    ln_rq = 0.5 * rng.standard_normal(n)
    ln_w50 = 4.0 - 0.6 * ln_rq + 0.3 * rng.standard_normal(n)
    ln_w50_diff = ln_w50 + 0.3 * rng.standard_normal(n)
    ln_rv = -9 + 0.8 * rng.standard_normal(n)
    eff = {"none": 0.0 * ln_rq, "rq": 0.03 * ln_rq, "w50": -0.03 * (ln_w50 - 4 + 0.6 * ln_rq)}
    mu = np.log(18.0)
    lv = np.empty(n)
    lv[0] = mu
    for t in range(n - 1):
        lv[t + 1] = lv[t] - 0.02 * (lv[t] - mu) + eff[vix_on][t] + 0.06 * rng.standard_normal()
    d = pd.DataFrame(index=idx)
    d["rv"] = np.exp(ln_rv)
    d["fai"] = np.exp(0.5 * (ln_rv + 9) + 0.5 * rng.standard_normal(n))
    d["f_bar"] = np.exp(np.clip(0.2 + 0.09 * rng.standard_normal(n), 0, np.log(np.pi / 2)))
    d["fai_w"] = d["fai"] * d["f_bar"]
    d["fai_w_cs"] = d["fai"] * 1.2
    d["fai_c"] = d["fai"] * 1.5
    d["w50"] = np.exp(ln_w50)
    d["d5_75"] = np.exp(ln_w50 + 0.4 + 0.05 * rng.standard_normal(n))
    d["d5_95"] = np.exp(ln_w50 + 0.8 + 0.05 * rng.standard_normal(n))
    d["w50_diff"] = np.exp(ln_w50_diff)
    d["d5_75_diff"] = np.exp(ln_w50_diff + 0.4 + 0.05 * rng.standard_normal(n))
    d["fai_diff"] = d["fai"] * np.exp(0.1 * rng.standard_normal(n))
    d["fai_w_diff"] = d["fai_diff"] * d["f_bar"]
    d["rq_ratio"] = np.exp(ln_rq)
    d["jump_share"] = rng.uniform(0, 0.3, n)
    d["down_share"] = rng.uniform(0.3, 0.7, n)
    noise = 0.2 * rng.standard_normal(n)
    # the effect rides on the part of the differenced W50 that r~'s W50 does not share
    d["vr_skip2"] = 1 + vr_on_w50_diff * (ln_w50_diff - ln_w50) + noise
    for c in ["vr", "vr_skip", "vr_skip_60"]:
        d[c] = d["vr_skip2"] + 0.05 * rng.standard_normal(n)
    d["fomc"] = False
    d.iloc[::40, d.columns.get_loc("fomc")] = True
    d["half_day"] = False
    d["in_tests"] = True
    close = pd.Series(100 * np.exp(np.cumsum(0.01 * rng.standard_normal(n))), index=idx)
    vix_close = pd.Series(np.exp(lv), index=idx)
    div = pd.Series([0.5, 0.6], index=idx[[400, 3000]])
    return d, close, vix_close, div


CHAIR = pd.DatetimeIndex(["2012-02-29", "2012-03-01", "2015-07-15", "2016-08-26",
                          "2024-07-09"])


def _spec_row(df, test, spec, x):
    m = (df["test"] == test) & (df["spec"] == spec) & (df["x"] == x)
    assert m.sum() == 1, (test, spec, x)
    return df.loc[m].iloc[0]


def test_extra_columns_are_logs_and_levels():
    d, *_ = _synthetic()
    e = rob.extra_columns(d)
    assert np.allclose(e["ln_rq_ratio"], np.log(d["rq_ratio"]))
    assert np.allclose(e["ln_fai_w_diff"], np.log(d["fai_w_diff"]))
    assert np.allclose(e["jump_share"], d["jump_share"])          # shares stay in levels


def test_missing_differenced_weighting_fails_loudly():
    d, *_ = _synthetic()
    try:
        rob.extra_columns(d.drop(columns=["fai_w_diff"]))
    except ValueError as err:
        assert "rerun the measures stage" in str(err)
    else:
        raise AssertionError("expected a ValueError")


def test_samples_match_the_registered_scripts():
    d, close, vix_close, div = _synthetic(seed=1)
    res = rob.run(d, close, vix_close, div, CHAIR)
    assert res["d1"].index.equals(rob.h1_tests.test_sample(d).index)
    frame = rob.vix.h2_frame(d, close, vix_close, div)
    assert res["d2"].index.equals(rob.h2_tests.test_sample(frame).index)
    reg = _spec_row(res["d018"], "H2b", "W50 alone (registered)", "ln_w50")
    ins, _ = rob.h2_tests.periods(res["d2"])
    main = rob.vix.nw_ols(res["d2"].loc[ins], rob.Y, ["ln_w50", *rob.vix.CONTROLS])
    assert np.isclose(reg["coef"], main.loc["ln_w50", "coef"])


def test_a_w50_effect_that_is_really_unevenness_goes_away_with_the_rq_control():
    """VIX responds to unevenness only; W50 is correlated with unevenness, so W50 alone
    'predicts' VIX. With ln RQ ratio as a control (D-018 a), W50 loses it."""
    res = rob.run(*_synthetic(seed=2, vix_on="rq"), CHAIR)
    t = res["d018"]
    alone = _spec_row(t, "H2b", "W50 alone (registered)", "ln_w50")
    ctrl = _spec_row(t, "H2b", "(a) W50 + ln RQ ratio", "ln_w50")
    rq = _spec_row(t, "H2b", "(a) W50 + ln RQ ratio", "ln_rq_ratio")
    assert alone["p"] < 0.05 and ctrl["p"] > 0.05 and rq["p"] < 0.05


def test_timing_beyond_unevenness_survives_the_rq_control():
    res = rob.run(*_synthetic(seed=3, vix_on="w50"), CHAIR)
    ctrl = _spec_row(res["d018"], "H2b", "(a) W50 + all three", "ln_w50")
    assert ctrl["p"] < 0.05 and ctrl["coef"] < 0
    oos = res["d018_oos"].set_index("x")
    assert oos.loc["ln_w50", "r2_os"] > 0


def test_h3_flags_an_improvement_only_where_the_differenced_signal_passes_alone():
    none = rob.run(*_synthetic(seed=4), CHAIR)["h3"].set_index("test")
    assert not none.loc["H1b", "improves"]
    assert set(none["verdict"]) <= {"no", "not judged"}
    planted = rob.run(*_synthetic(seed=4, vr_on_w50_diff=0.1), CHAIR)["h3"].set_index("test")
    assert not planted.loc["H1b", "passes"]
    assert planted.loc["H1b", "passes_diff"] and planted.loc["H1b", "improves"]
    assert planted.loc["H1b", "verdict"] == "yes"          # strong effect: survives Holm
    assert planted.loc["H1b", "t_diff"] > planted.loc["H1b", "t"]
    assert set(planted.index) == {"H1b", "H1b, D5-75", "H2a (i)", "H2a (ii)", "H2b",
                                  "H2b, D5-75", "H2a out of sample", "H2b out of sample",
                                  "H2b out of sample, D5-75"}


def test_fed_chair_version_leaves_out_exactly_the_listed_days():
    d, close, vix_close, div = _synthetic(seed=5)
    res = rob.run(d, close, vix_close, div, CHAIR)
    fc, info = res["fed_chair"], res["fed_chair_info"]
    d1 = res["d1"]
    in_sample = CHAIR[CHAIR.isin(d1.index)]
    also_fomc = int(d1.loc[in_sample, "fomc"].sum())
    assert info["chair_days_in_sample"] == len(in_sample)
    assert info["chair_days_also_fomc"] == also_fomc
    reg = _spec_row(fc, "H1b", "registered (FOMC days out)", "ln_w50")
    alt = _spec_row(fc, "H1b", "FOMC and Fed Chair days out (D-025 a)", "ln_w50")
    assert reg["n"] - alt["n"] == len(in_sample) - also_fomc
    assert np.isclose(reg["coef"], rob.h1_tests.h1b(d1).query(
        "y == 'vr_skip2' and x == 'ln W50'")["coef"].iloc[0])


def test_report_renders():
    res = rob.run(*_synthetic(seed=1), CHAIR)
    text = "\n".join(rob.section("Primary: flagged prints removed", res))
    for s in ["D-018 benchmark comparison", "H3: differenced signal", "Fed Chair",
              "ln RQ ratio", "improves"]:
        assert s in text


def test_measures_stage_weights_the_differenced_signal_like_the_primary_one():
    """H3 (run_all.liquidity_weighting): FAI_w on the differenced signal is its unweighted
    FAI (same trailing normalizer as measures.fai_diff) times the day's mean damping
    factor, exactly as FAI_w = FAI x f_bar for r~."""
    spec = importlib.util.spec_from_file_location("ra", ROOT / "scripts" / "run_all.py")
    ra = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ra)
    from fai.measures import daily_measures
    from fai.seasonality import deseasonalize, seasonal_variance, to_matrix
    rng = np.random.default_rng(0)
    days = pd.bdate_range("2020-01-01", periods=120)
    n = 390
    frames = []
    for d in days:
        p = 300 * np.exp(np.cumsum(0.0005 * rng.standard_normal(n)))
        frames.append(pd.DataFrame({"date": d, "tau": np.arange(n), "close": p,
                                    "high": p * 1.0002, "low": p * 0.9998,
                                    "volume": rng.integers(10_000, 100_000, n)}))
    m = pd.concat(frames, ignore_index=True)
    m["r"] = np.log(m["close"]).groupby(m["date"]).diff().fillna(0.0)
    m["gap"] = 1
    R, G = to_matrix(m, "r"), to_matrix(m, "gap")
    Rt = deseasonalize(R, G, seasonal_variance(R, G))
    out = ra.liquidity_weighting(m, R, Rt, G, exclude=pd.DatetimeIndex([]))
    j = daily_measures(R, Rt)[["fai_diff"]].join(out[["fai_w_diff", "f_bar_diff"]]).dropna()
    assert len(j) >= 15
    assert np.allclose(j["fai_w_diff"], j["fai_diff"] * j["f_bar_diff"])
    assert j["f_bar_diff"].between(1.0, np.pi / 2).all()


def _h3_table(**over):
    """Nine comparisons, none improving, then the overrides {test: (passes, passes_diff, p)}."""
    tests = ["H1b", "H1b, D5-75", "H2a (i)", "H2a (ii)", "H2b", "H2b, D5-75",
             "H2a out of sample", "H2b out of sample", "H2b out of sample, D5-75"]
    rows = []
    for t in tests:
        passes, passes_diff, p = over.get(t, (False, False, 0.5))
        rows.append({"test": t, "passes": passes, "passes_diff": passes_diff, "p_diff": p})
    return pd.DataFrame(rows)


def test_h3_three_tiers_d036():
    """No improvement = as predicted; a raw improvement that fails Holm over the six main
    comparisons = 'before Holm only'; one that survives Holm = 'yes' (not as predicted);
    the D5-75 versions are never judged; a test that already passed with r~ cannot improve."""
    v = rob.h3_verdicts(_h3_table()).set_index("test")
    assert set(v["verdict"]) == {"no", "not judged"}
    assert rob.h3_summary(v.reset_index()).startswith("as predicted")

    v = rob.h3_verdicts(_h3_table(**{"H1b": (False, True, 0.03)})).set_index("test")
    assert np.isclose(v.loc["H1b", "holm_diff"], 0.18)             # 6 x 0.03
    assert v.loc["H1b", "verdict"] == "before Holm only"
    assert rob.h3_summary(v.reset_index()).startswith("improves before Holm only")

    v = rob.h3_verdicts(_h3_table(**{"H1b": (False, True, 0.001)})).set_index("test")
    assert v.loc["H1b", "verdict"] == "yes"
    assert rob.h3_summary(v.reset_index()).startswith("not as predicted")

    v = rob.h3_verdicts(_h3_table(**{"H2b": (True, True, 0.001),
                                     "H1b, D5-75": (False, True, 0.0001)})).set_index("test")
    assert v.loc["H2b", "verdict"] == "no"                          # passed with r~ too
    assert v.loc["H1b, D5-75", "verdict"] == "not judged"
    assert np.isnan(v.loc["H1b, D5-75", "holm_diff"])
