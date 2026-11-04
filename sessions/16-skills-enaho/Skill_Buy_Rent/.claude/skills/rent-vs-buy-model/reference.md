# Model reference

## Formulas

All amounts in nominal soles. Annual rates are decimals. The simulation is monthly and wealth is
read at the end of each year H = 0..30.

### Mortgage

```
i   = (1 + TEA)^(1/12) − 1                         monthly rate from the annual effective rate
n   = 12 × loan_term_years
M   = L · i / (1 − (1 + i)^(−n))                   constant monthly payment (i = 0 → L / n)
B_k = L (1 + i)^k − M ((1 + i)^k − 1) / i          balance after k payments; B_k = 0 for k ≥ n
```

Check: L = 100,000, TEA = 8%, 20 years → M ≈ 819, B_240 = 0 (the repo tests).

### Buyer

```
P0 = realistic_price × (1 − negotiation_discount)
D  = d × P0                       down payment, d in [0.05, 0.50]
L  = P0 − D − subsidy             subsidy = 0 in v1
own_t = (property_tax_pct + insurance_pct) × P0 / 12 × (1 + π)^(y) + fee × (1 + π)^(y)
O_t   = M · 1[t ≤ n] + own_t      buyer's monthly outflow; y = completed years before month t
W_buy(H) = P0 (1 + g_p)^H (1 − c_sell) − B_{12H}
```

### Renter

```
R_t = R0 (1 + g_r)^(y) + fee × (1 + π)^(y) · 1[renter_pays_maintenance]
V_0 = D + c_buy × P0              the renter keeps the cash the buyer spent up front
j   = (1 + r_o)^(1/12) − 1
V_t = V_{t−1} (1 + j) + (O_t − R_t)
W_rent(H) = V_{12H}
```

When the buyer's outflow is lower than rent (for example after the loan ends), the difference is
negative and the renter draws down the portfolio. If V goes below zero, the warning
`renter_budget_exhausted` is raised.

`renter_pays_maintenance` (default `true`, an assumption: in Lima tenants usually pay the building
fee) adds the fee to the renter's side too, so with `true` the fee cancels out.

### Comparison

```
Δ(H)      = W_buy(H) − W_rent(H)            buying wins when Δ(H) > 0
Δ_real(H) = Δ(H) / (1 + π)^H
Δ(0)      = −(c_buy + c_sell) P0             identity tested in the repo tests
```

### Grid, verdicts and sensitivity

- Mortgage-rate grid: market average + {−2, −1, 0, +1, +2} pp, floored at 0.1%.
- Opportunity-cost options: the three options of `opportunity_costs.json` at their base return.
- Verdict per district and horizon: share of the 15 grid scenarios where Δ > 0.
- Sensitivity at the market rate, per option: price growth ±2 pp, rent growth ±2 pp, negotiation
  discount 0/5/10%, reported at 10 and 20 years.

## Parameters

| Parameter | Field | Source | If unknown (`null`) |
| --- | --- | --- | --- |
| Realistic price | `market_summary.districts[].sale.realistic_price` | Median of in-range, non-outlier, non-duplicate sale listings | District not analysed, reported |
| Realistic rent | `market_summary.districts[].rent.realistic_rent` | Same rule on comparable rent listings | District not analysed, reported |
| Down payment d | `inputs.down_payment_pct / 100` | User | Intake asks again |
| Mortgage rate | `housing_params.mortgage.average_tea` | SBS average | Mean of `by_bank`, warning; none → stop |
| Loan term | `defaults.loan_term_years` | Assumption (20) | — |
| Price growth g_p | `housing_params.price_growth_by_district[d]` or `price_growth` | Researched | Equal to inflation (0% real), warning |
| Rent growth g_r | `rent_growth_by_district[d]` or `rent_growth` | Researched | Equal to inflation, warning |
| Inflation π | `housing_params.inflation` | BCRP | `fallbacks.inflation`, warning |
| Buying costs c_buy | `housing_params.buy_cost_pct` | Notary, registry, alcabala, appraisal | `fallbacks.buy_cost_pct`, warning |
| Selling costs c_sell | `housing_params.sell_cost_pct` | Commission, fees | `fallbacks.sell_cost_pct`, warning |
| Property tax | `housing_params.property_tax_pct` | Municipal (predial) | `fallbacks.property_tax_pct`, warning |
| Insurance | `housing_params.insurance_pct` | Property + desgravamen | `fallbacks.insurance_pct`, warning |
| Building fee | `market_summary...maintenance_fee_median` | Listings | `fallbacks.maintenance_fee_monthly`, warning |
| Opportunity return r_o | `opportunity_costs.options[].return_base` (low/high in the dashboard) | Agent 2 | Option missing → not compared |
| S&P 500 FX change | `opportunity_costs.fx_change_assumption` | Assumption, default 0% | — |
| Negotiation discount | `market_summary.negotiation_discount` | Assumption, default 0% | — |
| Verdict thresholds | `defaults.verdict_thresholds` | Assumption (80% / 20%) | — |

Every fallback appears in `analysis_summary.json → districts[].parameter_sources[name].origin = "fallback"`
and as a line in `warnings`. The dashboard shows them as "needs your input".
