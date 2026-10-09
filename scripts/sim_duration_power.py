#!/usr/bin/env python
"""How well does each Husid diagnostic separate a burst from a grind with identical RV?

Monte Carlo in deseasonalised space: a burst day has volatility multiplied by `mult`
for 15 minutes; a grind day is uniform. Both days are rescaled to the same total
energy, so RV cannot tell them apart. Reports mean +/- SD of each diagnostic and the
separation d = (mean_grind - mean_burst) / pooled SD. Result shaped the choice of
primary concentration measure (DECISIONS.md D-009).

    python scripts/sim_duration_power.py --reps 1500
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from fai.husid import husid_times  # noqa: E402


def draw(rng, n, mult, length, start, df):
    z = rng.standard_t(df, n) / np.sqrt(df / (df - 2)) if df else rng.standard_normal(n)
    z[start:start + length] *= mult
    return z


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=1500)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)
    rows = []
    for mult, df in [(12, None), (6, None), (4, None), (6, 4)]:
        zb = np.array([draw(rng, 390, mult, 15, 200, df) for _ in range(args.reps)])
        zg = np.array([draw(rng, 390, 1, 15, 200, df) for _ in range(args.reps)])
        zg *= np.sqrt((zb ** 2).sum(1, keepdims=True) / (zg ** 2).sum(1, keepdims=True))
        hb, hg = husid_times(pd.DataFrame(zb)), husid_times(pd.DataFrame(zg))
        for col in ["d5_95", "d5_75", "w50"]:
            b, g = hb[col], hg[col]
            rows.append({
                "burst": f"x{mult} for 15 min", "noise": f"t{df}" if df else "normal",
                "measure": col, "burst_mean": b.mean(), "burst_sd": b.std(),
                "grind_mean": g.mean(), "grind_sd": g.std(),
                "separation_d": (g.mean() - b.mean()) / np.sqrt((g.var() + b.var()) / 2),
            })
    print(pd.DataFrame(rows).round(1).to_string(index=False))


if __name__ == "__main__":
    main()
