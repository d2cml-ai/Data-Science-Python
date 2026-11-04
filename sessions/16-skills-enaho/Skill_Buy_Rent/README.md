# Skill_Buy_Rent: buy vs rent in Lima

A Claude Code plugin (`housing-lima`) that answers **"Is buying better than renting?"** for one user's search in
Lima: one orchestrator skill, four agents and a local Streamlit dashboard, on top of one tested Python package
(`housing_lima`).

The user gives a price range, minimum m² and bedrooms, districts, a down-payment percentage and any extra wishes.
The tool compares buying with a mortgage against renting the same kind of home and investing the cash the buyer
would have tied up (the opportunity cost), per district, for 5, 10, 15, 20 and 30 years and several mortgage rates.

> Educational use only. Not personalized financial, tax or investment advice.

## How it works

```
/housing-lima:buy-vs-rent  (orchestrator skill: intake, validation, order, report)
        │  writes runs/<run-id>/inputs.json
        ├──► market-data        ──► listings.csv, market_summary.json, housing_params.json, market_log.md
        ├──► opportunity-cost   ──► opportunity_costs.json, opportunity_log.md          (in parallel)
        ▼
     financial-analysis         ──► analysis_results.csv, analysis_summary.json, analysis_report.md
        ▼
     streamlit-builder          ──► tested dashboard + launch command
```

Agents exchange files in the run folder, never chat messages. Every handoff is validated against a JSON schema in
`schemas/` before the next step starts.

| Skill | Used by | Role |
| --- | --- | --- |
| `buy-vs-rent` | You | Orchestrator: intake, validation, run order, final report |
| `peru-listings-search` | market-data | Listings search, schema, de-duplication, CSV fallback, housing parameters |
| `peru-safe-investments` | opportunity-cost | Deposit, S&P 500 and BVL returns with sources |
| `rent-vs-buy-model` | financial-analysis | Formulas, parameters, verdict rules, tests |
| `streamlit-dashboard` | streamlit-builder | Layout, controls, Spanish labels, testing |

## Folder layout

```text
Skill_Buy_Rent/                 # plugin root (the plan's "housing-lima/" folder)
├── .claude-plugin/plugin.json
├── pyproject.toml              # pip install -e . provides housing_lima
├── scripts/hl.py               # CLI launcher, works without installing
├── skills/                     # 5 skills (SKILL.md + references/ + scripts/)
├── agents/                     # 4 agents
├── src/housing_lima/           # model, analysis, listings, intake, returns, validate, loaders, subsidy (stub), cli
├── app/                        # Streamlit app: app.py, state.py, labels.py, components/
├── schemas/                    # JSON schemas for every handoff file
├── config/defaults.yaml        # modelling assumptions, each commented
├── data/fallback/              # listings_template.csv (your listings.csv is git-ignored)
├── tests/                      # unit, schema, CLI, plugin and AppTest tests; fixtures/sample_run (SYNTHETIC)
└── runs/                       # run folders (git-ignored)
```

## Install

Python 3.11+ (tested on 3.14). Dependencies: pandas, numpy, streamlit, plotly, jsonschema, pyyaml, pytest.

```bash
cd sessions/16-skills-enaho/Skill_Buy_Rent
pip install -e ".[test]"        # optional: scripts/hl.py and the app also work without installing
```

## Use

**As a plugin in Claude Code** (from the repo, no marketplace needed):

```bash
claude --plugin-dir sessions/16-skills-enaho/Skill_Buy_Rent
```

Then type `/housing-lima:buy-vs-rent`, or just ask "¿me conviene comprar o alquilar en Lima?". The orchestrator
asks the five questions, runs the agents and gives you the dashboard command.

**Dry run with synthetic data** (no web access needed):

```bash
python scripts/hl.py fixture-run            # builds runs/<timestamp>-fixture-dry-run/
python scripts/hl.py summary --run runs/<run-id>
```

or `/housing-lima:buy-vs-rent fixture` inside Claude Code.

**Dashboard** (local, offline, Spanish labels):

```bash
streamlit run app/app.py -- --run runs/<run-id>
```

Without `--run` it opens the newest run in `runs/`, or the synthetic fixture when there is none. The sidebar has
the mortgage rate, down payment, opportunity cost (three options or a custom rate, low/base/high, USD/PEN change
for the S&P 500), purchase price (bounded by your range, default = median of the listings found), negotiation
discount, loan term, price and rent growth, and real vs nominal.

**CLI commands** (`python scripts/hl.py <command>`): `check-env`, `new-run --answers a.json`,
`listings --run D --raw f.csv --source-mode live|csv|mixed`, `validate --run D --stage research|analysis|all`,
`analyze --run D`, `summary --run D`, `returns --prices levels.csv`, `fixture-run`.

## Refresh the listings fallback

If live search is blocked, copy `data/fallback/listings_template.csv` to `data/fallback/listings.csv`, paste one
row per listing you see on the portals (with its URL and date), and run a new search. Details:
`skills/peru-listings-search/references/fallback-csv.md`. The run is then labelled `source_mode: csv`.

## Tests

```bash
python -m pytest -q                                       # 95 tests, no network
HOUSING_LIMA_RUN=runs/<run-id> python -m pytest -q tests/test_app.py   # dashboard tests on a real run
python tests/fixtures/make_fixture.py                     # regenerate the synthetic fixture
```

Covered: amortization (S/100,000 at 8% over 20 years → S/819, balance 0 after 240 payments), the identity at
H = 0, monotonicity in mortgage rate and opportunity return, loan-term edge cases, schemas (valid and invalid
fixtures), listings logic (de-duplication, IQR outliers, USD conversion, no record without URL), intake
validation, the end-to-end dry run, plugin structure, and Streamlit `AppTest` (every control changes the result,
network blocked).

## Model in one paragraph

The buyer pays the realistic price (median of in-range listings, minus an optional negotiation discount) with
the down payment and a constant-payment mortgage, plus ownership costs that grow with inflation. The renter pays
the realistic rent of a comparable home and invests the down payment, the buying costs and every monthly
difference at the opportunity-cost return. Buying wins at horizon H when the house value after selling costs
minus the remaining balance exceeds the renter's portfolio. Formulas:
`skills/rent-vs-buy-model/references/formulas.md`.

## Decisions and assumptions

- Horizons 5, 10, 15, 20, 30 years; loan term a separate parameter, default 20 years (assumption, editable).
- Mortgage grid: market average −2 to +2 percentage points.
- Verdict: "buy" when buying wins in ≥ 80% of grid scenarios, "rent" at ≤ 20%, otherwise "depends"
  (`config/defaults.yaml`).
- "Fondo a plazo" read as a fixed-term deposit in soles; "Bolsa de Perú" as the S&P/BVL Peru General.
- S&P 500 converted to soles with an editable USD/PEN change, default 0% per year.
- The renter is assumed to pay the building fee (common in Lima), so it cancels out; editable in `defaults.yaml`.
- Unknown researched values are `null`, listed in `unknowns`, replaced by a named fallback from `defaults.yaml`
  and shown as a warning ("necesita tu dato"); never silently zero.
- Subsidies (e.g. Bono del Buen Pagador) are not modelled in v1; `housing_lima.subsidy.SubsidyProvider` is the
  extension point.

## Open items

- Confirm "fondo a plazo" = fixed-term deposit (only option 1 of Agent 2 changes otherwise).
- Confirm the 20-year default term and the 80% / 20% thresholds.
- Live listing search depends on portal access at run time; the CSV fallback covers blocked sites.
- A subsidy module for a later version.
