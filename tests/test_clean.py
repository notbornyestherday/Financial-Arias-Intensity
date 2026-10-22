import numpy as np
import pandas as pd

from fai.clean import clean
from fai.sessions import synthetic_sessions
from fai.sim import simulate_panel


def _one_day(seed=4):
    rng = np.random.default_rng(seed)
    bars, sessions, _ = simulate_panel(rng, 1)
    return bars, sessions


def test_first_bar_rule_and_gap():
    bars, sessions = _one_day()
    bars = bars.drop(index=[50, 51, 52]).reset_index(drop=True)   # missing minutes 50-52
    minutes, dq, _ = clean(bars, sessions)
    first = minutes.iloc[0]
    assert first["tau"] == 0 and np.isclose(first["r"], np.log(first["close"] / first["open"]))
    row = minutes.loc[minutes["tau"] == 53].iloc[0]
    assert row["gap"] == 4
    c49 = minutes.loc[minutes["tau"] == 49, "close"].iloc[0]
    assert np.isclose(row["r"], np.log(row["close"] / c49))
    assert dq.iloc[0]["n_missing"] == 3 and dq.iloc[0]["max_gap"] == 4


def test_out_of_hours_offgrid_and_duplicates():
    bars, sessions = _one_day()
    extra = bars.iloc[[0, 0, 0]].copy()
    extra["ts"] = [bars["ts"].iloc[0] - pd.Timedelta(minutes=5),          # pre-market
                   bars["ts"].iloc[-1] + pd.Timedelta(minutes=1),         # 16:00 bar
                   bars["ts"].iloc[10] + pd.Timedelta(seconds=30)]        # off-grid
    dup = bars.iloc[[20]].copy()
    allb = pd.concat([bars, extra, dup], ignore_index=True)
    minutes, dq, stats = clean(allb, sessions)
    assert len(minutes) == 390
    assert stats["bars_outside_rth"] == 2 and stats["bars_off_minute_grid"] == 1
    assert dq.iloc[0]["n_dupes"] == 1


def test_bad_print_is_flagged_and_can_be_dropped():
    bars, sessions = _one_day()
    t = 150
    bars.loc[t, ["open", "high", "low", "close"]] *= 1.02          # off-market print
    minutes, dq, _ = clean(bars, sessions)
    assert bool(minutes.loc[minutes["tau"] == t, "spike"].iloc[0])
    assert dq.iloc[0]["n_spikes"] == 1

    dropped, dq2, _ = clean(bars, sessions, drop_spikes=True)
    assert t not in set(dropped["tau"])
    row = dropped.loc[dropped["tau"] == t + 1].iloc[0]
    c_prev = dropped.loc[dropped["tau"] == t - 1, "close"].iloc[0]
    assert row["gap"] == 2 and np.isclose(row["r"], np.log(row["close"] / c_prev))


def test_half_day_session_length():
    s = synthetic_sessions(["2015-11-27"], n_minutes=210)
    assert bool(s["half_day"].iloc[0]) and s["n_minutes"].iloc[0] == 210


def test_dq_report_writes(tmp_path):
    from fai.clean import write_dq_report
    from fai.sessions import day_flags

    rng = np.random.default_rng(6)
    bars, sessions, _ = simulate_panel(rng, 5)
    bars.loc[700, ["open", "high", "low", "close"]] *= 1.02
    minutes, dq, stats = clean(bars, sessions)
    path = write_dq_report(dq, stats, day_flags(sessions.index), "SIM", tmp_path)
    text = path.read_text()
    assert "Spike-and-revert bars flagged: 1" in text
    assert "dropped from all tests): 0." in text            # D-016: no outage days
    assert (tmp_path / "dq_SIM.csv").exists()


def test_genuine_whipsaw_is_not_flagged():
    """A crash-style V (big drop, big rebound) whose closes sit inside neighbouring
    ranges is real trading, not a bad print (modelled on SPY, 2010-05-06 14:44-14:47)."""
    bars, sessions = _one_day()
    p = bars.loc[198, "close"]
    v = {199: (1.000, 1.010, 0.960, 0.970),   # open, high, low, close as multiples of p
         200: (0.970, 1.000, 0.940, 0.995),   # +2.5% into a wide-range minute
         201: (0.995, 1.000, 0.950, 0.972)}   # -2.3%: the next minute undoes most of it
    for t, mult in v.items():
        bars.loc[t, ["open", "high", "low", "close"]] = [p * m for m in mult]
    minutes, dq, _ = clean(bars, sessions)
    assert not minutes.loc[minutes["tau"].between(199, 202), "spike"].any()
    assert dq.iloc[0]["n_spikes"] == 0


# --- D-016: vendor-outage days ------------------------------------------------

def _day_missing(taus, start="2015-01-05", seed=7):
    """One simulated day with the bars at ``taus`` removed; returns its dq row."""
    bars, sessions, _ = simulate_panel(np.random.default_rng(seed), 1, start=start)
    bars = bars.loc[~bars.index.isin(list(taus))].reset_index(drop=True)
    _, dq, _ = clean(bars, sessions)
    return dq.iloc[0]


def test_outage_threshold_is_strictly_more_than_30_minutes():
    scattered = range(40, 340, 10)                          # 30 single missing minutes
    assert _day_missing(scattered)["n_missing_unexplained"] == 30
    assert not _day_missing(scattered)["outage"]            # exactly 30: kept
    assert _day_missing([*scattered, 345])["outage"]        # 31: dropped


def test_missing_opening_block_is_an_outage():
    """Modelled on 2021-04-12: the opening minutes are gone, so the first-bar rule
    (D-002) would start the day late and the opening move would be lost."""
    row = _day_missing(range(0, 40))
    assert row["first_tau"] == 40 and row["n_missing"] == 40 and row["outage"]


def test_market_halt_explains_only_its_own_pause():
    halt = range(4, 19)                                     # 15 bars missing, gap of 16
    on_halt_day = _day_missing([*halt, *range(100, 400, 15)], start="2020-03-09")
    assert on_halt_day["n_missing_halt"] == 15
    assert on_halt_day["n_missing_unexplained"] == 20 and not on_halt_day["outage"]
    # The same 35 missing minutes on an ordinary day are not explained by anything.
    ordinary = _day_missing([*halt, *range(100, 400, 15)], start="2020-03-10")
    assert ordinary["n_missing_halt"] == 0 and ordinary["outage"]
    # A long outage on a halt day is excused only for the 15-minute pause.
    long_gap = _day_missing(range(100, 152), start="2020-03-09")
    assert long_gap["n_missing_halt"] == 15 and long_gap["n_missing_unexplained"] == 37
    assert long_gap["outage"]


def test_session_with_no_data_is_an_outage():
    bars, sessions, _ = simulate_panel(np.random.default_rng(8), 2)
    bars = bars.loc[bars["ts"].dt.tz_localize(None).dt.normalize() == sessions.index[0]]
    _, dq, _ = clean(bars, sessions)
    assert not dq["outage"].iloc[0]
    assert dq["no_data"].iloc[1] and dq["outage"].iloc[1]
