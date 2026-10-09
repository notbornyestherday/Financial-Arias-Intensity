"""Trading sessions and day-level flags.

Named sessions.py rather than calendar.py to avoid shadowing the stdlib module.
"""

from __future__ import annotations

import warnings

import pandas as pd

from . import config


def _finish(s: pd.DataFrame) -> pd.DataFrame:
    s = s.copy()
    s["n_minutes"] = ((s["close"] - s["open"]) / pd.Timedelta(minutes=1)).astype(int)
    s["half_day"] = s["n_minutes"] < config.FULL_DAY_MINUTES
    s.index.name = "date"
    return s


def nyse_sessions(start: str, end: str) -> pd.DataFrame:
    """NYSE sessions between start and end (inclusive).

    Returns a DataFrame indexed by naive session date with columns
    open, close (tz-aware, America/New_York), n_minutes, half_day.
    Early closes and special closures (e.g. Hurricane Sandy) come from
    pandas_market_calendars rather than a hand-maintained list.
    """
    try:
        import pandas_market_calendars as mcal
    except ImportError as exc:  # pragma: no cover
        raise ImportError("pip install pandas_market_calendars") from exc

    sched = mcal.get_calendar("NYSE").schedule(start_date=start, end_date=end)
    out = pd.DataFrame(
        {
            "open": sched["market_open"].dt.tz_convert(config.TZ),
            "close": sched["market_close"].dt.tz_convert(config.TZ),
        }
    )
    out.index = pd.DatetimeIndex(sched.index).tz_localize(None).normalize()
    return _finish(out)


def synthetic_sessions(dates, n_minutes: int = config.FULL_DAY_MINUTES) -> pd.DataFrame:
    """Sessions opening 09:30 ET for an arbitrary list of dates (used by sim/tests)."""
    idx = pd.DatetimeIndex(dates).normalize()
    if idx.tz is not None:
        idx = idx.tz_localize(None)
    open_ = (idx + pd.Timedelta(hours=9, minutes=30)).tz_localize(config.TZ)
    out = pd.DataFrame(
        {"open": open_, "close": open_ + pd.Timedelta(minutes=n_minutes)}, index=idx
    )
    return _finish(out)


def _load_ref(name: str) -> pd.DataFrame:
    path = config.REF / name
    if not path.exists():
        warnings.warn(f"{path} missing; its flags will be empty", stacklevel=3)
        return pd.DataFrame(columns=["date"]).set_index("date")
    df = pd.read_csv(path, comment="#", dtype={"time_et": str})
    if df.empty:
        warnings.warn(f"ref/{name} has no rows; its flags are empty", stacklevel=3)
    df["date"] = pd.to_datetime(df["date"])
    return df.set_index("date")


def load_fomc_dates(rth_only: bool = True) -> pd.DataFrame:
    """FOMC statements from ref/fomc_dates.csv (columns: date,time_et,type,in_rth,notes).

    By default only releases inside regular hours, which is what defines an FOMC day.
    """
    df = _load_ref("fomc_dates.csv")
    if rth_only and "in_rth" in df.columns:
        df = df[df["in_rth"].astype(bool)]
    return df


def load_macro_dates() -> pd.DataFrame:
    """ISM release days from ref/macro_dates.csv (columns: date,time_et,release,certain,notes)."""
    return _load_ref("macro_dates.csv")


def day_flags(dates) -> pd.DataFrame:
    """Boolean/label flags for each session date."""
    idx = pd.DatetimeIndex(dates)
    events = {pd.Timestamp(k): v for k, v in config.EVENTS.items()}
    halts = set(pd.to_datetime(config.MARKET_HALT_DAYS))
    prints = set(pd.to_datetime(config.PRINT_QUALITY_DAYS))
    fomc = set(load_fomc_dates().index)
    macro = set(load_macro_dates().index)
    return pd.DataFrame(
        {
            "event": [events.get(d, "") for d in idx],
            "market_halt": [d in halts for d in idx],
            "print_quality": [d in prints for d in idx],
            "fomc": [d in fomc for d in idx],
            "macro_release": [d in macro for d in idx],
        },
        index=idx,
    )
