#!/usr/bin/env python
"""Event detection on the full sample, placebo days, and the event table (D-032).

Exploratory (HYPOTHESES.md lists "event-detection windows" under exploratory); nothing
here changes an H1 or H2 verdict.

* Detection (fai.detection) runs on every session; days in the tests (2010-2025) are
  reported.
* Placebo days: for each named day in config.EVENTS, the 5 test days closest in ln RV,
  leaving out named days and the 10 sessions either side of any named day.
* Event table: named and placebo days side by side; and the share of all test days with
  at least one detected event, by RV decile (how often the detector fires on days that
  nobody remembers).

Uses the primary files (flagged prints removed, D-005). Writes reports/event_table.md,
reports/event_table.csv and reports/events_all.csv.

    python scripts/event_table.py
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fai import config  # noqa: E402
from fai.detection import detect_events  # noqa: E402

_spec = importlib.util.spec_from_file_location("h1", ROOT / "scripts" / "h1_tests.py")
h1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(h1)

N_PLACEBO = 5
GAP_SESSIONS = 10


def clock(tau) -> str:
    if not np.isfinite(tau):
        return ""
    m = 30 + int(tau)
    return f"{9 + m // 60}:{m % 60:02d}"


def placebo_days(d: pd.DataFrame, named, calendar, k: int = N_PLACEBO,
                 gap: int = GAP_SESSIONS) -> pd.DataFrame:
    """For each named day, the k test days closest in ln RV, outside every named day's
    +/- ``gap`` sessions (``calendar`` is the full list of sessions). One row per match."""
    named = pd.DatetimeIndex(named)
    pos = pd.Series(np.arange(len(calendar)), index=pd.DatetimeIndex(calendar))
    blocked = set()
    for p in pos.reindex(named).dropna().astype(int):
        blocked.update(range(p - gap, p + gap + 1))
    cand = d.loc[~d.index.isin(named) & ~pos.reindex(d.index).isin(blocked).to_numpy()]
    rows = []
    for nd in named:
        dist = (np.log(cand["rv"]) - np.log(d.at[nd, "rv"])).abs().nsmallest(k)
        for rank, day in enumerate(dist.index, 1):
            rows.append({"for": nd, "day": day, "rank": rank,
                         "rv_ratio": d.at[day, "rv"] / d.at[nd, "rv"]})
    return pd.DataFrame(rows)


def detection_by_decile(d: pd.DataFrame) -> pd.DataFrame:
    g = d.dropna(subset=["n_events"]).groupby("rv_decile")
    out = pd.DataFrame({"days": g.size(),
                        "share_with_event": g["n_events"].apply(lambda x: float((x > 0).mean())),
                        "mean_events": g["n_events"].mean(),
                        "mean_energy_share_in_events": g["energy_share_events"].mean()})
    out.index = out.index + 1
    return out


def build(daily: pd.DataFrame, summary: pd.DataFrame, calendar) -> dict:
    d = h1.test_sample(daily).join(summary, how="left")
    d["q_w50"] = h1.decile_percentile(d, "w50")
    named = pd.DatetimeIndex(sorted(config.EVENTS))
    missing = [str(x.date()) for x in named if x not in d.index]
    if missing:
        raise ValueError(f"named days not in the test sample: {missing}")
    pl = placebo_days(d, named, calendar)
    cols = ["rv", "rv_decile", "w50", "q_w50", "d5_75", "vr_skip2", "f_bar", "n_events",
            "largest_start", "largest_end", "energy_share_events"]
    rows = []
    for nd in named:
        rows.append({"kind": "named", "for": nd, "day": nd, "label": config.EVENTS[str(nd.date())],
                     "rv_ratio": 1.0, **d.loc[nd, cols].to_dict()})
        for r in pl.loc[pl["for"] == nd].itertuples():
            rows.append({"kind": "placebo", "for": nd, "day": r.day, "label": "",
                         "rv_ratio": r.rv_ratio, **d.loc[r.day, cols].to_dict()})
    table = pd.DataFrame(rows)
    table["vol_pct"] = 100 * np.sqrt(table["rv"])
    table["rv_decile"] = table["rv_decile"] + 1
    return {"sample": d, "table": table, "by_decile": detection_by_decile(d),
            "reused": int(pl["day"].duplicated().sum())}


def _fmt(v, f):
    return "" if v is None or (isinstance(v, float) and not np.isfinite(v)) else format(v, f)


def report(res: dict) -> list[str]:
    t, bd, d = res["table"], res["by_decile"], res["sample"]
    det = d["n_events"].dropna()
    lines = ["# Event table (exploratory, D-032)", "",
             f"Detection on {len(det):,} test days: {float((det > 0).mean()):.1%} have at "
             f"least one event. Named days and their placebo days (5 closest in RV, outside "
             f"the 10 sessions either side of any named day; {res['reused']} placebo days "
             "serve more than one named day). Vol = 100 x sqrt(RV), the day's volatility in "
             "percent. q = W50 percentile within the RV decile (as H1a; low = concentrated). "
             "Largest event = the detected window holding the most energy. Read its start, "
             "not its length: sigma looks back 15 minutes, so a window can run up to 15 "
             "minutes past the last large move (those minutes add little energy).", "",
             "| day | kind | label | RV ratio | vol % | decile | W50 | q | D5-75 | VR** | f̄ | events | largest event | energy in events |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in t.itertuples():
        window = f"{clock(r.largest_start)}–{clock(r.largest_end)}" if np.isfinite(r.largest_start) else ""
        day = f"**{r.day.date()}**" if r.kind == "named" else f"{r.day.date()}"
        lines.append(f"| {day} | {r.kind} | {r.label} | {r.rv_ratio:.2f} | {r.vol_pct:.2f} | "
                     f"{int(r.rv_decile)} | {_fmt(r.w50, '.0f')} | {_fmt(r.q_w50, '.0f')} | "
                     f"{_fmt(r.d5_75, '.0f')} | {_fmt(r.vr_skip2, '.2f')} | {_fmt(r.f_bar, '.2f')} | "
                     f"{_fmt(r.n_events, '.0f')} | {window} | {_fmt(r.energy_share_events, '.0%')} |")
    lines += ["", "## How often the detector fires, by RV decile (all test days)", "",
              "| RV decile | days | share with an event | mean events | mean energy share in events |",
              "|---|---|---|---|---|",
              *[f"| {i} | {int(r.days)} | {r.share_with_event:.1%} | {r.mean_events:.2f} | "
                f"{r.mean_energy_share_in_events:.1%} |" for i, r in bd.iterrows()], ""]
    return lines


def main(symbol: str = "SPY") -> None:
    from fai.seasonality import deseasonalize, seasonal_variance, to_matrix
    tag = "_nospikes"
    minutes = pd.read_parquet(config.PROCESSED / f"{symbol}_minutes{tag}.parquet")
    sessions = pd.read_parquet(config.PROCESSED / "sessions.parquet")
    daily = pd.read_parquet(config.PROCESSED / f"{symbol}_daily{tag}.parquet")
    R, G = to_matrix(minutes, "r"), to_matrix(minutes, "gap")
    half_days = sessions.index[sessions["half_day"]]
    Rt = deseasonalize(R, G, seasonal_variance(R, G, exclude=half_days))
    eligible = daily["in_tests"].reindex(Rt.index).fillna(False).astype(bool)
    events, summary = detect_events(Rt, eligible)
    res = build(daily, summary, sessions.index)
    lines = report(res)
    config.REPORTS.mkdir(parents=True, exist_ok=True)
    (config.REPORTS / "event_table.md").write_text("\n".join(lines), encoding="utf-8")
    res["table"].to_csv(config.REPORTS / "event_table.csv", index=False)
    ev = events.loc[events["day"].isin(res["sample"].index)].copy()
    ev["start_clock"], ev["end_clock"] = ev["start"].map(clock), ev["end"].map(clock)
    ev.to_csv(config.REPORTS / "events_all.csv", index=False)
    print("\n".join(lines))


if __name__ == "__main__":
    main(*sys.argv[1:])
