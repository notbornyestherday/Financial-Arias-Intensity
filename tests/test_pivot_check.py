"""The pivot check (D-028) on synthetic daily tables."""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("pivot", ROOT / "scripts" / "pivot_check.py")
pivot = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pivot)


def _daily(sd_ln_fbar, seed=0, fai_scale=1.0):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2009-01-01", "2025-12-31")
    n = idx.size
    ln_rv = rng.standard_normal(n)
    ln_fai = fai_scale * (0.6 * ln_rv + 0.4 * rng.standard_normal(n))
    f_bar = np.clip(np.exp(np.log(1.2) + sd_ln_fbar * rng.standard_normal(n)), 1, np.pi / 2)
    d = pd.DataFrame({"rv": np.exp(ln_rv), "fai": np.exp(ln_fai), "f_bar": f_bar,
                      "in_tests": True, "pi_missing": 0.01}, index=idx)
    d["fai_w"] = d["fai"] * d["f_bar"]
    d["fai_w_cs"] = d["fai"] * 1.2
    d["fai_c"] = d["fai"] * np.exp(rng.standard_normal(n))
    return d


def test_small_weighting_triggers_the_reframe():
    res = pivot.pivot(pivot.test_days(_daily(0.03)))
    assert res["trigger"] > 0.95 and res["reframe"]
    assert res["table"].iloc[0]["pair"].startswith("ln FAI_w vs ln FAI")
    assert res["sd_ln_fbar"] < res["sd_ln_fai"]


def test_weighting_that_reorders_days_does_not():
    """Only when days differ little in energy can a weighting bounded by pi/2 reorder them:
    ln f_bar lies in [0, ln(pi/2)] = [0, 0.45], so its spread is at most about 0.23."""
    res = pivot.pivot(pivot.test_days(_daily(0.6, fai_scale=0.2)))
    assert res["trigger"] < 0.95 and not res["reframe"]
    wide = pivot.pivot(pivot.test_days(_daily(0.6)))
    assert wide["trigger"] > 0.95                      # same weighting, ordinary spread of FAI


def test_sample_is_test_days_2010_to_2025():
    d = _daily(0.03)
    d.iloc[600, d.columns.get_loc("in_tests")] = False
    s = pivot.test_days(d)
    assert s.index.min() >= pd.Timestamp("2010-01-01") and s["in_tests"].all()
    assert len(s) == len(d.loc["2010":"2025"]) - 1


def test_report_renders():
    lines = pivot.report(pivot.pivot(pivot.test_days(_daily(0.03))), "check")
    assert any("Trigger (D-028)" in x for x in lines)
