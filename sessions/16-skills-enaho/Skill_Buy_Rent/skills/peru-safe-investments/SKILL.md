---
name: peru-safe-investments
description: Researches what a home down payment could earn in Peru if invested instead, limited to three mainstream options (best fixed-term deposit in soles, S&P 500, S&P/BVL Peru General), with low/base/high annual returns in soles, risk, taxes and sources. Use for the opportunity-cost step of a buy-vs-rent run.
---

# Peru safe investments (opportunity cost)

You write `<run_dir>/opportunity_costs.json` (schema `schemas/opportunity_costs.schema.json`) and
`<run_dir>/opportunity_log.md`. Details of each option: [references/options.md](references/options.md).
Where to look: [references/sources.md](references/sources.md).

## The three options (no others)

| # | id | Option | Risk rank |
| --- | --- | --- | --- |
| 1 | `deposit` | Best fixed-term deposit in soles (depósito a plazo), 1–5 year terms | 1 (lowest) |
| 2 | `sp500` | S&P 500 total return, converted to soles | 2 |
| 3 | `bvl` | S&P/BVL Peru General index | 3 |

The ranking is by risk, lowest first. Confirm it with the volatility you find; if your data clearly
contradicts it, keep the data and explain in `caveats`.

## Steps

1. Read `inputs.json` (only to know the run; the amount does not change the returns).
2. Deposit: collect the highest TEA by bank for 1–5 year terms in soles (SBS comparator and bank pages, with the
   minimum amount and conditions). low = average of the top rates for the shortest term, base = average across
   1–5 year terms of the best rates, high = best rate found. Say exactly how you computed them in `basis`.
3. S&P 500: annualized total return over 10, 20 and 30 years, volatility, worst calendar year, from an index
   provider or a large index fund's published total-return history. If you can get a level series as CSV,
   compute with:

   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/peru-safe-investments/scripts/index_returns.py" \
     --prices levels.csv --date-col date --value-col close --band-window 10
   ```

   low/base/high = 25th percentile / median / 75th percentile of rolling 10-year annualized returns.
   Store `return_usd_low/base/high`, then convert: `r_pen = (1 + r_usd) × (1 + fx_change) − 1`, with
   `fx_change_assumption` = 0.0 by default (editable in the dashboard). Show recent USD/PEN history in
   `usd_pen_context` (a few dated points with source).
4. BVL: annualized return over 5, 10 and 20 years in soles where available, volatility, worst year; same band rule.
5. Taxes and fees for an individual investor in Peru (interest income, capital gains on foreign and local
   shares, broker and custody fees). Put what you find, with source, in `tax_and_fees`. If you cannot source it,
   `tax_and_fees: null` and add `"tax_and_fees: <id>"` to `unknowns`. Never assume zero.
6. Real returns: `return_real_base = (1 + return_base) / (1 + inflation) − 1`, with the recent CPI inflation
   (same value as in `housing_params.json` when available) stored in `inflation_used`.
7. For each option write `explanation`: two plain-language sentences (what it is, main risk).
8. Validate: `python "${CLAUDE_PLUGIN_ROOT}/scripts/hl.py" validate --run <run_dir> --stage opportunity`.

## Rules

- No made-up numbers: each figure has a URL in `source_urls` and an `as_of` date.
- All returns are annual decimals **in soles** (`currency: "PEN"`).
- Horizon mismatch: a deposit rate observed today is not a 30-year guarantee. Say it in `caveats`.
- `disclaimer`: "Educational information, not personalized investment advice."
- Log every page used in `opportunity_log.md` (URL, date, what was taken from it).

## Return to the orchestrator

Only the three options with low/base/high, risk rank, the `unknowns` and the two file paths.
