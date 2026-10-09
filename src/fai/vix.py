"""Week 5: VIX tests (renamed from tests_vix.py; see DECISIONS.md D-006).

* next_day_regression: d ln VIX_{t+1} on X_t, ln RV_t, r_t, d ln VIX_t with
  Newey-West SEs, lag rule floor(4 (T/100)^(2/9)).
* spike_logit: P(d ln VIX_{t+1} > ln 1.2).
* out_of_sample: fit 2010-2018, fixed coefficients, evaluate 2019-2025, Clark-West test.
Timing: VIX closes after SPY (16:15 vs 16:00 ET), so day-t SPY measures are known
before the d ln VIX_{t+1} window opens.
"""

from __future__ import annotations


def next_day_regression(*args, **kwargs):
    raise NotImplementedError("Week 5")


def spike_logit(*args, **kwargs):
    raise NotImplementedError("Week 5")


def out_of_sample(*args, **kwargs):
    raise NotImplementedError("Week 5")
