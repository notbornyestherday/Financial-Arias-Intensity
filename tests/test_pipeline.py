"""End-to-end: simulated Alpha Vantage files -> every run_all.py stage.

Uses the real NYSE calendar and real parquet files, so anything that only breaks when
outputs are written to disk (as the DataFrame.attrs bug did) fails here first.
"""

import importlib.util
import json
from argparse import Namespace
from pathlib import Path

import numpy as np
import pandas as pd

from fai import config
from fai.clean import clean
from fai.sessions import nyse_sessions
from fai.sim import Burst, simulate_day

ROOT = Path(__file__).resolve().parents[1]
MINUTE = pd.Timedelta(minutes=1)


def _load_run_all():
    spec = importlib.util.spec_from_file_location("run_all", ROOT / "scripts" / "run_all.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _simulated_bars(sessions, rng, burst_day=None):
    """Bars on real NYSE sessions, cut at each session's close (half-days included)."""
    frames, p = [], 200.0
    for d, row in sessions.iterrows():
        kw = {"bursts": [Burst(200, 15, 12.0)]} if d == burst_day else {}
        bars, _ = simulate_day(rng, p0=p * np.exp(0.008 * rng.standard_normal()), **kw)
        bars = bars.loc[bars["tau"] < row["n_minutes"]].copy()
        bars["ts"] = row["open"] + bars["tau"] * MINUTE
        frames.append(bars)
        p = float(bars["close"].iloc[-1])
    return pd.concat(frames, ignore_index=True)


def _write_alphavantage(bars, out_dir):
    """Monthly CSVs in Alpha Vantage's layout: newest first, naive Eastern timestamps."""
    out_dir.mkdir(parents=True, exist_ok=True)
    b = bars.copy()
    b["timestamp"] = b["ts"].dt.tz_localize(None).dt.strftime("%Y-%m-%d %H:%M:%S")
    for month, g in b.groupby(b["ts"].dt.strftime("%Y-%m")):
        cols = ["timestamp", "open", "high", "low", "close", "volume"]
        g.sort_values("ts", ascending=False)[cols].to_csv(out_dir / f"SPY_{month}.csv", index=False)


def test_minutes_attrs_are_json_safe():
    sessions = nyse_sessions("2015-11-02", "2015-11-06")
    bars = _simulated_bars(sessions, np.random.default_rng(0))
    minutes, _, _ = clean(bars, sessions)
    json.dumps(minutes.attrs)  # parquet serialises attrs as JSON


def test_run_all_end_to_end(tmp_path, monkeypatch):
    for name in ("RAW", "INTERIM", "PROCESSED", "REPORTS"):
        monkeypatch.setattr(config, name, tmp_path / name.lower())

    # ~125 sessions; both half-days (Nov 27, Dec 24) fall after the 40-day seasonality warm-up
    sessions = nyse_sessions("2015-09-01", "2016-02-29")
    burst_day = sessions.index[100]
    bars = _simulated_bars(sessions, np.random.default_rng(1), burst_day=burst_day)
    _write_alphavantage(bars, config.RAW / "alphavantage" / "SPY")

    run_all = _load_run_all()
    args = Namespace(vendor="alphavantage", symbol="SPY", raw=None, member=None,
                     bar_label="auto", drop_spikes=False)
    run_all.stage_ingest(args)
    run_all.stage_clean(args)
    run_all.stage_measures(args)

    interim = pd.read_parquet(config.INTERIM / "SPY_1min.parquet")
    assert len(interim) == len(bars)

    minutes = pd.read_parquet(config.PROCESSED / "SPY_minutes.parquet")
    assert len(minutes) == len(bars)                        # nothing outside regular hours
    half = pd.Timestamp("2015-11-27")
    assert (minutes["date"] == half).sum() == 210           # 09:30-13:00 only

    report = (config.REPORTS / "dq_SPY.md").read_text()
    assert f"Sessions in calendar: {len(sessions)}; with no data: 0." in report

    daily = pd.read_parquet(config.PROCESSED / "SPY_daily.parquet")
    assert len(daily) == len(sessions)
    assert bool(daily.at[half, "half_day"]) and daily.at[half, "n_obs"] == 210
    assert daily["d5_95"].iloc[:40].isna().all()           # warm-up: no prior seasonality
    assert daily["d5_95"].iloc[40:].notna().all()
    calm_w50 = daily["w50"].iloc[45:99].median()
    assert daily.at[burst_day, "w50"] < 20 < calm_w50
