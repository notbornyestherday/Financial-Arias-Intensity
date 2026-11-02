#!/usr/bin/env python
"""Exploratory (not registered): candidate fixes for the D-022 B2 failure.

Same simulated markets as scripts/sim_h1b_null_pipeline.py (A, B1, B2, C), plus two
"H1b is true" markets in which half of burst days carry a transient (liquidity)
component that decays with a 10-minute half-life, so prices really do reverse.

Estimators of intraday reversal, all on the same deseasonalised returns:
  vr30_5      the registered VR(30/5)
  vr30_10     longer base blocks: VR(30/10)
  vr30_5skip  VR(30/5) without the lag-1 block cross-products. Under Roll bounce the only
              block-level effect of the noise is a negative lag-1 covariance and an inflated
              block variance; dropping the lag-1 products from the numerator leaves
              E[ratio] = 1 whatever the spread pattern. Reversal at 10-30 minutes is kept;
              reversal within 5-10 minutes is given up.

Nothing here touches real data.
"""

import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import importlib.util

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
spec = importlib.util.spec_from_file_location("reg", REPO / "scripts" / "sim_h1b_null_pipeline.py")
reg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reg)

from fai.husid import husid_times  # noqa: E402
from fai.inference import fe_slope, nw_lag  # noqa: E402
from fai.measures import variance_ratio  # noqa: E402
from fai.seasonality import deseasonalize, seasonal_variance  # noqa: E402

SEED = 2301                     # different from the registered run
HALF_LIFE = 10.0                # minutes, transient component
KAPPAS = {"P05": 0.5, "P10": 1.0}


def vr_skip(A: np.ndarray, base=5, long=30) -> np.ndarray:
    x = np.nan_to_num(A, nan=0.0)
    n_days, n = x.shape
    nb = n // base
    b = x[:, : nb * base].reshape(n_days, nb, base).sum(axis=2)
    m = long // base
    nl = nb // m
    b = b[:, : nl * m].reshape(n_days, nl, m)
    L2 = (b.sum(axis=2) ** 2).sum(axis=1)
    lag1 = (b[:, :, 1:] * b[:, :, :-1]).sum(axis=(1, 2))
    den = (b ** 2).sum(axis=(1, 2))
    with np.errstate(invalid="ignore", divide="ignore"):
        return (L2 - 2 * lag1) / den


def transient(rng, vol, burst, kappa):
    """Transient log-price deviation on liquidity days: tau_t = phi tau_{t-1} + eta_t."""
    n_days, n = vol.shape
    liq_day = rng.random(n_days) < 0.5
    eta = rng.standard_normal(vol.shape) * kappa * vol * (burst & liq_day[:, None])
    phi = 2 ** (-1 / HALF_LIFE)
    tau = np.zeros_like(eta)
    for t in range(n):
        tau[:, t] = (phi * tau[:, t - 1] if t else 0.0) + eta[:, t]
    d = np.diff(tau, axis=1, prepend=0.0)
    return d


def regressions(R, Rt):
    A = pd.DataFrame(Rt)
    h = husid_times(A)
    rv = (R ** 2).sum(axis=1)
    dec = pd.qcut(rv, 10, labels=False)
    vrs = {
        "vr30_5": variance_ratio(A, 5, 30).to_numpy(),
        "vr30_10": variance_ratio(A, 10, 30).to_numpy(),
        "vr30_5skip": vr_skip(Rt),
    }
    out = []
    for est, vr in vrs.items():
        for m in ("w50", "d5_75"):
            r = fe_slope(vr, np.log(h[m].to_numpy()), dec, lag=nw_lag(len(vr)))
            out.append({"estimator": est, "measure": m, "slope": r["slope"], "t": r["t"],
                        "se": r["se"], "mean_vr": float(np.nanmean(vr))})
    return out


def one_rep(args):
    rep, n_days = args
    ss = np.random.SeedSequence([SEED, rep])
    g_eff, g_bounce, g_tr = (np.random.default_rng(s) for s in ss.spawn(3))
    eff, vol, burst = reg.efficient_panel(g_eff, n_days + reg.WARMUP)
    q = g_bounce.choice([-1.0, 1.0], size=eff.shape)
    q_open = g_bounce.choice([-1.0, 1.0], size=eff.shape[0])
    true_s = reg.SIGMA * reg.u_shape(reg.N_MIN)
    rows = []
    for sc in ["A", "B1", "B2", "C", *KAPPAS]:
        noise_sc = sc if sc in ("A", "B1", "B2", "C") else "A"
        R = reg.observed_returns(eff, reg.half_spread(noise_sc, vol, burst), q, q_open)
        if sc in KAPPAS:
            R = R + transient(g_tr, vol, burst, KAPPAS[sc])
        if sc == "C":
            Rdf, G = pd.DataFrame(R), pd.DataFrame(np.ones_like(R))
            Rt = deseasonalize(Rdf, G, seasonal_variance(Rdf, G)).to_numpy()
        else:
            Rt = R / true_s[None, :]
        R, Rt = R[reg.WARMUP:], Rt[reg.WARMUP:]
        for r in regressions(R, Rt):
            rows.append({"scenario": sc, "rep": rep, **r})
    return rows


def main(reps=300, days=reg.N_DAYS, workers=2):
    t0 = time.time()
    with ProcessPoolExecutor(workers) as ex:
        df = pd.DataFrame([r for rows in ex.map(one_rep, [(i, days) for i in range(reps)], chunksize=4)
                           for r in rows])
    out = REPO / "reports" / "explore_h1b_fixes_reps.csv"
    df.to_csv(out, index=False)
    g = df.groupby(["scenario", "estimator", "measure"], sort=False)
    s = g.agg(mean_vr=("mean_vr", "mean"), mean_slope=("slope", "mean"), sd_slope=("slope", "std"),
              reject=("t", lambda t: float((t.abs() > 1.96).mean())),
              reject_pos=("t", lambda t: float((t > 1.96).mean())))
    s["bias_in_sd"] = s["mean_slope"] / s["sd_slope"]
    pd.set_option("display.width", 200)
    print(f"{reps} reps x {days} days, {time.time() - t0:.0f} s")
    print(s.round(4).to_string())


if __name__ == "__main__":
    main(*(int(a) for a in sys.argv[1:]))
