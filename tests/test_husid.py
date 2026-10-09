import numpy as np
import pandas as pd

from fai.husid import husid_times, shortest_window, significant_times


def test_uniform_energy_gives_point_nine_of_the_day():
    t5, t95, d = significant_times(np.ones(390))
    assert np.isclose(t5, 19.5) and np.isclose(t95, 370.5) and np.isclose(d, 351.0)


def test_single_spike_collapses_duration():
    a2 = np.zeros(390)
    a2[123] = 1.0
    t5, t95, d = significant_times(a2)
    assert np.isclose(t5, 123.05) and np.isclose(t95, 123.95) and np.isclose(d, 0.9)


def test_two_equal_spikes():
    a2 = np.zeros(390)
    a2[[50, 300]] = 1.0
    t5, t95, d = significant_times(a2)
    assert np.isclose(t5, 50.1) and np.isclose(t95, 300.9)


def test_scale_invariance_and_nan_as_zero():
    rng = np.random.default_rng(0)
    A = pd.DataFrame(rng.standard_normal((3, 390)))
    A.iloc[1, 10:20] = np.nan
    base = husid_times(A)
    scaled = husid_times(A * 7.3)
    assert np.allclose(base.to_numpy(), scaled.to_numpy())
    filled = husid_times(A.fillna(0.0))
    assert np.allclose(base.to_numpy(), filled.to_numpy())


def test_empty_day_is_nan():
    A = pd.DataFrame(np.full((1, 390), np.nan))
    assert husid_times(A).isna().all(axis=None)


def test_shortest_window_limits():
    assert np.isclose(shortest_window(np.ones(390)), 195.0)
    spike = np.zeros(390)
    spike[77] = 1.0
    assert np.isclose(shortest_window(spike), 0.5)
    block = np.ones(390)
    block[100:110] = 100.0          # 1000 of 1380 energy in 10 minutes
    assert shortest_window(block) < 10


def test_husid_times_columns():
    A = pd.DataFrame(np.ones((2, 390)))
    out = husid_times(A)
    assert list(out.columns) == ["t5", "t95", "d5_95", "d5_75", "w50"]
    assert np.allclose(out["d5_75"], 0.7 * 390) and np.allclose(out["w50"], 195.0)
