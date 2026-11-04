# Parameters

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
and as a line in `warnings`. The dashboard shows them as "necesita tu dato".
