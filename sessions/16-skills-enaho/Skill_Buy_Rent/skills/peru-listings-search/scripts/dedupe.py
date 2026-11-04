"""Step 2: flag cross-portal duplicates and IQR outliers (rows are kept).

python dedupe.py --run <run_dir>     # reads listings_normalized.csv, writes listings_flagged.csv
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

import pandas as pd  # noqa: E402

from housing_lima.listings import dedupe, flag_outliers  # noqa: E402
from housing_lima.loaders import load_defaults  # noqa: E402

p = argparse.ArgumentParser()
p.add_argument("--run", required=True)
a = p.parse_args()

run = Path(a.run)
d = load_defaults()
df = pd.read_csv(run / "listings_normalized.csv")
df = flag_outliers(dedupe(df, d["dedupe_price_tolerance"], d["dedupe_area_tolerance"]))
df.to_csv(run / "listings_flagged.csv", index=False)
print(json.dumps({"rows": len(df), "duplicates": int(df["duplicate_of"].notna().sum()),
                  "outliers": int(df["outlier_flag"].sum())}, indent=2))
