import numpy as np
import pandas as pd
import pytest

from housing_lima.returns import cagr, real_return, summarize_index, usd_to_pen


def steady_index(rate: float, years: int) -> pd.Series:
    dates = pd.date_range("2000-01-31", periods=12 * years + 1, freq="ME")
    return pd.Series((1 + rate) ** (np.arange(len(dates)) / 12), index=dates)


def test_usd_to_pen_formula():
    assert usd_to_pen(0.10, 0.0) == pytest.approx(0.10)
    assert usd_to_pen(0.10, 0.02) == pytest.approx(1.10 * 1.02 - 1)
    assert usd_to_pen(0.10, -0.02) == pytest.approx(1.10 * 0.98 - 1)


def test_real_return():
    assert real_return(0.05, 0.02) == pytest.approx(1.05 / 1.02 - 1)


def test_cagr_of_steady_index():
    s = steady_index(0.07, 25)
    assert cagr(s, 10) == pytest.approx(0.07, abs=1e-6)
    assert cagr(s, 30) is None  # not enough history


def test_summarize_index_band():
    out = summarize_index(steady_index(0.08, 30), band_window=10)
    assert out["return_base"] == pytest.approx(0.08, abs=1e-6)
    assert out["return_low"] <= out["return_base"] <= out["return_high"]
    assert out["worst_1y"] == pytest.approx(0.08, abs=1e-6)
