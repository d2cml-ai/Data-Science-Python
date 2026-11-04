"""Buy vs rent financial model. Single source of truth for the analysis agent and the dashboard.

All amounts are nominal soles; annual rates are decimals (0.08 = 8%).
See skills/rent-vs-buy-model/references/formulas.md for the derivation.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Optional

import numpy as np
import pandas as pd

from .subsidy import NoSubsidy, SubsidyProvider

MIN_DOWN_PAYMENT = 0.05
MAX_DOWN_PAYMENT = 0.50
_EPS = 1e-9


def monthly_rate(annual_effective: float) -> float:
    """Monthly rate equivalent to an annual effective rate (TEA)."""
    return (1.0 + annual_effective) ** (1.0 / 12.0) - 1.0


def mortgage_payment(loan: float, tea: float, term_years: int) -> float:
    """Fixed monthly payment of a French-style (constant payment) mortgage."""
    n = int(term_years * 12)
    if loan <= 0:
        return 0.0
    i = monthly_rate(tea)
    if abs(i) < 1e-12:
        return loan / n
    return loan * i / (1.0 - (1.0 + i) ** (-n))


def remaining_balance(loan: float, tea: float, term_years: int, k: int) -> float:
    """Balance left after k monthly payments; 0 once the loan is paid off."""
    n = int(term_years * 12)
    if loan <= 0 or k >= n:
        return 0.0
    if k <= 0:
        return float(loan)
    i = monthly_rate(tea)
    m = mortgage_payment(loan, tea, term_years)
    if abs(i) < 1e-12:
        return max(loan - m * k, 0.0)
    g = (1.0 + i) ** k
    return max(loan * g - m * (g - 1.0) / i, 0.0)


@dataclass(frozen=True)
class Scenario:
    """One buy-vs-rent scenario. Every market input is explicit: no hidden zeros."""

    price: float                    # realistic asking price, soles
    monthly_rent: float             # realistic rent for a comparable home, soles/month
    down_payment_pct: float         # decimal, 0.05-0.50
    mortgage_rate: float            # TEA, decimal
    opportunity_return: float       # annual return of the renter's portfolio, decimal, in soles
    price_growth: float             # annual house price growth
    rent_growth: float              # annual rent growth (applied in yearly steps)
    inflation: float                # annual CPI inflation (ownership costs and real terms)
    buy_cost_pct: float             # buying costs, share of price paid
    sell_cost_pct: float            # selling costs, share of sale value
    property_tax_pct: float         # annual property tax, share of price paid
    insurance_pct: float            # annual insurance, share of price paid
    maintenance_fee_monthly: float  # building fee (mantenimiento), soles/month at year 1
    loan_term_years: int = 20
    negotiation_discount: float = 0.0
    renter_pays_maintenance: bool = True

    def __post_init__(self) -> None:
        if self.price <= 0:
            raise ValueError("price must be positive")
        if self.monthly_rent < 0:
            raise ValueError("monthly_rent cannot be negative")
        if not (MIN_DOWN_PAYMENT - _EPS <= self.down_payment_pct <= MAX_DOWN_PAYMENT + _EPS):
            raise ValueError("down_payment_pct must be between 0.05 and 0.50 (5%-50%)")
        if self.loan_term_years < 1:
            raise ValueError("loan_term_years must be at least 1")
        if not (0.0 <= self.negotiation_discount < 0.9):
            raise ValueError("negotiation_discount must be in [0, 0.9)")
        for name in ("mortgage_rate", "opportunity_return", "price_growth", "rent_growth", "inflation"):
            if getattr(self, name) <= -1.0:
                raise ValueError(f"{name} must be greater than -100%")
        for name in ("buy_cost_pct", "sell_cost_pct", "property_tax_pct", "insurance_pct", "maintenance_fee_monthly"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} cannot be negative")

    def with_(self, **changes) -> "Scenario":
        return replace(self, **changes)


@dataclass
class SimulationResult:
    scenario: Scenario
    yearly: pd.DataFrame            # one row per year 0..years
    price_paid: float
    down_payment: float
    loan: float
    monthly_payment: float
    upfront_cash: float
    subsidy: float
    renter_budget_exhausted: bool
    first_exhausted_month: Optional[int] = None
    warnings: list[str] = field(default_factory=list)

    def at(self, horizon: int) -> pd.Series:
        return self.yearly.loc[self.yearly["year"] == horizon].iloc[0]

    def break_even(self) -> tuple[Optional[int], bool]:
        return break_even(self.yearly)


def simulate(s: Scenario, years: int = 30, subsidy: Optional[SubsidyProvider] = None) -> SimulationResult:
    """Month-by-month simulation; returns buyer and renter wealth at the end of each year."""
    subsidy = subsidy or NoSubsidy()
    p0 = s.price * (1.0 - s.negotiation_discount)
    down = s.down_payment_pct * p0
    sub = max(float(subsidy.amount(s, p0)), 0.0)
    loan = max(p0 - down - sub, 0.0)
    n = s.loan_term_years * 12
    pmt = mortgage_payment(loan, s.mortgage_rate, s.loan_term_years)
    j = monthly_rate(s.opportunity_return)

    upfront = down + s.buy_cost_pct * p0
    portfolio = upfront
    exhausted_at: Optional[int] = None

    rows = [_year_row(0, s, p0, loan, portfolio, 0.0, 0.0)]
    cum_buy_out = 0.0
    cum_rent_out = 0.0
    for t in range(1, years * 12 + 1):
        y = (t - 1) // 12  # completed years before this month
        infl_factor = (1.0 + s.inflation) ** y
        fee = s.maintenance_fee_monthly * infl_factor
        ownership = (s.property_tax_pct + s.insurance_pct) * p0 / 12.0 * infl_factor + fee
        buyer_out = (pmt if t <= n else 0.0) + ownership
        renter_out = s.monthly_rent * (1.0 + s.rent_growth) ** y + (fee if s.renter_pays_maintenance else 0.0)
        portfolio = portfolio * (1.0 + j) + (buyer_out - renter_out)
        cum_buy_out += buyer_out
        cum_rent_out += renter_out
        if portfolio < 0 and exhausted_at is None:
            exhausted_at = t
        if t % 12 == 0:
            rows.append(_year_row(t // 12, s, p0, loan, portfolio, cum_buy_out, cum_rent_out))

    yearly = pd.DataFrame(rows)
    warnings = []
    if exhausted_at is not None:
        warnings.append("renter_budget_exhausted")
    return SimulationResult(
        scenario=s, yearly=yearly, price_paid=p0, down_payment=down, loan=loan,
        monthly_payment=pmt, upfront_cash=upfront, subsidy=sub,
        renter_budget_exhausted=exhausted_at is not None,
        first_exhausted_month=exhausted_at, warnings=warnings,
    )


def _year_row(h: int, s: Scenario, p0: float, loan: float, portfolio: float,
              cum_buy_out: float, cum_rent_out: float) -> dict:
    house_value = p0 * (1.0 + s.price_growth) ** h
    balance = remaining_balance(loan, s.mortgage_rate, s.loan_term_years, 12 * h)
    w_buy = house_value * (1.0 - s.sell_cost_pct) - balance
    w_rent = portfolio
    deflator = (1.0 + s.inflation) ** h
    return {
        "year": h,
        "house_value": house_value,
        "mortgage_balance": balance,
        "w_buy": w_buy,
        "w_rent": w_rent,
        "delta": w_buy - w_rent,
        "w_buy_real": w_buy / deflator,
        "w_rent_real": w_rent / deflator,
        "delta_real": (w_buy - w_rent) / deflator,
        "cum_buyer_outflow": cum_buy_out,
        "cum_renter_outflow": cum_rent_out,
    }


def break_even(yearly: pd.DataFrame) -> tuple[Optional[int], bool]:
    """First year (1..max) where buying beats renting, and whether it turns negative again later."""
    scan = yearly[yearly["year"] >= 1]
    positive = scan["delta"].to_numpy() > 0
    if not positive.any():
        return None, False
    first_idx = int(np.argmax(positive))
    first_year = int(scan["year"].iloc[first_idx])
    reverts = bool((~positive[first_idx:]).any())
    return first_year, reverts


def rate_grid(market_rate: float, offsets: list[float], floor: float = 0.001) -> list[float]:
    """Mortgage rates around the market average, e.g. average -2..+2 percentage points."""
    return sorted({round(max(market_rate + o, floor), 6) for o in offsets})
