import copy
import json

import pytest

from housing_lima.validate import schema_errors, validate_file, validate_run


def load(run, name):
    return json.loads((run / name).read_text(encoding="utf-8"))


def test_fixture_run_validates_completely(sample_run):
    assert validate_run(sample_run, "all") == []


@pytest.mark.parametrize("name,schema,mutate", [
    ("inputs.json", "inputs.schema.json", lambda d: d.update(down_payment_pct=0)),
    ("inputs.json", "inputs.schema.json", lambda d: d.update(districts=[])),
    ("inputs.json", "inputs.schema.json", lambda d: d.pop("extras")),
    ("housing_params.json", "housing_params.schema.json", lambda d: d["inflation"].update(source_url=None)),
    ("housing_params.json", "housing_params.schema.json", lambda d: d.pop("unknowns")),
    ("opportunity_costs.json", "opportunity_costs.schema.json", lambda d: d["options"][0].update(source_urls=[])),
    ("opportunity_costs.json", "opportunity_costs.schema.json", lambda d: d["options"].append(copy.deepcopy(d["options"][0])) or d["options"].append(d["options"][0])),
    ("market_summary.json", "market_summary.schema.json", lambda d: d.update(source_mode="guess")),
    ("analysis_summary.json", "analysis_summary.schema.json", lambda d: d["districts"][0]["verdicts"][0].update(label="maybe")),
])
def test_invalid_fixtures_rejected(sample_run, name, schema, mutate):
    data = load(sample_run, name)
    assert schema_errors(data, schema) == []
    mutate(data)
    assert schema_errors(data, schema)


def test_researched_value_needs_source(sample_run):
    data = load(sample_run, "housing_params.json")
    data["price_growth"] = {"value": 0.05}
    assert any("source_url" in e for e in schema_errors(data, "housing_params.schema.json"))
    data["price_growth"] = {"value": None}
    assert schema_errors(data, "housing_params.schema.json") == []


def test_listings_without_url_rejected(sample_run):
    import pandas as pd
    path = sample_run / "listings.csv"
    df = pd.read_csv(path)
    df.loc[0, "source_url"] = None
    df.to_csv(path, index=False)
    assert any("source_url" in e for e in validate_file(path))
