# Buy vs rent analysis: 20261103-0900-synthetic-fixture

> **SYNTHETIC DATA.** This run uses a labelled fixture, not real listings.

## Method

For each district, the buyer pays the realistic price (median of in-range listings) with the user's down payment and a fixed-payment mortgage. The renter rents a comparable home and invests the down payment, the buying costs and every monthly difference between the buyer's outflow and the rent at the opportunity-cost return. Buying wins at horizon H when the buyer's net wealth (sale value after selling costs minus the remaining balance) exceeds the renter's portfolio.

- Mortgage rate grid (TEA): 6.50%, 7.50%, 8.50%, 9.50%, 10.50% (market average 8.50%)
- Opportunity-cost options (base return): Fixed-term deposit (synthetic) 5.00%, S&P 500 (synthetic) 10.00%, S&P/BVL Peru General (synthetic) 8.00%
- Loan term: 20 years (assumption); down payment: 20%
- Verdict: 'buy' when buying wins in >= 80% of the grid, 'rent' when <= 20%, otherwise 'depends'.

## Results

| District | Price | Rent/month | 5y | 10y | 15y | 20y | 30y |
| --- | ---: | ---: | --- | --- | --- | --- | --- |
| Jesús María | S/ 362,000 | S/ 2,095 | depends (60%) | buy (80%) | buy (80%) | buy (87%) | buy (80%) |
| Pueblo Libre | S/ 349,875 | S/ 1,945 | depends (53%) | depends (67%) | depends (73%) | depends (73%) | depends (73%) |
| San Miguel | S/ 338,000 | S/ 1,840 | depends (47%) | depends (67%) | depends (73%) | depends (73%) | depends (67%) |

## Verdicts

- Jesús María: at the market mortgage rate (8.50%), buying wins from year 3 against the fixed-term deposit; buying wins from year 9 against the S&P 500 (but the advantage reverses later); buying wins from year 5 against the S&P/BVL Peru General. Share of grid scenarios where buying wins: 60% at 5y, 80% at 10y, 80% at 15y, 87% at 20y, 80% at 30y.
- Pueblo Libre: at the market mortgage rate (8.50%), buying wins from year 4 against the fixed-term deposit; renting wins for all 30 years against the S&P 500; buying wins from year 6 against the S&P/BVL Peru General. Share of grid scenarios where buying wins: 53% at 5y, 67% at 10y, 73% at 15y, 73% at 20y, 73% at 30y.
- San Miguel: at the market mortgage rate (8.50%), buying wins from year 4 against the fixed-term deposit; renting wins for all 30 years against the S&P 500; buying wins from year 6 against the S&P/BVL Peru General. Share of grid scenarios where buying wins: 47% at 5y, 67% at 10y, 73% at 15y, 73% at 20y, 67% at 30y.

## Warnings and caveats

- unknown: rent_growth
- unknown: insurance_pct
- unknown: tax_and_fees: deposit
- unknown: tax_and_fees: sp500
- unknown: tax_and_fees: bvl
- listings source_mode is 'csv': data came (partly) from a CSV file, not a live search
- SYNTHETIC fixture data: not real market information
- Jesús María: insurance_pct unknown: assumption from defaults.yaml = 0.003
- Jesús María: rent_growth unknown: assumed equal to inflation (0% real)
- Jesús María: renter_budget_exhausted: in some scenarios the renter's portfolio goes negative
- Pueblo Libre: insurance_pct unknown: assumption from defaults.yaml = 0.003
- Pueblo Libre: rent_growth unknown: assumed equal to inflation (0% real)
- Pueblo Libre: renter_budget_exhausted: in some scenarios the renter's portfolio goes negative
- San Miguel: insurance_pct unknown: assumption from defaults.yaml = 0.003
- San Miguel: rent_growth unknown: assumed equal to inflation (0% real)
- San Miguel: renter_budget_exhausted: in some scenarios the renter's portfolio goes negative
- Asking prices are not transaction prices; see the negotiation discount.
- Deposit rates observed today are not guaranteed for 30 years.
- Subsidies (e.g. Bono del Buen Pagador) are not modelled in v1.

## Disclaimer

Educational use only. This tool compares scenarios built from public, dated information and stated assumptions. It is not personalized financial, tax or investment advice.
