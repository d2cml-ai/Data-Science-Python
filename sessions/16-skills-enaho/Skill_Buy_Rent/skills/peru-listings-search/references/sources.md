# Sources

Starting points. Sites change: confirm each page is public and still has the data before using it, and
record the exact URL and date you used. If a site blocks automated access, stop using it and log it.

## Listings (asking prices)

| Portal | Notes |
| --- | --- |
| Urbania (urbania.pe) | Large Lima portal; sale and rent; district filters |
| Adondevivir (adondevivir.com) | Same group as Urbania; expect cross-portal duplicates |
| Properati (properati.com.pe) | Aggregator; check for duplicates with the two above |
| Nexo Inmobiliario (nexoinmobiliario.pe) | New projects (useful when `is_new` is requested) |

Search queries that work with a web search tool, for example:
`departamento venta Jesús María 2 dormitorios 70 m2 site:urbania.pe`,
`alquiler departamento Pueblo Libre 2 dormitorios`.

## Request limits (per run)

- At most 10 page fetches per district and operation, and at most 80 fetches per run.
- Wait between fetches of the same site; do not run parallel fetches against one site.
- Stop at 30 listings per district and operation.

## Housing parameters

| Parameter | Where to look | Field |
| --- | --- | --- |
| Mortgage rates by bank and system average (TEA, soles) | SBS: interest rate statistics by credit type (hipotecario) and the SBS rate comparator; bank rate pages | `mortgage.by_bank`, `mortgage.average_tea` |
| Inflation (CPI Lima Metropolitana, 12-month change) | BCRP: BCRPData statistics, latest monthly value | `inflation` |
| House price growth | BCRP: residential real-estate price indicators for Lima (price per m² by district, quarterly) or the monthly Urbania price index | `price_growth`, `price_growth_by_district` |
| Rent growth | Same sources, rent series, or the CPI rent component | `rent_growth`, `rent_growth_by_district` |
| Published price per m² for the sanity check | Same index as above, by district | `price_index_ppm2_by_district` |
| Buying costs | Alcabala (municipal property transfer tax: research the current rate and the UIT exemption), notary, SUNARP registry, appraisal (tasación) | `buy_cost_pct` + `cost_breakdown` |
| Selling costs | Typical broker commission, notary | `sell_cost_pct` |
| Property tax | Impuesto predial (progressive, on the municipal valuation, not the market price) | `property_tax_pct` |
| Insurance | Desgravamen and property insurance required by banks | `insurance_pct` |
| USD/PEN | SBS or BCRP exchange rate of the collection date | `fx_usd_pen` |

Express every percentage as a decimal share of the **market price** (0.03 = 3%). When a cost is not a
simple share (for example a tax on the value above an exemption), compute the share for the realistic price,
explain it in `note`, and list the parts in `cost_breakdown`.
