#!/usr/bin/env python
"""The registered H2 tests (HYPOTHESES.md, with D-027 and D-029) and the Holm family.

Regression (D-027 adds today's VIX level; the registered version without it is reported):

    d ln VIX_{d+1} = a + b X_d + g1 ln RV_d + g2 r_d + g3 min(r_d, 0) + g4 d ln VIX_d
                     + g5 ln VIX_d + e

In sample, 2010-2018, test days (``in_tests``: half-days and the D-016 outage day out;
FOMC days stay in):

H2a (i)   X = ln FAI_w (Amihud weighting, D-030/D-031). Prediction: b != 0.
H2a (ii)  X = ln FAI_w with ln FAI also in the regression. Since ln FAI_w = ln FAI +
          ln f_bar, b here equals the coefficient on ln f_bar: the weighting alone.
H2b       X = ln W50. b != 0, direction not predicted. Robustness rule: repeated with
          ln D5-75; a W50 result that reverses sign or loses significance is fragile.
Out of sample, 2019-2025, coefficients fitted on 2010-2018 and held fixed: the model with
          X against the model without it, for H2a (X = ln FAI_w) and H2b (X = ln W50; D5-75 as
          robustness). A pass needs both a one-sided Clark-West p below 5% and a lower
          2019-2025 MSE for the model with X (R2_OS > 0), D-034.

Verdicts use the D-027 regression and raw p at 5% (D-029). If a test passes only in the
registered regression, it is reported as a fail (interpretation table, H2a). Reported
alongside, not judged: H2a with the Corwin-Schultz weighting and the floored 1/C comparison
(D-030); the secondary jump logit (d ln VIX_{d+1} > ln 1.2); a leave-one-year-out influence
check (D-034, exploratory); the main tests with r_d not adjusted for dividends (D-034).
Holm (D-029) over H1b and H1c
concentration (raw p from ``reports/h1_results.csv``), H2a (i), H2a (ii), H2b and the two
out-of-sample tests.

Runs: flagged prints removed (primary, as for H1) and kept. Not in this run (robustness
and exploratory, Nov 17): the D-018 benchmark measures in H2b, H3 (differenced signal).

Inputs: ``data/processed/SPY_daily{,_nospikes}.parquet`` and ``SPY_minutes{...}.parquet``
(measures stage), ``data/raw/cboe/VIX_History.csv`` (``python scripts/download.py vix``),
``ref/spy_dividends.csv``.

    python scripts/h2_tests.py

Writes ``reports/h2_results.md`` and ``reports/h2_results.csv``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fai import config  # noqa: E402
from fai import vix  # noqa: E402
from fai.inference import holm  # noqa: E402

Y = "dlnvix_next"
Z_5 = 1.959964
PRIMARY_RUN = "Primary: flagged prints removed"
RUNS = [(PRIMARY_RUN, "_nospikes"), ("Flagged prints kept", "")]
CONTROL_SETS = {"D-027": vix.CONTROLS, "registered": vix.CONTROLS_REGISTERED}

LABELS = {"ln_fai_w": "ln FAI_w", "ln_fai": "ln FAI", "ln_w50": "ln W50",
          "ln_d5_75": "ln D5-75", "ln_fai_w_cs": "ln FAI_w (Corwin-Schultz)",
          "ln_fai_c": "ln FAI_c (floored 1/C)", "ln_rv": "ln RV", "r": "r",
          "r_neg": "min(r, 0)", "dlnvix": "d ln VIX", "ln_vix": "ln VIX", "none": "(none)"}

# (test, X, other regressors besides the controls, role)
IN_SAMPLE_TESTS = [
    ("H2a (i)", "ln_fai_w", [], "primary"),
    ("H2a (ii)", "ln_fai_w", ["ln_fai"], "primary"),
    ("H2b", "ln_w50", [], "primary"),
    ("H2b", "ln_d5_75", [], "robustness"),
    ("H2a (i)", "ln_fai_w_cs", [], "alongside (D-030)"),
    ("H2a (ii)", "ln_fai_w_cs", ["ln_fai"], "alongside (D-030)"),
    ("H2a (i)", "ln_fai_c", [], "alongside (D-030)"),
    ("H2a (ii)", "ln_fai_c", ["ln_fai"], "alongside (D-030)"),
]
OOS_TESTS = [
    ("H2a out of sample", "ln_fai_w", "primary"),
    ("H2b out of sample", "ln_w50", "primary"),
    ("H2b out of sample", "ln_d5_75", "robustness"),
]
LOGIT_X = [None, "ln_fai_w", "ln_w50"]
# Every primary-sample day must have these, so all tests use the same days.
REQUIRED = [Y, *vix.CONTROLS, "ln_fai_w", "ln_fai", "ln_w50", "ln_d5_75"]


# --- sample ---------------------------------------------------------------------------

def test_sample(frame: pd.DataFrame) -> pd.DataFrame:
    """Test days 2010-2025, in time order, complete for every primary variable."""
    missing = sorted(set(REQUIRED) - set(frame.columns))
    if missing:
        raise ValueError(f"H2 frame lacks {missing}: rerun the measures stage")
    d = frame.sort_index().loc[config.IN_SAMPLE[0]:config.OUT_OF_SAMPLE[1]]
    d = d.loc[d["in_tests"].astype(bool)]
    return d.dropna(subset=REQUIRED).copy()


def periods(d: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    idx = d.index
    ts = pd.Timestamp
    ins = (idx >= ts(config.IN_SAMPLE[0])) & (idx <= ts(config.IN_SAMPLE[1]))
    oos = (idx >= ts(config.OUT_OF_SAMPLE[0])) & (idx <= ts(config.OUT_OF_SAMPLE[1]))
    return ins, oos


# --- tests ----------------------------------------------------------------------------

def in_sample(d: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Every in-sample regression; returns (rows for X, full coefficient tables)."""
    ins, _ = periods(d)
    s = d.loc[ins]
    rows, coefs = [], []
    for spec, controls in CONTROL_SETS.items():
        for test, x, extra, role in IN_SAMPLE_TESTS:
            if x not in s.columns:
                continue
            xs = [x, *extra, *controls]
            r = vix.nw_ols(s, Y, xs)
            b = r.loc[x]
            rows.append({"test": test, "x": x, "also": "+".join(extra), "spec": spec,
                         "role": role, "coef": b["coef"], "se": b["se"], "t": b["t"],
                         "p": b["p"], "n": int(b["n"]), "lag": int(b["lag"]),
                         "sd_x": float(s[x].std()),
                         "coef_x_sd": float(b["coef"] * s[x].std())})
            coefs.append(r.assign(test=test, x=x, spec=spec, role=role)
                         .rename_axis("regressor").reset_index())
    return pd.DataFrame(rows), pd.concat(coefs, ignore_index=True)


def out_of_sample(d: pd.DataFrame) -> pd.DataFrame:
    ins, oos = periods(d)
    rows = []
    for spec, controls in CONTROL_SETS.items():
        for test, x, role in OOS_TESTS:
            res = vix.out_of_sample(d, Y, x, controls, ins, oos)
            rows.append({"test": test, "spec": spec, "role": role, **res})
    return pd.DataFrame(rows)


LOYO_TESTS = [("H2a (i)", "ln_fai_w", []), ("H2a (ii)", "ln_fai_w", ["ln_fai"]),
              ("H2b", "ln_w50", []), ("H2b", "ln_d5_75", [])]


def leave_one_year_out(d: pd.DataFrame) -> pd.DataFrame:
    """Exploratory influence check (D-034), named before the run: each in-sample test
    refitted nine times, leaving out one calendar year of 2010-2018 each time (D-027
    regression). Days are left out by date, never by the size of the VIX move, so the
    check does not select on the outcome. One row per test and year left out."""
    ins, _ = periods(d)
    s = d.loc[ins]
    rows = []
    for test, x, extra in LOYO_TESTS:
        for yr in sorted(set(s.index.year)):
            r = vix.nw_ols(s.loc[s.index.year != yr], Y, [x, *extra, *vix.CONTROLS]).loc[x]
            rows.append({"test": test, "x": x, "year_left_out": int(yr), "coef": r["coef"],
                         "se": r["se"], "t": r["t"], "p": r["p"], "n": int(r["n"])})
    return pd.DataFrame(rows)


def loyo_summary(loyo: pd.DataFrame, ins: pd.DataFrame) -> pd.DataFrame:
    """Per test: the range of b and t over the nine refits, how many keep the full-sample
    sign at 5%, and the year whose omission moves t furthest toward zero."""
    out = []
    for (test, x), g in loyo.groupby(["test", "x"], sort=False):
        full = _pick(ins, test=test, x=x, spec="D-027",
                     role="primary" if x != "ln_d5_75" else "robustness")
        sign = np.sign(full["t"])
        moved = g.loc[(g["t"] * sign).idxmin()]
        out.append({"test": test, "x": x, "t_full": full["t"], "b_min": g["coef"].min(),
                    "b_max": g["coef"].max(), "t_min": g["t"].min(), "t_max": g["t"].max(),
                    "sig_same_sign": int(((g["t"] * sign) >= Z_5).sum()), "fits": len(g),
                    "year_most_influential": int(moved["year_left_out"]),
                    "t_without_it": moved["t"]})
    return pd.DataFrame(out)


def jump_logit(d: pd.DataFrame) -> pd.DataFrame:
    """Secondary: P(d ln VIX_{d+1} > ln 1.2), D-027 regressors, in sample."""
    ins, _ = periods(d)
    s = d.loc[ins]
    rows = []
    for x in LOGIT_X:
        xs = ([x] if x else []) + vix.CONTROLS
        r = vix.logit_hac(s, "jump_next", xs)
        key = x or "ln_vix"
        b = r.loc[key]
        rows.append({"x": x or "none", "reported": key, "coef": b["coef"], "se": b["se"],
                     "t": b["t"], "p": b["p"], "n": int(b["n"]), "events": int(b["events"]),
                     "converged": bool(b["converged"])})
    return pd.DataFrame(rows)


# --- verdicts -------------------------------------------------------------------------

def _pick(df: pd.DataFrame, **kw) -> pd.Series:
    m = np.ones(len(df), bool)
    for k, v in kw.items():
        m &= (df[k] == v).to_numpy()
    if m.sum() != 1:
        raise KeyError(f"expected one row for {kw}, found {int(m.sum())}")
    return df.loc[m].iloc[0]


def _two_sided(row: pd.Series) -> str:
    if abs(row["t"]) < Z_5:
        return "not significant"
    return f"b != 0 (b {'> 0' if row['coef'] > 0 else '< 0'})"


def verdicts(ins: pd.DataFrame, oos: pd.DataFrame) -> dict:
    out = {}
    for test, extra in [("H2a (i)", ""), ("H2a (ii)", "ln_fai")]:
        main = _pick(ins, test=test, x="ln_fai_w", spec="D-027", role="primary")
        reg = _pick(ins, test=test, x="ln_fai_w", spec="registered", role="primary")
        v = _two_sided(main)
        if v == "not significant" and abs(reg["t"]) >= Z_5:
            v = ("fails: significant only without the VIX-level control "
                 "(reported as a fail, D-027)")
        out[test] = {"verdict": v, "passes": v.startswith("b != 0"), "p": float(main["p"])}
    w = _pick(ins, test="H2b", x="ln_w50", spec="D-027", role="primary")
    dd = _pick(ins, test="H2b", x="ln_d5_75", spec="D-027", role="robustness")
    reg = _pick(ins, test="H2b", x="ln_w50", spec="registered", role="primary")
    v = _two_sided(w)
    if v.startswith("b != 0"):
        same = np.sign(dd["coef"]) == np.sign(w["coef"]) and abs(dd["t"]) >= Z_5
        v += ", and holds with D5-75" if same else ", but fragile (D5-75 disagrees)"
    elif abs(reg["t"]) >= Z_5:
        v = "fails: significant only without the VIX-level control (reported as a fail, D-027)"
    out["H2b"] = {"verdict": v, "passes": v.startswith("b != 0"), "p": float(w["p"]),
                  "with_d5_75": _two_sided(dd)}
    for test, x in [("H2a out of sample", "ln_fai_w"), ("H2b out of sample", "ln_w50")]:
        r = _pick(oos, test=test, x=x, spec="D-027", role="primary")
        ok = r["p"] < 0.05 and r["r2_os"] > 0                      # D-034 (b): both
        if ok:
            v = "passes"
        elif r["p"] < 0.05:
            v = "fails: Clark-West significant, but the model with X had the higher MSE"
        else:
            v = "fails"
        out[test] = {"verdict": v, "passes": bool(ok), "p": float(r["p"])}
    rob = _pick(oos, test="H2b out of sample", x="ln_d5_75", spec="D-027", role="robustness")
    rob_ok = rob["p"] < 0.05 and rob["r2_os"] > 0
    out["H2b out of sample"]["with_d5_75"] = "passes" if rob_ok else "fails"
    return out


def holm_family(v: dict, h1_csv: Path) -> pd.DataFrame | None:
    """The seven-test Holm family of D-029, from the primary runs of H1 and H2."""
    if not h1_csv.exists():
        return None
    h1 = pd.read_csv(h1_csv)
    h1 = h1.loc[(h1["run"] == PRIMARY_RUN) & h1["primary"].astype(bool)]
    p_b = float(_pick(h1, test="H1b")["p"])
    p_c = float(_pick(h1, test="H1c concentration")["p"])
    fam = [("H1b", p_b, "two-sided"), ("H1c concentration", p_c, "two-sided"),
           ("H2a (i)", v["H2a (i)"]["p"], "two-sided"),
           ("H2a (ii)", v["H2a (ii)"]["p"], "two-sided"),
           ("H2b", v["H2b"]["p"], "two-sided"),
           ("H2a out of sample", v["H2a out of sample"]["p"], "one-sided (Clark-West)"),
           ("H2b out of sample", v["H2b out of sample"]["p"], "one-sided (Clark-West)")]
    t = pd.DataFrame(fam, columns=["test", "p_raw", "p_kind"])
    t["p_holm"] = holm(t["p_raw"].to_numpy())
    t["raw_5pct"] = t["p_raw"] < 0.05
    t["holm_5pct"] = t["p_holm"] < 0.05
    return t


# --- inputs ---------------------------------------------------------------------------

def load_inputs(symbol: str, tag: str):
    from fai.ingest import load_cboe_vix
    from fai.sessions import load_dividends
    daily = pd.read_parquet(config.PROCESSED / f"{symbol}_daily{tag}.parquet")
    minutes = pd.read_parquet(config.PROCESSED / f"{symbol}_minutes{tag}.parquet",
                              columns=["date", "tau", "close"])
    vix_path = config.RAW / "cboe" / "VIX_History.csv"
    if not vix_path.exists():
        sys.exit(f"{vix_path} is missing: python scripts/download.py vix")
    if not (config.REF / "spy_dividends.csv").exists():
        sys.exit("ref/spy_dividends.csv is missing: r_d would keep the ex-dividend drops")
    vix_close = load_cboe_vix(vix_path)["close"]
    return daily, vix.last_close(minutes), vix_close, load_dividends()


def run(daily, close, vix_close, dividends) -> dict:
    frame = vix.h2_frame(daily, close, vix_close, dividends)
    d = test_sample(frame)
    ins, coefs = in_sample(d)
    oos = out_of_sample(d)
    in_tests_days = frame.index[frame["in_tests"]] if "in_tests" in frame else frame.index
    span = in_tests_days[(in_tests_days >= pd.Timestamp(config.IN_SAMPLE[0]))
                         & (in_tests_days <= pd.Timestamp(config.OUT_OF_SAMPLE[1]))]
    ex = dividends.index[(dividends.index >= span.min()) & (dividends.index <= span.max())]
    notes = {"alignment": vix.alignment(span, vix_close),
             "n_test_days": int(len(span)), "n_used": int(len(d)),
             "dropped": [str(x.date()) for x in span.difference(d.index)],
             "n_ex_dividend_days": int(len(ex)),
             "jump_days_in_sample": int(d.loc[periods(d)[0], "jump_next"].sum())}
    return {"sample": d, "in_sample": ins, "coefs": coefs, "oos": oos,
            "logit": jump_logit(d), "verdicts": verdicts(ins, oos), "notes": notes,
            "loyo": (loyo := leave_one_year_out(d)), "loyo_summary": loyo_summary(loyo, ins),
            "unadjusted": unadjusted(daily, close, vix_close, d.index)}


def unadjusted(daily, close, vix_close, days: pd.DatetimeIndex) -> dict:
    """Reported alongside (D-034): the main tests with r_d left unadjusted on ex-dividend
    days, as the raw prices give it, on the same days as the main run. Not judged."""
    f = vix.h2_frame(daily, close, vix_close, None)
    d = f.loc[f.index.isin(days)].sort_index()
    ins, _ = in_sample(d)
    oos = out_of_sample(d)
    keep = lambda t: t.loc[(t["spec"] == "D-027") & t["role"].isin(["primary", "robustness"])]
    return {"in_sample": keep(ins).reset_index(drop=True),
            "oos": keep(oos).reset_index(drop=True)}


# --- report ---------------------------------------------------------------------------

def _lab(x: str) -> str:
    return LABELS.get(x, x)


def section(name: str, res: dict, holm_t: pd.DataFrame | None) -> list[str]:
    d, v, nt = res["sample"], res["verdicts"], res["notes"]
    ins_mask, oos_mask = periods(d)
    lines = [f"## {name}", "",
             f"{nt['n_used']:,} test days with every H2 variable ({int(ins_mask.sum()):,} in "
             f"2010-2018, {int(oos_mask.sum()):,} in 2019-2025) of {nt['n_test_days']:,} test "
             f"days; {nt['n_ex_dividend_days']} ex-dividend days with the dividend added back.",
             f"Days dropped for a missing variable: {', '.join(nt['dropped']) or 'none'}. "
             f"SPY days without a VIX close: "
             f"{', '.join(nt['alignment']['spy_days_without_vix']) or 'none'}. VIX dates that "
             f"are not SPY sessions: {', '.join(nt['alignment']['vix_days_not_spy']) or 'none'}.",
             "", "### Verdicts (D-027 regression, raw p at 5%)", ""]
    for k in ["H2a (i)", "H2a (ii)", "H2b", "H2a out of sample", "H2b out of sample"]:
        extra = f" With D5-75: {v[k]['with_d5_75']}." if "with_d5_75" in v[k] else ""
        lines.append(f"- {k}: {v[k]['verdict']} (p {v[k]['p']:.3f}).{extra}")
    if holm_t is not None:
        lines += ["", "### Holm family (D-029)", "",
                  "| test | raw p | kind | Holm p | raw < 5% | Holm < 5% |",
                  "|---|---|---|---|---|---|"]
        for r in holm_t.itertuples():
            lines.append(f"| {r.test} | {r.p_raw:.4f} | {r.p_kind} | {r.p_holm:.4f} | "
                         f"{r.raw_5pct} | {r.holm_5pct} |")
    lines += ["", "### In sample, 2010-2018 (coefficient on X)", "",
              "b x SD(X) is the change in next-day d ln VIX for a one-SD move in X.", "",
              "| test | X | also in | spec | role | b | se | t | p | b x SD(X) | n | lag |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in res["in_sample"].itertuples():
        lines.append(f"| {r.test} | {_lab(r.x)} | {_lab(r.also) if r.also else ''} | {r.spec} | "
                     f"{r.role} | {r.coef:+.4f} | {r.se:.4f} | {r.t:+.2f} | {r.p:.3f} | "
                     f"{r.coef_x_sd:+.4f} | {r.n} | {r.lag} |")
    c = res["coefs"]
    c = c.loc[(c["test"] == "H2a (i)") & (c["x"] == "ln_fai_w") & (c["spec"] == "D-027")]
    lines += ["", "Full D-027 regression for H2a (i):", "",
              "| regressor | coef | se | t |", "|---|---|---|---|"]
    for r in c.itertuples():
        lines.append(f"| {_lab(r.regressor)} | {r.coef:+.4f} | {r.se:.4f} | {r.t:+.2f} |")
    lines += ["", "### Out of sample, 2019-2025 (coefficients fixed on 2010-2018)", "",
              "R2_OS = 1 - MSE(with X) / MSE(without X). Clark-West p is one-sided.", "",
              "| test | X | spec | role | b (2010-2018) | MSE without | MSE with | R2_OS | "
              "CW t | CW p | n |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in res["oos"].itertuples():
        lines.append(f"| {r.test} | {_lab(r.x)} | {r.spec} | {r.role} | {r.beta_fit:+.4f} | "
                     f"{r.mse_small:.6f} | {r.mse_big:.6f} | {r.r2_os:+.4f} | {r.cw_t:+.2f} | "
                     f"{r.p:.3f} | {r.n} |")
    lines += ["", "### Leave one year out (exploratory influence check, D-034)", "",
              "Each in-sample test refitted nine times, leaving out one year of 2010-2018. "
              "The verdicts above come from the full sample; this shows how much a result "
              "rests on one stretch of history. \"Kept\" counts refits significant at 5% "
              "with the full-sample sign.", "",
              "| test | X | t (full) | b range | t range | kept | most influential year | "
              "t without it |", "|---|---|---|---|---|---|---|---|"]
    for r in res["loyo_summary"].itertuples():
        lines.append(f"| {r.test} | {_lab(r.x)} | {r.t_full:+.2f} | {r.b_min:+.4f} to "
                     f"{r.b_max:+.4f} | {r.t_min:+.2f} to {r.t_max:+.2f} | "
                     f"{r.sig_same_sign} of {r.fits} | {r.year_most_influential} | "
                     f"{r.t_without_it:+.2f} |")
    ua, main = res["unadjusted"], res["in_sample"]
    lines += ["", "### Dividends not added back (reported alongside, D-034)", "",
              "The main tests with r_d as the unadjusted prices give it on ex-dividend days, "
              "same days, D-027 regression. Not judged; it shows what the adjustment changes.", "",
              "| test | X | b (main) | t (main) | b (unadjusted) | t (unadjusted) |",
              "|---|---|---|---|---|---|"]
    for r in ua["in_sample"].itertuples():
        m = _pick(main, test=r.test, x=r.x, spec="D-027", role=r.role)
        lines.append(f"| {r.test} | {_lab(r.x)} | {m['coef']:+.4f} | {m['t']:+.2f} | "
                     f"{r.coef:+.4f} | {r.t:+.2f} |")
    for r in ua["oos"].itertuples():
        m = _pick(res["oos"], test=r.test, x=r.x, spec="D-027", role=r.role)
        lines.append(f"| {r.test} | {_lab(r.x)} | R2_OS {m['r2_os']:+.4f} | CW p {m['p']:.3f} | "
                     f"R2_OS {r.r2_os:+.4f} | CW p {r.p:.3f} |")
    lines += ["", "### Secondary: next-day VIX jump logit (d ln VIX > ln 1.2), 2010-2018", "",
              f"{nt['jump_days_in_sample']} jump days in sample. D-027 regressors.", "",
              "| X | coefficient shown | coef | se | t | p | n | events | converged |",
              "|---|---|---|---|---|---|---|---|---|"]
    for r in res["logit"].itertuples():
        lines.append(f"| {_lab(r.x)} | {_lab(r.reported)} | {r.coef:+.3f} | {r.se:.3f} | "
                     f"{r.t:+.2f} | {r.p:.3f} | {r.n} | {r.events} | {r.converged} |")
    return lines + [""]


def main(symbol: str = "SPY") -> None:
    results = {}
    for name, tag in RUNS:
        if not (config.PROCESSED / f"{symbol}_daily{tag}.parquet").exists():
            if tag == "_nospikes":
                sys.exit("SPY_daily_nospikes.parquet is missing. Run once:\n"
                         "    python scripts/run_all.py --stages clean,measures --drop-spikes")
            continue
        results[name] = run(*load_inputs(symbol, tag))
    h1_csv = config.REPORTS / "h1_results.csv"
    holm_t = holm_family(results[PRIMARY_RUN]["verdicts"], h1_csv)
    lines = ["# H2 results (registered tests, with D-027)", "",
             "Written by `scripts/h2_tests.py`. How each outcome is read was fixed in advance "
             "in `paper/interpretation_table.md`.", ""]
    if holm_t is None:
        lines += [f"{h1_csv.name} not found: run `python scripts/h1_tests.py` for the Holm "
                  "family.", ""]
    rows = []
    for name, res in results.items():
        lines += section(name, res, holm_t if name == PRIMARY_RUN else None)
        rows += [res["in_sample"].assign(part="in sample", run=name),
                 res["oos"].assign(part="out of sample", run=name),
                 res["logit"].assign(part="jump logit", run=name),
                 res["loyo"].assign(part="leave one year out", run=name),
                 res["unadjusted"]["in_sample"].assign(
                     part="in sample, dividends not added back", run=name),
                 res["unadjusted"]["oos"].assign(
                     part="out of sample, dividends not added back", run=name)]
    if holm_t is not None:
        rows.append(holm_t.assign(part="holm", run=PRIMARY_RUN))
    config.REPORTS.mkdir(parents=True, exist_ok=True)
    out = config.REPORTS / "h2_results.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    pd.concat(rows, ignore_index=True).to_csv(config.REPORTS / "h2_results.csv", index=False)
    print(out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main(*sys.argv[1:])
