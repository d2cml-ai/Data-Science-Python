import json

import pandas as pd
import pytest

from housing_lima.analysis import AnalysisError, analyze, build_scenario, resolve_params, run_analysis, verdict_label
from housing_lima.loaders import load_defaults, load_run


@pytest.fixture
def defaults():
    return load_defaults()


def test_run_analysis_writes_outputs(sample_run, defaults):
    for name in ("analysis_results.csv", "analysis_summary.json", "analysis_report.md"):
        (sample_run / name).unlink()
    summary = run_analysis(sample_run)
    assert (sample_run / "analysis_report.md").read_text(encoding="utf-8").count("Educational use only") == 1
    res = pd.read_csv(sample_run / "analysis_results.csv")
    n_districts = len(summary["districts"])
    assert len(res) == n_districts * len(defaults["horizons"]) * 5 * 3
    assert sorted(res["horizon"].unique()) == [5, 10, 15, 20, 30]
    assert res["option_id"].nunique() == 3
    assert res["mortgage_rate"].nunique() == 5


def test_rate_grid_centered_on_market_average(sample_run, defaults):
    _, summary = analyze(load_run(sample_run), defaults)
    assert summary["mortgage_rate_grid"] == [0.065, 0.075, 0.085, 0.095, 0.105]


def test_unknowns_become_visible_warnings(sample_run, defaults):
    _, summary = analyze(load_run(sample_run), defaults)
    assert "unknown: rent_growth" in summary["warnings"]
    assert "unknown: insurance_pct" in summary["warnings"]
    d = summary["districts"][0]
    assert any(w.startswith("rent_growth unknown") for w in d["warnings"])
    assert d["parameter_sources"]["insurance_pct"]["origin"] == "fallback"
    assert any("SYNTHETIC" in w for w in summary["warnings"])
    assert any("source_mode is 'csv'" in w for w in summary["warnings"])


def test_price_comes_from_listings(sample_run, defaults):
    run = load_run(sample_run)
    for d in run.market["districts"]:
        s = build_scenario(run, d["district"], defaults)
        assert s.price == d["sale"]["realistic_price"]
        assert s.monthly_rent == d["rent"]["realistic_rent"]
        assert s.down_payment_pct == pytest.approx(run.inputs["down_payment_pct"] / 100)


def test_verdict_thresholds():
    t = {"buy": 0.8, "rent": 0.2}
    assert verdict_label(0.8, t) == "buy"
    assert verdict_label(0.2, t) == "rent"
    assert verdict_label(0.5, t) == "depends"


def test_results_monotonic_in_rate(sample_run, defaults):
    res, _ = analyze(load_run(sample_run), defaults)
    df = pd.DataFrame(res)
    for (_, _, _), g in df.groupby(["district", "horizon", "option_id"]):
        g = g.sort_values("mortgage_rate")
        assert g["delta"].is_monotonic_decreasing


def test_missing_mortgage_rate_stops(sample_run, defaults):
    p = sample_run / "housing_params.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    data["mortgage"] = {"average_tea": {"value": None}, "by_bank": []}
    p.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(AnalysisError):
        analyze(load_run(sample_run), defaults)


def test_mean_of_banks_used_when_average_unknown(sample_run, defaults):
    p = sample_run / "housing_params.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    data["mortgage"]["average_tea"] = {"value": None}
    p.write_text(json.dumps(data), encoding="utf-8")
    rp = resolve_params(load_run(sample_run), "Pueblo Libre", defaults)
    assert rp.values["mortgage_rate"] == pytest.approx((0.079 + 0.086 + 0.092) / 3)
    assert any("mean of the bank rates" in w for w in rp.warnings)
