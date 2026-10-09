"""Week 3: liquidity proxies and the bounded damping weight.

Planned (Section 3 of the brief):
* amihud(minutes): |r| / (price * volume) over a trailing 30-minute window, lagged one
  bar so the proxy never contains the return it weights.
* corwin_schultz(minutes): two-bar high/low spread estimator, negatives set to 0.
* liquidity_percentile(proxy): percentile against the trailing 60-day distribution
  (prior days only); high liquidity -> high zeta.
* fai_weighted: sum f(zeta_t) a_t^2 / R_m with f from measures.damping_factor.
* fai_floored: sum a_t^2 / (R_m * max(C_t, c_min)), the comparison.
"""

from __future__ import annotations


def amihud(*args, **kwargs):
    raise NotImplementedError("Week 3")


def corwin_schultz(*args, **kwargs):
    raise NotImplementedError("Week 3")


def liquidity_percentile(*args, **kwargs):
    raise NotImplementedError("Week 3")
