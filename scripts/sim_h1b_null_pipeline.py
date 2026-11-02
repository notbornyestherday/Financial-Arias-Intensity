#!/usr/bin/env python
"""Full-pipeline null check for H1b (DECISIONS.md D-022; extends D-011).

Simulates samples of SPY-like days in which nothing ever reverses, adds bid-ask
bounce, runs the registered H1b regression on each sample, and asks two questions:

* is the average slope of VR(30/5) on ln W50 (and ln D5-75) close to zero?
* does the 5% test reject about 5% of the time, as it should when nothing is there?

Scenarios (500 samples each, same efficient prices across scenarios):

* A   constant half-spread, 1 bp (about five times SPY's typical, on purpose);
* B1  half-spread proportional to local volatility (control: should pass);
* B2  half-spread x10 inside bursts, 1 bp otherwise (more than volatility in most bursts);
* C   as A, but deseasonalized by the pipeline's own trailing estimate (D-020 settings)
      instead of the true intraday profile.

Pass rule (fixed in D-022 before this was run): for W50 and D5-75 alike, the rejection
rate is at most 7.5% and |mean slope| is at most a quarter of the slopes' SD.

    python scripts/sim_h1b_null_pipeline.py                 # the registered run
    python scripts/sim_h1b_null_pipeline.py --reps 4 --days 300 --out-dir <tmp>   # smoke test
"""

from __future__ import annotations

import argparse
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
from fai.measures import variance_ratio  # noqa: E402
from fai.seasonality import deseasonalize, seasonal_variance  # noqa: E402
from fai.sim import u_shape  # noqa: E402

# --- Registered settings (D-022) ----------------------------------------------
SEED = 22
N_DAYS = 3850            # about the H1b sample: 2010-2025 less half-days, FOMC days, outage
N_REPS = 500
N_MIN = config.FULL_DAY_MINUTES
SIGMA = 4e-4             # typical one-minute SD at the bottom of the U (as fai.sim)
DAY_LOG_SD = 0.5         # SD of the log daily volatility level
MAX_BURSTS = 3           # 0-3 bursts a day
BURST_LEN = (3, 30)      # minutes, lower inclusive, upper exclusive (as D-011)
BURST_LOG_MULT = 2.5     # volatility multiplier exp(U(0, 2.5)), up to about x12
T_DF = 4                 # t(4) innovations, scaled to unit variance
HALF_SPREAD = 1e-4       # 1 bp
B2_MULT = 10.0
WARMUP = config.SEAS_WINDOW_DAYS
SCENARIOS = ["A", "B1", "B2", "C"]
MEASURES = ["w50", "d5_75", "d5_95"]     # d5_95 reported only
JUDGED = ["w50", "d5_75"]
MAX_REJECT = 0.075
MAX_BIAS_SD = 0.25
ALPHA_Z = 1.959963984540054


def efficient_panel(rng: np.random.Generator, n_days: int, n: int = N_MIN):
    """Efficient one-minute log returns with no reversal anywhere.

    Returns (eff, vol, burst): returns, their true SD, and a mask of burst minutes.
    """
    season = u_shape(n)
    level = np.exp(DAY_LOG_SD * rng.standard_normal(n_days))
    mult = np.ones((n_days, n))
    burst = np.zeros((n_days, n), bool)
    n_b = rng.integers(0, MAX_BURSTS + 1, n_days)
    for i in np.nonzero(n_b)[0]:
        for _ in range(n_b[i]):
            s = rng.integers(0, n - BURST_LEN[1])
            length = rng.integers(*BURST_LEN)
            mult[i, s: s + length] *= np.exp(rng.uniform(0, BURST_LOG_MULT))
            burst[i, s: s + length] = True
    vol = SIGMA * season[None, :] * level[:, None] * mult
    z = rng.standard_t(T_DF, (n_days, n)) / np.sqrt(T_DF / (T_DF - 2))
    return vol * z, vol, burst


def half_spread(scenario: str, vol: np.ndarray, burst: np.ndarray) -> np.ndarray:
    """Half-spread (in log terms) at each minute's closing print."""
    if scenario in ("A", "C"):
        return np.full(vol.shape, HALF_SPREAD)
    if scenario == "B1":
        typical = SIGMA * u_shape(vol.shape[1]).mean()   # level 1, no burst
        return HALF_SPREAD * vol / typical
    if scenario == "B2":
        return HALF_SPREAD * np.where(burst, B2_MULT, 1.0)
    raise ValueError(scenario)


def observed_returns(eff: np.ndarray, h: np.ndarray, q: np.ndarray, q_open: np.ndarray) -> np.ndarray:
    """Roll bounce: each close prints at the bid (q = -1) or the ask (q = +1).

    r_t = eff_t + h_t q_t - h_{t-1} q_{t-1}. The first bar (D-002) runs from the day's
    opening print, which bounces too, with the first minute's spread.
    """
    noise = h * q
    prev = np.concatenate([(h[:, 0] * q_open)[:, None], noise[:, :-1]], axis=1)
    return eff + noise - prev


def h1b_regressions(R: np.ndarray, Rt: np.ndarray) -> list[dict]:
    """The registered H1b regression on one sample, once per duration measure."""
    idx = pd.RangeIndex(R.shape[0])
    A = pd.DataFrame(Rt, index=idx)
    vr = variance_ratio(A).to_numpy()
    h = husid_times(A)
    rv = (R ** 2).sum(axis=1)
    decile = pd.qcut(rv, 10, labels=False)
    out = []
    for m in MEASURES:
        res = fe_slope(vr, np.log(h[m].to_numpy()), decile, lag=nw_lag(len(vr)))
        out.append({"measure": m, **res, "mean_vr": float(np.nanmean(vr))})
    return out


def one_rep(args) -> list[dict]:
    rep, n_days = args
    ss = np.random.SeedSequence([SEED, rep])
    g_eff, g_bounce = (np.random.default_rng(s) for s in ss.spawn(2))
    eff, vol, burst = efficient_panel(g_eff, n_days + WARMUP)
    q = g_bounce.choice([-1.0, 1.0], size=eff.shape)
    q_open = g_bounce.choice([-1.0, 1.0], size=eff.shape[0])
    true_s = SIGMA * u_shape(N_MIN)            # the true profile at the long-run level
    rows = []
    for sc in SCENARIOS:
        R = observed_returns(eff, half_spread(sc, vol, burst), q, q_open)
        if sc == "C":
            Rdf = pd.DataFrame(R)
            G = pd.DataFrame(np.ones_like(R))
            Rt = deseasonalize(Rdf, G, seasonal_variance(Rdf, G)).to_numpy()
        else:
            Rt = R / true_s[None, :]
        R, Rt = R[WARMUP:], Rt[WARMUP:]       # same days in every scenario
        for r in h1b_regressions(R, Rt):
            rows.append({"scenario": sc, "rep": rep, **r})
    return rows


def summarize(reps: pd.DataFrame) -> pd.DataFrame:
    g = reps.groupby(["scenario", "measure"], sort=False)
    s = g.agg(samples=("slope", "size"), mean_slope=("slope", "mean"),
              sd_slope=("slope", "std"), mean_se=("se", "mean"),
              reject=("t", lambda t: float((t.abs() > ALPHA_Z).mean())),
              mean_vr=("mean_vr", "mean"))
    s["bias_in_sd"] = s["mean_slope"] / s["sd_slope"]
    s["se_ratio"] = s["mean_se"] / s["sd_slope"]
    judged = s.index.get_level_values("measure").isin(JUDGED)
    ok = (s["reject"] <= MAX_REJECT) & (s["bias_in_sd"].abs() <= MAX_BIAS_SD)
    s["verdict"] = np.where(judged, np.where(ok, "pass", "FAIL"), "(reported only)")
    return s.reset_index()


def write_report(summary: pd.DataFrame, info: dict, out_dir: Path) -> Path:
    cols = ["scenario", "measure", "samples", "mean_vr", "mean_slope", "sd_slope",
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
    scen = summary.loc[summary["measure"].isin(JUDGED)].groupby("scenario", sort=False)["verdict"]
    verdicts = [f"- {k}: {'pass' if (v == 'pass').all() else 'FAIL'}" for k, v in scen]
    lines = [
        "# H1b null check on the full pipeline (D-022)",
        "",
        f"{info['reps']} simulated samples per scenario, {info['days']} days each, no reversal "
        f"anywhere; Newey-West lag {info['lag']}; seed {SEED}; {info['seconds']:.0f} s.",
        "Pass: rejection rate at most 7.5% and |mean slope| at most 0.25 SD, for W50 and D5-75.",
        "`se_ratio` is the average Newey-West SE over the actual spread of the slopes "
        "(about 1 if the SEs are right).",
        "",
        "## Verdict by scenario",
        "",
        *verdicts,
        "",
        "## Detail",
        "",
        head, sep, *rows,
        "",
    ]
    path = out_dir / "h1b_null_check.md"
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
    reps.to_csv(args.out_dir / "h1b_null_check_reps.csv", index=False)
    summary = summarize(reps)
    info = {"reps": args.reps, "days": args.days, "lag": nw_lag(args.days),
            "seconds": time.time() - t0}
    path = write_report(summary, info, args.out_dir)
    print(path.read_text())


if __name__ == "__main__":
    main()
