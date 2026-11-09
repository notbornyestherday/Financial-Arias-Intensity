#!/usr/bin/env python
"""Week 3 pivot check, as defined before it runs (D-028).

Trigger: the Pearson correlation of ln FAI_w with ln FAI (unweighted) over the test days
(``in_tests``, 2010-2025). FAI_w and FAI share the deseasonalizing and the normalizer,
so the only difference between them is the liquidity weighting. At 0.95 or above the
paper reframes around concentration (expected; it is already the headline).

Also reported, to keep the brief's version visible: the correlation of FAI_w with RV in
logs and in levels; the same trigger for the Corwin-Schultz weighting and the floored
1/C comparison; and the spread of ln f_bar (= ln FAI_w - ln FAI) next to that of ln FAI.
How each outcome is read is in paper/interpretation_table.md.

    python scripts/pivot_check.py            # primary: flagged prints removed (D-005)
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fai import config  # noqa: E402

TEST_YEARS = ("2010-01-01", "2025-12-31")
THRESHOLD = 0.95


def test_days(daily: pd.DataFrame) -> pd.DataFrame:
    need = {"in_tests", "rv", "fai", "fai_w", "fai_w_cs", "fai_c", "f_bar", "pi_missing"}
    missing = sorted(need - set(daily.columns))
    if missing:
        raise ValueError(f"daily table lacks {missing}: rerun the measures stage "
                         "(python scripts/run_all.py --stages measures, and with --drop-spikes)")
    d = daily.sort_index().loc[TEST_YEARS[0]:TEST_YEARS[1]]
    return d.loc[d["in_tests"].astype(bool)]


def _corr(x: pd.Series, y: pd.Series) -> tuple[float, int]:
    ok = np.isfinite(x) & np.isfinite(y)
    return float(np.corrcoef(x[ok], y[ok])[0, 1]), int(ok.sum())


def pivot(d: pd.DataFrame) -> dict:
    ln = lambda c: np.log(d[c].where(d[c] > 0))  # noqa: E731
    trig, n = _corr(ln("fai_w"), ln("fai"))
    rows = [
        ("ln FAI_w vs ln FAI (trigger, D-028)", trig, n),
        ("ln FAI_w vs ln RV", *_corr(ln("fai_w"), ln("rv"))),
        ("FAI_w vs RV (levels)", *_corr(d["fai_w"], d["rv"])),
        ("ln FAI vs ln RV", *_corr(ln("fai"), ln("rv"))),
        ("ln FAI_w(Corwin-Schultz) vs ln FAI", *_corr(ln("fai_w_cs"), ln("fai"))),
        ("ln FAI_c (floored 1/C) vs ln FAI", *_corr(ln("fai_c"), ln("fai"))),
    ]
    lf = np.log(d["f_bar"])
    return {"trigger": trig, "n": n, "reframe": trig >= THRESHOLD,
            "table": pd.DataFrame(rows, columns=["pair", "corr", "n"]),
            "sd_ln_fai": float(ln("fai").std()), "sd_ln_fbar": float(lf.std()),
            "fbar_range": (float(d["f_bar"].quantile(0.01)), float(d["f_bar"].quantile(0.99))),
            "pi_missing": float(d["pi_missing"].mean())}


def report(res: dict, name: str) -> list[str]:
    lo, hi = res["fbar_range"]
    return [f"## {name}", "",
            f"Trigger (D-028): corr(ln FAI_w, ln FAI) = **{res['trigger']:.4f}** over "
            f"{res['n']:,} test days: {'at or above' if res['reframe'] else 'below'} "
            f"{THRESHOLD}, so the paper {'reframes around concentration' if res['reframe'] else 'keeps the weighting as a contribution to test'}.",
            "",
            "| pair | corr | n |", "|---|---|---|",
            *[f"| {r.pair} | {r.corr:.4f} | {r.n:,} |" for r in res["table"].itertuples()],
            "",
            f"Why: ln FAI_w = ln FAI + ln f_bar, and ln f_bar (the energy-weighted average "
            f"damping factor) has SD {res['sd_ln_fbar']:.3f} across days against "
            f"{res['sd_ln_fai']:.3f} for ln FAI; f_bar runs from {lo:.3f} to {hi:.3f} "
            f"(1st to 99th percentile; bounds 1 and {np.pi / 2:.3f}). Minutes with no "
            f"liquidity percentile (weighted as typical): {res['pi_missing']:.1%} on average.",
            ""]


def main(symbol: str = "SPY") -> None:
    lines = ["# Pivot check (D-028)", "",
             "Written by `scripts/pivot_check.py`; the reading of each outcome was fixed in "
             "`paper/interpretation_table.md` before the run.", ""]
    for name, tag in [("Primary: flagged prints removed", "_nospikes"), ("Flagged prints kept", "")]:
        path = config.PROCESSED / f"{symbol}_daily{tag}.parquet"
        if path.exists():
            lines += report(pivot(test_days(pd.read_parquet(path))), name)
        elif tag == "_nospikes":
            sys.exit(f"{path.name} is missing: python scripts/run_all.py --stages clean,measures --drop-spikes")
    out = config.REPORTS / "pivot_check.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main(*sys.argv[1:])
