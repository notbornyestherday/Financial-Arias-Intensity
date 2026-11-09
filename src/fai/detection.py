"""Event detection (brief Section 3; D-032). Exploratory: it labels windows only.

sigma(t) is the root mean square of the deseasonalized return over the trailing 15
minutes of the same day (from 5 minutes on, so nothing is detected before 9:34).
Each day's baseline and theta come from all minutes of the prior 30 sessions in the
tests: baseline = median of sigma, theta = 1.4826 x its median absolute deviation (a
robust standard deviation), so one crisis day does not raise the threshold for the
next 30 days. An event starts when sigma >= baseline + 3 theta and ends at the last
minute before 15 consecutive minutes with sigma <= baseline + 0.5 theta, or at the
close, in which case it is flagged as cut off.

Every measure is still computed on every day; detection only says where the
volatile stretches were (selecting windows by volatility would be circular).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config

SIGMA_MIN_MIN = 5          # minutes needed in the trailing window (D-032)
MAD_TO_SD = 1.4826         # median absolute deviation -> SD under normality


def trailing_sigma(Rt: pd.DataFrame, window: int = config.EVT_SIGMA_WINDOW_MIN,
                   min_periods: int = SIGMA_MIN_MIN) -> pd.DataFrame:
    """RMS of r~ over the trailing ``window`` minutes, within each day."""
    ms = (Rt ** 2).T.rolling(window, min_periods=min_periods).mean().T
    return np.sqrt(ms)


def thresholds(sigma: pd.DataFrame, eligible, days: int = config.EVT_BASELINE_DAYS) -> pd.DataFrame:
    """Per day: baseline (median) and theta (1.4826 x MAD) of sigma over all minutes of
    the prior ``days`` eligible sessions. NaN until ``days`` such sessions exist."""
    x = sigma.to_numpy(float)
    elig = np.flatnonzero(np.asarray(eligible, bool))
    base = np.full(len(x), np.nan)
    theta = np.full(len(x), np.nan)
    for d in range(len(x)):
        prior = elig[elig < d][-days:]
        if prior.size < days:
            continue
        v = x[prior].ravel()
        v = v[np.isfinite(v)]
        if v.size == 0:
            continue
        m = np.median(v)
        base[d] = m
        theta[d] = MAD_TO_SD * np.median(np.abs(v - m))
    return pd.DataFrame({"baseline": base, "theta": theta}, index=sigma.index)


def detect_day(s: np.ndarray, start_level: float, end_level: float,
               run: int = config.EVT_END_RUN_MIN) -> list[tuple[int, int, bool]]:
    """Events in one day's sigma path: (first minute, last minute, cut off at close)."""
    events = []
    n, t = len(s), 0
    while t < n:
        if not (np.isfinite(s[t]) and s[t] >= start_level):
            t += 1
            continue
        first, quiet, u, last = t, 0, t + 1, None
        while u < n:
            quiet = quiet + 1 if (np.isfinite(s[u]) and s[u] <= end_level) else 0
            if quiet == run:
                last = u - run              # the minute before the quiet run began
                break
            u += 1
        if last is None:
            events.append((first, n - 1, True))
            break
        events.append((first, last, False))
        t = u + 1
    return events


def detect_events(Rt: pd.DataFrame, eligible,
                  start_k: float = config.EVT_START_K,
                  end_k: float = config.EVT_END_K) -> tuple[pd.DataFrame, pd.DataFrame]:
    """All events, and a per-day summary.

    Events: day, first and last minute (after the open), cut_off, minutes, energy and
    share of the day's energy, peak sigma. Days: n_events, event_minutes,
    energy_share_events, and the largest event's (by energy) first and last minute.
    Days without a baseline (warm-up) get NaN; days with a baseline and no event get 0.
    """
    sigma = trailing_sigma(Rt)
    th = thresholds(sigma, eligible)
    e2 = (Rt ** 2).to_numpy(float)
    S = sigma.to_numpy(float)
    rows, days = [], []
    for i, day in enumerate(Rt.index):
        b, th_ = th.iat[i, 0], th.iat[i, 1]
        total = np.nansum(e2[i])
        if not (np.isfinite(b) and np.isfinite(th_)) or total <= 0:
            days.append({"n_events": np.nan, "event_minutes": np.nan,
                         "energy_share_events": np.nan, "largest_start": np.nan,
                         "largest_end": np.nan})
            continue
        found = detect_day(S[i], b + start_k * th_, b + end_k * th_)
        best, best_e, minutes, energy = None, -1.0, 0, 0.0
        for first, last, cut in found:
            en = float(np.nansum(e2[i, first:last + 1]))
            rows.append({"day": day, "start": first, "end": last, "cut_off": cut,
                         "minutes": last - first + 1, "energy": en,
                         "energy_share": en / total,
                         "peak_sigma": float(np.nanmax(S[i, first:last + 1]))})
            minutes += last - first + 1
            energy += en
            if en > best_e:
                best, best_e = (first, last), en
        days.append({"n_events": len(found), "event_minutes": minutes,
                     "energy_share_events": energy / total,
                     "largest_start": best[0] if best else np.nan,
                     "largest_end": best[1] if best else np.nan})
    events = pd.DataFrame(rows, columns=["day", "start", "end", "cut_off", "minutes",
                                         "energy", "energy_share", "peak_sigma"])
    summary = pd.DataFrame(days, index=Rt.index).join(th)
    return events, summary
