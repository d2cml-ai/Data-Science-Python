---
name: rent-vs-buy-model
description: Buy-vs-rent financial model for Lima. Use when running or changing the comparison of buying a home with a mortgage against renting and investing the difference, over 5-30 year horizons and a mortgage-rate grid, from a run folder that already holds inputs.json, market_summary.json, housing_params.json and opportunity_costs.json.
---

# Rent vs buy model

The model lives in one Python package, `housing_lima` (`src/housing_lima/`). The dashboard
imports the same code, so there is a single source of truth. **Never re-implement the
formulas in a script or a notebook**: call the package.

- `housing_lima.model`: `Scenario`, `simulate`, `mortgage_payment`, `remaining_balance`, `break_even`, `rate_grid`.
- `housing_lima.analysis`: `resolve_params`, `build_scenario`, `analyze`, `run_analysis`.
- Formulas and their derivation: [references/formulas.md](references/formulas.md).
- Every parameter, where it comes from, and the fallbacks: [references/parameters.md](references/parameters.md).

## Run it

All commands go through the launcher, which needs no install:

```bash
HL="${CLAUDE_PLUGIN_ROOT}/scripts/hl.py"
python "$HL" validate --run <run_dir> --stage research   # all four input files must pass
python "$HL" analyze  --run <run_dir>                     # writes the three outputs
python "$HL" validate --run <run_dir> --stage analysis
```

`analyze` writes:

| File | Content |
| --- | --- |
| `analysis_results.csv` | One row per district × horizon (5, 10, 15, 20, 30) × mortgage rate (market −2..+2 pp) × option (3) |
| `analysis_summary.json` | Verdicts per district and horizon, break-even years, sensitivity, warnings |
| `analysis_report.md` | One-page method, results, caveats and disclaimer |

## Rules

1. Market numbers come only from the run folder. Modelling choices live in `config/defaults.yaml`, each
   commented as an assumption. Do not hard-code numbers in code.
2. A `null` researched value is never treated as zero. `resolve_params` replaces it with a named fallback
   from `defaults.yaml` **and** records a warning; `analysis_summary.json` keeps both.
3. Loan term defaults to 20 years. Horizon < term: the buyer sells and repays the balance. Horizon > term:
   no mortgage payments after the term, only ownership costs.
4. Results are nominal soles; the `_real` columns are deflated by CPI inflation.
5. Verdict per district and horizon = share of grid scenarios where buying wins: `buy` ≥ 80%, `rent` ≤ 20%,
   otherwise `depends` (thresholds in `defaults.yaml`).
6. Break-even = first year 1–30 where Δ > 0; `reverts: true` when Δ turns negative again later.
7. `renter_budget_exhausted` is raised when the renter's portfolio goes below zero.
8. Subsidies are not modelled in v1. `housing_lima.subsidy.SubsidyProvider` is the extension point.
9. A low-confidence district (fewer than 8 listings per side) is analysed and labelled, never hidden.

## Tests

```bash
cd "${CLAUDE_PLUGIN_ROOT}" && python -m pytest -q
```

The amortization, identity, monotonicity, loan-term and schema tests must pass before any result is reported.
If you change a formula, add a test first.
