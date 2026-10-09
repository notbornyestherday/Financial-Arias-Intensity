#!/usr/bin/env python
"""One command from raw files to every computed output.

    python scripts/run_all.py --vendor alphavantage --symbol SPY
    python scripts/run_all.py --vendor firstrate --symbol SPY --raw data/raw/firstrate/SPY_full_1min.zip --bar-label start
    python scripts/run_all.py --stages ingest          # just one stage

Stages: ingest -> clean -> measures. Later weeks add liquidity, detection, vix, figures.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd  # noqa: E402

from fai import config  # noqa: E402
from fai.clean import clean, write_dq_report  # noqa: E402
from fai.ingest import (bar_label_diagnostics, load_alphavantage_dir,  # noqa: E402
                        load_firstrate, to_bar_start)
from fai.measures import daily_measures  # noqa: E402
from fai.seasonality import deseasonalize, seasonal_variance, to_matrix  # noqa: E402
from fai.sessions import day_flags, nyse_sessions  # noqa: E402

STAGES = ["ingest", "clean", "measures"]


def stage_ingest(args) -> None:
    if args.vendor == "alphavantage":
        bars = load_alphavantage_dir(Path(args.raw or config.RAW / "alphavantage" / args.symbol))
    else:
        if not args.raw:
            sys.exit("--raw path required for firstrate")
        bars = load_firstrate(Path(args.raw), member=args.member)
    diag = bar_label_diagnostics(bars)
    print(json.dumps(diag, indent=2))
    label = args.bar_label if args.bar_label != "auto" else diag["guess"]
    if label not in {"start", "end"}:
        sys.exit("Bar timestamp convention is ambiguous: check the vendor docs and the "
                 "volume profile above, then pass --bar-label start|end")
    bars = to_bar_start(bars, label)
    bars = bars.loc[(bars["ts"] >= pd.Timestamp(config.SAMPLE_START, tz=config.TZ))
                    & (bars["ts"] <= pd.Timestamp(config.SAMPLE_END, tz=config.TZ) + pd.Timedelta(days=1))]
    config.INTERIM.mkdir(parents=True, exist_ok=True)
    bars.to_parquet(config.INTERIM / f"{args.symbol}_1min.parquet", index=False)
    print(f"ingest: {len(bars):,} bars, label={label}")


def stage_clean(args) -> None:
    bars = pd.read_parquet(config.INTERIM / f"{args.symbol}_1min.parquet")
    first = bars["ts"].min().strftime("%Y-%m-%d")
    last = bars["ts"].max().strftime("%Y-%m-%d")
    sessions = nyse_sessions(first, last)
    minutes, dq, stats = clean(bars, sessions, drop_spikes=args.drop_spikes)
    config.PROCESSED.mkdir(parents=True, exist_ok=True)
    tag = "_nospikes" if args.drop_spikes else ""
    minutes.to_parquet(config.PROCESSED / f"{args.symbol}_minutes{tag}.parquet", index=False)
    sessions.to_parquet(config.PROCESSED / "sessions.parquet")
    path = write_dq_report(dq, stats, day_flags(sessions.index), args.symbol + tag)
    print(f"clean: {len(minutes):,} minutes; report at {path}")


def stage_measures(args) -> None:
    tag = "_nospikes" if args.drop_spikes else ""
    minutes = pd.read_parquet(config.PROCESSED / f"{args.symbol}_minutes{tag}.parquet")
    sessions = pd.read_parquet(config.PROCESSED / "sessions.parquet")
    R, G = to_matrix(minutes, "r"), to_matrix(minutes, "gap")
    S2 = seasonal_variance(R, G, exclude=sessions.index[sessions["half_day"]])
    Rt = deseasonalize(R, G, S2)
    daily = daily_measures(R, Rt).join(sessions[["half_day"]]).join(day_flags(R.index))
    daily.to_parquet(config.PROCESSED / f"{args.symbol}_daily{tag}.parquet")
    daily.to_csv(config.PROCESSED / f"{args.symbol}_daily{tag}.csv")   # computed measures only
    print(f"measures: {len(daily):,} days")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vendor", choices=["alphavantage", "firstrate"], default="alphavantage")
    ap.add_argument("--symbol", default="SPY")
    ap.add_argument("--raw", help="raw file or directory (defaults per vendor)")
    ap.add_argument("--member", help="file inside a FirstRate zip")
    ap.add_argument("--bar-label", choices=["auto", "start", "end"], default="auto")
    ap.add_argument("--drop-spikes", action="store_true", help="robustness: remove flagged prints")
    ap.add_argument("--stages", default=",".join(STAGES))
    args = ap.parse_args()
    for s in args.stages.split(","):
        {"ingest": stage_ingest, "clean": stage_clean, "measures": stage_measures}[s.strip()](args)


if __name__ == "__main__":
    main()
