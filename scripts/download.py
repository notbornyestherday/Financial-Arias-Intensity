#!/usr/bin/env python
"""Fetch raw data into data/raw/. Raw vendor data is never committed (see .gitignore).

    python scripts/download.py alphavantage --symbol SPY --start 2009-01 --end 2025-12
    python scripts/download.py alphavantage --symbol SPY --start 2010-05 --end 2010-05   # free-key test
    python scripts/download.py firstrate --src ~/Downloads/SPY_full_1min.zip
    python scripts/download.py vix

Alpha Vantage key: set ALPHAVANTAGE_API_KEY in the environment or in a .env file at the
repo root (copy .env.example). Downloads are resumable: existing month files are skipped.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from fai import config  # noqa: E402

AV_URL = "https://www.alphavantage.co/query"
# Verify this URL if it fails; Cboe has moved it before.
CBOE_VIX_URL = "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv"


def read_key() -> str:
    key = os.environ.get("ALPHAVANTAGE_API_KEY")
    env = ROOT / ".env"
    if not key and env.exists():
        for line in env.read_text().splitlines():
            if line.strip().startswith("ALPHAVANTAGE_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not key:
        sys.exit("Set ALPHAVANTAGE_API_KEY (environment or .env)")
    return key


def fetch(url: str, params: dict | None = None, timeout: int = 120) -> str:
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "fai-research/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8")


def cmd_alphavantage(args) -> None:
    key = read_key()
    out = config.RAW / "alphavantage" / args.symbol
    out.mkdir(parents=True, exist_ok=True)
    months = pd.period_range(args.start, args.end, freq="M").strftime("%Y-%m")
    pause = 60.0 / args.rate
    for m in months:
        f = out / f"{args.symbol}_{m}.csv"
        if f.exists() and f.stat().st_size > 0 and not args.force:
            continue
        params = {
            "function": "TIME_SERIES_INTRADAY", "symbol": args.symbol, "interval": "1min",
            "month": m, "outputsize": "full", "extended_hours": "false",
            "adjusted": "false", "datatype": "csv", "apikey": key,
        }
        text = fetch(AV_URL, params)
        if not text.lstrip().lower().startswith("timestamp"):
            sys.exit(f"{m}: vendor returned no bars. Response starts:\n{text[:400]}")
        first_ts = text.splitlines()[1].split(",")[0] if len(text.splitlines()) > 1 else ""
        if not first_ts.startswith(m):
            print(f"WARNING {m}: first row is {first_ts!r}; check the month parameter")
        f.write_text(text)
        print(f"{m}: {len(text.splitlines()) - 1} bars")
        time.sleep(pause)


def cmd_firstrate(args) -> None:
    src = Path(args.src).expanduser()
    out = config.RAW / "firstrate"
    out.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, out / src.name)
    print(f"copied {src} -> {out / src.name}")


def cmd_vix(args) -> None:
    out = config.RAW / "cboe"
    out.mkdir(parents=True, exist_ok=True)
    text = fetch(args.url)
    if "DATE" not in text.splitlines()[0].upper():
        sys.exit(f"Unexpected response from {args.url}:\n{text[:300]}")
    (out / "VIX_History.csv").write_text(text)
    print(f"VIX: {len(text.splitlines()) - 1} rows")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    av = sub.add_parser("alphavantage")
    av.add_argument("--symbol", default="SPY")
    av.add_argument("--start", default="2009-01")
    av.add_argument("--end", default="2025-12")
    av.add_argument("--rate", type=float, default=70, help="requests per minute")
    av.add_argument("--force", action="store_true")
    av.set_defaults(func=cmd_alphavantage)

    fr = sub.add_parser("firstrate")
    fr.add_argument("--src", required=True, help="file downloaded from FirstRate")
    fr.set_defaults(func=cmd_firstrate)

    vx = sub.add_parser("vix")
    vx.add_argument("--url", default=CBOE_VIX_URL)
    vx.set_defaults(func=cmd_vix)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
