"""Checks on the hand-compiled and generated reference calendars (D-017)."""

import importlib.util
from pathlib import Path

import pandas as pd

from fai.sessions import day_flags, load_fomc_dates, load_macro_dates, nyse_sessions

ROOT = Path(__file__).resolve().parents[1]


def _builder():
    spec = importlib.util.spec_from_file_location("bmd", ROOT / "scripts" / "build_macro_dates.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_fomc_scheduled_meetings_per_year():
    df = load_fomc_dates(rth_only=False)
    counts = df[df["type"] == "scheduled"].groupby(df[df["type"] == "scheduled"].index.year).size()
    assert list(counts.index) == list(range(2009, 2026))
    for year, n in counts.items():
        assert n == (7 if year == 2020 else 8), year      # March 2020 meeting was cancelled


def test_fomc_release_time_by_era():
    df = load_fomc_dates(rth_only=False)
    s = df[df["type"] == "scheduled"]
    assert (s.loc[:"2013-01-31", "time_et"].isin(["14:15", "12:30"])).all()
    assert (s.loc["2013-03-01":, "time_et"] == "14:00").all()
    assert set(s[s["time_et"] == "12:30"].index.year) == {2011, 2012}


def test_fomc_regular_hours_rows_are_trading_days_and_in_hours():
    df = load_fomc_dates(rth_only=True)
    sessions = nyse_sessions("2009-01-01", "2025-12-31")
    assert df.index.isin(sessions.index).all()
    assert df["time_et"].between("09:30", "15:59").all()
    assert {"2019-10-11", "2020-03-03", "2025-08-22"} <= set(df.index.strftime("%Y-%m-%d"))
    assert pd.Timestamp("2020-03-23") not in df.index        # 8:00 am, before the open


def test_ism_rule_matches_published_2026_schedule():
    published = {  # ismworld.org release calendar, 2026
        "ISM Manufacturing": ["01-05", "02-02", "03-02", "04-01", "05-01", "06-01",
                              "07-01", "08-03", "09-01", "10-01", "11-02", "12-01"],
        "ISM Services": ["01-07", "02-04", "03-04", "04-06", "05-05", "06-03",
                         "07-06", "08-05", "09-03", "10-05", "11-04", "12-03"],
    }
    b = _builder()
    for release, dates in published.items():
        for month, md in enumerate(dates, start=1):
            cands = b.candidates(2026, month, b.RELEASES[release])
            assert pd.Timestamp(f"2026-{md}") in cands, (release, md, cands)
            if month != 1 and not (release == "ISM Services" and month == 4):
                assert len(cands) == 1, (release, month, cands)


def test_ism_dated_historical_releases_are_listed():
    df = load_macro_dates()
    known = [("2015-02-04", "ISM Services"),        # release PDF: "FOR RELEASE: February 4, 2015"
             ("2017-01-03", "ISM Manufacturing"),   # December 2016 report
             ("2018-07-05", "ISM Services"),        # June 2018 report, after July 4
             ("2021-01-05", "ISM Manufacturing")]   # December 2020 report; Jan 4 was skipped
    for d, release in known:
        rows = df.loc[[pd.Timestamp(d)]] if pd.Timestamp(d) in df.index else df.iloc[:0]
        assert (rows["release"] == release).any(), (d, release)


def test_ism_file_matches_generator():
    b = _builder()
    fresh = b.build(2009, 2025)
    on_disk = load_macro_dates().reset_index()
    assert len(fresh) == len(on_disk)
    assert (fresh["date"].values == on_disk["date"].dt.strftime("%Y-%m-%d").values).all()


def test_day_flags_use_the_calendars():
    f = day_flags(pd.to_datetime(["2013-09-18", "2020-03-23", "2012-05-01", "2012-05-02"]))
    assert f["fomc"].tolist() == [True, False, False, False]
    assert f["macro_release"].tolist() == [False, False, True, False]
