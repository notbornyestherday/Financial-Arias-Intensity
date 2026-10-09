"""Checks the real NYSE calendar (pandas_market_calendars) against known dates."""

import pandas as pd

from fai.sessions import nyse_sessions


def test_known_holiday_and_half_days():
    s = nyse_sessions("2015-11-20", "2015-12-31")
    assert pd.Timestamp("2015-11-26") not in s.index             # Thanksgiving: closed
    assert s.at[pd.Timestamp("2015-11-27"), "n_minutes"] == 210  # closes 13:00
    assert s.at[pd.Timestamp("2015-12-24"), "n_minutes"] == 210  # closes 13:00
    assert bool(s.at[pd.Timestamp("2015-12-24"), "half_day"])
    assert s.at[pd.Timestamp("2015-11-30"), "n_minutes"] == 390
    assert s.at[pd.Timestamp("2015-11-30"), "open"].strftime("%H:%M") == "09:30"
    assert str(s["open"].dt.tz) == "America/New_York"


def test_hurricane_sandy_closure():
    s = nyse_sessions("2012-10-26", "2012-11-01")
    assert pd.Timestamp("2012-10-29") not in s.index
    assert pd.Timestamp("2012-10-30") not in s.index
    assert pd.Timestamp("2012-10-31") in s.index
