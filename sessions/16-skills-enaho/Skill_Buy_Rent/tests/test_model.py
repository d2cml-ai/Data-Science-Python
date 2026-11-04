import pytest

from housing_lima import model
from housing_lima.model import Scenario, mortgage_payment, remaining_balance, simulate
from housing_lima.subsidy import NoSubsidy, SubsidyProvider


def base(**kw) -> Scenario:
    values = dict(
        price=350_000, monthly_rent=1_800, down_payment_pct=0.20, mortgage_rate=0.085,
        opportunity_return=0.06, price_growth=0.03, rent_growth=0.03, inflation=0.025,
        buy_cost_pct=0.04, sell_cost_pct=0.03, property_tax_pct=0.002, insurance_pct=0.003,
        maintenance_fee_monthly=250, loan_term_years=20,
    )
    values.update(kw)
    return Scenario(**values)


def test_amortization_payment_and_payoff():
    m = mortgage_payment(100_000, 0.08, 20)
    assert m == pytest.approx(819, abs=1)
    assert remaining_balance(100_000, 0.08, 20, 240) == pytest.approx(0, abs=1e-6)
    assert remaining_balance(100_000, 0.08, 20, 0) == 100_000


def test_balance_is_decreasing():
    balances = [remaining_balance(100_000, 0.08, 20, k) for k in range(0, 241, 12)]
    assert all(a > b for a, b in zip(balances, balances[1:]))


def test_zero_rate_loan():
    assert mortgage_payment(120_000, 0.0, 10) == pytest.approx(1_000)
    assert remaining_balance(120_000, 0.0, 10, 60) == pytest.approx(60_000)


def test_identity_at_time_zero():
    s = base(price_growth=0.0, rent_growth=0.0, inflation=0.0)
    r = simulate(s, years=5)
    row0 = r.at(0)
    expected = -(s.buy_cost_pct + s.sell_cost_pct) * s.price
    assert row0["delta"] == pytest.approx(expected)


def test_identity_with_negotiation_discount():
    s = base(negotiation_discount=0.10)
    p0 = s.price * 0.9
    assert simulate(s, years=1).at(0)["delta"] == pytest.approx(-(s.buy_cost_pct + s.sell_cost_pct) * p0)


@pytest.mark.parametrize("horizon", [5, 10, 20, 30])
def test_higher_mortgage_rate_lowers_buying_advantage(horizon):
    low = simulate(base(mortgage_rate=0.07)).at(horizon)["delta"]
    high = simulate(base(mortgage_rate=0.10)).at(horizon)["delta"]
    assert high < low


@pytest.mark.parametrize("horizon", [5, 10, 20, 30])
def test_higher_opportunity_return_lowers_buying_advantage(horizon):
    low = simulate(base(opportunity_return=0.04)).at(horizon)["delta"]
    high = simulate(base(opportunity_return=0.09)).at(horizon)["delta"]
    assert high < low


def test_horizon_shorter_than_term_repays_balance():
    s = base(loan_term_years=20)
    r = simulate(s, years=30)
    row = r.at(10)
    expected_balance = remaining_balance(r.loan, s.mortgage_rate, 20, 120)
    assert row["mortgage_balance"] == pytest.approx(expected_balance)
    assert row["w_buy"] == pytest.approx(row["house_value"] * (1 - s.sell_cost_pct) - expected_balance)


def test_horizon_longer_than_term_has_no_payments_after_term():
    s = base(loan_term_years=15, maintenance_fee_monthly=0, property_tax_pct=0, insurance_pct=0)
    r = simulate(s, years=30)
    assert r.at(20)["mortgage_balance"] == 0
    y = r.yearly.set_index("year")
    buyer_outflow_year_16 = y.loc[16, "cum_buyer_outflow"] - y.loc[15, "cum_buyer_outflow"]
    buyer_outflow_year_15 = y.loc[15, "cum_buyer_outflow"] - y.loc[14, "cum_buyer_outflow"]
    assert buyer_outflow_year_16 == pytest.approx(0)
    assert buyer_outflow_year_15 == pytest.approx(12 * r.monthly_payment)


def test_real_terms_deflate_by_inflation():
    s = base(inflation=0.03)
    row = simulate(s).at(10)
    assert row["w_buy_real"] == pytest.approx(row["w_buy"] / 1.03 ** 10)
    assert row["delta_real"] == pytest.approx(row["delta"] / 1.03 ** 10)


def test_break_even_found_and_reverts_flag():
    r = simulate(base(opportunity_return=0.02))
    year, reverts = r.break_even()
    assert year is not None and 1 <= year <= 30
    assert isinstance(reverts, bool)


def test_break_even_none_when_renting_always_wins():
    r = simulate(base(opportunity_return=0.15, price_growth=0.0, monthly_rent=600))
    assert r.break_even() == (None, False)


def test_renter_budget_exhausted_flag():
    # Rent far above the buyer's outflow drains the renter's portfolio.
    r = simulate(base(monthly_rent=9_000, rent_growth=0.05))
    assert r.renter_budget_exhausted
    assert "renter_budget_exhausted" in r.warnings


@pytest.mark.parametrize("bad", [0.0, 0.04, 0.51])
def test_down_payment_bounds(bad):
    with pytest.raises(ValueError):
        base(down_payment_pct=bad)


def test_no_subsidy_is_default_and_provider_reduces_loan():
    class Fixed(SubsidyProvider):
        def amount(self, scenario, price_paid):
            return 10_000

    s = base()
    assert simulate(s, subsidy=NoSubsidy()).loan == simulate(s).loan
    assert simulate(s, subsidy=Fixed()).loan == pytest.approx(simulate(s).loan - 10_000)


def test_rate_grid_around_market_with_floor():
    assert model.rate_grid(0.085, [-0.02, -0.01, 0, 0.01, 0.02]) == [0.065, 0.075, 0.085, 0.095, 0.105]
    assert model.rate_grid(0.01, [-0.02, 0.0], floor=0.001) == [0.001, 0.01]
