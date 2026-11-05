#!/usr/bin/env python
"""Exploratory (not registered): candidate fixes after VR* failed scenario D (D-023).

Scenario D (spreads x10 in bursts, trade signs persistent: same side as the previous
print with probability 0.9) leaves VR* with a small bias toward H1b's sign. With
persistent signs, bounce at one 5-minute boundary is still correlated with bounce at
the boundary after next, so the lag-2 block products carry noise too.

Candidates, each a variance ratio with some within-block cross products removed:
  vr_skip      VR*(30/5): lag-1 products removed (the D-023 measure)
  vr_skip2     VR**(30/5): lag-1 and lag-2 products removed; reversal over 15-30 min
  vr_skip_10   VR*(30/10): 10-minute blocks, lag-1 products removed; reversal over 20-30 min
  vr_skip_60   VR*(60/10): 10-minute blocks in hour blocks, lag-1 removed; 20-60 min
Markets: A, B2, D (p = 0.9), D95 (p = 0.95, harsher), and two with real reversal (half of
burst days carry a transient component with a 10-minute half-life; kappa 0.5, 1.0) to
compare power. Same seed and construction as explore_h1b_fixes.py. No real data.
"""

import importlib.util
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from fai.husid import husid_times  # noqa: E402
from fai.inference import fe_slope, nw_lag  # noqa: E402


def _load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


d022 = _load("d022", "sim_h1b_null_pipeline.py")
d023 = _load("d023", "sim_h1b_null_d023.py")
ex1 = _load("ex1", "explore_h1b_fixes.py")

SEED = 2401
KAPPAS = {"P05": 0.5, "P10": 1.0}


def vr_skip_k(A: np.ndarray, base: int, long: int, skip: int) -> np.ndarray:
    """Variance ratio with within-block cross products at lags 1..skip removed."""
    x = np.nan_to_num(A, nan=0.0)
    n_days, n = x.shape
    nb = n // base
    b = x[:, : nb * base].reshape(n_days, nb, base).sum(axis=2)
    m = long // base
    nl = nb // m
    b = b[:, : nl * m].reshape(n_days, nl, m)
    num = (b.sum(axis=2) ** 2).sum(axis=1)
    for k in range(1, skip + 1):
        num = num - 2 * (b[:, :, k:] * b[:, :, :-k]).sum(axis=(1, 2))
    with np.errstate(invalid="ignore", divide="ignore"):
        return num / (b ** 2).sum(axis=(1, 2))


ESTIMATORS = {
    "vr_skip": lambda a: vr_skip_k(a, 5, 30, 1),
    "vr_skip2": lambda a: vr_skip_k(a, 5, 30, 2),
    "vr_skip_10": lambda a: vr_skip_k(a, 10, 30, 1),
    "vr_skip_60": lambda a: vr_skip_k(a, 10, 60, 1),
}


def one_rep(args):
    rep, n_days = args
    ss = np.random.SeedSequence([SEED, rep])
    g_eff, g_b, g_p, g_tr = (np.random.default_rng(s) for s in ss.spawn(4))
    eff, vol, burst = d022.efficient_panel(g_eff, n_days)
    q = g_b.choice([-1.0, 1.0], size=eff.shape)
    q0 = g_b.choice([-1.0, 1.0], size=eff.shape[0])
    q90, q90o = d023.persistent_signs(g_p, *eff.shape, p_same=0.9)
    q95, q95o = d023.persistent_signs(g_p, *eff.shape, p_same=0.95)
    true_s = d022.SIGMA * d022.u_shape(d022.N_MIN)
    markets = {
        "A": (d022.half_spread("A", vol, burst), q, q0, None),
        "B2": (d022.half_spread("B2", vol, burst), q, q0, None),
        "D": (d022.half_spread("B2", vol, burst), q90, q90o, None),
        "D95": (d022.half_spread("B2", vol, burst), q95, q95o, None),
        **{k: (d022.half_spread("A", vol, burst), q, q0, kap) for k, kap in KAPPAS.items()},
    }
    rows = []
    for name, (h, qq, qo, kap) in markets.items():
        R = d022.observed_returns(eff, h, qq, qo)
        if kap is not None:
            R = R + ex1.transient(g_tr, vol, burst, kap)
        Rt = R / true_s[None, :]
        hh = husid_times(pd.DataFrame(Rt))
        dec = pd.qcut((R ** 2).sum(axis=1), 10, labels=False)
        for est, fn in ESTIMATORS.items():
            vr = fn(Rt)
            for m in ("w50", "d5_75"):
                r = fe_slope(vr, np.log(hh[m].to_numpy()), dec, lag=nw_lag(len(vr)))
                rows.append({"market": name, "estimator": est, "measure": m, "rep": rep,
                             "slope": r["slope"], "t": r["t"], "mean_vr": float(np.nanmean(vr))})
    return rows


def main(reps=300, days=d022.N_DAYS, workers=2):
    t0 = time.time()
    with ProcessPoolExecutor(workers) as ex:
        df = pd.DataFrame([r for rows in ex.map(one_rep, [(i, days) for i in range(reps)], chunksize=4)
                           for r in rows])
    (ROOT / "reports").mkdir(exist_ok=True)
    df.to_csv(ROOT / "reports" / "explore_h1b_fixes_d024_reps.csv", index=False)
    g = df.groupby(["market", "estimator", "measure"], sort=False)
    s = g.agg(mean_vr=("mean_vr", "mean"), mean_slope=("slope", "mean"), sd_slope=("slope", "std"),
              reject=("t", lambda t: float((t.abs() > 1.96).mean())))
    s["bias_in_sd"] = s["mean_slope"] / s["sd_slope"]
    pd.set_option("display.width", 200)
    text = f"{reps} reps x {days} days, seed {SEED}, {time.time() - t0:.0f} s\n" + s.round(4).to_string()
    (ROOT / "reports" / "explore_h1b_fixes_d024.txt").write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main(*(int(a) for a in sys.argv[1:]))
