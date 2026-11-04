"""Schema validation for every handoff file in a run folder."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from .paths import SCHEMAS_DIR

JSON_FILES = {
    "inputs.json": "inputs.schema.json",
    "market_summary.json": "market_summary.schema.json",
    "housing_params.json": "housing_params.schema.json",
    "opportunity_costs.json": "opportunity_costs.schema.json",
    "analysis_summary.json": "analysis_summary.schema.json",
}

STAGES = {
    "inputs": ["inputs.json"],
    "market": ["listings.csv", "market_summary.json", "housing_params.json"],
    "opportunity": ["opportunity_costs.json"],
    "research": ["inputs.json", "listings.csv", "market_summary.json", "housing_params.json", "opportunity_costs.json"],
    "analysis": ["analysis_results.csv", "analysis_summary.json"],
}
STAGES["all"] = STAGES["research"] + STAGES["analysis"]

LISTING_COLUMNS = [
    "id", "operation", "district", "address_hint",
    "price_pen", "price_original", "currency_original", "fx_used",
    "area_m2", "bedrooms", "bathrooms", "parking", "age_years", "is_new",
    "maintenance_fee_pen", "source_portal", "source_url", "listing_date", "collected_at",
    "outlier_flag", "duplicate_of", "in_range", "notes",
]

RESULT_COLUMNS = [
    "district", "horizon", "mortgage_rate", "rate_offset", "option_id", "opportunity_return",
    "w_buy", "w_rent", "delta", "w_buy_real", "w_rent_real", "delta_real", "buy_wins",
    "break_even_year", "break_even_reverts", "renter_budget_exhausted", "low_confidence",
]


class ValidationFailed(Exception):
    def __init__(self, errors: list[str]):
        super().__init__("\n".join(errors))
        self.errors = errors


@lru_cache(maxsize=1)
def _registry() -> Registry:
    resources = []
    for path in SCHEMAS_DIR.glob("*.schema.json"):
        schema = json.loads(path.read_text(encoding="utf-8"))
        resources.append((schema["$id"], Resource.from_contents(schema)))
    return Registry().with_resources(resources)


def schema_errors(data: Any, schema_name: str) -> list[str]:
    schema = _registry().get_or_retrieve(schema_name).value.contents
    validator = Draft202012Validator(schema, registry=_registry())
    errors = []
    for err in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        where = "/".join(str(p) for p in err.path) or "<root>"
        errors.append(f"{schema_name}: {where}: {err.message}")
    return errors


def validate_json(data: Any, schema_name: str) -> None:
    errors = schema_errors(data, schema_name)
    if errors:
        raise ValidationFailed(errors)


def listings_errors(df: pd.DataFrame) -> list[str]:
    errors = []
    missing = [c for c in LISTING_COLUMNS if c not in df.columns]
    if missing:
        errors.append(f"listings.csv: missing columns {missing}")
        return errors
    no_url = df["source_url"].isna() | (df["source_url"].astype(str).str.strip() == "")
    if no_url.any():
        errors.append(f"listings.csv: {int(no_url.sum())} rows without source_url")
    if df["collected_at"].isna().any():
        errors.append("listings.csv: rows without collected_at")
    bad_op = ~df["operation"].isin(["sale", "rent"])
    if bad_op.any():
        errors.append(f"listings.csv: invalid operation values {sorted(df.loc[bad_op, 'operation'].astype(str).unique())}")
    if (pd.to_numeric(df["price_pen"], errors="coerce") <= 0).any():
        errors.append("listings.csv: non-positive price_pen")
    if df["id"].duplicated().any():
        errors.append("listings.csv: duplicated id values")
    return errors


def results_errors(df: pd.DataFrame) -> list[str]:
    missing = [c for c in RESULT_COLUMNS if c not in df.columns]
    return [f"analysis_results.csv: missing columns {missing}"] if missing else []


def validate_file(path: Path) -> list[str]:
    path = Path(path)
    if not path.exists():
        return [f"{path.name}: file not found"]
    try:
        if path.name in JSON_FILES:
            return schema_errors(json.loads(path.read_text(encoding="utf-8")), JSON_FILES[path.name])
        if path.name == "listings.csv":
            return listings_errors(pd.read_csv(path))
        if path.name == "analysis_results.csv":
            return results_errors(pd.read_csv(path))
    except (json.JSONDecodeError, pd.errors.ParserError) as exc:
        return [f"{path.name}: cannot parse ({exc})"]
    return []


def validate_run(run_dir: Path, stage: str = "research") -> list[str]:
    errors: list[str] = []
    for name in STAGES[stage]:
        errors.extend(validate_file(Path(run_dir) / name))
    return errors
