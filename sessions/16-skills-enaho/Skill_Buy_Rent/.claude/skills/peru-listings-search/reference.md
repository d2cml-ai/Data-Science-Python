# Listings reference

## Sources

Starting points. Sites change: confirm each page is public and still has the data before using it, and
record the exact URL and date you used. If a site blocks automated access, stop using it and log it.

### Listings (asking prices)

| Portal | Notes |
| --- | --- |
| Urbania (urbania.pe) | Large Lima portal; sale and rent; district filters |
| Adondevivir (adondevivir.com) | Same group as Urbania; expect cross-portal duplicates |
| Properati (properati.com.pe) | Aggregator; check for duplicates with the two above |
| Nexo Inmobiliario (nexoinmobiliario.pe) | New projects (useful when `is_new` is requested) |

Search queries that work with a web search tool, for example:
`departamento venta Jesús María 2 dormitorios 70 m2 site:urbania.pe`,
`alquiler departamento Pueblo Libre 2 dormitorios`.

### Request limits (per run)

- At most 10 page fetches per district and operation, and at most 80 fetches per run.
- Wait between fetches of the same site; do not run parallel fetches against one site.
- Stop at 30 listings per district and operation.

### Housing parameters

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

## Listing schema

### Raw file (what you write: `raw_listings_live.csv` or the fallback CSV)

| Column | Required | Meaning |
| --- | --- | --- |
| `operation` | yes | `sale` or `rent` (also accepted: `venta`, `alquiler`) |
| `district` | yes | District name; aliases like "Surco" or "SMP" are normalized |
| `address_hint` | no | Approximate area only |
| `price_original` | yes | Asking price; for rent, the monthly rent |
| `currency_original` | yes | `PEN` or `USD` (also `S/`, `US$`) |
| `area_m2` | yes | Built or total area as listed |
| `bedrooms`, `bathrooms`, `parking` | bedrooms yes | Integers |
| `age_years`, `is_new` | no | Building age when known |
| `maintenance_fee_pen` | no | Monthly building fee, soles |
| `source_portal` | yes | Site name, e.g. `urbania` |
| `source_url` | **yes** | Link to the listing page; rows without it are dropped |
| `listing_date` | no | Publication date if shown |
| `collected_at` | no | Defaults to today |
| `id`, `notes` | no | Id is generated from the URL when empty |

### Final file (`listings.csv`, written by the pipeline)

The same columns plus:

| Column | Meaning |
| --- | --- |
| `price_pen` | Price in soles (`price_original × fx_used`) |
| `fx_used` | 1 for soles, the USD/PEN rate of the collection date for dollars |
| `duplicate_of` | Id of the original when the same home appears on another portal (or the same URL twice) |
| `outlier_flag` | IQR rule (1.5 × IQR) per district and operation |
| `in_range` | Sale: within the user's range and filters. Rent: comparable to the sale sample |

Duplicate rule: same operation, district and bedrooms, different portal, price within 2% and area within 3%
(tolerances in `buy-vs-rent/scripts/housing_lima/config/defaults.yaml`).

## CSV fallback

Used when live search is blocked or returns too few listings.

- Template: `listings_template.csv` (in this skill folder) (raw schema header, no data).
- The user's file: `data/listings.csv` (in the working folder) (ignored by git, because it holds collected listings).

### How the user refreshes it

1. Copy the template to `data/listings.csv` (in the working folder).
2. Open the portals in a browser, search the districts and filters of the run, and paste one row per listing,
   including the listing URL and the date. Prices exactly as shown, with their currency.
3. Save as UTF-8 CSV.
4. Ask for a new run, or run the pipeline directly:

   ```bash
   python "${CLAUDE_SKILL_DIR}/../buy-vs-rent/scripts/hl.py" listings --run outputs/<run-id> --raw data/listings.csv \
     --source-mode csv --fx <usd_pen> --fx-date <date> --fx-source <url>
   ```

### Rules for the agent

- Use the fallback only after trying live search, and say so in `market_log.md` and in the summary.
- Never write invented rows into the fallback file. If it does not exist, tell the orchestrator.
- When both live rows and fallback rows are used, pass both files to `--raw` and use `--source-mode mixed`.
