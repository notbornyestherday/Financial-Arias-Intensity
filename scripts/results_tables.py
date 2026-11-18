#!/usr/bin/env python
"""Results tables for the paper, built from the H1 and H2 runs. No new analysis.

Every number is read from the files the registered test scripts wrote:

    reports/h1_results.csv   H1b and H1c regressions (scripts/h1_tests.py)
    reports/h1_results.md    the H1a named-days table and its medians (h1_tests.py writes
                             these to the report only, so they are parsed from it)
    reports/h2_results.csv   H2 in and out of sample, leave-one-year-out, dividends not
                             added back, jump logit (scripts/h2_tests.py)

Verdict labels are recomputed from those numbers with the registered rules, so a table
cannot say more than the tests did:

- each test is judged on its raw two-sided p at 5% (D-029 a);
- a raw pass that fails after the Holm adjustment over the seven tests that predict an
  effect is "significant before, not after, Holm adjustment" (D-029 b, c);
- robustness rule (HYPOTHESES.md): a W50 result that changes sign or loses significance
  with D5-75 is "fragile";
- out of sample, a pass needs a one-sided Clark-West p below 5% and R2_OS > 0 (D-034 b);
- the H1c dummy passes by *not* being significantly negative and is not in the Holm family.

The tables show the primary run (flagged prints removed, D-005). The scorecard's notes say
whether any verdict differs in the run with flagged prints kept, and give the largest
change in any t statistic between the two runs.

    python scripts/results_tables.py

Writes ``paper/tables/*.tex`` (each a complete ``table`` environment, for ``\\input`` in
``paper/main.tex``) and ``reports/results_tables.md`` (the same tables, for reading).
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fai import config  # noqa: E402

PRIMARY_RUN = "Primary: flagged prints removed"
KEPT_RUN = "Flagged prints kept"
ALPHA = 0.05
Z_5 = 1.959964                                   # two-sided 5%
TABLES_DIR = ROOT / "paper" / "tables"

H1A_DAYS = {"2010-05-06": "Flash Crash",
            "2015-08-24": "Aug 2015 selloff",
            "2020-03-09": "Market-wide halt",
            "2020-03-12": "Market-wide halt",
            "2020-03-16": "Market-wide halt",
            "2020-03-18": "Market-wide halt"}
H1A_COLUMNS = ["day", "RV", "RV decile", "W50 (min)", "q", "D5-75 (min)", "q (D5-75)",
               "W50 without open", "q without open"]
VR_ROWS = [("vr_skip2", "VR** (primary, D-024)"), ("vr", "VR(30/5) (registered)"),
           ("vr_skip", "VR* (D-023)"), ("vr_skip_60", "VR*(60/10) (D-024)")]
X_LABEL = {"ln_fai_w": "ln FAI_w", "ln_fai_w_cs": "ln FAI_w (Corwin-Schultz)",
           "ln_fai_c": "ln FAI_c (floored 1/C)", "ln_w50": "ln W50", "ln_d5_75": "ln D5-75",
           "none": "(none)"}
HOLM_ORDER = ["H1b", "H1c concentration", "H2a (i)", "H2a (ii)", "H2b",
              "H2a out of sample", "H2b out of sample"]


# --- reading the inputs ---------------------------------------------------------------

def _section(md: str, heading: str) -> str:
    """Text of a '## ' section, up to the next '## ' heading."""
    start = md.find(heading + "\n")
    if start < 0:
        raise ValueError(f"section {heading!r} not found in h1_results.md")
    nxt = md.find("\n## ", start + len(heading))
    return md[start: nxt if nxt >= 0 else len(md)]


def parse_h1a(md: str, run: str = PRIMARY_RUN) -> tuple[pd.DataFrame, dict]:
    """The H1a named-days table and medians of one run, from h1_results.md.

    Strict: the column names must be the ones h1_tests.py writes, so a change in that
    script's report breaks this loudly rather than shifting a column.
    """
    sec = _section(md, f"## {run}")
    line = next((ln for ln in sec.splitlines() if ln.startswith("- H1a:")), None)
    if line is None:
        raise ValueError(f"no H1a verdict line in section {run!r}")
    m_med = re.search(r"median q of the 2020 halt days (\d+(?:\.\d+)?)", line)
    m_rob = re.search(r"H1a (holds|is falsified) \(with D5-75: (holds|falsified); median q "
                      r"of the 2020 days (\d+(?:\.\d+)?)\)", line)
    m_open = re.search(r"Without the first 30 minutes: median q (\d+(?:\.\d+)?)", line)
    if not (m_med and m_rob and m_open):
        raise ValueError(f"H1a verdict line not in the expected form: {line}")
    summary = {"median_q": float(m_med.group(1)), "holds": m_rob.group(1) == "holds",
               "holds_with_d5_75": m_rob.group(2) == "holds",
               "median_q_d5_75": float(m_rob.group(3)),
               "median_q_no_open": float(m_open.group(1))}
    lines = sec.splitlines()
    i = lines.index("### H1a: named days")
    rows = []
    for ln in lines[i + 1:]:
        if not ln.strip():
            if rows:
                break
            continue
        rows.append([c.strip() for c in ln.strip().strip("|").split("|")])
    header, body = rows[0], [r for r in rows[2:]]
    if header != H1A_COLUMNS:
        raise ValueError(f"H1a table columns changed: {header}")
    t = pd.DataFrame(body, columns=header).set_index("day")
    t = t.apply(pd.to_numeric)
    if sorted(t.index) != sorted(H1A_DAYS):
        raise ValueError(f"H1a table days changed: {list(t.index)}")
    return t, summary


def load_inputs(reports: Path = config.REPORTS) -> dict:
    h1 = pd.read_csv(reports / "h1_results.csv")
    h2 = pd.read_csv(reports / "h2_results.csv")
    md = (reports / "h1_results.md").read_text(encoding="utf-8")
    return {"h1": h1, "h2": h2, "h1_md": md}


def _one(df: pd.DataFrame, **match) -> pd.Series:
    """The single row of ``df`` matching every column=value (NaN matches NaN)."""
    mask = pd.Series(True, index=df.index)
    for col, val in match.items():
        mask &= df[col].isna() if val is None else (df[col] == val)
    hit = df.loc[mask]
    if len(hit) != 1:
        raise ValueError(f"expected one row for {match}, found {len(hit)}")
    return hit.iloc[0]


# --- the registered rules -------------------------------------------------------------

def holm(p: dict[str, float]) -> dict[str, float]:
    """Holm step-down adjusted p-values (D-029 b)."""
    order = sorted(p, key=p.get)
    m, running, out = len(order), 0.0, {}
    for i, k in enumerate(order):
        running = max(running, min(1.0, (m - i) * p[k]))
        out[k] = running
    return out


def regression_verdict(coef: float, p: float, predicted: str, holm_p: float | None = None,
                       robust: tuple[float, float] | None = None) -> str:
    """Verdict for a test judged on its raw p; ``predicted`` is '+', '-' or '!=0'.

    ``robust`` is (coef, p) of the same test with D5-75 in place of W50.
    """
    if p >= ALPHA:
        return "Not supported" if predicted in ("+", "-") else "Not significant"
    if predicted in ("+", "-") and np.sign(coef) != (1 if predicted == "+" else -1):
        return "Opposite sign"
    out = "Supported" if predicted in ("+", "-") else "Significant"
    if holm_p is not None and holm_p >= ALPHA:
        out = "Significant before Holm only"
    if robust is not None and (robust[1] >= ALPHA or np.sign(robust[0]) != np.sign(coef)):
        out += "; fragile"
    return out


def dummy_verdict(t: float) -> str:
    """H1c (2): the FOMC dummy must not be significantly negative."""
    return "Fails" if t <= -Z_5 else "Holds"


def oos_verdict(cw_p: float, r2_os: float) -> str:
    """D-034 (b): Clark-West p < 5% and a lower out-of-sample MSE."""
    if cw_p < ALPHA and r2_os > 0:
        return "Passes"
    if cw_p < ALPHA:
        return "Fails (Clark-West significant, higher MSE)"
    return "Fails"


# --- the scorecard --------------------------------------------------------------------

def scorecard(inp: dict, run: str = PRIMARY_RUN) -> dict:
    """One record per confirmatory test, with its verdict under the registered rules."""
    h1 = inp["h1"].loc[inp["h1"]["run"] == run]
    h2 = inp["h2"].loc[inp["h2"]["run"] == run]
    t_a, a = parse_h1a(inp["h1_md"], run)

    def h1row(test, y, x):
        return _one(h1, test=test, y=y, x=x)

    def ins(test, x, also=None, spec="D-027"):
        return _one(h2, part="in sample", test=test, x=x, also=also, spec=spec)

    def oos(test, x, spec="D-027"):
        return _one(h2, part="out of sample", test=test, x=x, spec=spec)

    b, b_r = h1row("H1b", "vr_skip2", "ln W50"), h1row("H1b", "vr_skip2", "ln D5-75")
    c, c_r = (h1row("H1c concentration", "ln W50", "FOMC"),
              h1row("H1c concentration", "ln D5-75", "FOMC"))
    dm, dm_r = (h1row("H1c dummy", "vr_skip2", "FOMC (with ln W50)"),
                h1row("H1c dummy", "vr_skip2", "FOMC (with ln D5-75)"))
    a1, a2 = ins("H2a (i)", "ln_fai_w"), ins("H2a (ii)", "ln_fai_w", also="ln_fai")
    hb, hb_r = ins("H2b", "ln_w50"), ins("H2b", "ln_d5_75")
    oa, ob, ob_r = (oos("H2a out of sample", "ln_fai_w"), oos("H2b out of sample", "ln_w50"),
                    oos("H2b out of sample", "ln_d5_75"))

    raw = {"H1b": b["p"], "H1c concentration": c["p"], "H2a (i)": a1["p"],
           "H2a (ii)": a2["p"], "H2b": hb["p"], "H2a out of sample": oa["p"],
           "H2b out of sample": ob["p"]}
    hp = holm(raw)

    crash_q = t_a.loc[["2010-05-06", "2015-08-24"], "q"]
    fails = [f"{d}: q {q:.1f}" for d, q in crash_q.items() if q >= 10]
    if a["median_q"] <= 50:
        fails.append(f"2020 median q {a['median_q']:.1f}")
    h1a_verdict = "Holds" if not fails else "Falsified"
    if (not fails) != a["holds"]:
        raise ValueError("H1a verdict recomputed from the table disagrees with h1_tests.py")

    def reg(key, label, pred_text, pred, r, robust=None, in_family=True, verdict=None):
        lo, hi = r["coef"] - Z_5 * r["se"], r["coef"] + Z_5 * r["se"]
        hold = hp[key] if in_family else None
        rob = None if robust is None else (robust["coef"], robust["p"])
        return {"key": key, "label": label, "prediction": pred_text, "kind": "regression",
                "coef": r["coef"], "lo": lo, "hi": hi, "t": r["t"], "p": r["p"],
                "holm": hold, "robust_t": None if robust is None else robust["t"],
                "robust_p": None if robust is None else robust["p"],
                "verdict": verdict or regression_verdict(r["coef"], r["p"], pred, hold, rob)}

    def out_of_sample(key, label, r, robust=None):
        return {"key": key, "label": label, "prediction": "CW p < 5%, R2_OS > 0",
                "kind": "oos", "r2_os": r["r2_os"], "t": r["cw_t"], "p": r["p"],
                "holm": hp[key], "robust_p": None if robust is None else robust["p"],
                "robust_verdict": None if robust is None else
                oos_verdict(robust["p"], robust["r2_os"]),
                "verdict": oos_verdict(r["p"], r["r2_os"])}

    rows = [
        {"key": "H1a", "label": "H1a: W50 percentile q, named days", "kind": "h1a",
         "prediction": "q < 10 (crash days); 2020 median > 50",
         "crash_q": list(crash_q), "median_q": a["median_q"], "fails": fails,
         "robust_verdict": "Holds" if a["holds_with_d5_75"] else "Falsified",
         "verdict": h1a_verdict},
        reg("H1b", "H1b: VR** on ln W50", "b > 0", "+", b, robust=b_r),
        reg("H1c concentration", "H1c: ln W50 on FOMC", "c < 0", "-", c, robust=c_r),
        reg("H1c dummy", "H1c: FOMC dummy in H1b",
            "not signif. negative", "-", dm, robust=dm_r, in_family=False,
            verdict=dummy_verdict(dm["t"])),
        reg("H2a (i)", "H2a (i): ln FAI_w", "β ≠ 0", "!=0", a1),
        reg("H2a (ii)", "H2a (ii): ln FAI_w, with ln FAI", "β ≠ 0", "!=0", a2),
        reg("H2b", "H2b: ln W50", "β ≠ 0", "!=0", hb, robust=hb_r),
        out_of_sample("H2a out of sample", "H2a out of sample: ln FAI_w", oa),
        out_of_sample("H2b out of sample", "H2b out of sample: ln W50", ob,
                      robust=ob_r),
    ]
    # the dummy row's robustness cell reports its own verdict with D5-75
    rows[3]["robust_verdict"] = dummy_verdict(dm_r["t"])
    negative = (b["p"] >= ALPHA and rows[7]["verdict"].startswith("Fails")
                and rows[8]["verdict"].startswith("Fails"))
    return {"rows": rows, "holm": hp, "raw": raw, "negative_result": negative,
            "exp_c": float(np.exp(c["coef"])),
            "n": {"h1b": int(b["n"]), "h1c": int(c["n"]), "h1_lag": int(b["lag"]),
                  "h2_in": int(a1["n"]), "h2_lag": int(a1["lag"]), "h2_oos": int(oa["n"])}}


def compare_runs(inp: dict) -> dict:
    """Verdicts and t statistics of the primary run against the run with prints kept."""
    s1, s2 = scorecard(inp, PRIMARY_RUN), scorecard(inp, KEPT_RUN)
    changed = [r1["key"] for r1, r2 in zip(s1["rows"], s2["rows"])
               if r1["verdict"] != r2["verdict"]]
    keys1 = ["test", "y", "x"]
    h1 = inp["h1"]
    m1 = h1.loc[h1["run"] == PRIMARY_RUN].merge(h1.loc[h1["run"] == KEPT_RUN], on=keys1)
    dt = list((m1["t_x"] - m1["t_y"]).abs())
    h2 = inp["h2"].copy()
    h2["tt"] = h2["t"].fillna(h2["cw_t"])
    keys2 = ["part", "test", "x", "also", "spec", "role", "year_left_out"]
    h2[keys2] = h2[keys2].fillna("")
    h2 = h2.loc[h2["part"] != "holm"]
    m2 = h2.loc[h2["run"] == PRIMARY_RUN].merge(h2.loc[h2["run"] == KEPT_RUN], on=keys2)
    if len(m1) != (h1["run"] == PRIMARY_RUN).sum() or \
            len(m2) != (h2["run"] == PRIMARY_RUN).sum():
        raise ValueError("the two runs do not have the same rows")
    dt += list((m2["tt_x"] - m2["tt_y"]).abs().dropna())
    return {"verdicts_changed": changed, "max_abs_dt": float(max(dt))}


# --- formatting -----------------------------------------------------------------------

class B(str):
    """A cell shown in bold (the primary estimate)."""


@dataclass
class Panel:
    """A panel heading row inside a table."""
    title: str


@dataclass
class Table:
    """One table: cells are plain text; render_tex and render_md format them."""
    name: str
    number: str
    title: str
    header: list[str]
    rows: list
    notes: str
    tex_cols: str
    appendix: bool = False


def P(cm: float) -> str:
    """A ragged-right paragraph column (needs the array package)."""
    return rf">{{\raggedright\arraybackslash}}p{{{cm}cm}}"


def c4(x: float) -> str:
    return f"{x:+.4f}"


def t2(x: float) -> str:
    return f"{x:+.2f}"


def pv(p: float) -> str:
    return "<0.001" if p < 0.0005 else f"{p:.3f}"


def ct(coef: float, t: float) -> str:
    return f"{c4(coef)} ({t2(t)})"


# --- the tables -----------------------------------------------------------------------

def table_scorecard(inp: dict) -> Table:
    s, cmp = scorecard(inp), compare_runs(inp)
    rows = []
    for r in s["rows"]:
        if r["kind"] == "h1a":
            est = "{:.1f}, {:.1f}; {:.1f}".format(*r["crash_q"], r["median_q"])
            rows.append([r["label"], r["prediction"], est, "", "", "", "", r["robust_verdict"],
                         r["verdict"]])
        elif r["kind"] == "regression":
            rob = "" if r["robust_t"] is None else f"t {t2(r['robust_t'])}"
            if r.get("robust_verdict"):
                rob += f", {r['robust_verdict'].lower()}"
            rows.append([r["label"], r["prediction"], c4(r["coef"]),
                         f"[{r['lo']:+.3f}, {r['hi']:+.3f}]", t2(r["t"]), pv(r["p"]),
                         "—" if r["holm"] is None else pv(r["holm"]), rob, r["verdict"]])
        else:
            rob = "" if r["robust_p"] is None else \
                f"p {pv(r['robust_p'])}, {r['robust_verdict'].lower()}"
            rows.append([r["label"], r["prediction"], f"{r['r2_os'] * 100:+.2f}%", "",
                         t2(r["t"]), pv(r["p"]), pv(r["holm"]), rob, r["verdict"]])
    n = s["n"]
    h1a = next(r for r in s["rows"] if r["kind"] == "h1a")
    if cmp["verdicts_changed"]:
        kept = ("With flagged prints kept, these verdicts change: "
                + ", ".join(cmp["verdicts_changed"]) + ".")
    else:
        kept = "With flagged prints kept, no verdict changes"
    kept += f"; the largest change in any t statistic between the two runs is " \
            f"{cmp['max_abs_dt']:.2f}."
    neg = ("The pre-registered negative-result condition (HYPOTHESES.md) is met: b in H1b "
           "is indistinguishable from zero, and H2a and H2b fail out of sample."
           if s["negative_result"] else
           "The pre-registered negative-result condition (HYPOTHESES.md) is not met.")
    notes = (
        "Primary run (flagged prints removed). "
        "H1a (Table 2): q on 2010-05-06 and 2015-08-24, then the median over the four 2020 "
        "halt days; " + ("it holds. " if not h1a["fails"] else
                         "it fails on " + "; ".join(h1a["fails"]) + ". ")
        + f"H1b and H1c (Table 3): Newey-West standard errors (lag {n['h1_lag']}), RV-decile "
        f"fixed effects, 2010-2025; n = {n['h1b']:,} for H1b (FOMC days out) and "
        f"{n['h1c']:,} for H1c; exp(c) = {s['exp_c']:.2f}, so FOMC days' W50 is "
        f"{s['exp_c']:.2f} times that of days with similar RV. "
        "H2 (Tables 4 and 5): next-day d ln VIX on X with ln RV, r, min(r, 0), d ln VIX and "
        f"ln VIX (D-027), 2010-2018, n = {n['h2_in']:,}, lag {n['h2_lag']}. Out of sample, "
        f"2019-2025 with coefficients fixed in sample (n = {n['h2_oos']:,}), the estimate is "
        "R2_OS = 1 - MSE(with X) / MSE(without X), and t and p are the Clark-West statistic "
        "and its one-sided p. "
        "Verdicts use the raw p at 5% (D-029). Holm p: adjusted over the seven tests that "
        "predict an effect; the H1c dummy passes by not rejecting and is not in the family. "
        "Significant before Holm only: significant on the raw p but not after adjustment for "
        "multiple tests, read as weaker evidence. With D5-75: the same test with D5-75 in "
        "place of W50; a W50 result that changes sign or loses significance there is fragile "
        f"(HYPOTHESES.md). {kept} {neg}")
    return Table("tab_scorecard", "1", "Pre-registered tests and verdicts",
                 ["Test", "Prediction", "Estimate", "95% CI", "t", "p", "Holm p",
                  "With D5-75", "Verdict"], rows, notes,
                 tex_cols=P(2.4) + P(1.6) + "rlrrr" + P(1.5) + P(1.7))


def table_h1a(inp: dict) -> Table:
    t, a = parse_h1a(inp["h1_md"])
    rows = []
    for day, r in t.iterrows():
        rows.append([day, H1A_DAYS[day], f"{100 * np.sqrt(r['RV']):.2f}",
                     f"{r['W50 (min)']:.1f}", f"{r['q']:.1f}",
                     f"{r['D5-75 (min)']:.1f}", f"{r['q (D5-75)']:.1f}",
                     f"{r['W50 without open']:.1f}", f"{r['q without open']:.1f}"])
    deciles = sorted(t["RV decile"].astype(int).unique())
    where = (f"All six days are in RV decile {deciles[0]} (the top)." if deciles == [10] else
             "RV deciles: " + ", ".join(f"{d} {int(v)}" for d, v in t["RV decile"].items())
             + ".")
    rows.append(["Median, 2020 halt days", "", "", "", f"{a['median_q']:.1f}", "",
                 f"{a['median_q_d5_75']:.1f}", "", f"{a['median_q_no_open']:.1f}"])
    notes = ("q: percentile of the measure among test days in the same RV decile (low = "
             "concentrated). Predictions (HYPOTHESES.md): q < 10 on 2010-05-06 and "
             "2015-08-24; median q > 50 over the four 2020 halt days; falsified if any part "
             "fails. √RV: the day's realized volatility in percent. Without the first 30 "
             "minutes: W50 with the first 30 minutes of every day left out (the RV deciles "
             "are unchanged), reported because three of the four 2020 halts came within "
             "minutes of the open. " + where + " Illustrative: six days chosen in advance, "
             "a calibration check rather than a test.")
    return Table("tab_h1a", "2", "H1a: named days",
                 ["Day", "Event", "√RV (%)", "W50 (min)", "q", "D5-75 (min)", "q",
                  "W50, no open", "q"], rows, notes, tex_cols="llrrrrrrr")


def table_h1bc(inp: dict) -> Table:
    h1 = inp["h1"].loc[inp["h1"]["run"] == PRIMARY_RUN]
    rows: list = [Panel("Panel A. H1b: reversal on concentration, b (FOMC days out)")]
    for y, label in VR_ROWS:
        cells = [label]
        for m in ["ln W50", "ln D5-75", "ln D5-95"]:
            r = _one(h1, test="H1b", y=y, x=m)
            cell = ct(r["coef"], r["t"])
            cells.append(B(cell) if bool(r["primary"]) else cell)
        rows.append(cells)
    rows.append(Panel("Panel B. H1c: FOMC days (positive control, FOMC days in)"))
    cells = ["ln measure on FOMC dummy, c"]
    for m in ["ln W50", "ln D5-75"]:
        r = _one(h1, test="H1c concentration", y=m, x="FOMC")
        cells.append(B(ct(r["coef"], r["t"])) if bool(r["primary"]) else ct(r["coef"], r["t"]))
    rows.append(cells + ["—"])
    cells = ["FOMC dummy in the H1b regression"]
    for m in ["W50", "D5-75"]:
        r = _one(h1, test="H1c dummy", y="vr_skip2", x=f"FOMC (with ln {m})")
        cells.append(B(ct(r["coef"], r["t"])) if bool(r["primary"]) else ct(r["coef"], r["t"]))
    rows.append(cells + ["—"])
    b = _one(h1, test="H1b", y="vr_skip2", x="ln W50")
    c = _one(h1, test="H1c concentration", y="ln W50", x="FOMC")
    notes = ("Coefficient (t). Newey-West standard errors (lag "
             f"{int(b['lag'])}), RV-decile fixed effects, 2010-2025, half-days out. Panel A: "
             f"n = {int(b['n']):,}; the column is the concentration measure on the right-hand "
             "side, the row the variance ratio on the left. Prediction b > 0 (a shorter "
             "window, more reversal). Panel B: n = "
             f"{int(c['n']):,}; predictions c < 0, and the dummy not significantly negative. "
             "Bold: the registered primary test. VR** is the primary reversal measure "
             "(D-024); the registered VR(30/5), VR* and VR*(60/10) are reported alongside, "
             "not judged.")
    return Table("tab_h1bc", "3", "H1b and H1c regressions",
                 ["", "ln W50", "ln D5-75", "ln D5-95"], rows, notes, tex_cols="lrrr")


def table_h2_insample(inp: dict) -> Table:
    h2 = inp["h2"].loc[(inp["h2"]["run"] == PRIMARY_RUN) & (inp["h2"]["part"] == "in sample")]

    def line(test, x, also=None, spec="D-027"):
        d = _one(h2, test=test, x=x, also=also, spec=spec)
        bold = spec == "D-027" and d["role"] == "primary"
        # With ln FAI held fixed, X moves only through the weighting (ln f_bar), so a
        # one-SD move in ln FAI_w is not a possible comparison: no effect size for (ii).
        effect = "—" if also == "ln_fai" else f"{100 * d['coef_x_sd']:+.2f}"
        return [test, X_LABEL[x], B(c4(d["coef"])) if bold else c4(d["coef"]),
                t2(d["t"]), pv(d["p"]), effect]

    rows: list = [Panel("Panel A. Main regression (D-027)")]
    rows += [line("H2a (i)", "ln_fai_w"), line("H2a (ii)", "ln_fai_w", "ln_fai"),
             line("H2b", "ln_w50"), line("H2b", "ln_d5_75")]
    rows.append(Panel("Panel B. Registered regression, without ln VIX (reported alongside)"))
    rows += [line("H2a (i)", "ln_fai_w", spec="registered"),
             line("H2a (ii)", "ln_fai_w", "ln_fai", spec="registered"),
             line("H2b", "ln_w50", spec="registered"),
             line("H2b", "ln_d5_75", spec="registered")]
    rows.append(Panel("Panel C. Other liquidity weightings, D-027 (D-030; reported alongside)"))
    for x in ["ln_fai_w_cs", "ln_fai_c"]:
        rows += [line("H2a (i)", x), line("H2a (ii)", x, "ln_fai")]
    a1 = _one(h2, test="H2a (i)", x="ln_fai_w", also=None, spec="D-027")
    notes = ("Next-day d ln VIX on X, 2010-2018, n = "
             f"{int(a1['n']):,}, Newey-West lag {int(a1['lag'])}. Panel A, the main "
             "regression (D-027): controls ln RV, r, min(r, 0), d ln VIX and today's ln VIX "
             "(VIX mean-reverts, and the trailing normalization in FAI would otherwise carry "
             "that effect). Panel B: the regression as registered in HYPOTHESES.md, without "
             "ln VIX. H2a (ii) also includes unweighted ln FAI, so its β measures the "
             "liquidity weighting alone (ln FAI_w = ln FAI + ln f_bar). The ln D5-75 rows "
             "apply the robustness rule to H2b. 1 SD: 100 x β x SD(X), the change in next-day "
             "d ln VIX, roughly the % change in VIX, for a one-SD higher X; for ln W50 a "
             "negative value means a shorter window (a more concentrated day) is followed by "
             "a bigger VIX rise. None is shown for H2a (ii): with ln FAI held fixed, X can only "
             "move by the weighting, whose SD is about a tenth of ln FAI_w's (pivot check). "
             "Bold: the registered primary tests.")
    return Table("tab_h2_insample", "4", "H2: next-day VIX, in sample (2010-2018)",
                 ["Test", "X", "β", "t", "p", "1 SD (%)"], rows, notes,
                 tex_cols="llrrrr")


def table_h2_oos(inp: dict) -> Table:
    h2 = inp["h2"].loc[(inp["h2"]["run"] == PRIMARY_RUN)
                       & (inp["h2"]["part"] == "out of sample")]
    rows: list = []
    for spec, title in [("D-027", "Panel A. Main regression (D-027)"),
                        ("registered", "Panel B. Registered regression, without ln VIX "
                                       "(reported alongside)")]:
        rows.append(Panel(title))
        for test, x in [("H2a out of sample", "ln_fai_w"), ("H2b out of sample", "ln_w50"),
                        ("H2b out of sample", "ln_d5_75")]:
            d = _one(h2, test=test, x=x, spec=spec)
            verdict = oos_verdict(d["p"], d["r2_os"])
            rows.append([test.split()[0], X_LABEL[x], c4(d["beta_fit"]),
                         f"{d['mse_big']:.6f}", f"{100 * d['r2_os']:+.2f}", t2(d["cw_t"]),
                         pv(d["p"]), verdict if spec == "D-027" else f"({verdict.lower()})"])
    d0 = _one(h2, test="H2a out of sample", x="ln_fai_w", spec="D-027")
    r0 = _one(h2, test="H2a out of sample", x="ln_fai_w", spec="registered")
    notes = ("2019-2025 (targets from "
             f"{d0['test_start']} to {d0['test_end']}), n = {int(d0['n']):,}, with "
             "coefficients fixed on 2010-2018 (β shown). MSE: of the model with X; without X it "
             f"is {d0['mse_small']:.6f} (Panel A) and {r0['mse_small']:.6f} (Panel B). "
             "R2_OS = 1 - MSE(with X) / MSE(without X), in percent. Clark-West: one-sided test "
             "that X improves the forecast, with a Newey-West standard error. A pass needs "
             "both CW p < 5% and R2_OS > 0 (D-034); the ln D5-75 row applies the robustness "
             "rule to H2b. Panel B verdicts in brackets: reported, not judged.")
    return Table("tab_h2_oos", "5", "H2: next-day VIX, out of sample (2019-2025)",
                 ["Test", "X", "β (2010-2018)", "MSE", "R2_OS (%)", "CW t", "CW p",
                  "Verdict"], rows, notes, tex_cols="llrrrrrl")


def influence(h2: pd.DataFrame) -> pd.DataFrame:
    """Leave-one-year-out summary per test, recomputed from the refits (D-034 c)."""
    ins = h2.loc[(h2["part"] == "in sample") & (h2["spec"] == "D-027")
                 & (h2["role"].isin(["primary", "robustness"]))]
    loo = h2.loc[h2["part"] == "leave one year out"]
    out = []
    for _, f in ins.iterrows():
        # the refits are keyed by test and X ("H2a (ii)" already says ln FAI is in)
        g = loo.loc[(loo["test"] == f["test"]) & (loo["x"] == f["x"])]
        g = g.sort_values("year_left_out")
        if len(g) != 9:
            raise ValueError(f"expected 9 refits for {f['test']} {f['x']}, found {len(g)}")
        s = np.sign(f["coef"])
        kept = int(((g["p"] < ALPHA) & (np.sign(g["coef"]) == s)).sum())
        worst = g.loc[(s * g["t"]).idxmin()]
        out.append({"test": f["test"], "x": f["x"], "also": f["also"], "t_full": f["t"],
                    "t_by_year": dict(zip(g["year_left_out"].astype(int), g["t"])),
                    "kept": kept, "n_refits": len(g), "worst_year": int(worst["year_left_out"]),
                    "t_worst": worst["t"]})
    return pd.DataFrame(out)


def table_loyo(inp: dict) -> Table:
    h2 = inp["h2"].loc[inp["h2"]["run"] == PRIMARY_RUN]
    inf = influence(h2)
    years = sorted(next(iter(inf["t_by_year"])).keys())
    rows = []
    for _, r in inf.iterrows():
        cells = [r["test"], X_LABEL[r["x"]], t2(r["t_full"])]
        for y in years:
            v = t2(r["t_by_year"][y])
            cells.append(B(v) if y == r["worst_year"] else v)
        rows.append(cells + [f"{r['kept']} of {r['n_refits']}"])
    notes = ("t on X when one calendar year of 2010-2018 is left out (D-027 regression). Kept: "
             "refits significant at 5% with the full-sample sign. Bold: the year whose omission "
             "moves t furthest toward zero. Exploratory influence check named before the run "
             "(D-034 c); verdicts come from the full sample. H2a (ii) also includes ln FAI; "
             "the ln D5-75 row applies the robustness rule to H2b.")
    return Table("tab_h2_loyo", "A1", "H2 in sample: leave one year out",
                 ["Test", "X", "Full"] + [str(y) for y in years] + ["Kept"], rows, notes,
                 tex_cols="ll" + "r" * (len(years) + 1) + "l", appendix=True)


def table_dividends(inp: dict) -> Table:
    h2 = inp["h2"].loc[inp["h2"]["run"] == PRIMARY_RUN]
    rows = []
    for test, x, also, label in [("H2a (i)", "ln_fai_w", None, "H2a (i)"),
                                 ("H2a (ii)", "ln_fai_w", "ln_fai", "H2a (ii)"),
                                 ("H2b", "ln_w50", None, "H2b"),
                                 ("H2b", "ln_d5_75", None, "H2b")]:
        m = _one(h2, part="in sample", test=test, x=x, also=also, spec="D-027")
        u = _one(h2, part="in sample, dividends not added back", test=test, x=x, also=also,
                 spec="D-027")
        rows.append([label, X_LABEL[x], ct(m["coef"], m["t"]), ct(u["coef"], u["t"])])
    for test, x, label in [("H2a out of sample", "ln_fai_w", "H2a out of sample"),
                           ("H2b out of sample", "ln_w50", "H2b out of sample"),
                           ("H2b out of sample", "ln_d5_75", "H2b out of sample")]:
        m = _one(h2, part="out of sample", test=test, x=x, spec="D-027")
        u = _one(h2, part="out of sample, dividends not added back", test=test, x=x,
                 spec="D-027")
        rows.append([label, X_LABEL[x],
                     f"R2_OS {100 * m['r2_os']:+.2f}%, CW p {pv(m['p'])}",
                     f"R2_OS {100 * u['r2_os']:+.2f}%, CW p {pv(u['p'])}"])
    notes = ("r_d is SPY's close-to-close log return with the cash dividend added back on the "
             "64 ex-dividend days of 2010-2025 (D-034 a); the right column leaves it "
             "unadjusted, on the same days. In sample: β (t). Reported alongside, not judged.")
    return Table("tab_h2_dividends", "A2", "H2 with the return left unadjusted for dividends",
                 ["Test", "X", "Dividend added back (main)", "Unadjusted"], rows, notes,
                 tex_cols="llll", appendix=True)


def table_jump(inp: dict) -> Table:
    h2 = inp["h2"].loc[(inp["h2"]["run"] == PRIMARY_RUN) & (inp["h2"]["part"] == "jump logit")]
    rows = []
    for x in ["none", "ln_fai_w", "ln_w50"]:
        r = _one(h2, x=x)
        shown = "ln VIX" if r["reported"] == "ln_vix" else X_LABEL[r["reported"]]
        rows.append([X_LABEL[x], shown, f"{r['coef']:+.3f}", t2(r["t"]), pv(r["p"]),
                     "yes" if bool(r["converged"]) else "no"])
    r0 = _one(h2, x="none")
    notes = ("Logit for a next-day VIX jump, d ln VIX > ln 1.2, 2010-2018, n = "
             f"{int(r0['n']):,} with {int(r0['events'])} jump days, D-027 regressors, HAC "
             "sandwich standard errors. Secondary, reported but not a hypothesis "
             "(HYPOTHESES.md). The first row has no X and shows the coefficient on ln VIX.")
    return Table("tab_h2_jump", "A3", "Secondary: next-day VIX jump logit",
                 ["X", "Coefficient shown", "Coefficient", "t", "p", "Converged"], rows, notes,
                 tex_cols="llrrrl", appendix=True)


def all_tables(inp: dict) -> list[Table]:
    return [table_scorecard(inp), table_h1a(inp), table_h1bc(inp), table_h2_insample(inp),
            table_h2_oos(inp), table_loyo(inp), table_dividends(inp), table_jump(inp)]


# --- rendering ------------------------------------------------------------------------

# Order matters: VR** before VR*, and every token that needs math before "_" is escaped.
_TEX_WORDS = [("f_bar", r"$\bar{f}$"), ("r_d", r"$r_d$"), ("VR**", r"VR$^{**}$"),
              ("VR*", r"VR$^{*}$"), ("FAI_w", r"FAI$_w$"), ("FAI_c", r"FAI$_c$"),
              ("R2_OS", r"$R^2_{\mathrm{OS}}$"), ("√RV", r"$\sqrt{\mathrm{RV}}$"),
              ("D5-75", "D5--75"), ("D5-95", "D5--95"),
              ("%", r"\%"), ("&", r"\&"), ("—", "---"), ("≈", r"$\approx$"),
              ("≠", r"$\neq$"), ("β", r"$\beta$"), ("<", r"$<$"), (">", r"$>$")]


def tex(s: str) -> str:
    """Plain cell or note text to LaTeX."""
    s = str(s)
    s = re.sub(r"(\d{4})-(\d{4})", r"\1--\2", s)                  # year ranges
    for a, b in _TEX_WORDS:
        s = s.replace(a, b)
    s = re.sub(r"\bln ", r"$\\ln$ ", s)
    s = re.sub(r"(?<![\w.$-])-(?=\d)", "$-$", s)                   # minus signs
    s = re.sub(r"(?<![\w$])\+(?=\d)", "$+$", s)
    parts = s.split("$")                                           # escape _ outside math
    for i in range(0, len(parts), 2):
        parts[i] = parts[i].replace("_", r"\_")
    return "$".join(parts)


def render_tex(t: Table) -> str:
    ncol = len(t.header)
    out = [f"% Generated by scripts/results_tables.py from reports/; do not edit by hand.",
           r"\begin{table}[htbp]", r"\centering",
           rf"\caption{{{tex(t.title)}}}", rf"\label{{tab:{t.name[4:]}}}",
           r"\footnotesize", r"\setlength{\tabcolsep}{3pt}",
           rf"\begin{{tabular}}{{{t.tex_cols}}}", r"\toprule",
           " & ".join(tex(h) for h in t.header) + r" \\", r"\midrule"]
    for r in t.rows:
        if isinstance(r, Panel):
            if out[-1] != r"\midrule":
                out.append(r"\addlinespace")
            out.append(rf"\multicolumn{{{ncol}}}{{l}}{{\textit{{{tex(r.title)}}}}} \\")
            continue
        cells = [rf"\textbf{{{tex(c)}}}" if isinstance(c, B) else tex(c) for c in r]
        out.append(" & ".join(cells) + r" \\")
    out += [r"\bottomrule", r"\end{tabular}", r"\par\medskip",
            r"\begin{minipage}{0.97\linewidth}\footnotesize\textit{Notes:} "
            + tex(t.notes) + r"\end{minipage}", r"\end{table}", ""]
    return "\n".join(out)


def _md(s: str) -> str:
    return str(s).replace("*", r"\*").replace("|", r"\|")


def render_md(t: Table) -> str:
    where = " (appendix)" if t.appendix else ""
    out = [f"### Table {t.number}. {t.title}{where}", "",
           "| " + " | ".join(_md(h) for h in t.header) + " |",
           "|" + "---|" * len(t.header)]
    for r in t.rows:
        if isinstance(r, Panel):
            out.append(f"| *{_md(r.title)}* |" + " |" * (len(t.header) - 1))
            continue
        out.append("| " + " | ".join(f"**{_md(c)}**" if isinstance(c, B) else _md(c)
                                     for c in r) + " |")
    out += ["", f"Notes: {t.notes}", ""]
    return "\n".join(out)


def main(reports: Path = config.REPORTS, tables_dir: Path = TABLES_DIR) -> list[Table]:
    """Read the reports in ``reports``; write the .tex files and results_tables.md."""
    inp = load_inputs(reports)
    tables = all_tables(inp)
    tables_dir.mkdir(parents=True, exist_ok=True)
    for t in tables:
        (tables_dir / f"{t.name}.tex").write_text(render_tex(t), encoding="utf-8")
    md = ["# Results tables", "",
          "Written by `scripts/results_tables.py` from `reports/h1_results.csv`, "
          "`reports/h1_results.md` (H1a table) and `reports/h2_results.csv`; nothing is "
          "re-estimated. Primary run (flagged prints removed). LaTeX versions in "
          "`paper/tables/`.", ""]
    md += [render_md(t) for t in tables]
    (reports / "results_tables.md").write_text("\n".join(md), encoding="utf-8")
    print(f"Wrote {len(tables)} tables to {tables_dir} and {reports / 'results_tables.md'}")
    return tables


if __name__ == "__main__":
    main()
