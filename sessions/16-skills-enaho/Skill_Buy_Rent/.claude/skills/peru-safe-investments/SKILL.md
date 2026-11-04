---
name: peru-safe-investments
description: Researches what a home down payment could earn in Peru if invested instead (costo de oportunidad), limited to three mainstream options (best fixed-term deposit in soles, S&P 500, S&P/BVL Peru General), with low/base/high annual returns in soles, risk, taxes and sources. Use for the opportunity-cost step of a buy-vs-rent run.
---

# Peru safe investments (opportunity cost)

You write `<run_dir>/opportunity_costs.json` (schema in
`buy-vs-rent/scripts/housing_lima/schemas/opportunity_costs.schema.json`) and `<run_dir>/opportunity_log.md`.
Details of each option and where to look: [reference.md](reference.md).
`HL` means `python "${CLAUDE_SKILL_DIR}/../buy-vs-rent/scripts/hl.py"`.

## The three options (no others)

| # | id | Option | Risk rank |
| --- | --- | --- | --- |
| 1 | `deposit` | Best fixed-term deposit in soles (depósito a plazo), 1–5 year terms | 1 (lowest) |
| 2 | `sp500` | S&P 500 total return, converted to soles | 2 |
| 3 | `bvl` | S&P/BVL Peru General index | 3 |

Ranking by risk, lowest first. Confirm it with the volatility you find; if the data contradicts it, keep the
data and explain in `caveats`.

## Steps

1. Deposit: highest TEA by bank for 1–5 year terms in soles (SBS comparator and bank pages, with minimum amount and
   conditions). low = average of the top rates for the shortest term, base = average of the best rates across
   1–5 years, high = best rate found. Say exactly how in `basis`.
2. S&P 500: annualized total return over 10, 20 and 30 years, volatility, worst year, from an index provider or a
   large index fund's published history. With a level series as CSV:

   ```bash
   python "${CLAUDE_SKILL_DIR}/scripts/index_returns.py" --prices levels.csv --date-col date --value-col close \
     --band-window 10 --fx-change 0.0 --inflation <cpi>
   ```

   low/base/high = 25th percentile / median / 75th percentile of rolling 10-year annualized returns. Store
   `return_usd_low/base/high`, then `r_pen = (1 + r_usd) × (1 + fx_change) − 1` with `fx_change_assumption` = 0.0
   (editable in the dashboard). Put a few dated USD/PEN points in `usd_pen_context`.
3. BVL: annualized return over 5, 10 and 20 years in soles where available, volatility, worst year; same band rule.
4. Taxes and fees for an individual investor in Peru: what you find, with source, in `tax_and_fees`. If you cannot
   source it, `tax_and_fees: null` and add `"tax_and_fees: <id>"` to `unknowns`. Never assume zero.
5. Real returns: `return_real_base = (1 + return_base) / (1 + inflation) − 1`; store `inflation_used`.
6. `explanation`: two plain-language sentences per option (what it is, main risk).
7. `HL validate --run <run_dir> --stage opportunity`.

## Rules

- No made-up numbers: each figure has a URL in `source_urls` and an `as_of` date. Returns are annual decimals in soles.
- A deposit rate observed today is not a 30-year guarantee: say it in `caveats`.
- `disclaimer`: "Educational information, not personalized investment advice."
- Log every page used in `opportunity_log.md` (URL, date, what was taken).

## Return

Only the three options with low/base/high, risk rank, `unknowns` and the two file paths.
