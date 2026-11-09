"""Event detection (fai.detection) and the event table script (D-032)."""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

from fai import config
from fai.detection import detect_day, detect_events, thresholds, trailing_sigma

ROOT = Path(__file__).resolve().parents[1]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


evt = _load("event_table", "scripts/event_table.py")
th1 = _load("th1", "tests/test_h1_tests.py")


def test_detect_day_by_hand():
    s = np.full(100, 1.0)
    assert detect_day(s, 2.0, 1.2) == []
    s[40:50] = 3.0                                   # one burst
    assert detect_day(s, 2.0, 1.2) == [(40, 49, False)]
    s[80:] = 3.0                                     # still going at the close
    assert detect_day(s, 2.0, 1.2)[-1] == (80, 99, True)


def test_end_needs_a_full_quiet_run():
    s = np.full(120, 1.0)
    s[20] = 3.0
    s[30] = 1.5                                      # above the end level: resets the run
    ev = detect_day(s, 2.0, 1.2, run=15)
    assert ev == [(20, 30, False)]


def test_sigma_waits_for_five_minutes():
    Rt = pd.DataFrame(np.ones((1, 30)))
    sig = trailing_sigma(Rt)
    assert sig.iloc[0, :4].isna().all() and np.isclose(sig.iloc[0, 4], 1.0)


def test_one_crisis_day_barely_moves_the_threshold():
    rng = np.random.default_rng(0)
    S = pd.DataFrame(np.abs(1 + 0.2 * rng.standard_normal((32, 390))))
    calm = thresholds(S, np.ones(32, bool)).iloc[31]
    S.iloc[20] = 10.0                                # a crisis day inside the 30-day window
    crisis = thresholds(S, np.ones(32, bool)).iloc[31]
    assert abs(crisis["baseline"] - calm["baseline"]) < 0.05
    assert crisis["theta"] < 1.3 * calm["theta"]
    v = S.iloc[1:31].to_numpy().ravel()              # a mean and SD would jump
    assert v.std() > 5 * calm["theta"]


def test_detect_events_finds_a_planted_burst():
    rng = np.random.default_rng(1)
    Rt = pd.DataFrame(rng.standard_normal((40, 390)), index=pd.bdate_range("2015-01-05", periods=40))
    Rt.iloc[35, 200:215] *= 6.0
    events, days = detect_events(Rt, np.ones(40, bool))
    assert days["n_events"].iloc[:30].isna().all()          # no baseline yet
    d35 = days.iloc[35]
    assert d35["n_events"] >= 1 and d35["energy_share_events"] > 0.6
    assert d35["largest_start"] <= 202 <= d35["largest_end"]
    assert set(events.columns) >= {"day", "start", "end", "cut_off", "energy_share"}


def test_placebos_skip_the_named_episode_and_keep_one_per_episode():
    cal = pd.bdate_range("2020-01-01", periods=400)
    d = pd.DataFrame({"rv": np.linspace(1, 1.9, 400)}, index=cal)
    named = [cal[200]]
    d.loc[cal[180:221], "rv"] = d.at[cal[200], "rv"]        # the same crisis: identical RV
    pl = evt.placebo_days(d, named, cal, k=5, gap=20)
    assert len(pl) == 5
    assert not pl["day"].isin(cal[180:221]).any()           # outside +/- 20 sessions
    pos = np.sort([cal.get_loc(x) for x in pl["day"]])
    assert (np.diff(pos) > 20).all()                        # one per episode
    assert pl["rv_ratio"].between(0.5, 2).all()


def test_no_placebo_is_better_than_a_much_calmer_one():
    cal = pd.bdate_range("2020-01-01", periods=300)
    d = pd.DataFrame({"rv": 1.0}, index=cal)
    d.loc[cal[150], "rv"] = 10.0                            # nothing within a factor of 2
    d.loc[cal[[30, 260]], "rv"] = 6.0                       # two other episodes that qualify
    pl = evt.placebo_days(d, [cal[150]], cal)
    assert list(pl["day"]) == list(cal[[30, 260]]) or list(pl["day"]) == list(cal[[260, 30]])
    none = evt.placebo_days(d.assign(rv=lambda x: x["rv"].where(x.index == cal[150], 1.0)),
                            [cal[150]], cal)
    assert none.empty and list(none.columns) == ["for", "day", "rank", "rv_ratio"]


def test_build_and_report_on_synthetic_tables():
    daily = th1._synthetic_daily()
    daily["f_bar"] = 1.2
    rng = np.random.default_rng(2)
    summary = pd.DataFrame({"n_events": rng.integers(0, 3, len(daily)).astype(float),
                            "energy_share_events": rng.random(len(daily)),
                            "largest_start": 200.0, "largest_end": 230.0}, index=daily.index)
    res = evt.build(daily, summary, daily.index)
    t = res["table"]
    assert (t["kind"] == "named").sum() == len(config.EVENTS)
    n_pl = (t["kind"] == "placebo").sum()
    missing = int((evt.N_PLACEBO - res["short"]).sum())        # named days short of 5
    assert n_pl == evt.N_PLACEBO * len(config.EVENTS) - missing
    assert t["rv_decile"].between(1, 10).all()
    assert list(res["by_decile"].index) == list(range(1, 11))
    lines = evt.report(res)
    assert any("Flash Crash" in x for x in lines) and any("12:50–13:20" in x for x in lines)
