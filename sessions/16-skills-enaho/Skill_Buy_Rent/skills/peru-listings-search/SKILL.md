---
name: peru-listings-search
description: Finds real, dated sale and rent listings of apartments and houses in Lima districts, normalizes them to one schema, de-duplicates them, flags outliers, computes realistic price and rent per district, and collects the housing parameters (mortgage rates, growth, transaction costs, taxes, insurance, inflation) with sources. Use for the market-data step of a buy-vs-rent run.
---

# Peru listings search

You fill four files in the run folder: `listings.csv`, `market_summary.json`, `housing_params.json` and
`market_log.md`. The arithmetic (USD conversion, de-duplication, IQR outliers, percentiles, realistic
price) is done by the package, never by hand.

- Where to search and what to collect: [references/sources.md](references/sources.md)
- Raw and final column definitions: [references/listing-schema.md](references/listing-schema.md)
- CSV fallback and how to refresh it: [references/fallback-csv.md](references/fallback-csv.md)

## Steps

1. Read `<run_dir>/inputs.json`: price range (soles), minimum m² and bedrooms, districts, extras.
2. Get the USD/PEN rate of today with its source (SBS or BCRP) for converting dollar prices.
3. For each district, search **sale** listings inside the price range, ≥ minimum m² and bedrooms, matching
   the structured extras (`parking_min`, `max_age_years`, `is_new`). Read `extras.notes` as soft preferences.
4. For each district, search **rent** listings with the same bedrooms and an area within ±15% of the
   median area of the sale sample.
5. Target 15 sale + 15 rent per district; stop at 30 each. Keep requests slow and capped
   (see sources.md). Write each listing you actually saw as one row of
   `<run_dir>/raw_listings_live.csv` (raw schema). **A row without `source_url` is useless: skip it.**
6. If live search is blocked or gives fewer than 8 per side in a district, use the CSV fallback
   (`data/fallback/listings.csv`, same raw schema) and mark the run `csv` (only CSV) or `mixed`.
7. Collect the housing parameters into `<run_dir>/housing_params.json` (schema
   `schemas/housing_params.schema.json`). Every value has `source_url` and `as_of`; a value you cannot
   source is `{"value": null, ...}` and its name goes into `unknowns`. **Never guess.**
8. Run the pipeline (it reads `housing_params.json` for the published price index check):

   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/scripts/hl.py" listings --run <run_dir> \
     --raw <run_dir>/raw_listings_live.csv [more.csv] --source-mode live|csv|mixed \
     --fx <usd_pen> --fx-date <YYYY-MM-DD> --fx-source <url>
   python "${CLAUDE_PLUGIN_ROOT}/scripts/hl.py" validate --run <run_dir> --stage market
   ```

   Step by step is also possible with `scripts/normalize.py`, `scripts/dedupe.py` and `scripts/stats.py`.
9. Write `market_log.md`: queries run, pages fetched (URL + time), failures, blocked pages, what was skipped
   and why, the final counts per district.

## Rules

- Every record keeps `source_url` and `collected_at`. Never invent, copy-paste-modify or interpolate listings.
  Leave unknown fields empty.
- `address_hint` is approximate (street block or area name), never an exact private address or a person's name.
- Duplicates and outliers stay in the file with flags (`duplicate_of`, `outlier_flag`); they are excluded from
  the statistics, not deleted.
- Realistic price = median asking price of in-range, clean sale listings (P25–P75 band reported). Realistic
  rent = same rule on comparable rentals. `negotiation_discount` stays 0% unless the user says otherwise.
- Use only public pages; respect robots.txt and the terms of each site; no logins, no CAPTCHAs bypass, no APIs
  that need keys you were not given.
- Report districts with fewer than 8 listings per side; do not fill gaps.

## Return to the orchestrator

Only: `source_mode`, counts and realistic price/rent per district, flagged districts, the `unknowns` list and
the four file paths.
