# CSV fallback

Used when live search is blocked or returns too few listings.

- Template: `data/fallback/listings_template.csv` (raw schema header, no data).
- The user's file: `data/fallback/listings.csv` (ignored by git, because it holds collected listings).

## How the user refreshes it

1. Copy the template to `data/fallback/listings.csv`.
2. Open the portals in a browser, search the districts and filters of the run, and paste one row per listing,
   including the listing URL and the date. Prices exactly as shown, with their currency.
3. Save as UTF-8 CSV.
4. Ask for a new run, or run the pipeline directly:

   ```bash
   python scripts/hl.py listings --run runs/<run-id> --raw data/fallback/listings.csv \
     --source-mode csv --fx <usd_pen> --fx-date <date> --fx-source <url>
   ```

## Rules for the agent

- Use the fallback only after trying live search, and say so in `market_log.md` and in the summary.
- Never write invented rows into the fallback file. If it does not exist, tell the orchestrator.
- When both live rows and fallback rows are used, pass both files to `--raw` and use `--source-mode mixed`.
