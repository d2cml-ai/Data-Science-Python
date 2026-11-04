# Options

## 1. Fixed-term deposit in soles (`deposit`)

- What: a bank or financial-company deposit at a fixed rate for a fixed term (depósito a plazo).
- Find: TEA by institution for 360, 720, 1080, 1440 and 1800 days; minimum amount; whether the rate needs new money
  or a promotion; deposit insurance coverage (Fondo de Seguro de Depósitos) limit and source.
- Risk to state: lowest risk, but the rate is fixed only for the term and must be reinvested later at an
  unknown rate; early withdrawal may lose interest; only covered up to the insurance limit.
- Volatility: 0 within the term; `worst_1y` = lowest rate in the top group.

## 2. S&P 500 (`sp500`)

- What: the 500 largest US listed companies, held through an index fund or ETF.
- Find: annualized total return (dividends reinvested) over 10, 20, 30 years; annual volatility; worst calendar
  year; the source's as-of date.
- Risk to state: equity risk (falls of 30–50% have happened) and exchange-rate risk: the return in soles
  depends on USD/PEN.
- Conversion: `r_pen = (1 + r_usd) × (1 + fx_change) − 1`; `fx_change` default 0% per year, editable.

## 3. S&P/BVL Peru General (`bvl`)

- What: the broad index of the Lima stock exchange.
- Find: annualized return over 5, 10, 20 years in soles; volatility; worst year.
- Risk to state: concentrated in a few sectors (mining, finance), linked to commodity prices, less liquid and
  less diversified than the S&P 500.

## Output fields per option

`id`, `name` (Spanish, shown in the dashboard), `currency: "PEN"`, `original_currency`, `return_low`,
`return_base`, `return_high`, `return_real_base`, `volatility`, `worst_1y`, `risk_rank`, `basis`,
`explanation`, `source_urls`, `as_of`, `tax_and_fees`, `caveats`; for `sp500` also `return_usd_low/base/high`.
