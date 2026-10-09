"""Week 4: event detection.

sigma_i(t) = trailing 15-minute deseasonalised volatility. Start when
sigma_i >= baseline + 3*theta; end after 15 consecutive minutes with
sigma_i <= baseline + 0.5*theta. Baseline and theta from the prior 30 days.
All measures are still computed on every day; detection only labels windows.
"""

from __future__ import annotations


def detect_events(*args, **kwargs):
    raise NotImplementedError("Week 4")
