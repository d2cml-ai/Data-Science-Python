"""The explanation must add up to exactly the model's numbers, so it can never contradict the verdict."""

import pytest

from housing_lima import explain
from housing_lima.analysis import run_analysis
from housing_lima.model import Scenario, simulate


def base(**kw) -> Scenario:
    values = dict(
        price=350_000, monthly_rent=1_800, down_payment_pct=0.20, mortgage_rate=0.085,
        opportunity_return=0.06, price_growth=0.03, rent_growth=0.03, inflation=0.025,
        buy_cost_pct=0.04, sell_cost_pct=0.03, property_tax_pct=0.002, insurance_pct=0.003,
        maintenance_fee_monthly=250, loan_term_years=20,
    )
    values.update(kw)
    return Scenario(**values)


@pytest.mark.parametrize("h", [5, 10, 20, 30])
def test_wealth_breakdown_adds_up_to_the_model(h):
    s = base()
    bd = explain.wealth_breakdown(s, h)
    r = simulate(s, years=h).at(h)
    assert sum(v for _, v in bd["buyer"]) == pytest.approx(r["w_buy"])
    assert sum(v for _, v in bd["renter"]) == pytest.approx(r["w_rent"])
    assert bd["delta"] == pytest.approx(r["delta"])


def test_both_households_spend_the_same_each_month():
    split = explain.first_year_monthly(base())
    assert sum(split["buyer"].values()) == pytest.approx(split["total"])
    assert sum(split["renter"].values()) == pytest.approx(split["total"])
    sim = simulate(base(), years=1)
    assert split["buyer"]["Mortgage interest"] + split["buyer"]["Mortgage principal (becomes equity)"] == \
        pytest.approx(sim.monthly_payment)


def test_flip_point_is_where_buy_and_rent_tie():
    s = base()
    for f in explain.flip_points(s, 20):
        if f.flip is None:
            continue
        assert explain.delta_at(s.with_(**{f.param: f.flip}), 20) == pytest.approx(0, abs=50)
        step = 0.002 if f.is_rate else 0.01 * f.flip
        moved = f.flip + step if f.buy_wins_when == "above" else f.flip - step
        assert explain.delta_at(s.with_(**{f.param: moved}), 20) > 0


def test_flip_direction_makes_sense():
    flips = {f.param: f for f in explain.flip_points(base(), 20)}
    assert flips["mortgage_rate"].buy_wins_when == "below"
    assert flips["opportunity_return"].buy_wins_when == "below"
    assert flips["price_growth"].buy_wins_when == "above"
    assert flips["monthly_rent"].buy_wins_when == "above"


def test_scenario_vote_matches_threshold_rule():
    s = base()
    opts = [{"id": "a", "name": "A", "return": 0.04}, {"id": "b", "name": "B", "return": 0.10}]
    vote = explain.scenario_vote(s, 20, [0.06, 0.085, 0.10], opts, {"buy": 0.8, "rent": 0.2})
    assert vote["n"] == 6
    wins = sum(c["buy_wins"] for c in vote["cells"])
    assert vote["share"] == pytest.approx(wins / 6)


def test_report_has_the_explanation(sample_run):
    run_analysis(sample_run)
    text = (sample_run / "analysis_report.md").read_text(encoding="utf-8")
    assert "## How the recommendation was made" in text
    assert "What would change it" in text
