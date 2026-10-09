"""Husid curve, significant durations, and the shortest half-energy window.

Continuous-time convention: minute tau occupies [tau, tau+1). H(0) = 0 and
H(tau+1) = cumulative share of energy through minute tau, linearly interpolated.
So uniform energy over N minutes gives t5 = 0.05N, t95 = 0.95N, D5-95 = 0.9N
(351 minutes for a full day), and a single-minute spike gives D5-95 = 0.9.
R_m cancels, as does any constant rescaling of the signal.

All three diagnostics are Husid-curve durations: the time H takes to climb a set amount.
D5-95 (Trifunac and Brady 1975) and D5-75 (Bommer et al. 2009) fix the start at H = 0.05.
W50 is the shortest time H takes to climb 0.5, with the start free to move. An earthquake
record starts near quiet, so H = 0.05 falls where strong shaking begins; a trading day
accumulates background energy at a steady rate, so a fixed 5% start falls in background.
W50 is the energy-weighted analogue of the "shortest half" used in robust statistics
(Rousseeuw and Leroy 1988). scripts/sim_duration_power.py compares the three.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config


def husid_curve(a2: np.ndarray) -> np.ndarray:
    """H at u = 0..N for one day's squared signal (NaN treated as zero energy)."""
    e = np.nan_to_num(np.asarray(a2, float), nan=0.0)
    total = e.sum()
    if not np.isfinite(total) or total <= 0:
        return np.full(e.size + 1, np.nan)
    H = np.concatenate([[0.0], np.cumsum(e) / total])
    H[-1] = 1.0
    return H


def crossing_time(H: np.ndarray, p: float) -> float:
    """First u with H(u) = p, by linear interpolation."""
    if np.isnan(H).any():
        return np.nan
    i = int(np.searchsorted(H, p, side="left"))  # first H[i] >= p; H[0]=0 so i >= 1
    return (i - 1) + (p - H[i - 1]) / (H[i] - H[i - 1])


def significant_times(a2_row, lo: float = config.HUSID_LO,
                      hi: float = config.HUSID_HI) -> tuple[float, float, float]:
    H = husid_curve(a2_row)
    t_lo, t_hi = crossing_time(H, lo), crossing_time(H, hi)
    return t_lo, t_hi, t_hi - t_lo


def shortest_window(a2_row, frac: float = config.W_FRAC) -> float:
    """Length (minutes) of the shortest window holding ``frac`` of the day's energy.

    Windows start on minute boundaries; the end is interpolated as in the Husid curve.
    Uniform energy gives frac * N; a single-minute spike gives frac.
    """
    H = husid_curve(a2_row)
    if np.isnan(H).any():
        return np.nan
    starts = np.arange(H.size - 1)
    targets = H[:-1] + frac
    ok = targets <= 1.0 + 1e-12
    starts, targets = starts[ok], np.minimum(targets[ok], 1.0)
    j = np.searchsorted(H, targets, side="left")
    j = np.maximum(j, starts + 1)
    end = (j - 1) + (targets - H[j - 1]) / (H[j] - H[j - 1])
    return float((end - starts).min())


def husid_times(A: pd.DataFrame, lo: float = config.HUSID_LO,
                hi: float = config.HUSID_HI, mid: float = config.HUSID_MID,
                frac: float = config.W_FRAC) -> pd.DataFrame:
    """Per-row t5, t95 (minutes after the open), D5-95, D5-75 and W50."""
    a2 = A.to_numpy(float) ** 2
    rows = []
    for row in a2:
        H = husid_curve(row)
        t_lo, t_hi, t_mid = (crossing_time(H, p) for p in (lo, hi, mid))
        rows.append((t_lo, t_hi, t_hi - t_lo, t_mid - t_lo, shortest_window(row, frac)))
    cols = ["t5", "t95", "d5_95", "d5_75", "w50"]
    return pd.DataFrame(np.array(rows, float).reshape(-1, 5), index=A.index, columns=cols)
