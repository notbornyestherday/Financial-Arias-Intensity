#!/usr/bin/env python
"""Null check for H1b: with no reversal anywhere, VR should not depend on concentration.

Simulates days of independent deseasonalized returns where concentration varies a lot
(0-3 bursts per day of random size, length and position), then regresses the variance
ratio VR(30/5) on ln W50, ln D5-75 and ln D5-95. Any slope that is reliably nonzero here is
mechanical, not evidence of reversal, and would invalidate H1b. Week 2 repeats this on
the full pipeline (bid-ask bounce, estimated seasonality).

    python scripts/sim_h1b_null.py --days 16000 --seeds 10 20
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from fai.husid import husid_times  # noqa: E402
from fai.measures import variance_ratio  # noqa: E402


def null_panel(rng, n_days, n=390, df=None):
    if df:
        z = rng.standard_t(df, (n_days, n)) / np.sqrt(df / (df - 2))
    else:
        z = rng.standard_normal((n_days, n))
    for i in range(n_days):
        for _ in range(rng.integers(0, 4)):
            s, length = rng.integers(0, n - 30), rng.integers(3, 30)
            z[i, s:s + length] *= np.exp(rng.uniform(0, 2.5))
    return pd.DataFrame(z)


def slope(x, y):
    X = np.column_stack([np.ones_like(x), x])
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    r = y - X @ b
    se = np.sqrt(r.var() / ((x - x.mean()) ** 2).sum())
    return b[1], b[1] / se


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=16000)
    ap.add_argument("--seeds", type=int, nargs="+", default=[10, 20])
    args = ap.parse_args()
    rows = []
    for df in (None, 4):
        for seed in args.seeds:
            a = null_panel(np.random.default_rng(seed), args.days, df=df)
            h, vr = husid_times(a), variance_ratio(a).to_numpy()
            for col in ("w50", "d5_75", "d5_95"):
                b, t = slope(np.log(h[col].to_numpy()), vr)
                rows.append({"noise": f"t{df}" if df else "normal", "seed": seed,
                             "measure": col, "slope": b, "t": t})
    print(pd.DataFrame(rows).round(4).to_string(index=False))


if __name__ == "__main__":
    main()
