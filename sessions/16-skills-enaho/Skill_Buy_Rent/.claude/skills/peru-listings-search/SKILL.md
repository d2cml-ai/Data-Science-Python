---
name: peru-listings-search
description: Finds real, dated sale and rent listings of apartments and houses in Lima districts (Urbania, Adondevivir, Properati), normalizes them to one schema, de-duplicates them, flags outliers, computes the realistic price and rent per district, and collects the housing parameters (mortgage rates, growth, transaction costs, taxes, insurance, inflation) with sources. Use for the market-data step of a buy-vs-rent run.
---

# Peru listings search

You fill four files in the run folder: `listings.csv`, `market_summary.json`, `housing_params.json` and
`market_log.md`. The arithmetic (USD conversion, de-duplication, IQR outliers, percentiles, realistic price) is
done by the engine, never by hand.

`HL` means `python "${CLAUDE_SKILL_DIR}/../buy-vs-rent/scripts/hl.py"`. Details in [reference.md](reference.md):
sources and request limits, raw and final columns, CSV fallback. Empty raw template:
[listings_template.csv](listings_template.csv).

## Steps

1. Read `<run_dir>/inputs.json`: price range (soles), minimum m² and bedrooms, districts, extras.
2. Get today's USD/PEN rate with its source (SBS or BCRP) for converting dollar prices.
3. For each district, search **sale** listings inside the price range, ≥ minimum m² and bedrooms, matching the
   structured extras (`parking_min`, `max_age_years`, `is_new`). Read `extras.notes` as soft preferences.
4. For each district, search **rent** listings with the same bedrooms and an area within ±15% of the median area
   of the sale sample.
5. Target 15 sale + 15 rent per district; stop at 30 each. Keep requests slow and capped (reference.md). Write
   each listing you actually saw as one row of `<run_dir>/raw_listings_live.csv` (raw schema).
   **A row without `source_url` is useless: skip it.**
6. If live search is blocked or gives fewer than 8 per side in a district, use the CSV fallback
   `datos/listings.csv` (same raw schema) and mark the run `csv` (only CSV) or `mixed`.
7. Collect the housing parameters into `<run_dir>/housing_params.json` (schema in
   `buy-vs-rent/scripts/housing_lima/schemas/housing_params.schema.json`). Every value has `source_url` and
   `as_of`; a value you cannot source is `{"value": null, ...}` and its name goes into `unknowns`. **Never guess.**
8. Run the pipeline (it reads `housing_params.json` for the published price index check):

   ```bash
   HL listings --run <run_dir> --raw <run_dir>/raw_listings_live.csv [datos/listings.csv] \
      --source-mode live|csv|mixed --fx <usd_pen> --fx-date <YYYY-MM-DD> --fx-source <url>
   HL validate --run <run_dir> --stage market
   ```

   Step by step is also possible: `python "${CLAUDE_SKILL_DIR}/scripts/normalize.py"`, then `dedupe.py`, then
   `stats.py` (each takes `--run`).
9. Write `market_log.md`: queries run, pages fetched (URL + time), failures, blocked pages, what was skipped and
   why, the final counts per district.

## Rules

- Every record keeps `source_url` and `collected_at`. Never invent, copy-paste-modify or interpolate listings.
- `address_hint` is approximate (area or block), never an exact private address or a person's name.
- Duplicates and outliers stay in the file with flags; they are excluded from the statistics, not deleted.
- Realistic price = median asking price of in-range, clean sale listings (P25–P75 reported). Realistic rent = same
  rule on comparable rentals. `negotiation_discount` stays 0% unless the user says otherwise.
- Only public pages; respect robots.txt and each site's terms; no logins, no CAPTCHA bypass.
- Report districts with fewer than 8 listings per side; do not fill gaps.

## Return

Only: `source_mode`, counts and realistic price/rent per district, flagged districts, `unknowns`, file paths.
