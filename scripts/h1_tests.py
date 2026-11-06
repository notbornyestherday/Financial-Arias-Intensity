#!/usr/bin/env python
"""The registered H1 tests on the full sample (HYPOTHESES.md, with D-024 and D-026).

H1a  Percentile q of W50 on the named days among days in the same RV decile.
     Predictions: q < 10 on 2010-05-06 and 2015-08-24; median q > 50 over 2020-03-09,
     03-12, 03-16 and 03-18. The 2020 days are also reported with the first 30 minutes of
     every day left out of W50 (the RV deciles are unchanged).
H1b  VR**_d = a + b ln W50_d + RV-decile fixed effects, FOMC days out. Prediction b > 0.
     Robustness rule: repeated with D5-75 in place of W50; a W50 result that reverses
     sign or loses significance with D5-75 is reported as fragile. Reported alongside:
     D5-95, and the registered VR(30/5), VR* and VR*(60/10) in place of VR**.
H1c  (1) ln W50_d = a + c FOMC_d + RV-decile FE, FOMC days in. Prediction c < 0.
     (2) The H1b regression with FOMC days in and an FOMC dummy. Prediction: the dummy is
     not significantly negative. Both repeated with D5-75.

Sample: 2010-2025 (2009 is warm-up), days with ``in_tests`` (half-days and the D-016
outage day out). "RV decile" is the decile of RV over that full sample. Newey-West
standard errors with the registered lag; verdicts on raw two-sided tests at 5% (D-029).
The Holm adjustment over the seven confirmatory tests (D-029) needs the H2 results too, so
it is not computed here.

The primary run uses flagged prints removed (D-005, the ``_nospikes`` files); the run
with them kept is reported too. Not in this run: the D-025 exploratory version without
Fed Chair appearances (needs ``ref/fed_chair_dates.csv``, due with the robustness run).

    python scripts/run_all.py --stages clean,measures --drop-spikes    # once, if missing
    python scripts/h1_tests.py

Writes ``reports/h1_results.md`` and ``reports/h1_results.csv``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fai import config  # noqa: E402
from fai.inference import fe_ols, fe_slope, p_two_sided  # noqa: E402

TEST_YEARS = ("2010-01-01", "2025-12-31")
CRASH_DAYS = ["2010-05-06", "2015-08-24"]
HALT_DAYS_2020 = ["2020-03-09", "2020-03-12", "2020-03-16", "2020-03-18"]
SKIP_OPEN_MIN = 30
Z_5 = 1.959964                          # two-sided 5%

PRIMARY_VR = "vr_skip2"                 # VR** (D-024)
OTHER_VR = ["vr", "vr_skip", "vr_skip_60"]
PRIMARY_M, ROBUST_M, OTHER_M = "w50", "d5_75", ["d5_95"]
LABELS = {"vr_skip2": "VR** (primary)", "vr": "VR(30/5) (registered)", "vr_skip": "VR*",
          "vr_skip_60": "VR*(60/10)", "w50": "W50", "d5_75": "D5-75", "d5_95": "D5-95"}


# --- sample ---------------------------------------------------------------------------

def test_sample(daily: pd.DataFrame) -> pd.DataFrame:
    """Days 2010-2025 with in_tests, in time order, with the full-sample RV decile."""
    need = {"rv", "in_tests", "fomc", PRIMARY_VR, *OTHER_VR, PRIMARY_M, ROBUST_M, *OTHER_M}
    missing = sorted(need - set(daily.columns))
    if missing:
        raise ValueError(f"daily table lacks {missing}: rerun the measures stage "
                         "(python scripts/run_all.py --stages measures, and with --drop-spikes)")
    d = daily.sort_index().loc[TEST_YEARS[0]:TEST_YEARS[1]]
    d = d.loc[d["in_tests"].astype(bool)].copy()
    d["fomc"] = d["fomc"].astype(bool)
    d["rv_decile"] = pd.qcut(d["rv"], 10, labels=False)
    return d


# --- H1a ------------------------------------------------------------------------------

def decile_percentile(d: pd.DataFrame, col: str) -> pd.Series:
    """Percentile (0-100] of ``col`` among days in the same RV decile; low = concentrated."""
    return d.groupby("rv_decile")[col].rank(pct=True, method="average") * 100


def h1a(d: pd.DataFrame, w50_no_open: pd.Series | None = None) -> tuple[pd.DataFrame, dict]:
    d = d.copy()
    d["q"] = decile_percentile(d, PRIMARY_M)
    cols = ["rv", "rv_decile", PRIMARY_M, "q"]
    if w50_no_open is not None:
        d["w50_no_open"] = w50_no_open.reindex(d.index)
        d["q_no_open"] = decile_percentile(d, "w50_no_open")
        cols += ["w50_no_open", "q_no_open"]
    days = pd.DatetimeIndex(CRASH_DAYS + HALT_DAYS_2020)
    missing = [str(x.date()) for x in days if x not in d.index]
    if missing:
        raise ValueError(f"named H1a days not in the test sample: {missing}")
    t = d.loc[days, cols]
    crash_ok = bool((t.loc[pd.DatetimeIndex(CRASH_DAYS), "q"] < 10).all())
    halt_median = float(t.loc[pd.DatetimeIndex(HALT_DAYS_2020), "q"].median())
    out = {"crash_days_q_below_10": crash_ok, "halt_days_median_q": halt_median,
           "halt_days_median_above_50": halt_median > 50,
           "holds": crash_ok and halt_median > 50}
    if w50_no_open is not None:
        out["halt_days_median_q_no_open"] = float(
            t.loc[pd.DatetimeIndex(HALT_DAYS_2020), "q_no_open"].median())
    return t, out


# --- H1b and H1c ----------------------------------------------------------------------

def _row(test, y, x, res, sample, **extra) -> dict:
    return {"test": test, "y": y, "x": x, "coef": res["slope"], "se": res["se"],
            "t": res["t"], "p": p_two_sided(res["t"]), "n": res["n"], "lag": res["lag"],
            "sample": sample, **extra}


def h1b(d: pd.DataFrame) -> pd.DataFrame:
    """Every VR on every log concentration measure, FOMC days out."""
    base = d.loc[~d["fomc"]]
    rows = []
    for y in [PRIMARY_VR] + OTHER_VR:
        for m in [PRIMARY_M, ROBUST_M] + OTHER_M:
            res = fe_slope(base[y], np.log(base[m]), base["rv_decile"])
            rows.append(_row("H1b", y, f"ln {LABELS[m]}", res, "FOMC days out",
                             primary=(y == PRIMARY_VR and m == PRIMARY_M),
                             robustness=(y == PRIMARY_VR and m == ROBUST_M)))
    return pd.DataFrame(rows)


def h1c(d: pd.DataFrame) -> pd.DataFrame:
    rows = []
    fomc = d["fomc"].astype(float)
    for m in [PRIMARY_M, ROBUST_M]:
        res = fe_slope(np.log(d[m]), fomc, d["rv_decile"])
        rows.append(_row("H1c concentration", f"ln {LABELS[m]}", "FOMC", res, "FOMC days in",
                         primary=(m == PRIMARY_M), robustness=(m == ROBUST_M)))
    for m in [PRIMARY_M, ROBUST_M]:
        r = fe_ols(d[PRIMARY_VR], {f"ln {m}": np.log(d[m]), "FOMC": fomc}, d["rv_decile"])
        f = r.loc["FOMC"]
        rows.append({"test": "H1c dummy", "y": PRIMARY_VR, "x": f"FOMC (with ln {LABELS[m]})",
                     "coef": f["coef"], "se": f["se"], "t": f["t"], "p": f["p"],
                     "n": int(f["n"]), "lag": int(f["lag"]), "sample": "FOMC days in",
                     "primary": m == PRIMARY_M, "robustness": m == ROBUST_M,
                     "slope_on_measure": r.loc[f"ln {m}", "coef"]})
    return pd.DataFrame(rows)


# --- verdicts -------------------------------------------------------------------------

def sign_verdict(coef: float, t: float, predicted: str) -> str:
    """'supported' / 'not significant' / 'opposite sign' for a predicted sign + or -."""
    if abs(t) < Z_5:
        return "not significant"
    right = coef > 0 if predicted == "+" else coef < 0
    return "supported" if right else "opposite sign (significant)"


def verdicts(b: pd.DataFrame, c: pd.DataFrame) -> dict:
    prim = b.loc[b["primary"]].iloc[0]
    rob = b.loc[b["robustness"]].iloc[0]
    v_b = sign_verdict(prim["coef"], prim["t"], "+")
    v_rob = sign_verdict(rob["coef"], rob["t"], "+")
    if v_b == "supported":
        fragile = (np.sign(rob["coef"]) != np.sign(prim["coef"])) or abs(rob["t"]) < Z_5
        v_b_full = "supported, but fragile (D5-75 disagrees)" if fragile else \
            "supported, and holds with D5-75"
    else:
        v_b_full = v_b
    cc = c.loc[(c["test"] == "H1c concentration") & c["primary"]].iloc[0]
    cd = c.loc[(c["test"] == "H1c dummy") & c["primary"]].iloc[0]
    v_c1 = sign_verdict(cc["coef"], cc["t"], "-")
    dummy_neg = cd["t"] <= -Z_5
    return {"H1b": v_b_full, "H1b_with_D5-75": v_rob,
            "H1c_concentration": v_c1,
            "H1c_dummy": "significantly negative (fails)" if dummy_neg else
                         "not significantly negative (holds)",
            "H1c_holds": v_c1 == "supported" and not dummy_neg,
            # raw p of the two H1 tests in the D-029 Holm family, for the final table
            "holm_family_raw_p": {"H1b": float(prim["p"]), "H1c concentration": float(cc["p"])}}


# --- W50 without the first 30 minutes (H1a, 2020 days) ---------------------------------

def w50_without_open(symbol: str, tag: str, skip: int = SKIP_OPEN_MIN) -> pd.Series:
    from fai.husid import husid_times
    from fai.seasonality import deseasonalize, seasonal_variance, to_matrix
    minutes = pd.read_parquet(config.PROCESSED / f"{symbol}_minutes{tag}.parquet")
    sessions = pd.read_parquet(config.PROCESSED / "sessions.parquet")
    R, G = to_matrix(minutes, "r"), to_matrix(minutes, "gap")
    half_days = sessions.index[sessions["half_day"]]
    Rt = deseasonalize(R, G, seasonal_variance(R, G, exclude=half_days))
    days = Rt.loc[TEST_YEARS[0]:TEST_YEARS[1]]
    return husid_times(days.iloc[:, skip:])["w50"].rename("w50_no_open")


# --- report ---------------------------------------------------------------------------

def run(daily: pd.DataFrame, w50_no_open: pd.Series | None = None) -> dict:
    d = test_sample(daily)
    a_table, a = h1a(d, w50_no_open)
    b = h1b(d)
    c = h1c(d)
    return {"sample": d, "h1a_table": a_table, "h1a": a, "h1b": b, "h1c": c,
            "verdicts": verdicts(b, c)}


def _fmt_reg(df: pd.DataFrame) -> list[str]:
    head = "| test | y | x | coef | se | t | p | n | lag |"
    lines = [head, "|---|---|---|---|---|---|---|---|---|"]
    for r in df.itertuples():
        lines.append(f"| {r.test} | {LABELS.get(r.y, r.y)} | {r.x} | {r.coef:+.4f} | "
                     f"{r.se:.4f} | {r.t:+.2f} | {r.p:.3f} | {r.n} | {r.lag} |")
    return lines


def section(name: str, res: dict) -> list[str]:
    d, a, v = res["sample"], res["h1a"], res["verdicts"]
    at = res["h1a_table"].copy()
    lines = [f"## {name}", "",
             f"{len(d):,} test days ({d.index.min().date()} to {d.index.max().date()}), "
             f"of which {int(d['fomc'].sum())} FOMC days.", "",
             "### Verdicts", "",
             f"- H1a: crash days q < 10: {a['crash_days_q_below_10']}; median q of the 2020 "
             f"halt days {a['halt_days_median_q']:.1f} (> 50: {a['halt_days_median_above_50']}). "
             f"H1a {'holds' if a['holds'] else 'is falsified'}."
             + (f" Without the first {SKIP_OPEN_MIN} minutes: median q "
                f"{a['halt_days_median_q_no_open']:.1f}." if "halt_days_median_q_no_open" in a else ""),
             f"- H1b (VR** on ln W50): {v['H1b']}. With D5-75: {v['H1b_with_D5-75']}.",
             f"- H1c: FOMC days more concentrated: {v['H1c_concentration']}; FOMC dummy in the "
             f"H1b regression: {v['H1c_dummy']}. H1c {'holds' if v['H1c_holds'] else 'fails'}.",
             "", "Verdicts use raw two-sided tests at 5% (D-029). H1b and H1c concentration "
             "belong to the seven-test Holm family, adjusted once the H2 results exist; the "
             "H1c dummy is reported raw.",
             "", "### H1a: named days", "",
             "| day | RV | RV decile | W50 (min) | q |"
             + (" W50 without open | q without open |" if "q_no_open" in at else ""),
             "|---|---|---|---|---|" + ("---|---|" if "q_no_open" in at else "")]
    for day, r in at.iterrows():
        row = (f"| {day.date()} | {r['rv']:.3g} | {int(r['rv_decile']) + 1} | "
               f"{r['w50']:.1f} | {r['q']:.1f} |")
        if "q_no_open" in at:
            row += f" {r['w50_no_open']:.1f} | {r['q_no_open']:.1f} |"
        lines.append(row)
    lines += ["", "### H1b and H1c regressions", "",
              *_fmt_reg(pd.concat([res["h1b"], res["h1c"]], ignore_index=True)), ""]
    return lines


def main(symbol: str = "SPY") -> None:
    primary = config.PROCESSED / f"{symbol}_daily_nospikes.parquet"
    if not primary.exists():
        sys.exit(f"{primary.name} is missing. Run once:\n"
                 "    python scripts/run_all.py --stages clean,measures --drop-spikes")
    results = {}
    for name, tag in [("Primary: flagged prints removed", "_nospikes"),
                      ("Flagged prints kept", "")]:
        path = config.PROCESSED / f"{symbol}_daily{tag}.parquet"
        if not path.exists():
            continue
        no_open = w50_without_open(symbol, tag)
        results[name] = run(pd.read_parquet(path), no_open)
    lines = ["# H1 results (registered tests, full sample)", "",
             "Written by `scripts/h1_tests.py`. How each outcome is read was fixed in advance "
             "in `paper/interpretation_table.md`. Exploratory follow-ups named there are not "
             "in this run; nor is the D-025 version without Fed Chair appearances.", ""]
    rows = []
    for name, res in results.items():
        lines += section(name, res)
        for part in ("h1b", "h1c"):
            rows.append(res[part].assign(run=name))
    config.REPORTS.mkdir(parents=True, exist_ok=True)
    out = config.REPORTS / "h1_results.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    pd.concat(rows, ignore_index=True).to_csv(config.REPORTS / "h1_results.csv", index=False)
    print(out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main(*sys.argv[1:])
