"""The results tables: every number comes from the reports, and the verdicts follow the
registered rules (D-029, D-034, the robustness rule)."""

import importlib.util
import shutil
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
_spec = importlib.util.spec_from_file_location("rt", ROOT / "scripts" / "results_tables.py")
rt = importlib.util.module_from_spec(_spec)
sys.modules["rt"] = rt              # dataclasses look their module up while it loads
_spec.loader.exec_module(rt)


@pytest.fixture(scope="module")
def inp():
    return rt.load_inputs(REPORTS)


# --- reading --------------------------------------------------------------------------

def test_h1a_parsed_from_the_report(inp):
    t, a = rt.parse_h1a(inp["h1_md"])
    assert list(t.index) == list(rt.H1A_DAYS)
    assert t.loc["2010-05-06", "q"] == 0.3
    assert t.loc["2015-08-24", "q"] == 87.0
    assert t.loc["2020-03-12", "W50 (min)"] == 46.9
    assert (a["median_q"], a["median_q_d5_75"], a["median_q_no_open"]) == (56.4, 83.1, 55.6)
    assert not a["holds"] and not a["holds_with_d5_75"]
    # the printed median agrees with the median of the (rounded) table values
    halt = t.loc[["2020-03-09", "2020-03-12", "2020-03-16", "2020-03-18"], "q"]
    assert abs(halt.median() - a["median_q"]) <= 0.1


def test_h1a_parser_refuses_a_changed_table(inp):
    broken = inp["h1_md"].replace("| day | RV | RV decile |", "| day | RV | decile |")
    with pytest.raises(ValueError, match="columns changed"):
        rt.parse_h1a(broken)


# --- the rules ------------------------------------------------------------------------

def test_holm_reproduces_the_h2_report(inp):
    s = rt.scorecard(inp)
    h = inp["h2"].loc[inp["h2"]["part"] == "holm"].set_index("test")
    assert set(h.index) == set(rt.HOLM_ORDER)
    for k in rt.HOLM_ORDER:
        assert s["raw"][k] == pytest.approx(h.loc[k, "p_raw"], rel=1e-12)
        assert s["holm"][k] == pytest.approx(h.loc[k, "p_holm"], rel=1e-9)


def test_holm_small_example():
    # D-029 review example: raw 0.03, 0.001, 0.40 -> 0.06, 0.003, 0.40
    out = rt.holm({"a": 0.03, "b": 0.001, "c": 0.40})
    assert out == pytest.approx({"a": 0.06, "b": 0.003, "c": 0.40})


@pytest.mark.parametrize("args, expected", [
    ((0.01, 0.30, "+"), "Not supported"),
    ((0.01, 0.30, "!=0"), "Not significant"),
    ((-0.01, 0.01, "+"), "Opposite sign"),
    ((0.01, 0.01, "+", 0.02), "Supported"),
    ((0.01, 0.01, "+", 0.06), "Significant before Holm only"),
    ((-0.01, 0.01, "!=0", 0.02), "Significant"),
    ((0.01, 0.01, "+", 0.02, (0.01, 0.20)), "Supported; fragile"),        # loses significance
    ((0.01, 0.01, "+", 0.02, (-0.01, 0.01)), "Supported; fragile"),       # flips sign
    ((0.01, 0.01, "+", 0.02, (0.02, 0.01)), "Supported"),                 # holds with D5-75
])
def test_regression_verdict(args, expected):
    assert rt.regression_verdict(*args) == expected


def test_dummy_and_out_of_sample_rules():
    assert rt.dummy_verdict(-1.36) == "Holds"
    assert rt.dummy_verdict(-2.10) == "Fails"
    assert rt.dummy_verdict(+3.00) == "Holds"           # positive is not a failure
    assert rt.oos_verdict(0.01, 0.002) == "Passes"
    assert rt.oos_verdict(0.01, -0.001).startswith("Fails (Clark-West significant")
    assert rt.oos_verdict(0.20, 0.002) == "Fails"


# --- the scorecard on the actual runs -------------------------------------------------

def test_scorecard_verdicts(inp):
    v = {r["key"]: r["verdict"] for r in rt.scorecard(inp)["rows"]}
    assert v == {
        "H1a": "Falsified",
        "H1b": "Not supported",
        "H1c concentration": "Supported; fragile",
        "H1c dummy": "Holds",
        "H2a (i)": "Significant before Holm only",
        "H2a (ii)": "Not significant",
        "H2b": "Significant before Holm only; fragile",
        "H2a out of sample": "Fails",
        "H2b out of sample": "Fails",
    }
    assert rt.scorecard(inp)["negative_result"]


def test_negative_result_condition_responds_to_the_numbers(inp):
    h2 = inp["h2"].copy()
    m = ((h2["part"] == "out of sample") & (h2["test"] == "H2b out of sample")
         & (h2["x"] == "ln_w50") & (h2["spec"] == "D-027"))
    h2.loc[m, ["p", "r2_os"]] = [0.01, 0.002]
    s = rt.scorecard({**inp, "h2": h2})
    assert next(r for r in s["rows"] if r["key"] == "H2b out of sample")["verdict"] == "Passes"
    assert not s["negative_result"]


def test_flagged_prints_kept_changes_no_verdict(inp):
    c = rt.compare_runs(inp)
    assert c["verdicts_changed"] == []
    assert 0 < c["max_abs_dt"] < 0.02


def test_influence_summary_matches_the_h2_report(inp):
    h2 = inp["h2"].loc[inp["h2"]["run"] == rt.PRIMARY_RUN]
    inf = rt.influence(h2).set_index(["test", "x"])
    # values printed in reports/h2_results.md
    assert inf.loc[("H2a (i)", "ln_fai_w"), "kept"] == 8
    assert inf.loc[("H2a (i)", "ln_fai_w"), "worst_year"] == 2017
    assert inf.loc[("H2a (ii)", "ln_fai_w"), "worst_year"] == 2011
    assert inf.loc[("H2b", "ln_w50"), "kept"] == 9
    assert inf.loc[("H2b", "ln_w50"), "worst_year"] == 2010
    assert inf.loc[("H2b", "ln_d5_75"), "kept"] == 2


# --- the tables -----------------------------------------------------------------------

def test_cells_are_copied_from_the_csv(inp):
    tables = {t.name: t for t in rt.all_tables(inp)}
    h1 = inp["h1"].loc[inp["h1"]["run"] == rt.PRIMARY_RUN]
    b = h1.loc[(h1["test"] == "H1b") & (h1["y"] == "vr") & (h1["x"] == "ln D5-75")].iloc[0]
    assert tables["tab_h1bc"].rows[2][2] == f"{b['coef']:+.4f} ({b['t']:+.2f})"
    h2 = inp["h2"].loc[inp["h2"]["run"] == rt.PRIMARY_RUN]
    hb = h2.loc[(h2["part"] == "in sample") & (h2["test"] == "H2b") & (h2["x"] == "ln_w50")
                & (h2["spec"] == "D-027")].iloc[0]
    row = next(r for r in tables["tab_h2_insample"].rows
               if isinstance(r, list) and r[0] == "H2b" and r[1] == "ln W50")
    assert row[2] == f"{hb['coef']:+.4f}" and isinstance(row[2], rt.B)
    assert row[5] == f"{100 * hb['coef_x_sd']:+.2f}"
    ii = next(r for r in tables["tab_h2_insample"].rows
              if isinstance(r, list) and r[0] == "H2a (ii)")
    assert ii[5] == "—"                       # no 1-SD effect where ln FAI is held fixed


@pytest.mark.parametrize("plain, latex", [
    ("ln FAI_w", r"$\ln$ FAI$_w$"),
    ("D5-75", "D5--75"),
    ("ln D5-75", r"$\ln$ D5--75"),
    ("-0.0083 (-0.55)", "$-$0.0083 ($-$0.55)"),
    ("2010-2018", "2010--2018"),
    ("2010-05-06", "2010-05-06"),
    ("VR** and VR*(60/10)", r"VR$^{**}$ and VR$^{*}$(60/10)"),
    ("R2_OS 5%", r"$R^2_{\mathrm{OS}}$ 5\%"),
    ("x_y", r"x\_y"),
])
def test_tex(plain, latex):
    assert rt.tex(plain) == latex


def test_rendered_latex_is_well_formed(inp):
    for t in rt.all_tables(inp):
        out = rt.render_tex(t)
        for line in out.splitlines():
            if line.startswith(("%", r"\label")):          # comments and labels may use _
                continue
            assert line.count("$") % 2 == 0, (t.name, line)
            outside = line.split("$")[::2]
            assert not any("_" in seg.replace(r"\_", "") for seg in outside), (t.name, line)
        assert out.count("{") == out.count("}"), t.name
        body = [ln for ln in out.splitlines() if ln.endswith(r"\\")
                and not ln.startswith(r"\multicolumn")]
        ncol = len(t.header)
        assert all(ln.count(" & ") == ncol - 1 for ln in body), t.name


def test_main_writes_every_table(tmp_path):
    for f in ["h1_results.csv", "h1_results.md", "h2_results.csv"]:
        shutil.copy(REPORTS / f, tmp_path / f)
    tables = rt.main(tmp_path, tmp_path / "tables")
    written = sorted(p.stem for p in (tmp_path / "tables").glob("*.tex"))
    assert written == sorted(t.name for t in tables)
    md = (tmp_path / "results_tables.md").read_text(encoding="utf-8")
    assert md.count("### Table") == len(tables)
    assert "negative-result condition (HYPOTHESES.md) is met" in md
