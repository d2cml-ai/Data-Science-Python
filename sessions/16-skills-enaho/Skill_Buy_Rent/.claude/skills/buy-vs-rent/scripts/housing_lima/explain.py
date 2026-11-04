"""Explain a buy-vs-rent result step by step. Used by the dashboard, the figures and the report.

Everything here is computed with housing_lima.model.simulate, so the explanation always matches the verdict.
The story the functions tell:

1. Both households start with the same cash and spend the same amount every month.
2. The buyer's money goes into a home (minus interest, taxes, insurance); the renter's goes into rent
   and an investment portfolio.
3. After H years we compare what each one owns.
4. The verdict counts in how many mortgage-rate x investment scenarios buying comes out ahead.
5. The flip points say how far each input would have to move for the answer to change.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .model import Scenario, monthly_rate, mortgage_payment, remaining_balance, simulate


def delta_at(s: Scenario, horizon: int) -> float:
    """Buyer's wealth minus renter's wealth after `horizon` years (> 0: buying wins)."""
    return float(simulate(s, years=horizon).at(horizon)["delta"])


# ------------------------------------------------------------------ step 2: monthly money, year 1
def first_year_monthly(s: Scenario) -> dict:
    """Average monthly outflow in year 1 for both households, split by where the money goes.

    The buyer's mortgage payment is split into interest (gone) and principal (becomes home equity).
    The renter spends the same total: rent, the building fee, and the rest is invested.
    """
    p0 = s.price * (1.0 - s.negotiation_discount)
    loan = p0 * (1.0 - s.down_payment_pct)
    pmt = mortgage_payment(loan, s.mortgage_rate, s.loan_term_years)
    months = min(12, s.loan_term_years * 12)
    principal = (loan - remaining_balance(loan, s.mortgage_rate, s.loan_term_years, months)) / 12.0
    interest = pmt * months / 12.0 - principal
    taxes_ins = (s.property_tax_pct + s.insurance_pct) * p0 / 12.0
    fee = s.maintenance_fee_monthly
    buyer_total = interest + principal + taxes_ins + fee
    renter_fee = fee if s.renter_pays_maintenance else 0.0
    invested = buyer_total - s.monthly_rent - renter_fee
    return {
        "buyer": {"Mortgage interest": interest, "Mortgage principal (becomes equity)": principal,
                  "Property tax and insurance": taxes_ins, "Building fee": fee},
        "renter": {"Rent": s.monthly_rent, "Building fee": renter_fee,
                   "Invested each month (difference)": invested},
        "total": buyer_total,
        "payment": pmt,
    }


# ------------------------------------------------------------------ step 3: what each one owns
def wealth_breakdown(s: Scenario, horizon: int) -> dict:
    """Components of each household's wealth after `horizon` years (they add up to the model's numbers)."""
    sim = simulate(s, years=horizon)
    r = sim.at(horizon)
    house, balance = float(r["house_value"]), float(r["mortgage_balance"])
    sell = house * s.sell_cost_pct
    contributions = float(r["cum_buyer_outflow"] - r["cum_renter_outflow"])
    gains = float(r["w_rent"]) - sim.upfront_cash - contributions
    return {
        "horizon": horizon,
        "upfront": sim.upfront_cash,
        "down_payment": sim.down_payment,
        "buy_costs": sim.upfront_cash - sim.down_payment,
        "buyer": [("Home value", house), ("Selling costs", -sell), ("Mortgage still owed", -balance)],
        "renter": [("Day-1 cash invested", sim.upfront_cash), ("Monthly differences invested", contributions),
                   ("Investment returns", gains)],
        "w_buy": float(r["w_buy"]),
        "w_rent": float(r["w_rent"]),
        "delta": float(r["delta"]),
        "cash_spent": sim.upfront_cash + float(r["cum_buyer_outflow"]),
        "interest_paid": _interest_paid(sim.loan, s, horizon),
        "rent_paid": _rent_paid(s, horizon),
    }


def _interest_paid(loan: float, s: Scenario, horizon: int) -> float:
    months = min(horizon, s.loan_term_years) * 12
    pmt = mortgage_payment(loan, s.mortgage_rate, s.loan_term_years)
    return pmt * months - (loan - remaining_balance(loan, s.mortgage_rate, s.loan_term_years, months))


def _rent_paid(s: Scenario, horizon: int) -> float:
    return sum(12 * s.monthly_rent * (1 + s.rent_growth) ** y for y in range(horizon))


# ------------------------------------------------------------------ the three key comparisons
def drivers(s: Scenario) -> list[dict]:
    """The three comparisons that decide most buy-vs-rent results, in plain words.

    favours = "buy" or "rent": which side this comparison pushes toward.
    """
    rent_yield = 12 * s.monthly_rent / (s.price * (1 - s.negotiation_discount))
    return [
        {"name": "Rent vs cost of borrowing",
         "left": ("Rent per year, as % of the price", rent_yield),
         "right": ("Mortgage rate", s.mortgage_rate),
         "favours": "buy" if rent_yield > s.mortgage_rate else "rent",
         "why": "Renting is cheap relative to the price when the yearly rent is a small share of the price "
                "compared with the mortgage rate."},
        {"name": "Home growth vs investment return",
         "left": ("Home price growth per year", s.price_growth),
         "right": ("Investment return per year", s.opportunity_return),
         "favours": "buy" if s.price_growth > s.opportunity_return else "rent",
         "why": "The buyer's money grows with the home; the renter's grows with the investment."},
        {"name": "Home growth vs inflation",
         "left": ("Home price growth per year", s.price_growth),
         "right": ("Inflation", s.inflation),
         "favours": "buy" if s.price_growth > s.inflation else "rent",
         "why": "If homes grow slower than inflation, the home loses value in real terms while taxes, "
                "insurance and the fee keep rising with inflation."},
    ]


# ------------------------------------------------------------------ step 5: what would flip it
FLIP_PARAMS = {
    # name: (label, lower bound, upper bound, is a rate shown in %)
    "mortgage_rate": ("Mortgage rate", 0.001, 0.25, True),
    "opportunity_return": ("Investment return", -0.05, 0.25, True),
    "price_growth": ("Home price growth per year", -0.05, 0.15, True),
    "rent_growth": ("Rent growth per year", -0.05, 0.15, True),
    "monthly_rent": ("Monthly rent (S/)", None, None, False),
    "price": ("Purchase price (S/)", None, None, False),
}


@dataclass
class FlipPoint:
    param: str
    label: str
    current: float
    flip: Optional[float]           # value where buy and rent are equal; None if not in the searched range
    buy_wins_when: Optional[str]    # "above" or "below" the flip value
    is_rate: bool

    def sentence(self) -> str:
        fmt = (lambda v: f"{v:.2%}") if self.is_rate else (lambda v: f"S/ {v:,.0f}")
        if self.flip is None:
            return f"{self.label}: no realistic value changes the answer."
        return f"{self.label}: buying wins {self.buy_wins_when} {fmt(self.flip)} (now {fmt(self.current)})."


def flip_points(s: Scenario, horizon: int, params: Optional[list[str]] = None, iterations: int = 30) -> list[FlipPoint]:
    """For each input, the value at which buyer and renter end up equal after `horizon` years (bisection)."""
    out = []
    for name in params or list(FLIP_PARAMS):
        label, lo, hi, is_rate = FLIP_PARAMS[name]
        current = float(getattr(s, name))
        if lo is None:
            lo, hi = current * 0.3, current * 2.5
        f = lambda v: delta_at(s.with_(**{name: v}), horizon)  # noqa: E731
        d_lo, d_hi = f(lo), f(hi)
        if (d_lo > 0) == (d_hi > 0):
            out.append(FlipPoint(name, label, current, None, None, is_rate))
            continue
        a, b, fa = lo, hi, d_lo
        for _ in range(iterations):
            m = (a + b) / 2
            fm = f(m)
            if (fm > 0) == (fa > 0):
                a, fa = m, fm
            else:
                b = m
        out.append(FlipPoint(name, label, current, (a + b) / 2, "below" if d_lo > 0 else "above", is_rate))
    return out


# ------------------------------------------------------------------ step 4: the scenario vote
def scenario_vote(s: Scenario, horizon: int, rates: list[float], options: list[dict],
                  thresholds: dict) -> dict:
    """Re-run the verdict grid (mortgage rates x investment options) for one scenario.

    options: dicts with id, name and return (decimal). Returns the cells, the share and the label.
    """
    cells = []
    for opt in options:
        for rate in rates:
            d = delta_at(s.with_(mortgage_rate=rate, opportunity_return=opt["return"]), horizon)
            cells.append({"option_id": opt["id"], "option": opt["name"], "mortgage_rate": rate, "delta": d,
                          "buy_wins": d > 0})
    share = sum(c["buy_wins"] for c in cells) / len(cells) if cells else 0.0
    label = "buy" if share >= thresholds["buy"] else "rent" if share <= thresholds["rent"] else "depends"
    return {"cells": cells, "share": share, "label": label, "n": len(cells)}


__all__ = ["FlipPoint", "delta_at", "drivers", "first_year_monthly", "flip_points", "monthly_rate",
           "scenario_vote", "wealth_breakdown"]
