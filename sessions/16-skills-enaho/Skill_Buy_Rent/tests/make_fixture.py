"""Regenerate the SYNTHETIC fixture run in .claude/skills/buy-vs-rent/scripts/housing_lima/fixtures/sample_run/.

Every number here is made up for testing. Nothing in this folder is market data.
Run: python tests/make_fixture.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPTS = Path(__file__).resolve().parents[1] / ".claude" / "skills" / "buy-vs-rent" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from housing_lima.analysis import run_analysis  # noqa: E402
from housing_lima.listings import build_market  # noqa: E402
from housing_lima.loaders import load_defaults, write_json  # noqa: E402

OUT = SCRIPTS / "housing_lima" / "fixtures" / "sample_run"
SYN = "https://example.invalid/synthetic"
AS_OF = "2026-11-03"
FX = {"usd_pen": 3.75, "as_of": AS_OF, "source_url": f"{SYN}/fx", "note": "SYNTHETIC"}

INPUTS = {
    "run_id": "20261103-0900-synthetic-fixture",
    "created_at": "2026-11-03T09:00:00",
    "synthetic": True,
    "price_min_pen": 250000, "price_max_pen": 400000,
    "min_area_m2": 60, "min_bedrooms": 2,
    "districts": ["Jesús María", "Pueblo Libre", "San Miguel"],
    "down_payment_pct": 20,
    "currency_answered": "PEN", "fx_conversion": None,
    "extras": {"parking_min": None, "max_age_years": None, "max_monthly_payment": None,
               "is_new": None, "pets_allowed": None, "min_floor": None, "notes": "SYNTHETIC fixture"},
}

# Made-up price levels (soles per m2) and rents (soles per m2 per month).
LEVELS = {"Jesús María": (5200, 29.0), "Pueblo Libre": (5000, 27.5), "San Miguel": (4700, 26.0)}


def sv(value, note="SYNTHETIC"):
    if value is None:
        return {"value": None, "source_url": None, "as_of": None, "note": "unknown in fixture"}
    return {"value": value, "source_url": f"{SYN}/params", "as_of": AS_OF, "note": note}


def raw_listings(seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for d_i, (district, (ppm2, rent_m2)) in enumerate(LEVELS.items()):
        code = "".join(w[0] for w in district.split()).upper()
        for k in range(22):
            area = float(rng.integers(60, 82))
            price = round(area * ppm2 * rng.uniform(0.9, 1.1), -3)
            rows.append(dict(operation="sale", district=district, address_hint=f"zona {k % 4 + 1}",
                             price_original=price, currency_original="PEN", area_m2=area,
                             bedrooms=int(rng.choice([2, 3])), bathrooms=int(rng.choice([1, 2])),
                             parking=int(rng.choice([0, 1])), age_years=int(rng.integers(0, 25)),
                             is_new=False, maintenance_fee_pen=float(rng.integers(180, 360)),
                             source_portal="portal-main", source_url=f"{SYN}/sale/{code}-{k:03d}",
                             listing_date="2026-10-20", notes="SYNTHETIC"))
        for k in range(20):
            area = float(rng.integers(60, 80))
            rows.append(dict(operation="rent", district=district, address_hint=f"zona {k % 4 + 1}",
                             price_original=round(area * rent_m2 * rng.uniform(0.9, 1.1), -1),
                             currency_original="PEN", area_m2=area, bedrooms=int(rng.choice([2, 3])),
                             bathrooms=int(rng.choice([1, 2])), parking=int(rng.choice([0, 1])),
                             age_years=int(rng.integers(0, 25)), is_new=False,
                             maintenance_fee_pen=float(rng.integers(180, 360)),
                             source_portal="portal-main", source_url=f"{SYN}/rent/{code}-{k:03d}",
                             listing_date="2026-10-20", notes="SYNTHETIC"))
        # Quality cases: a cross-portal duplicate, a rent outlier, a USD price and a row without URL.
        first_sale, first_rent = rows[-42], rows[-20]
        rows.append(dict(first_sale, source_portal="portal-other", source_url=f"{SYN}/sale/{code}-dup",
                         price_original=first_sale["price_original"] * 1.005, notes="SYNTHETIC: cross-portal duplicate"))
        rows.append(dict(first_rent, source_url=f"{SYN}/rent/{code}-outlier", price_original=first_rent["price_original"] * 4,
                         notes="SYNTHETIC: rent outlier"))
        rows.append(dict(first_sale, source_url=f"{SYN}/sale/{code}-usd", area_m2=70.0,
                         price_original=round(70 * ppm2 / FX["usd_pen"], -2), currency_original="USD",
                         notes="SYNTHETIC: priced in USD"))
        rows.append(dict(first_sale, source_url="", notes="SYNTHETIC: no URL, must be dropped"))
    return pd.DataFrame(rows)


HOUSING_PARAMS = {
    "as_of": AS_OF,
    "synthetic": True,
    "mortgage": {
        "average_tea": sv(0.085),
        "by_bank": [
            {"bank": "Synthetic Bank A", "tea": 0.079, "source_url": f"{SYN}/bank-a", "as_of": AS_OF},
            {"bank": "Synthetic Bank B", "tea": 0.086, "source_url": f"{SYN}/bank-b", "as_of": AS_OF},
            {"bank": "Synthetic Bank C", "tea": 0.092, "source_url": f"{SYN}/bank-c", "as_of": AS_OF},
        ],
    },
    "price_growth": sv(0.035),
    "rent_growth": sv(None),
    "price_index_ppm2_by_district": {"Jesús María": sv(5150.0)},
    "inflation": sv(0.025),
    "buy_cost_pct": sv(0.04),
    "sell_cost_pct": sv(0.03),
    "property_tax_pct": sv(0.002),
    "insurance_pct": sv(None),
    "fx_usd_pen": sv(3.75),
    "unknowns": ["rent_growth", "insurance_pct"],
}

OPPORTUNITY = {
    "as_of": AS_OF,
    "synthetic": True,
    "disclaimer": "SYNTHETIC fixture. Educational use only, not personalized investment advice.",
    "fx_change_assumption": 0.0,
    "inflation_used": 0.025,
    "options": [
        {"id": "deposit", "name": "Fixed-term deposit (synthetic)", "currency": "PEN", "original_currency": "PEN",
         "return_low": 0.045, "return_base": 0.05, "return_high": 0.055, "return_real_base": 0.0244,
         "volatility": 0.0, "worst_1y": 0.045, "risk_rank": 1, "basis": "SYNTHETIC: made-up rates",
         "explanation": "Lowest risk. The rate is fixed only for the term and must be reinvested later.",
         "source_urls": [f"{SYN}/deposit"], "as_of": AS_OF, "tax_and_fees": None,
         "caveats": ["SYNTHETIC"]},
        {"id": "sp500", "name": "S&P 500 (synthetic)", "currency": "PEN", "original_currency": "USD",
         "return_low": 0.07, "return_base": 0.10, "return_high": 0.13, "return_real_base": 0.0732,
         "return_usd_low": 0.07, "return_usd_base": 0.10, "return_usd_high": 0.13,
         "volatility": 0.16, "worst_1y": -0.37, "risk_rank": 2, "basis": "SYNTHETIC: made-up returns",
         "explanation": "Diversified US equities. Carries equity risk and USD/PEN risk.",
         "source_urls": [f"{SYN}/sp500"], "as_of": AS_OF, "tax_and_fees": None, "caveats": ["SYNTHETIC"]},
        {"id": "bvl", "name": "S&P/BVL Peru General (synthetic)", "currency": "PEN", "original_currency": "PEN",
         "return_low": 0.04, "return_base": 0.08, "return_high": 0.12, "return_real_base": 0.0537,
         "volatility": 0.25, "worst_1y": -0.45, "risk_rank": 3, "basis": "SYNTHETIC: made-up returns",
         "explanation": "Peruvian equities, concentrated in mining and finance, less diversified.",
         "source_urls": [f"{SYN}/bvl"], "as_of": AS_OF, "tax_and_fees": None, "caveats": ["SYNTHETIC"]},
    ],
    "unknowns": ["tax_and_fees: deposit", "tax_and_fees: sp500", "tax_and_fees: bvl"],
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    raw = raw_listings()
    raw.to_csv(OUT / "raw_listings.csv", index=False)
    write_json(OUT / "inputs.json", INPUTS)
    write_json(OUT / "housing_params.json", HOUSING_PARAMS)
    write_json(OUT / "opportunity_costs.json", OPPORTUNITY)
    write_json(OUT / "fx.json", FX)
    df, summary, report = build_market(raw, INPUTS, load_defaults(), "csv", FX, AS_OF,
                                       HOUSING_PARAMS["price_index_ppm2_by_district"])
    df.to_csv(OUT / "listings.csv", index=False)
    write_json(OUT / "market_summary.json", summary)
    run_analysis(OUT)
    print(report)


if __name__ == "__main__":
    main()
