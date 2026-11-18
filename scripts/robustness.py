#!/usr/bin/env python
"""Robustness run (Week 6): exploratory checks around the registered H1 and H2 tests.

Nothing here changes a registered verdict, and nothing is in the Holm family (D-029). Every
check was named before the run; the choices left open are fixed in D-036.

1. D-018 benchmark comparison. W50 against three existing measures of uneven intraday
   variation, computed on the same deseasonalized returns (measures.benchmark_measures):
   jump share max(RV - BV, 0)/RV, the realized-quarticity ratio (in logs; it is n/3 times
   the Herfindahl index of the minutes' energy shares and ignores their order) and the
   downside semivariance share.
   (a) H1b and H2b with each benchmark added as a control, one at a time and all three
       together: does ln W50 keep its sign and significance?
   (b) Each benchmark in place of ln W50.
   (c) Out of sample (H2b's design, D-034 rule): each benchmark against the model without
       it, next to ln W50.
2. H3, the differenced signal a_t = r~_t - r~_{t-1} (HYPOTHESES.md). The concentration and
   energy measures are rebuilt from it (W50, D5-75, FAI, FAI_w); the variance ratio on the
   left of H1b and the H2 controls are unchanged, because they measure price reversal and
   the market state, not the signal. Prediction: no improvement. A comparison improves if
   the differenced version passes the registered rule where r~ fails. Read on three tiers
   (D-036), with Holm over the six main comparisons (H1b, H2a (i), H2a (ii), H2b and the two
   out-of-sample tests; the D5-75 versions are shown, not judged): no improvement = as
   predicted; an improvement that fails Holm = "improves before Holm only", within chance;
   one that survives Holm = not as predicted, to be checked against its own bid-ask null
   before it is believed.
3. Fed Chair appearances (D-025 a): H1b with FOMC days *and* the days in
   ``ref/fed_chair_dates.csv`` left out. Reported next to the registered H1b, never instead.

Both runs, as for H1 and H2: flagged prints removed (primary) and kept.

Needs the measures stage after the H3 change to run_all.py (columns fai_w_diff, f_bar_diff):

    python scripts/run_all.py --stages measures
    python scripts/run_all.py --stages measures --drop-spikes
    python scripts/robustness.py

Writes ``reports/robustness_results.md`` and ``reports/robustness_results.csv``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import h1_tests  # noqa: E402
import h2_tests  # noqa: E402
from fai import config, vix  # noqa: E402
from fai.inference import fe_ols, holm  # noqa: E402
from fai.sessions import load_fed_chair_dates  # noqa: E402

ALPHA = 0.05
PRIMARY_RUN, RUNS = h2_tests.PRIMARY_RUN, h2_tests.RUNS
VR = h1_tests.PRIMARY_VR                       # VR** (D-024)
Y = h2_tests.Y
BENCH = ["jump_share", "ln_rq_ratio", "down_share"]
LABELS = {**h2_tests.LABELS, "jump_share": "jump share", "ln_rq_ratio": "ln RQ ratio",
          "down_share": "downside share", "ln_w50_diff": "ln W50 (diff)",
          "ln_d5_75_diff": "ln D5-75 (diff)", "ln_fai_diff": "ln FAI (diff)",
          "ln_fai_w_diff": "ln FAI_w (diff)", VR: "VR**"}
# r~ test -> its differenced counterpart (X, other regressors)
H3_PAIRS = [("H2a (i)", ("ln_fai_w", []), ("ln_fai_w_diff", [])),
            ("H2a (ii)", ("ln_fai_w", ["ln_fai"]), ("ln_fai_w_diff", ["ln_fai_diff"])),
            ("H2b", ("ln_w50", []), ("ln_w50_diff", [])),
            ("H2b, D5-75", ("ln_d5_75", []), ("ln_d5_75_diff", []))]
# H3 is judged on these six comparisons (D-036); the D5-75 versions are shown, not judged.
H3_MAIN = ["H1b", "H2a (i)", "H2a (ii)", "H2b", "H2a out of sample", "H2b out of sample"]
H3_OOS = [("H2a out of sample", "ln_fai_w", "ln_fai_w_diff"),
          ("H2b out of sample", "ln_w50", "ln_w50_diff"),
          ("H2b out of sample, D5-75", "ln_d5_75", "ln_d5_75_diff")]
NEEDED = ["jump_share", "rq_ratio", "down_share", "w50_diff", "d5_75_diff", "fai_diff",
          "fai_w_diff"]


# --- columns --------------------------------------------------------------------------

def extra_columns(daily: pd.DataFrame) -> pd.DataFrame:
    """The benchmark and differenced-signal regressors, by day."""
    missing = sorted(set(NEEDED) - set(daily.columns))
    if missing:
        raise ValueError(f"daily table lacks {missing}: rerun the measures stage "
                         "(python scripts/run_all.py --stages measures, and with --drop-spikes)")
    out = pd.DataFrame(index=daily.index)
    out["jump_share"] = daily["jump_share"].astype(float)
    out["down_share"] = daily["down_share"].astype(float)
    with np.errstate(divide="ignore", invalid="ignore"):
        out["ln_rq_ratio"] = np.log(daily["rq_ratio"].astype(float))
        for c in ["w50_diff", "d5_75_diff", "fai_diff", "fai_w_diff"]:
            out[f"ln_{c}"] = np.log(daily[c].astype(float))
    return out.replace([np.inf, -np.inf], np.nan)


def h1_sample(daily: pd.DataFrame) -> pd.DataFrame:
    """The registered H1 sample (h1_tests.test_sample) with the extra regressors."""
    d = h1_tests.test_sample(daily)
    e = extra_columns(daily)
    d = d.drop(columns=d.columns.intersection(e.columns)).join(e)   # shares are copied as is
    d["ln_w50"], d["ln_d5_75"] = np.log(d["w50"]), np.log(d["d5_75"])
    return d


def h2_sample(daily, close, vix_close, dividends) -> pd.DataFrame:
    """The registered H2 sample (h2_tests.test_sample, same days) with the extra regressors."""
    frame = vix.h2_frame(daily, close, vix_close, dividends)
    return h2_tests.test_sample(frame).join(extra_columns(daily))


# --- regressions ----------------------------------------------------------------------

def _rows(res: pd.DataFrame, keep: list[str], **info) -> list[dict]:
    return [{**info, "x": k, "coef": res.loc[k, "coef"], "se": res.loc[k, "se"],
             "t": res.loc[k, "t"], "p": res.loc[k, "p"], "n": int(res.loc[k, "n"]),
             "lag": int(res.loc[k, "lag"])} for k in keep]


def h1b_fit(base: pd.DataFrame, xs: list[str]) -> pd.DataFrame:
    """VR** on xs with RV-decile fixed effects (Newey-West, registered lag)."""
    return fe_ols(base[VR], {x: base[x] for x in xs}, base["rv_decile"])


def h2_fit(s: pd.DataFrame, xs: list[str]) -> pd.DataFrame:
    """Next-day d ln VIX on xs and the D-027 controls."""
    return vix.nw_ols(s, Y, [*xs, *vix.CONTROLS])


def d018(d1: pd.DataFrame, d2: pd.DataFrame) -> pd.DataFrame:
    """D-018 (a) controls, (b) replacements, in sample, for H1b and H2b."""
    rows = []
    base = d1.loc[~d1["fomc"]]
    ins, _ = h2_tests.periods(d2)
    s = d2.loc[ins]
    for test, fit, data in [("H1b", h1b_fit, base), ("H2b", h2_fit, s)]:
        rows += _rows(fit(data, ["ln_w50"]), ["ln_w50"], test=test, part="D-018",
                      spec="W50 alone (registered)")
        for b in BENCH:
            rows += _rows(fit(data, ["ln_w50", b]), ["ln_w50", b], test=test, part="D-018",
                          spec=f"(a) W50 + {LABELS[b]}")
        rows += _rows(fit(data, ["ln_w50", *BENCH]), ["ln_w50", *BENCH], test=test,
                      part="D-018", spec="(a) W50 + all three")
        for b in BENCH:
            rows += _rows(fit(data, [b]), [b], test=test, part="D-018",
                          spec=f"(b) {LABELS[b]} in place of W50")
    return pd.DataFrame(rows)


def oos_rows(d2: pd.DataFrame, xs: list[str], **info) -> pd.DataFrame:
    ins, oos = h2_tests.periods(d2)
    rows = []
    for x in xs:
        r = vix.out_of_sample(d2, Y, x, vix.CONTROLS, ins, oos)
        rows.append({**info, **r, "x": x, "passes": bool(r["p"] < ALPHA and r["r2_os"] > 0)})
    return pd.DataFrame(rows)


def d018_oos(d2: pd.DataFrame) -> pd.DataFrame:
    """D-018 (c): each benchmark out of sample against the model without it; W50 alongside."""
    return oos_rows(d2, ["ln_w50", *BENCH], test="H2b out of sample", part="D-018 (c)",
                    spec="D-027")


def _passes_in_sample(row: dict, predicted: str) -> bool:
    if row["p"] >= ALPHA:
        return False
    return predicted == "!=0" or (row["coef"] > 0) == (predicted == "+")


def h3(d1: pd.DataFrame, d2: pd.DataFrame) -> pd.DataFrame:
    """H3: each registered test with r~ and with the differenced signal, read by
    ``h3_verdicts``."""
    rows = []
    base = d1.loc[~d1["fomc"]]
    for name, x, xd in [("H1b", "ln_w50", "ln_w50_diff"), ("H1b, D5-75", "ln_d5_75",
                                                            "ln_d5_75_diff")]:
        a = _rows(h1b_fit(base, [x]), [x])[0]
        b = _rows(h1b_fit(base, [xd]), [xd])[0]
        rows.append(_h3_row(name, a, b, "+"))
    ins, _ = h2_tests.periods(d2)
    s = d2.loc[ins]
    for name, (x, ex), (xd, exd) in H3_PAIRS:
        a = _rows(h2_fit(s, [x, *ex]), [x])[0]
        b = _rows(h2_fit(s, [xd, *exd]), [xd])[0]
        rows.append(_h3_row(name, a, b, "!=0"))
    for name, x, xd in H3_OOS:
        a = oos_rows(d2, [x]).iloc[0].to_dict()
        b = oos_rows(d2, [xd]).iloc[0].to_dict()
        rows.append({"test": name, "x": x, "x_diff": xd, "stat": "R2_OS",
                     "value": a["r2_os"], "p": a["p"], "passes": a["passes"],
                     "value_diff": b["r2_os"], "p_diff": b["p"], "passes_diff": b["passes"],
                     "n": int(b["n"])})
    return h3_verdicts(pd.DataFrame(rows))


def h3_verdicts(rows: pd.DataFrame) -> pd.DataFrame:
    """The D-036 reading of H3, per comparison.

    ``improves`` (raw): the differenced version passes where r~ fails. Holm over the six main
    comparisons' differenced p-values (two-sided in sample, Clark-West one-sided out of
    sample). ``verdict``: "no"; "before Holm only" (raw improvement, Holm p >= 5%); "yes"
    (raw improvement that survives Holm); "not judged" for the D5-75 versions.
    """
    out = rows.copy()
    out["main"] = out["test"].isin(H3_MAIN)
    if out["main"].sum() != len(H3_MAIN):
        raise ValueError("H3 needs exactly the six main comparisons")
    out["holm_diff"] = np.nan
    out.loc[out["main"], "holm_diff"] = holm(out.loc[out["main"], "p_diff"].to_numpy())
    out["improves"] = out["passes_diff"].astype(bool) & ~out["passes"].astype(bool)
    out["verdict"] = np.where(~out["main"], "not judged",
                     np.where(~out["improves"], "no",
                     np.where(out["holm_diff"] < ALPHA, "yes", "before Holm only")))
    return out


def h3_summary(h: pd.DataFrame) -> str:
    """One sentence for H3 under the D-036 tiers."""
    yes = list(h.loc[h["verdict"] == "yes", "test"])
    raw = list(h.loc[h["verdict"] == "before Holm only", "test"])
    if yes:
        return ("not as predicted: with the differenced signal " + ", ".join(yes)
                + " passes where r~ fails, after Holm over the six comparisons; not to be "
                "interpreted before its own bid-ask null check (differencing amplifies bounce)")
    if raw:
        return ("improves before Holm only: " + ", ".join(raw) + " passes on its raw p with "
                "the differenced signal but not after Holm over the six comparisons, which is "
                "within what chance would produce")
    return "as predicted: the differenced signal improves none of the six comparisons"


def _h3_row(name: str, a: dict, b: dict, predicted: str) -> dict:
    pa, pb = _passes_in_sample(a, predicted), _passes_in_sample(b, predicted)
    return {"test": name, "x": a["x"], "x_diff": b["x"], "stat": "b (t)", "value": a["coef"],
            "t": a["t"], "p": a["p"], "passes": pa, "value_diff": b["coef"], "t_diff": b["t"],
            "p_diff": b["p"], "passes_diff": pb, "n": b["n"]}


def fed_chair(d1: pd.DataFrame, chair_days: pd.DatetimeIndex) -> tuple[pd.DataFrame, dict]:
    """D-025 (a): H1b with FOMC days and Fed Chair days out, next to the registered H1b."""
    reg = d1.loc[~d1["fomc"]]
    chair = d1.index.isin(chair_days)
    alt = d1.loc[~d1["fomc"] & ~chair]
    rows = []
    for x in ["ln_w50", "ln_d5_75"]:
        rows += _rows(h1b_fit(reg, [x]), [x], test="H1b", part="Fed Chair",
                      spec="registered (FOMC days out)")
        rows += _rows(h1b_fit(alt, [x]), [x], test="H1b", part="Fed Chair",
                      spec="FOMC and Fed Chair days out (D-025 a)")
    info = {"chair_days_in_sample": int(chair.sum()),
            "chair_days_also_fomc": int((chair & d1["fomc"].to_numpy()).sum()),
            "chair_days_listed_2010_2025": int(((chair_days >= "2010-01-01")
                                                & (chair_days <= "2025-12-31")).sum())}
    return pd.DataFrame(rows), info


# --- run ------------------------------------------------------------------------------

def run(daily, close, vix_close, dividends, chair_days) -> dict:
    d1 = h1_sample(daily)
    d2 = h2_sample(daily, close, vix_close, dividends)
    fc, fc_info = fed_chair(d1, pd.DatetimeIndex(chair_days))
    return {"d1": d1, "d2": d2, "d018": d018(d1, d2), "d018_oos": d018_oos(d2),
            "h3": h3(d1, d2), "fed_chair": fc, "fed_chair_info": fc_info}


def _lab(x: str) -> str:
    return LABELS.get(x, x)


def _reg_table(df: pd.DataFrame) -> list[str]:
    lines = ["| test | specification | regressor | b | se | t | p | n |",
             "|---|---|---|---|---|---|---|---|"]
    for r in df.itertuples():
        lines.append(f"| {r.test} | {r.spec} | {_lab(r.x)} | {r.coef:+.4f} | {r.se:.4f} | "
                     f"{r.t:+.2f} | {r.p:.3f} | {r.n} |")
    return lines


def section(name: str, res: dict) -> list[str]:
    d1, d2, fi = res["d1"], res["d2"], res["fed_chair_info"]
    ins, oos = h2_tests.periods(d2)
    lines = [f"## {name}", "",
             f"H1 sample: {len(d1):,} test days ({int((~d1['fomc']).sum()):,} without FOMC "
             f"days). H2 sample: {int(ins.sum()):,} days in 2010-2018, {int(oos.sum()):,} in "
             "2019-2025, the same days as the registered H2 run.", "",
             "### 1. D-018 benchmark comparison (exploratory)", "",
             "(a) ln W50 with each benchmark as a control, and all three; (b) each benchmark in "
             "place of ln W50. H1b: VR** with RV-decile fixed effects, FOMC days out. H2b: "
             "next-day d ln VIX with the D-027 controls, 2010-2018.", "",
             *_reg_table(res["d018"]), "",
             "(c) Out of sample, 2019-2025 (coefficients fixed on 2010-2018; pass = Clark-West "
             "p < 5% and R2_OS > 0, as D-034).", "",
             "| X | b (2010-2018) | R2_OS | CW t | CW p | passes | n |",
             "|---|---|---|---|---|---|---|"]
    for r in res["d018_oos"].itertuples():
        lines.append(f"| {_lab(r.x)} | {r.beta_fit:+.4f} | {r.r2_os:+.4f} | {r.cw_t:+.2f} | "
                     f"{r.p:.3f} | {r.passes} | {r.n} |")
    h = res["h3"]
    lines += ["", "### 2. H3: differenced signal (registered check)", "",
              "Each test with r~ and with a_t = r~_t - r~_{t-1}. Pass = the registered rule "
              "(raw p at 5%, b > 0 for H1b; out of sample, CW p < 5% and R2_OS > 0). Improves = "
              "passes with the differenced signal where r~ fails; Holm over the six main "
              "comparisons (D-036); the D5-75 versions are shown, not judged.", "",
              "| test | r~ | pass | differenced | pass | p (diff) | Holm p | improves |",
              "|---|---|---|---|---|---|---|---|"]
    for r in h.itertuples():
        if r.stat == "R2_OS":
            a = f"R2_OS {r.value:+.4f} (CW p {r.p:.3f})"
            b = f"R2_OS {r.value_diff:+.4f} (CW p {r.p_diff:.3f})"
        else:
            a = f"{r.value:+.4f} (t {r.t:+.2f})"
            b = f"{r.value_diff:+.4f} (t {r.t_diff:+.2f})"
        hp = "" if np.isnan(r.holm_diff) else f"{r.holm_diff:.3f}"
        lines.append(f"| {r.test} | {a} | {r.passes} | {b} | {r.passes_diff} | "
                     f"{r.p_diff:.3f} | {hp} | {r.verdict} |")
    lines += ["", f"H3 {h3_summary(h)}.", "",
              "### 3. H1b without Fed Chair appearances (D-025 a, exploratory)", "",
              f"{fi['chair_days_listed_2010_2025']} Fed Chair days listed for 2010-2025; "
              f"{fi['chair_days_in_sample']} are H1 test days, of which "
              f"{fi['chair_days_also_fomc']} are also FOMC days (already out).", "",
              *_reg_table(res["fed_chair"]), ""]
    return lines


def main(symbol: str = "SPY") -> None:
    chair = load_fed_chair_dates()
    if chair.empty:
        sys.exit("ref/fed_chair_dates.csv is missing or empty (D-025)")
    results = {}
    for name, tag in RUNS:
        if not (config.PROCESSED / f"{symbol}_daily{tag}.parquet").exists():
            if tag == "_nospikes":
                sys.exit("SPY_daily_nospikes.parquet is missing. Run once:\n"
                         "    python scripts/run_all.py --stages clean,measures --drop-spikes")
            continue
        daily, close, vix_close, div = h2_tests.load_inputs(symbol, tag)
        results[name] = run(daily, close, vix_close, div, chair.index)
    lines = ["# Robustness results (exploratory; D-018, H3, D-025 a)", "",
             "Written by `scripts/robustness.py`. Nothing here changes a registered verdict or "
             "enters the Holm family. How each outcome is read was fixed in advance in "
             "`paper/interpretation_table.md` (robustness rows, D-036).", ""]
    rows = []
    for name, res in results.items():
        lines += section(name, res)
        for part in ["d018", "d018_oos", "h3", "fed_chair"]:
            rows.append(res[part].assign(block=part, run=name))
    config.REPORTS.mkdir(parents=True, exist_ok=True)
    out = config.REPORTS / "robustness_results.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    pd.concat(rows, ignore_index=True).to_csv(config.REPORTS / "robustness_results.csv",
                                              index=False)
    print(out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main(*sys.argv[1:])
