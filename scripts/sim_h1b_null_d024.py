#!/usr/bin/env python
"""Null check for the D-024 fix: does VR**(30/5) pass where VR* failed (scenario D)?

Same simulated markets and seed as the D-023 check, so scenarios A-D are exactly the D-023
samples. One extra market, run and reported but not judged:

* D95  as D, with each closing print on the same side as the previous one with
       probability 0.95 (sign autocorrelation 0.9^k at lag k minutes).

Estimators on every sample: VR** (``vr_skip2``, judged by D-022's pass rule on W50 and
D5-75), and, reported alongside, the registered VR(30/5) (``vr``), VR* (``vr_skip``) and
the robustness measure VR*(60/10) (``vr_skip_60``).

    python scripts/sim_h1b_null_d024.py                 # the registered run (D-024)
    python scripts/sim_h1b_null_d024.py --reps 4 --days 300 --out-dir <tmp>   # smoke test
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

_spec = importlib.util.spec_from_file_location("d023", ROOT / "scripts" / "sim_h1b_null_d023.py")
d023 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(d023)
d022 = d023.d022

# --- Registered settings (D-024) ------------------------------------------------
SEED = d022.SEED                     # 22: A-D are the D-022 / D-023 samples
N_DAYS = d022.N_DAYS
N_REPS = d022.N_REPS
SCENARIOS = ["A", "B1", "B2", "C", "D", "D95"]
JUDGED_SCENARIOS = ["A", "B1", "B2", "C", "D"]
P_SAME_D95 = 0.95
ESTIMATORS = {
    "vr_skip2": lambda A: variance_ratio_skip(A, skip=2),
    "vr": variance_ratio,
    "vr_skip": variance_ratio_skip,
    "vr_skip_60": lambda A: variance_ratio_skip(A, base=10, long=60),
}
JUDGED_ESTIMATOR = "vr_skip2"
JUDGED_MEASURES = d022.JUDGED        # w50, d5_75
MEASURES = d022.MEASURES             # plus d5_95, reported only


def regressions(R: np.ndarray, Rt: np.ndarray) -> list[dict]:
    A = pd.DataFrame(Rt)
    h = husid_times(A)
    decile = pd.qcut((R ** 2).sum(axis=1), 10, labels=False)
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
    g_eff, g_bounce, g_persist, g_persist95 = (np.random.default_rng(s) for s in ss.spawn(4))
    # The first three streams are the D-023 streams: same prices and signs for A-D.
    eff, vol, burst = d022.efficient_panel(g_eff, n_days + d022.WARMUP)
    q = g_bounce.choice([-1.0, 1.0], size=eff.shape)
    q_open = g_bounce.choice([-1.0, 1.0], size=eff.shape[0])
    q_d, q_open_d = d023.persistent_signs(g_persist, *eff.shape)
    q_95, q_open_95 = d023.persistent_signs(g_persist95, *eff.shape, p_same=P_SAME_D95)
    true_s = d022.SIGMA * d022.u_shape(d022.N_MIN)
    rows = []
    for sc in SCENARIOS:
        if sc == "D":
            R = d022.observed_returns(eff, d022.half_spread("B2", vol, burst), q_d, q_open_d)
        elif sc == "D95":
            R = d022.observed_returns(eff, d022.half_spread("B2", vol, burst), q_95, q_open_95)
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
    sc = s.index.get_level_values("scenario")
    est = s.index.get_level_values("estimator")
    meas = s.index.get_level_values("measure")
    judged = sc.isin(JUDGED_SCENARIOS) & (est == JUDGED_ESTIMATOR) & meas.isin(JUDGED_MEASURES)
    ok = (s["reject"] <= d022.MAX_REJECT) & (s["bias_in_sd"].abs() <= d022.MAX_BIAS_SD)
    s["verdict"] = np.where(judged, np.where(ok, "pass", "FAIL"),
                            np.where(ok, "(reported: would pass)", "(reported: would fail)"))
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
    judged = summary.loc[summary["verdict"].isin(["pass", "FAIL"])].groupby("scenario", sort=False)["verdict"]
    verdicts = [f"- {k}: {'pass' if (v == 'pass').all() else 'FAIL'}" for k, v in judged]
    lines = [
        "# H1b null check for the D-024 fix (VR**)",
        "",
        f"{info['reps']} simulated samples per scenario, {info['days']} days each, no reversal "
        f"anywhere; Newey-West lag {info['lag']}; seed {SEED} (A-D are the D-023 samples); "
        f"{info['seconds']:.0f} s.",
        "Judged: VR** (`vr_skip2`) on W50 and D5-75 in A, B1, B2, C, D; pass = rejection rate at "
        "most 7.5% and |mean slope| at most 0.25 SD. Reported only: D95, and the estimators "
        "`vr` (registered VR(30/5)), `vr_skip` (VR*) and `vr_skip_60` (VR*(60/10)).",
        "",
        "## Verdict by scenario (VR**)",
        "",
        *verdicts,
        "",
        "## Detail",
        "",
        head, sep, *rows,
        "",
    ]
    path = out_dir / "h1b_null_check_d024.md"
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
    reps.to_csv(args.out_dir / "h1b_null_check_d024_reps.csv", index=False)
    summary = summarize(reps)
    info = {"reps": args.reps, "days": args.days, "lag": nw_lag(args.days),
            "seconds": time.time() - t0}
    path = write_report(summary, info, args.out_dir)
    print(path.read_text())


if __name__ == "__main__":
    main()
