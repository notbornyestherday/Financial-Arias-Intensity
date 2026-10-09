"""Canonical bars -> regular-hours minute returns + data-quality report.

Return rules (DECISIONS.md D-002, D-003):
* Only bars inside the session [open, close) are used; overnight returns are excluded.
* The first bar of the day contributes ln(close/open) of that bar, so the opening
  burst is kept but the overnight gap is not.
* Every later bar contributes ln(close_t / close_prev), where prev is the previous
  bar *present*. ``gap`` records how many minutes that return spans (1 normally,
  >1 across halts or missing bars). Seasonality handles gap>1 (seasonality.py).
* Suspect prints are flagged, never silently deleted. ``drop_spikes=True`` removes
  the flagged bars and recomputes returns across them, for robustness runs.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from . import config

MINUTE = pd.Timedelta(minutes=1)


def attach_sessions(bars: pd.DataFrame, sessions: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Keep regular-hours, on-grid bars and add date / tau (minutes since open)."""
    b = bars.copy()
    b["date"] = b["ts"].dt.tz_localize(None).dt.normalize()
    s = sessions[["open", "n_minutes"]].rename(columns={"open": "sess_open"})
    n_in = len(b)
    b = b.join(s, on="date", how="inner")
    n_session_days = len(b)
    tau = (b["ts"] - b["sess_open"]) / MINUTE
    on_grid = np.isclose(tau, np.round(tau))
    b["tau"] = np.round(tau).astype(int)
    rth = (b["tau"] >= 0) & (b["tau"] < b["n_minutes"])
    stats = {
        "bars_in": n_in,
        "bars_not_on_session_dates": n_in - n_session_days,
        "bars_off_minute_grid": int((~on_grid).sum()),
        "bars_outside_rth": int((on_grid & ~rth).sum()),
    }
    b = b.loc[on_grid & rth].drop(columns=["sess_open"])
    return b.reset_index(drop=True), stats


def count_duplicates(rth: pd.DataFrame) -> pd.Series:
    """Bars per day that share a (date, tau) with a later bar; compute_returns keeps the last."""
    return rth.duplicated(["date", "tau"], keep="last").groupby(rth["date"]).sum()


def compute_returns(rth: pd.DataFrame) -> pd.DataFrame:
    """Add r (log return ending at this bar) and gap (minutes spanned); drop duplicate bars.

    Nothing is stored in DataFrame.attrs: parquet writes attrs as JSON and fails on
    anything that is not plain JSON (a Series, for instance).
    """
    df = rth.sort_values(["date", "tau"], kind="stable")
    df = df.loc[~df.duplicated(["date", "tau"], keep="last")].copy()

    g = df.groupby("date", sort=False)
    prev_close = g["close"].shift(1)
    prev_tau = g["tau"].shift(1)
    first = prev_close.isna()

    with np.errstate(divide="ignore", invalid="ignore"):
        r_cc = np.log(df["close"]) - np.log(prev_close)
        r_first = np.log(df["close"]) - np.log(df["open"])
    df["r"] = r_cc.where(~first, r_first)
    df["gap"] = (df["tau"] - prev_tau).where(~first, 1).astype(int)
    df["ohlc_bad"] = (
        (df[["open", "high", "low", "close"]] <= 0).any(axis=1)
        | (df["high"] < df[["open", "close"]].max(axis=1))
        | (df["low"] > df[["open", "close"]].min(axis=1))
        | (df["volume"] < 0)
    )
    return df.reset_index(drop=True)


def flag_spikes(df: pd.DataFrame, z: float = config.SPIKE_Z,
                revert_frac: float = config.SPIKE_REVERT_FRAC) -> pd.Series:
    """Flag suspected bad prints: an isolated close that the next minute undoes.

    All three must hold:
    * the return into the bar is more than ``z`` robust SDs (1.4826 * MAD of the day's
      single-minute returns);
    * the next minute reverses at least (1 - revert_frac) of it;
    * the bar's close lies outside the combined high-low range of the bars on either
      side. Returns are close-to-close, so only a bad close can distort them.

    The third condition is what separates a bad print from a genuine liquidity
    whipsaw: on 2010-05-06 the crash minutes are huge and reverse, but each close sits
    inside its neighbours' ranges, because the market really traded there (D-014).
    """
    one = df["r"].where(df["gap"] == 1)
    med = one.groupby(df["date"]).transform("median")
    mad = (one - med).abs().groupby(df["date"]).transform("median")
    scale = (1.4826 * mad).replace(0, np.nan)
    zt = df["r"] / scale
    g = df.groupby("date", sort=False)
    z_next = zt.groupby(df["date"]).shift(-1)
    gap_next = g["gap"].shift(-1)
    nb_high = pd.concat([g["high"].shift(1), g["high"].shift(-1)], axis=1).max(axis=1)
    nb_low = pd.concat([g["low"].shift(1), g["low"].shift(-1)], axis=1).min(axis=1)
    isolated = (df["close"] > nb_high) | (df["close"] < nb_low)
    return (
        (zt.abs() > z)
        & (gap_next == 1)
        & (np.sign(z_next) == -np.sign(zt))
        & ((zt + z_next).abs() < revert_frac * zt.abs())
        & isolated
    ).fillna(False)


def clean(bars: pd.DataFrame, sessions: pd.DataFrame, drop_spikes: bool = False
          ) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Full cleaning pass. Returns (minutes, dq_by_day, summary_stats)."""
    rth, stats = attach_sessions(bars, sessions)
    n_dupes = count_duplicates(rth)
    df = compute_returns(rth)
    df["spike"] = flag_spikes(df)
    if drop_spikes and df["spike"].any():
        df = compute_returns(df.loc[~df["spike"], rth.columns])
        df["spike"] = False
    dq = quality_by_day(df, sessions, n_dupes)
    stats["sessions"] = len(sessions)
    stats["sessions_without_data"] = int(dq["no_data"].sum())
    return df, dq, stats


def quality_by_day(df: pd.DataFrame, sessions: pd.DataFrame,
                   n_dupes: pd.Series | None = None) -> pd.DataFrame:
    g = df.groupby("date")
    dq = pd.DataFrame(index=sessions.index)
    dq["n_expected"] = sessions["n_minutes"]
    dq["half_day"] = sessions["half_day"]
    dq["n_bars"] = g.size().reindex(dq.index).fillna(0).astype(int)
    dq["n_missing"] = dq["n_expected"] - dq["n_bars"]
    dq["max_gap"] = g["gap"].max().reindex(dq.index)
    dq["first_tau"] = g["tau"].min().reindex(dq.index)
    dq["last_tau"] = g["tau"].max().reindex(dq.index)
    dq["n_dupes"] = (n_dupes if n_dupes is not None else pd.Series(dtype=int)
                     ).reindex(dq.index).fillna(0).astype(int)
    dq["n_spikes"] = g["spike"].sum().reindex(dq.index).fillna(0).astype(int)
    dq["n_ohlc_bad"] = g["ohlc_bad"].sum().reindex(dq.index).fillna(0).astype(int)
    r2 = df["r"] ** 2
    dq["max_share_raw"] = (r2.groupby(df["date"]).max()
                           / r2.groupby(df["date"]).sum()).reindex(dq.index)
    dq["no_data"] = dq["n_bars"] == 0
    return dq


def write_dq_report(dq: pd.DataFrame, stats: dict, flags: pd.DataFrame,
                    symbol: str, out_dir: Path | None = None) -> Path:
    """Write reports/dq_<symbol>.csv and a short markdown summary."""
    out_dir = Path(out_dir) if out_dir is not None else config.REPORTS
    out_dir.mkdir(parents=True, exist_ok=True)
    full = dq.join(flags)
    full.to_csv(out_dir / f"dq_{symbol}.csv")
    have = full.loc[~full["no_data"]]
    full_days = have.loc[~have["half_day"]]

    def table(frame: pd.DataFrame, cols: list[str]) -> str:
        frame = frame[cols].round(3).reset_index()[["date", *cols]]
        frame["date"] = frame["date"].dt.date
        head = "| " + " | ".join(frame.columns) + " |"
        sep = "|" + "---|" * len(frame.columns)
        rows = ["| " + " | ".join(str(v) for v in row) + " |" for row in frame.to_numpy()]
        return "\n".join([head, sep, *rows])

    lines = [
        f"# Data-quality report: {symbol}",
        "",
        f"Sessions in calendar: {stats['sessions']}; with no data: {stats['sessions_without_data']}.",
        f"Bars read: {stats['bars_in']}; outside RTH: {stats['bars_outside_rth']}; "
        f"off the minute grid: {stats['bars_off_minute_grid']}; "
        f"on non-session dates: {stats['bars_not_on_session_dates']}.",
        f"Full days with any missing minute: {(full_days['n_missing'] > 0).sum()} "
        f"of {len(full_days)}; half-days: {int(have['half_day'].sum())}.",
        f"Spike-and-revert bars flagged: {int(have['n_spikes'].sum())} on "
        f"{int((have['n_spikes'] > 0).sum())} days. OHLC-inconsistent bars: "
        f"{int(have['n_ohlc_bad'].sum())}. Duplicate timestamps: {int(have['n_dupes'].sum())}.",
        "",
        "## Days where one minute holds the most energy (raw returns)",
        "W50 and D5-95 are fragile on these; check each against the event list.",
        "",
        table(have.nlargest(20, "max_share_raw"),
              ["max_share_raw", "n_spikes", "event", "half_day"]),
        "",
        "## Largest gaps (halts, missing bars)",
        "",
        table(have.nlargest(20, "max_gap"), ["max_gap", "n_missing", "event", "market_halt"]),
        "",
        "## Flagged days",
        "",
        table(full.loc[(full["event"] != "") | full["market_halt"] | full["print_quality"]],
              ["n_bars", "n_missing", "max_gap", "n_spikes", "max_share_raw", "event"]),
        "",
    ]
    path = out_dir / f"dq_{symbol}.md"
    path.write_text("\n".join(lines))
    return path
