"""Vendor files -> canonical 1-minute bars.

Canonical schema: ts (tz-aware America/New_York, labelled at bar START),
open, high, low, close, volume. Everything downstream assumes start labels.
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from . import config

CANON = ["ts", "open", "high", "low", "close", "volume"]


class VendorError(RuntimeError):
    """Vendor returned something other than bar data."""


def _canon(df: pd.DataFrame) -> pd.DataFrame:
    df = df[CANON].copy()
    for c in CANON[1:]:
        df[c] = pd.to_numeric(df[c], errors="coerce").astype(float)
    return df.sort_values("ts", kind="stable").reset_index(drop=True)


def _localize(ts: pd.Series) -> pd.Series:
    ts = pd.to_datetime(ts)
    if ts.dt.tz is None:
        return ts.dt.tz_localize(config.TZ)
    return ts.dt.tz_convert(config.TZ)


# --- Alpha Vantage -------------------------------------------------------------

def parse_alphavantage_csv(text: str) -> pd.DataFrame:
    """Parse one TIME_SERIES_INTRADAY response (datatype=csv)."""
    head = text.lstrip()
    if head.startswith("{") or not head.lower().startswith("timestamp"):
        raise VendorError(f"Expected CSV bars, got: {head[:300]!r}")
    df = pd.read_csv(io.StringIO(text))
    df.columns = [c.strip().lower() for c in df.columns]
    df = df.rename(columns={"timestamp": "ts"})
    df["ts"] = _localize(df["ts"])
    return _canon(df)


def load_alphavantage_dir(path: Path) -> pd.DataFrame:
    files = sorted(Path(path).glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"No CSVs in {path}")
    return _canon(pd.concat([parse_alphavantage_csv(f.read_text()) for f in files]))


# --- FirstRate -----------------------------------------------------------------

def parse_firstrate(buf) -> pd.DataFrame:
    """Parse a FirstRate 1-minute text/CSV file, with or without a header row."""
    df = pd.read_csv(buf, header=None)
    if pd.isna(pd.to_datetime(str(df.iloc[0, 0]), errors="coerce")):
        df = df.iloc[1:]
    df = df.iloc[:, :6]
    df.columns = CANON
    df["ts"] = _localize(df["ts"])
    return _canon(df)


def load_firstrate(path: Path, member: str | None = None) -> pd.DataFrame:
    path = Path(path)
    if path.suffix.lower() != ".zip":
        return parse_firstrate(path)
    with zipfile.ZipFile(path) as zf:
        names = [n for n in zf.namelist() if not n.endswith("/")]
        if member is None:
            cands = [n for n in names if "1min" in n.lower()] or names
            if len(cands) != 1:
                raise ValueError(f"Pick a member with --member; candidates: {cands}")
            member = cands[0]
        with zf.open(member) as fh:
            return parse_firstrate(io.TextIOWrapper(fh))


# --- Cboe VIX ------------------------------------------------------------------

def load_cboe_vix(path: Path) -> pd.DataFrame:
    """Cboe VIX_History.csv -> DataFrame indexed by date with open/high/low/close."""
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    df["date"] = pd.to_datetime(df["date"])
    return df.set_index("date")[["open", "high", "low", "close"]].sort_index()


# --- Bar timestamp convention --------------------------------------------------

def bar_label_diagnostics(bars: pd.DataFrame) -> dict:
    """Evidence for whether timestamps mark the start or the end of each bar.

    RTH-only data: start-labelled bars run 09:30..15:59, end-labelled 09:31..16:00.
    With extended hours both 09:30 and 16:00 exist, so presence is not decisive;
    the median-volume profile around the open and close is returned for eyeballing,
    and ``guess`` is "unknown". Confirm against the vendor's documentation.
    """
    t = bars["ts"].dt
    hm = t.hour * 60 + t.minute
    date = t.tz_localize(None).dt.normalize()
    days = date.nunique()
    has_ext = bool(((hm < 570) | (hm > 960)).any())
    frac = lambda m: float(date[hm == m].nunique()) / max(days, 1)
    vol = bars.groupby(hm)["volume"].median()
    profile = {f"{m // 60:02d}:{m % 60:02d}": float(vol.get(m, np.nan))
               for m in [568, 569, 570, 571, 572, 957, 958, 959, 960, 961]}
    guess = "unknown"
    if not has_ext:
        f930, f1600 = frac(570), frac(960)
        if f930 > 0.9 and f1600 < 0.1:
            guess = "start"
        elif f1600 > 0.9 and f930 < 0.1:
            guess = "end"
    return {
        "guess": guess,
        "has_extended_hours": has_ext,
        "frac_days_with_0930": frac(570),
        "frac_days_with_1600": frac(960),
        "median_volume_by_minute": profile,
    }


def to_bar_start(bars: pd.DataFrame, label: str) -> pd.DataFrame:
    if label not in {"start", "end"}:
        raise ValueError("label must be 'start' or 'end'")
    out = bars.copy()
    if label == "end":
        out["ts"] = out["ts"] - pd.Timedelta(minutes=1)
    return out
