import io

import pandas as pd

from fai.ingest import (VendorError, bar_label_diagnostics, parse_alphavantage_csv,
                        parse_firstrate, to_bar_start)


def _rth_bars(label: str, days=("2016-03-01", "2016-03-02")) -> pd.DataFrame:
    rows = []
    for d in days:
        start = pd.Timestamp(f"{d} 09:30", tz="America/New_York")
        offset = 0 if label == "start" else 1
        for i in range(390):
            rows.append((start + pd.Timedelta(minutes=i + offset), 1, 1, 1, 1, 100))
    return pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close", "volume"])


def test_alphavantage_csv_parses_and_sorts():
    text = ("timestamp,open,high,low,close,volume\n"
            "2010-05-06 09:31:00,116.1,116.2,116.0,116.1,1000\n"
            "2010-05-06 09:30:00,116.0,116.3,115.9,116.1,2000\n")
    df = parse_alphavantage_csv(text)
    assert list(df.columns) == ["ts", "open", "high", "low", "close", "volume"]
    assert str(df["ts"].dt.tz) == "America/New_York"
    assert df["ts"].is_monotonic_increasing


def test_alphavantage_error_message_raises():
    try:
        parse_alphavantage_csv('{"Information": "Thank you for using Alpha Vantage!"}')
    except VendorError:
        return
    raise AssertionError("expected VendorError")


def test_firstrate_with_and_without_header():
    body = "2010-05-06 09:30:00,116.0,116.3,115.9,116.1,2000\n"
    a = parse_firstrate(io.StringIO(body))
    b = parse_firstrate(io.StringIO("timestamp,open,high,low,close,volume\n" + body))
    pd.testing.assert_frame_equal(a, b)


def test_bar_label_guess_on_rth_only_data():
    assert bar_label_diagnostics(_rth_bars("start"))["guess"] == "start"
    assert bar_label_diagnostics(_rth_bars("end"))["guess"] == "end"
    shifted = to_bar_start(_rth_bars("end"), "end")
    assert shifted["ts"].dt.strftime("%H:%M").iloc[0] == "09:30"
