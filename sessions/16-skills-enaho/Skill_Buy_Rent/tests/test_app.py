"""Streamlit AppTest smoke tests on the SYNTHETIC fixture run, with network access blocked."""

import json
import os
import socket
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from housing_lima.paths import APP_FILE as APP, FIXTURE_RUN as FIXTURE
# Set HOUSING_LIMA_RUN to test a real run folder instead of the synthetic fixture.
RUN = Path(os.environ.get("HOUSING_LIMA_RUN") or FIXTURE)
INPUTS = json.loads((RUN / "inputs.json").read_text(encoding="utf-8"))
MARKET = json.loads((RUN / "market_summary.json").read_text(encoding="utf-8"))
DISTRICTS = [d for d in MARKET["districts"] if d["sale"]["realistic_price"] and d["rent"]["realistic_rent"]]


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def guard(*args, **kwargs):
        raise AssertionError("the dashboard must not make network calls")
    monkeypatch.setattr(socket.socket, "connect", guard)
    monkeypatch.setattr(socket, "create_connection", guard)


@pytest.fixture
def app(monkeypatch, tmp_path):
    monkeypatch.setenv("HOUSING_LIMA_RUN", str(RUN))
    monkeypatch.setenv("HOUSING_LIMA_RUNS", str(tmp_path / "no_runs"))
    at = AppTest.from_file(str(APP), default_timeout=60)
    at.run()
    assert not at.exception, at.exception
    return at


def metrics(at):
    return [(m.label, m.value, m.delta) for m in at.metric]


def test_app_starts_with_listing_based_defaults(app):
    first = DISTRICTS[0]
    price = app.slider(key=f"price_{first['district']}")
    expected = min(max(first["sale"]["realistic_price"], INPUTS["price_min_pen"]), INPUTS["price_max_pen"])
    assert price.value == pytest.approx(expected)
    assert len(app.metric) == len(DISTRICTS) * 5  # districts x five horizons
    if INPUTS.get("synthetic"):
        assert any("SYNTHETIC" in w.value for w in app.warning)
    assert any("Educational use only" in i.value for i in app.info)


@pytest.mark.parametrize("key,step", [
    ("mortgage_rate", 1.0),
    ("down_payment", 10),
    ("discount", 5.0),
])
def test_slider_controls_change_output(app, key, step):
    before = metrics(app)
    slider = app.slider(key=key)
    value = slider.value + step if slider.value + step <= slider.max else slider.value - step
    slider.set_value(value).run()
    assert not app.exception
    assert metrics(app) != before


def test_price_and_growth_controls_change_output(app):
    district = app.selectbox(key="district").value
    for key, value in ((f"price_{district}", float(INPUTS["price_min_pen"])), (f"price_growth_{district}", 0.0),
                       (f"rent_growth_{district}", 6.0)):
        before = metrics(app)
        app.slider(key=key).set_value(value).run()
        assert not app.exception
        assert metrics(app) != before, key


def test_opportunity_option_and_level_change_output(app):
    opp = json.loads((RUN / "opportunity_costs.json").read_text(encoding="utf-8"))
    ids = [o["id"] for o in sorted(opp["options"], key=lambda o: o["risk_rank"])]
    before = metrics(app)
    other = ids[-1]
    if other != ids[0]:
        app.radio(key="option").set_value(other).run()
        after_option = metrics(app)
        assert after_option != before
    else:
        after_option = before
    app.radio(key=f"level_{other}").set_value("high").run()
    assert metrics(app) != after_option
    app.radio(key="option").set_value("custom").run()
    custom = metrics(app)
    app.slider(key="ret_custom").set_value(12.0).run()
    assert metrics(app) != custom


def test_loan_term_and_real_toggle_change_output(app):
    before = metrics(app)
    app.selectbox(key="loan_term").set_value(30).run()
    after_term = metrics(app)
    assert after_term != before
    app.toggle(key="real").set_value(True).run()
    assert metrics(app) != after_term
    assert not app.exception


def test_explanation_section_is_shown_and_follows_the_horizon(app):
    md = " ".join(m.value for m in app.markdown)
    for step in ("Step 1", "Step 2", "Step 3", "Step 4", "Step 5", "Step 6"):
        assert step in md, step
    assert "after 20 years" in md
    assert "spend the same" in md or "same money" in md.lower()
    app.select_slider(key="horizon").set_value(10).run()
    assert not app.exception
    assert "after 10 years" in " ".join(m.value for m in app.markdown)


def test_district_switch_and_horizon(app):
    app.selectbox(key="district").set_value(DISTRICTS[-1]["district"]).run()
    assert not app.exception
    app.select_slider(key="horizon").set_value(30).run()
    assert not app.exception
