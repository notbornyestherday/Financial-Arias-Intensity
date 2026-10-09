"""Central parameters.

Every number a robustness check might vary lives here, so Week 6 is a matter of
changing values rather than hunting through modules. Section references are to the
project brief.
"""

from __future__ import annotations

import os
from pathlib import Path

# Repo root: src/fai/config.py -> parents[2]. Override with FAI_ROOT if needed.
ROOT = Path(os.environ.get("FAI_ROOT", Path(__file__).resolve().parents[2]))
DATA = ROOT / "data"          # gitignored
RAW = DATA / "raw"
INTERIM = DATA / "interim"
PROCESSED = DATA / "processed"
REPORTS = ROOT / "reports"    # computed summaries only, safe to commit
REF = ROOT / "ref"            # small hand-maintained reference tables

TZ = "America/New_York"
FULL_DAY_MINUTES = 390

# --- Sample (Section 4; extended to 2025, see DECISIONS.md D-001) -------------
SAMPLE_START = "2009-01-01"   # 2009 is warm-up for the trailing windows
SAMPLE_END = "2025-12-31"
IN_SAMPLE = ("2010-01-01", "2018-12-31")
OUT_OF_SAMPLE = ("2019-01-01", "2025-12-31")

# --- Seasonality (Section 3) --------------------------------------------------
SEAS_WINDOW_DAYS = 60
SEAS_MIN_DAYS = 40
SEAS_METHOD = "rms"           # "rms" (brief) or "median" (robustness)

# --- Energy normalisation R_m -------------------------------------------------
RM_WINDOW_DAYS = 90
RM_MIN_DAYS = 60

# --- Husid / significant duration ---------------------------------------------
HUSID_LO = 0.05
HUSID_HI = 0.95
HUSID_MID = 0.75     # D5-75, the "strong phase" duration also used in seismology
W_FRAC = 0.50        # W50: shortest window holding half the day's energy

# --- Variance ratio for H1b (see HYPOTHESES.md) -------------------------------
VR_BASE_MIN = 5
VR_LONG_MIN = 30

# --- Liquidity weighting (Week 3) ---------------------------------------------
AMIHUD_WINDOW_MIN = 30
LIQ_PCT_WINDOW_DAYS = 60
ZETA_CAP = 0.99
CMIN_PERCENTILE = 5

# --- Event detection (Week 4) -------------------------------------------------
EVT_SIGMA_WINDOW_MIN = 15
EVT_BASELINE_DAYS = 30
EVT_START_K = 3.0
EVT_END_K = 0.5
EVT_END_RUN_MIN = 15

# --- Cleaning -----------------------------------------------------------------
# A bar is a "spike-and-revert" suspect if its return is SPIKE_Z robust SDs from
# zero and the next minute undoes at least (1 - SPIKE_REVERT_FRAC) of it.
SPIKE_Z = 8.0
SPIKE_REVERT_FRAC = 0.3

# --- Named days (Section 5). Illustrations only; evidence is full-sample. -----
EVENTS = {
    "2010-05-06": "Flash Crash",
    "2015-08-24": "ETF open dislocation",
    "2018-02-05": "Volmageddon",
    "2020-03-09": "COVID circuit breaker",
    "2020-03-12": "COVID circuit breaker",
    "2020-03-16": "COVID circuit breaker",
    "2020-03-18": "COVID circuit breaker",
    "2024-08-05": "Yen-carry unwind",
    "2025-04-03": "Tariff selloff",
    "2025-04-04": "Tariff selloff",
    "2025-04-07": "Tariff headline whipsaw",
    "2025-04-09": "Tariff pause rally",
}

# Market-wide (Level 1) circuit-breaker halts. Detect the actual gaps from the
# data; this list is only for flagging.
MARKET_HALT_DAYS = ["2020-03-09", "2020-03-12", "2020-03-16", "2020-03-18"]

# Days with known single-security halts or busted/suspicious prints market-wide.
# Whether SPY itself was affected is an empirical question for the DQ report.
PRINT_QUALITY_DAYS = ["2010-05-06", "2015-08-24"]
