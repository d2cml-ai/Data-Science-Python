# Buy vs rent analysis: 20261103-2350-pueblo-libre-jesus-maria-magdalena

## Method

For each district, the buyer pays the realistic price (median of in-range listings) with the user's down payment and a fixed-payment mortgage. The renter rents a comparable home and invests the down payment, the buying costs and every monthly difference between the buyer's outflow and the rent at the opportunity-cost return. Buying wins at horizon H when the buyer's net wealth (sale value after selling costs minus the remaining balance) exceeds the renter's portfolio.

- Mortgage rate grid (TEA): 5.67%, 6.67%, 7.67%, 8.67%, 9.67% (market average 7.67%)
- Opportunity-cost options (base return): Fixed-term deposit in soles 5.75%, S&P 500 (total return, in soles) 10.39%, S&P/BVL Peru General index 7.74%
- Loan term: 20 years (assumption); down payment: 20.0%
- Verdict: 'buy' when buying wins in >= 80% of the grid, 'rent' when <= 20%, otherwise 'depends'.

## Results

| District | Price | Rent/month | 5y | 10y | 15y | 20y | 30y |
| --- | ---: | ---: | --- | --- | --- | --- | --- |
| Pueblo Libre | S/ 496,302 | S/ 2,200 | rent (0%) | rent (0%) | rent (0%) | rent (0%) | rent (0%) |
| Jesús María | S/ 488,170 | S/ 2,500 | rent (0%) | rent (7%) | rent (7%) | rent (7%) | rent (7%) |
| Magdalena del Mar | S/ 528,352 | S/ 2,500 | rent (0%) | rent (0%) | rent (0%) | rent (0%) | rent (0%) |

## Verdicts

- Pueblo Libre: at the market mortgage rate (7.67%), renting wins for all 30 years against the fixed-term deposit; renting wins for all 30 years against the S&P 500; renting wins for all 30 years against the S&P/BVL Peru General. Share of grid scenarios where buying wins: 0% at 5y, 0% at 10y, 0% at 15y, 0% at 20y, 0% at 30y.
- Jesús María: at the market mortgage rate (7.67%), renting wins for all 30 years against the fixed-term deposit; renting wins for all 30 years against the S&P 500; renting wins for all 30 years against the S&P/BVL Peru General. Share of grid scenarios where buying wins: 0% at 5y, 7% at 10y, 7% at 15y, 7% at 20y, 7% at 30y.
- Magdalena del Mar: at the market mortgage rate (7.67%), renting wins for all 30 years against the fixed-term deposit; renting wins for all 30 years against the S&P 500; renting wins for all 30 years against the S&P/BVL Peru General. Share of grid scenarios where buying wins: 0% at 5y, 0% at 10y, 0% at 15y, 0% at 20y, 0% at 30y.

## Parameters used

| Parameter | Pueblo Libre | Jesús María | Magdalena del Mar | Origin |
| --- | ---: | ---: | ---: | --- |
| inflation | 0.0455 | 0.0455 | 0.0455 | researched (BCRP PN01273PM, CPI Lima Metropolitana 12-month change, Sep-2026 = 4.5487% (latest published).), https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01273PM/json/2026-9/2026-9 |
| price_growth | 0.0125 | 0.0125 | 0.0125 | researched (city-wide value; no district series found), https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PD38030PQ/json/2021-1/2026-1 |
| rent_growth | 0.0039 | 0.0039 | 0.0039 | researched (city-wide value; no district series found), https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01305PM/json/2025-10/2026-9 |
| buy_cost_pct | 0.04 | 0.04 | 0.04 | fallback (assumption from defaults.yaml = 0.04) |
| sell_cost_pct | 0.03 | 0.03 | 0.03 | fallback (assumption from defaults.yaml = 0.03) |
| property_tax_pct | 0.002 | 0.002 | 0.002 | fallback (assumption from defaults.yaml = 0.002) |
| insurance_pct | 0.003 | 0.003 | 0.003 | fallback (assumption from defaults.yaml = 0.003) |
| maintenance_fee_monthly | 245 | 250 | 235 | researched (median of listings), listings.csv |
| mortgage_rate | 0.0767 | 0.0767 | 0.0767 | researched (SBS 'Tasa de interés promedio del sistema bancario', moneda nacional, Préstamos hipotecarios para vivienda, operations of the last 30 business days to 03/11/2026, column Promedio.), https://www.sbs.gob.pe/app/pp/EstadisticasSAEEPortal/Paginas/TIActivaTipoCreditoEmpresa.aspx?tip=B |

## Warnings and caveats

- unknown: buy_cost_pct
- unknown: sell_cost_pct
- unknown: property_tax_pct
- unknown: insurance_pct
- unknown: price_growth_by_district
- unknown: rent_growth_by_district
- unknown: buy_cost.notary
- unknown: buy_cost.sunarp_registration
- unknown: buy_cost.appraisal
- unknown: tax_and_fees: deposit (income tax rate on interest from 2027-01-01 if the exemption is not extended)
- unknown: tax_and_fees: sp500 (US dividend withholding and foreign tax credit, fund expense ratio, broker and FX fees; SUNAT treatment of a US ETF not confirmed)
- unknown: tax_and_fees: bvl (broker, Cavali and fund fees; whether any 2026 capital-gains exemption applies)
- unknown: deposit rates for 1440 and 1800 day terms (none published found)
- All districts: buy_cost_pct unknown: assumption from defaults.yaml = 0.04
- All districts: insurance_pct unknown: assumption from defaults.yaml = 0.003
- All districts: property_tax_pct unknown: assumption from defaults.yaml = 0.002
- All districts: sell_cost_pct unknown: assumption from defaults.yaml = 0.03
- Asking prices are not transaction prices; see the negotiation discount.
- Deposit rates observed today are not guaranteed for 30 years.
- Subsidies (e.g. Bono del Buen Pagador) are not modelled in v1.

## Disclaimer

Educational use only. This tool compares scenarios built from public, dated information and stated assumptions. It is not personalized financial, tax or investment advice.
