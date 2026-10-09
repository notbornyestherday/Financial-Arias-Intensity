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
    assert (tmp_path / "dq_SIM.csv").exists()
