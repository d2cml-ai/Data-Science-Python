"""Step 3: mark in-range listings and write listings.csv + market_summary.json.

python stats.py --run <run_dir> --source-mode live|csv|mixed [--fx 3.75 --fx-date D --fx-source URL]
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

# The housing_lima package lives in the sibling skill buy-vs-rent.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "buy-vs-rent" / "scripts"))

import pandas as pd  # noqa: E402

from housing_lima.listings import district_summary, mark_in_range  # noqa: E402
from housing_lima.loaders import load_defaults, read_json, write_json  # noqa: E402

p = argparse.ArgumentParser()
p.add_argument("--run", required=True)
p.add_argument("--source-mode", required=True, choices=["live", "csv", "mixed"])
p.add_argument("--fx", type=float)
p.add_argument("--fx-date")
p.add_argument("--fx-source")
a = p.parse_args()

run = Path(a.run)
d = load_defaults()
inputs = read_json(run / "inputs.json")
df = pd.read_csv(run / "listings_flagged.csv")
df = df[df["district"].isin(inputs["districts"])].reset_index(drop=True)
df = mark_in_range(df, inputs, d["rent_area_tolerance"])
params = run / "housing_params.json"
index = read_json(params).get("price_index_ppm2_by_district") if params.exists() else None
summary = {
    "run_id": inputs["run_id"], "synthetic": bool(inputs.get("synthetic", False)),
    "source_mode": a.source_mode, "collected_at": date.today().isoformat(),
    "fx_used": {"usd_pen": a.fx, "as_of": a.fx_date, "source_url": a.fx_source} if a.fx else None,
    "negotiation_discount": d["negotiation_discount"],
    "dropped_without_url": 0,
    "districts": district_summary(df, inputs, d, a.source_mode, index),
}
df.to_csv(run / "listings.csv", index=False)
write_json(run / "market_summary.json", summary)
print(json.dumps([{k: x[k] for k in ("district", "low_confidence", "warnings")} | {
    "sale_n": x["sale"]["n"], "rent_n": x["rent"]["n"],
    "realistic_price": x["sale"]["realistic_price"], "realistic_rent": x["rent"]["realistic_rent"]}
    for x in summary["districts"]], ensure_ascii=False, indent=2))
