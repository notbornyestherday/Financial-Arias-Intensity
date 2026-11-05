#!/usr/bin/env python
"""Null check for the D-023 fix: does VR*(30/5) pass where VR(30/5) failed?

Same simulated markets as the D-022 check (``sim_h1b_null_pipeline.py``), drawn from the
same seed, so scenarios A, B1, B2 and C use exactly the same prices as that run. One new
scenario:

* D   as B2 (half-spread x10 inside bursts), but trade signs are persistent: each minute's
      closing print is on the same side as the previous one with probability 0.9, so the
      sign autocorrelation is 0.8^k at lag k minutes. VR* assumes bounce is uncorrelated
      across block boundaries; D checks that it survives when it is not.

Both estimators are run on every sample. VR* (``vr_skip``) is judged by D-022's pass rule
(rejection rate at most 7.5% and |mean slope| at most 0.25 SD, for W50 and D5-75); the
registered VR(30/5) (``vr``) is reported alongside.

    python scripts/sim_h1b_null_d023.py                 # the registered run (D-023)
    python scripts/sim_h1b_null_d023.py --reps 4 --days 300 --out-dir <tmp>   # smoke test
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fai import config  # noqa: E402
from fai.husid import husid_times  # noqa: E402
from fai.inference import fe_slope, nw_lag  # noqa: E402
from fai.measures import variance_ratio, variance_ratio_skip  # noqa: E402
from fai.seasonality import deseasonalize, seasonal_variance  # noqa: E402

_spec = importlib.util.spec_from_file_location("d022", ROOT / "scripts" / "sim_h1b_null_pipeline.py")
d022 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(d022)

# --- Registered settings (D-023) ------------------------------------------------
SEED = d022.SEED                     # 22: same samples as the D-022 run
N_DAYS = d022.N_DAYS
N_REPS = d022.N_REPS
SCENARIOS = ["A", "B1", "B2", "C", "D"]
P_SAME_SIDE = 0.9                    # scenario D
ESTIMATORS = {"vr_skip": variance_ratio_skip, "vr": variance_ratio}
JUDGED_ESTIMATOR = "vr_skip"
JUDGED_MEASURES = d022.JUDGED        # w50, d5_75
MEASURES = d022.MEASURES             # plus d5_95, reported only


def persistent_signs(rng: np.random.Generator, n_days: int, n: int,
                     p_same: float = P_SAME_SIDE) -> tuple[np.ndarray, np.ndarray]:
    """Bid/ask sides that stick: each print repeats the previous side with prob. p_same.

    Returns (q, q_open): the closing prints (n_days x n) and each day's opening print,
    which starts the chain. Sign autocorrelation is (2 p_same - 1)^k at lag k.
    """
    first = rng.choice([-1.0, 1.0], size=(n_days, 1))
    flips = rng.random((n_days, n)) > p_same
    chain = first * np.where(np.cumsum(flips, axis=1) % 2 == 1, -1.0, 1.0)
    return chain, first[:, 0]


def regressions(R: np.ndarray, Rt: np.ndarray) -> list[dict]:
    """The H1b regression on one sample, for each estimator and duration measure."""
    A = pd.DataFrame(Rt)
    h = husid_times(A)
    rv = (R ** 2).sum(axis=1)
    decile = pd.qcut(rv, 10, labels=False)
    out = []
    for est, fn in ESTIMATORS.items():
        vr = fn(A).to_numpy()
        for m in MEASURES:
            res = fe_slope(vr, np.log(h[m].to_numpy()), decile, lag=nw_lag(len(vr)))
            out.append({"estimator": est, "measure": m, **res, "mean_vr": float(np.nanmean(vr))})
    return out


def one_rep(args) -> list[dict]:
    rep, n_days = args
    ss = np.random.SeedSequence([SEED, rep])
    g_eff, g_bounce, g_persist = (np.random.default_rng(s) for s in ss.spawn(3))
    # The first two streams are the D-022 streams: same prices and bounce for A-C.
    eff, vol, burst = d022.efficient_panel(g_eff, n_days + d022.WARMUP)
    q = g_bounce.choice([-1.0, 1.0], size=eff.shape)
    q_open = g_bounce.choice([-1.0, 1.0], size=eff.shape[0])
    q_d, q_open_d = persistent_signs(g_persist, *eff.shape)
    true_s = d022.SIGMA * d022.u_shape(d022.N_MIN)
    rows = []
    for sc in SCENARIOS:
        if sc == "D":
            R = d022.observed_returns(eff, d022.half_spread("B2", vol, burst), q_d, q_open_d)
        else:
            R = d022.observed_returns(eff, d022.half_spread(sc, vol, burst), q, q_open)
        if sc == "C":
            Rdf, G = pd.DataFrame(R), pd.DataFrame(np.ones_like(R))
            Rt = deseasonalize(Rdf, G, seasonal_variance(Rdf, G)).to_numpy()
        else:
            Rt = R / true_s[None, :]
        R, Rt = R[d022.WARMUP:], Rt[d022.WARMUP:]
        for r in regressions(R, Rt):
            rows.append({"scenario": sc, "rep": rep, **r})
    return rows


def summarize(reps: pd.DataFrame) -> pd.DataFrame:
    g = reps.groupby(["scenario", "estimator", "measure"], sort=False)
    s = g.agg(samples=("slope", "size"), mean_slope=("slope", "mean"),
              sd_slope=("slope", "std"), mean_se=("se", "mean"),
              reject=("t", lambda t: float((t.abs() > d022.ALPHA_Z).mean())),
              mean_vr=("mean_vr", "mean"))
    s["bias_in_sd"] = s["mean_slope"] / s["sd_slope"]
    s["se_ratio"] = s["mean_se"] / s["sd_slope"]
    est = s.index.get_level_values("estimator")
    meas = s.index.get_level_values("measure")
    judged = (est == JUDGED_ESTIMATOR) & meas.isin(JUDGED_MEASURES)
    ok = (s["reject"] <= d022.MAX_REJECT) & (s["bias_in_sd"].abs() <= d022.MAX_BIAS_SD)
    s["verdict"] = np.where(judged, np.where(ok, "pass", "FAIL"), "(reported only)")
    return s.reset_index()


def write_report(summary: pd.DataFrame, info: dict, out_dir: Path) -> Path:
    cols = ["scenario", "estimator", "measure", "samples", "mean_vr", "mean_slope", "sd_slope",
            "bias_in_sd", "se_ratio", "reject", "verdict"]
    t = summary[cols].copy()
    for c in ["mean_vr", "bias_in_sd", "se_ratio"]:
        t[c] = t[c].map("{:.3f}".format)
    for c in ["mean_slope", "sd_slope"]:
        t[c] = t[c].map("{:+.4f}".format)
    t["reject"] = summary["reject"].map("{:.1%}".format)
    head = "| " + " | ".join(cols) + " |"
    sep = "|" + "---|" * len(cols)
    rows = ["| " + " | ".join(str(v) for v in r) + " |" for r in t.to_numpy()]
    judged = summary.loc[summary["verdict"] != "(reported only)"].groupby("scenario", sort=False)["verdict"]
    verdicts = [f"- {k}: {'pass' if (v == 'pass').all() else 'FAIL'}" for k, v in judged]
    lines = [
        "# H1b null check for the D-023 fix (VR*)",
        "",
        f"{info['reps']} simulated samples per scenario, {info['days']} days each, no reversal "
        f"anywhere; Newey-West lag {info['lag']}; seed {SEED} (A-C are the D-022 samples); "
        f"{info['seconds']:.0f} s.",
        "Judged: VR* (`vr_skip`) on W50 and D5-75; pass = rejection rate at most 7.5% and "
        "|mean slope| at most 0.25 SD. The registered VR(30/5) (`vr`) is reported alongside.",
        "",
        "## Verdict by scenario (VR*)",
        "",
        *verdicts,
        "",
        "## Detail",
        "",
        head, sep, *rows,
        "",
    ]
    path = out_dir / "h1b_null_check_d023.md"
    path.write_text("\n".join(lines))
    return path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--reps", type=int, default=N_REPS)
    ap.add_argument("--days", type=int, default=N_DAYS)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--out-dir", type=Path, default=config.REPORTS)
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    jobs = [(r, args.days) for r in range(args.reps)]
    with ProcessPoolExecutor(args.workers) as ex:
        reps = pd.DataFrame([row for rows in ex.map(one_rep, jobs, chunksize=4) for row in rows])
    reps.to_csv(args.out_dir / "h1b_null_check_d023_reps.csv", index=False)
    summary = summarize(reps)
    info = {"reps": args.reps, "days": args.days, "lag": nw_lag(args.days),
            "seconds": time.time() - t0}
    path = write_report(summary, info, args.out_dir)
    print(path.read_text())


if __name__ == "__main__":
    main()
