"""The intraday-profile figure's helpers."""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("ushape", ROOT / "scripts" / "fig_ushape.py")
ushape = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ushape)


def test_profile_is_in_basis_points_over_the_chosen_days():
    days = pd.bdate_range("2010-01-04", periods=4)
    S2 = pd.DataFrame([[1e-8, 4e-8]] * 3 + [[1.0, 1.0]], index=days)   # last day not chosen
    p = ushape.profile(S2, days[:3])
    assert np.allclose(p["median"], [1.0, 2.0])
    assert (p["p10"] <= p["median"]).all() and (p["median"] <= p["p90"]).all()


def test_standouts_find_a_spike_and_clock_labels():
    med = pd.Series(np.ones(390))
    med[30] = 3.0
    top = ushape.standouts(med, k=1)
    assert top.index[0] == 30 and np.isclose(top.iloc[0], 3.0)
    assert ushape.clock(0) == "9:30" and ushape.clock(30) == "10:00" and ushape.clock(389) == "15:59"
