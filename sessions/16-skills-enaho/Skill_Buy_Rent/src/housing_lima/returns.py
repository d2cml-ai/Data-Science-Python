"""Return statistics for the opportunity-cost agent (index levels -> annualized returns)."""

from __future__ import annotations

from typing import Iterable, Optional

import numpy as np
import pandas as pd


def usd_to_pen(r_usd: float, fx_change: float) -> float:
    """Return in soles of a USD asset: (1 + r_usd) * (1 + fx_change) - 1."""
    return (1.0 + r_usd) * (1.0 + fx_change) - 1.0


def real_return(r_nominal: float, inflation: float) -> float:
    return (1.0 + r_nominal) / (1.0 + inflation) - 1.0


def _monthly(levels: pd.Series) -> pd.Series:
    s = levels.dropna().sort_index()
    s.index = pd.to_datetime(s.index)
    return s.resample("ME").last().dropna()


def cagr(levels: pd.Series, years: int) -> Optional[float]:
    """Annualized return over the last `years` years of a (total-return) index."""
    s = _monthly(levels)
    if s.empty:
        return None
    end = s.index[-1]
    start_target = end - pd.DateOffset(years=years)
    tolerance = pd.Timedelta(days=3)  # month-end dates do not line up exactly (e.g. Feb 28 vs 29)
    if s.index[0] > start_target + tolerance:
        return None  # history too short
    start_val = s[s.index <= start_target + tolerance].iloc[-1]
    return float((s.iloc[-1] / start_val) ** (1.0 / years) - 1.0)


def annual_returns(levels: pd.Series) -> pd.Series:
    """Rolling 12-month returns from monthly levels."""
    s = _monthly(levels)
    return (s / s.shift(12) - 1.0).dropna()


def rolling_annualized(levels: pd.Series, window_years: int) -> pd.Series:
    s = _monthly(levels)
    k = 12 * window_years
    return ((s / s.shift(k)) ** (1.0 / window_years) - 1.0).dropna()


def summarize_index(levels: pd.Series, windows: Iterable[int] = (5, 10, 20, 30), band_window: int = 10) -> dict:
    """CAGR per window, volatility, worst 12-month return, and low/base/high from rolling returns.

    low/base/high = 25th percentile / median / 75th percentile of rolling `band_window`-year
    annualized returns; if history is too short, the window shrinks to what is available.
    """
    yearly = annual_returns(levels)
    out = {"cagr": {f"{w}y": cagr(levels, w) for w in windows},
           "volatility": float(yearly.std()) if len(yearly) > 2 else None,
           "worst_1y": float(yearly.min()) if not yearly.empty else None}
    s = _monthly(levels)
    span_years = (s.index[-1] - s.index[0]).days / 365.25 if len(s) > 1 else 0
    w = band_window
    while w > 1 and span_years < w + 2:
        w -= 1
    roll = rolling_annualized(levels, w) if w >= 1 else pd.Series(dtype=float)
    if roll.empty:
        out.update({"return_low": None, "return_base": None, "return_high": None, "band_window_years": None})
    else:
        out.update({"return_low": float(np.percentile(roll, 25)), "return_base": float(np.median(roll)),
                    "return_high": float(np.percentile(roll, 75)), "band_window_years": w})
    out["first_date"] = s.index[0].date().isoformat() if len(s) else None
    out["last_date"] = s.index[-1].date().isoformat() if len(s) else None
    return out
