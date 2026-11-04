"""Annualized returns, volatility, worst 12 months and low/base/high from an index level CSV.

python index_returns.py --prices levels.csv --date-col date --value-col close [--band-window 10]
          [--fx-change 0.0] [--inflation 0.025]
"""

import argparse
import json
import sys
from pathlib import Path

# The housing_lima package lives in the sibling skill buy-vs-rent.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "buy-vs-rent" / "scripts"))

import pandas as pd  # noqa: E402

from housing_lima.returns import real_return, summarize_index, usd_to_pen  # noqa: E402

p = argparse.ArgumentParser()
p.add_argument("--prices", required=True)
p.add_argument("--date-col", default="date")
p.add_argument("--value-col", default="close")
p.add_argument("--band-window", type=int, default=10)
p.add_argument("--fx-change", type=float, help="convert a USD index to soles with this annual USD/PEN change")
p.add_argument("--inflation", type=float, help="add real returns")
a = p.parse_args()

df = pd.read_csv(a.prices)
levels = pd.Series(pd.to_numeric(df[a.value_col], errors="coerce").to_numpy(), index=pd.to_datetime(df[a.date_col]))
out = summarize_index(levels, band_window=a.band_window)
if a.fx_change is not None:
    for k in ("return_low", "return_base", "return_high"):
        if out[k] is not None:
            out[k.replace("return_", "return_usd_")] = out[k]
            out[k] = usd_to_pen(out[k], a.fx_change)
    out["fx_change_assumption"] = a.fx_change
if a.inflation is not None and out["return_base"] is not None:
    out["return_real_base"] = real_return(out["return_base"], a.inflation)
print(json.dumps(out, indent=2))
