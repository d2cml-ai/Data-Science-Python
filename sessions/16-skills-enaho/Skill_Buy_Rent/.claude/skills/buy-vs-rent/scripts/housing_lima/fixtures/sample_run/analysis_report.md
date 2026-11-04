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

## How the recommendation was made (20 years)

Both households start with the same cash and spend the same amount every month. The buyer puts it into a home with a mortgage at 8.50%; the renter pays rent and invests the rest in Fixed-term deposit (synthetic) at 5.00%. After 20 years we compare what each owns.

### Jesús María

1. **Homes.** Price S/ 362,000 (median of the sale listings); rent S/ 2,095/month (median of the rent listings). One year of rent = 6.9% of the price.
2. **Same money.** Day 1: S/ 86,880 (down payment + buying costs). Each month in year 1 both spend S/ 2,907: the buyer S/ 1,957 interest, S/ 499 principal, S/ 151 tax and insurance, S/ 300 fee; the renter S/ 2,095 rent, S/ 300 fee and invests S/ 512.
3. **After 20 years.** Buyer: home S/ 720,304 − selling costs S/ 21,609 − loan left S/ 0 = **S/ 698,694**. Renter: day-1 cash S/ 86,880 + monthly differences S/ -6,535 + returns S/ 178,389 = **S/ 258,734**. **Buying wins by S/ 439,960.**
4. **Why.** rent per year, as % of the price 6.94% vs mortgage rate 8.50% (points to renting); home price growth per year 3.50% vs investment return per year 5.00% (points to renting); home price growth per year 3.50% vs inflation 2.50% (points to buying).
5. **Scenario vote.** Buying wins in 87% of the 5 mortgage rates × 3 options → **buy**.
6. **What would change it** (one input at a time): Mortgage rate: buying wins below 14.60% (now 8.50%); Investment return: buying wins below 10.03% (now 5.00%); Home price growth per year: buying wins above -1.52% (now 3.50%); Monthly rent (S/): buying wins above S/ 1,212 (now S/ 2,095); Purchase price (S/): buying wins below S/ 625,868 (now S/ 362,000).

### Pueblo Libre

1. **Homes.** Price S/ 349,875 (median of the sale listings); rent S/ 1,945/month (median of the rent listings). One year of rent = 6.7% of the price.
2. **Same money.** Day 1: S/ 83,970 (down payment + buying costs). Each month in year 1 both spend S/ 2,786: the buyer S/ 1,892 interest, S/ 482 principal, S/ 146 tax and insurance, S/ 266 fee; the renter S/ 1,945 rent, S/ 266 fee and invests S/ 574.
3. **After 20 years.** Buyer: home S/ 696,177 − selling costs S/ 20,885 − loan left S/ 0 = **S/ 675,292**. Renter: day-1 cash S/ 83,970 + monthly differences S/ 18,154 + returns S/ 187,707 = **S/ 289,832**. **Buying wins by S/ 385,461.**
4. **Why.** rent per year, as % of the price 6.67% vs mortgage rate 8.50% (points to renting); home price growth per year 3.50% vs investment return per year 5.00% (points to renting); home price growth per year 3.50% vs inflation 2.50% (points to buying).
5. **Scenario vote.** Buying wins in 73% of the 5 mortgage rates × 3 options → **depends**.
6. **What would change it** (one input at a time): Mortgage rate: buying wins below 14.05% (now 8.50%); Investment return: buying wins below 9.50% (now 5.00%); Home price growth per year: buying wins above -0.79% (now 3.50%); Monthly rent (S/): buying wins above S/ 1,171 (now S/ 1,945); Purchase price (S/): buying wins below S/ 581,057 (now S/ 349,875).

### San Miguel

1. **Homes.** Price S/ 338,000 (median of the sale listings); rent S/ 1,840/month (median of the rent listings). One year of rent = 6.5% of the price.
2. **Same money.** Day 1: S/ 81,120 (down payment + buying costs). Each month in year 1 both spend S/ 2,684: the buyer S/ 1,827 interest, S/ 466 principal, S/ 141 tax and insurance, S/ 250 fee; the renter S/ 1,840 rent, S/ 250 fee and invests S/ 594.
3. **After 20 years.** Buyer: home S/ 672,549 − selling costs S/ 20,176 − loan left S/ 0 = **S/ 652,372**. Renter: day-1 cash S/ 81,120 + monthly differences S/ 29,488 + returns S/ 188,805 = **S/ 299,413**. **Buying wins by S/ 352,959.**
4. **Why.** rent per year, as % of the price 6.53% vs mortgage rate 8.50% (points to renting); home price growth per year 3.50% vs investment return per year 5.00% (points to renting); home price growth per year 3.50% vs inflation 2.50% (points to buying).
5. **Scenario vote.** Buying wins in 73% of the 5 mortgage rates × 3 options → **depends**.
6. **What would change it** (one input at a time): Mortgage rate: buying wins below 13.77% (now 8.50%); Investment return: buying wins below 9.24% (now 5.00%); Home price growth per year: buying wins above -0.45% (now 3.50%); Monthly rent (S/): buying wins above S/ 1,131 (now S/ 1,840); Purchase price (S/): buying wins below S/ 549,689 (now S/ 338,000).


## Parameters used

| Parameter | Jesús María | Pueblo Libre | San Miguel | Origin |
| --- | ---: | ---: | ---: | --- |
| inflation | 0.025 | 0.025 | 0.025 | researched (SYNTHETIC), https://example.invalid/synthetic/params |
| price_growth | 0.035 | 0.035 | 0.035 | researched (city-wide value; no district series found), https://example.invalid/synthetic/params |
| rent_growth | 0.025 | 0.025 | 0.025 | fallback (assumed equal to inflation (0% real)) |
| buy_cost_pct | 0.04 | 0.04 | 0.04 | researched (SYNTHETIC), https://example.invalid/synthetic/params |
| sell_cost_pct | 0.03 | 0.03 | 0.03 | researched (SYNTHETIC), https://example.invalid/synthetic/params |
| property_tax_pct | 0.002 | 0.002 | 0.002 | researched (SYNTHETIC), https://example.invalid/synthetic/params |
| insurance_pct | 0.003 | 0.003 | 0.003 | fallback (assumption from defaults.yaml = 0.003) |
| maintenance_fee_monthly | 300.5 | 266.5 | 250 | researched (median of listings), listings.csv |
| mortgage_rate | 0.085 | 0.085 | 0.085 | researched (SYNTHETIC), https://example.invalid/synthetic/params |

## Warnings and caveats

- unknown: rent_growth
- unknown: insurance_pct
- unknown: tax_and_fees: deposit
- unknown: tax_and_fees: sp500
- unknown: tax_and_fees: bvl
- listings source_mode is 'csv': data came (partly) from a CSV file, not a live search
- SYNTHETIC fixture data: not real market information
- All districts: insurance_pct unknown: assumption from defaults.yaml = 0.003
- All districts: rent_growth unknown: assumed equal to inflation (0% real)
- All districts: renter_budget_exhausted: in some scenarios the renter's portfolio goes negative
- Asking prices are not transaction prices; see the negotiation discount.
- Deposit rates observed today are not guaranteed for 30 years.
- Subsidies (e.g. Bono del Buen Pagador) are not modelled in v1.

## Disclaimer

Educational use only. This tool compares scenarios built from public, dated information and stated assumptions. It is not personalized financial, tax or investment advice.
