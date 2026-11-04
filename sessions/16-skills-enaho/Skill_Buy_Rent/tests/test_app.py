"""Streamlit AppTest smoke tests on the SYNTHETIC fixture run, with network access blocked."""

import socket
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app" / "app.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sample_run"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def guard(*args, **kwargs):
        raise AssertionError("the dashboard must not make network calls")
    monkeypatch.setattr(socket.socket, "connect", guard)
    monkeypatch.setattr(socket, "create_connection", guard)


@pytest.fixture
def app(monkeypatch, tmp_path):
    monkeypatch.setenv("HOUSING_LIMA_RUN", str(FIXTURE))
    monkeypatch.setenv("HOUSING_LIMA_RUNS", str(tmp_path / "no_runs"))
    at = AppTest.from_file(str(APP), default_timeout=60)
    at.run()
    assert not at.exception, at.exception
    return at


def metrics(at):
    return [(m.label, m.value, m.delta) for m in at.metric]


def test_app_starts_with_listing_based_defaults(app):
    import json
    market = json.loads((FIXTURE / "market_summary.json").read_text(encoding="utf-8"))
    first = market["districts"][0]
    price = app.slider(key=f"price_{first['district']}")
    assert price.value == pytest.approx(first["sale"]["realistic_price"])
    assert len(app.metric) == 3 * 5  # three districts x five horizons
    assert any("SINTÉTICOS" in w.value for w in app.warning)
    assert any("Uso educativo" in i.value for i in app.info)


@pytest.mark.parametrize("key,value", [
    ("mortgage_rate", 10.5),
    ("down_payment", 35),
    ("discount", 5.0),
])
def test_slider_controls_change_output(app, key, value):
    before = metrics(app)
    app.slider(key=key).set_value(value).run()
    assert not app.exception
    assert metrics(app) != before


def test_price_and_growth_controls_change_output(app):
    district = app.selectbox(key="district").value
    for key, value in ((f"price_{district}", 260000.0), (f"price_growth_{district}", 0.0),
                       (f"rent_growth_{district}", 6.0)):
        before = metrics(app)
        app.slider(key=key).set_value(value).run()
        assert not app.exception
        assert metrics(app) != before, key


def test_opportunity_option_and_level_change_output(app):
    before = metrics(app)
    app.radio(key="option").set_value("sp500").run()
    after_option = metrics(app)
    assert after_option != before
    app.radio(key="level_sp500").set_value("high").run()
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


def test_district_switch_and_horizon(app):
    app.selectbox(key="district").set_value("San Miguel").run()
    assert not app.exception
    app.select_slider(key="horizon").set_value(30).run()
    assert not app.exception
