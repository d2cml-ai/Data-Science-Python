"""Step 1: raw listing CSVs -> <run_dir>/listings_normalized.csv (schema columns, soles, no URL-less rows).

python normalize.py --run <run_dir> --raw a.csv [b.csv] [--fx 3.75]
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

import pandas as pd  # noqa: E402

from housing_lima.listings import normalize  # noqa: E402

p = argparse.ArgumentParser()
p.add_argument("--run", required=True)
p.add_argument("--raw", required=True, nargs="+")
p.add_argument("--fx", type=float)
p.add_argument("--collected-at")
a = p.parse_args()

raw = pd.concat([pd.read_csv(f) for f in a.raw], ignore_index=True)
df, report = normalize(raw, a.fx, a.collected_at)
df.to_csv(Path(a.run) / "listings_normalized.csv", index=False)
print(json.dumps(report, ensure_ascii=False, indent=2))
