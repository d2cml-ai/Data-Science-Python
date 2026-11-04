# Skill_Buy_Rent · Buy or rent in Lima? Claude Code skills

Five Claude Code skills and four subagents that answer **"should I buy or rent?"** for a specific home search in
Lima. An orchestrator skill asks the questions; two agents research in parallel (real sale and rent listings, and
what the down payment would earn if invested instead); a third runs the financial model; a fourth checks the
dashboard and exports the figures.

You give a price range, a minimum size and number of bedrooms, the districts, your down-payment percentage and
any extra wishes. The tool compares buying with a mortgage against renting a similar home and investing the cash
the buyer would have tied up (the opportunity cost), per district, over 5, 10, 15, 20 and 30 years and across a
grid of mortgage rates.

> Educational use only. Not personalized financial, tax or investment advice.

A complete real run lives in [`../Example`](../Example).

## How it works

```text
/buy-vs-rent ── intake questions ── outputs/<run-id>/inputs.json
      ├──► market-data        real listings + housing parameters  ┐ in parallel
      ├──► opportunity-cost   deposit, S&P 500, BVL returns        ┘
      ▼
   financial-analysis  ──►  streamlit-builder  ──►  outputs/validation.txt, figures/, dashboard
```

- **The orchestrator does no heavy work.** It asks, validates, launches the agents and summarizes. Agents pass
  each other files in a run folder, not chat messages, so each one keeps a clean context.
- **One model.** The formulas exist once, in the `housing_lima` package. The analysis, the figures and the
  dashboard all import it.
- **Nothing invented.** Every listing and every researched number keeps its URL and date. A value without a
  source is `null`, replaced by a named assumption and shown as a warning ("needs your input").
- **Everything is validated.** Each handoff file is checked against a JSON schema before the next step. A failure
  stops the pipeline.

### Skills

| Skill | Used by | Input | Output |
|---|---|---|---|
| `buy-vs-rent` | You (orchestrator) | Your five answers | `outputs/<run-id>/inputs.json` and the final summary |
| `peru-listings-search` | `market-data` agent | `inputs.json` | `listings.csv`, `market_summary.json`, `housing_params.json`, `market_log.md` |
| `peru-safe-investments` | `opportunity-cost` agent | `inputs.json` | `opportunity_costs.json`, `opportunity_log.md` |
| `rent-vs-buy-model` | `financial-analysis` agent | The four research files | `analysis_results.csv`, `analysis_summary.json`, `analysis_report.md` |
| `streamlit-dashboard` | `streamlit-builder` agent | The finished run | `figures/*.png` and a checked dashboard |

### Agents

| Agent | Tools | Job |
|---|---|---|
| `market-data` | Web search and fetch, Bash | Finds sale and rent listings, cleans them (dollars to soles, duplicates, outliers), sets the realistic price and rent per district, collects mortgage rates, costs, taxes and inflation with sources |
| `opportunity-cost` | Web search and fetch, Bash | Low, base and high yearly returns in soles for the best fixed-term deposit, the S&P 500 and the S&P/BVL Peru General |
| `financial-analysis` | Bash only (no web) | Runs the model for every district × horizon × mortgage rate × option, break-even years, sensitivity, verdicts |
| `streamlit-builder` | Bash only (no web) | Checks the dashboard on the run and exports the figures |

## Folder structure

```text
Skill_Buy_Rent/
├── .claude/
│   ├── skills/
│   │   ├── buy-vs-rent/            SKILL.md, reference.md, scripts/hl.py (launcher)
│   │   │   └── scripts/housing_lima/   the engine: model, analysis, listings, intake, schemas/, config/, app/
│   │   ├── peru-listings-search/   SKILL.md, reference.md, listings_template.csv, scripts/
│   │   ├── peru-safe-investments/  SKILL.md, reference.md, scripts/index_returns.py
│   │   ├── rent-vs-buy-model/      SKILL.md, reference.md
│   │   └── streamlit-dashboard/    SKILL.md, reference.md
│   └── agents/                     market-data.md, opportunity-cost.md, financial-analysis.md, streamlit-builder.md
├── tests/                          94 tests: model, listings, intake, schemas, analysis, CLI, dashboard
├── evaluation.md                   requests to run with and without skills
├── install.py                      copies the skills and agents to ~/.claude
├── pyproject.toml
└── README.md
```

The engine lives inside the orchestrator skill, so every skill folder is self-contained: the same files work from
this repository and from `~/.claude/skills`.

## Outputs

Every run writes into the folder you work from:

| Path | Content |
|---|---|
| `outputs/<run-id>/inputs.json` | Your normalized search |
| `outputs/<run-id>/listings.csv` | Every listing with its URL, date, price in soles and duplicate / outlier / in-range flags |
| `outputs/<run-id>/market_summary.json` | Per district: counts, P25 / median / P75, realistic price and rent |
| `outputs/<run-id>/housing_params.json` | Mortgage rates, growth, costs, taxes, insurance, inflation, each with source and date |
| `outputs/<run-id>/opportunity_costs.json` | The three investment options with low / base / high returns |
| `outputs/<run-id>/analysis_*.{csv,json,md}` | Results grid, verdicts, and a one-page report |
| `outputs/<run-id>/*_log.md` | What each research agent searched, fetched and skipped |
| `outputs/validation.txt` | Summary of the latest validation: listings per district, values without a source, verdicts |
| `figures/verdicts.png` | Share of scenarios where buying wins, by district and horizon |
| `figures/<district>_wealth.png` | Buyer vs renter wealth over 30 years |
| `figures/<district>_heatmap_20y.png` | Buy minus rent after 20 years, mortgage rate × investment option |
| `data/listings.csv` | Optional: listings you paste by hand if the portals block automated search |

## Install

Requirements: Python 3.11+ (tested on 3.14) with pandas, numpy, streamlit, plotly, matplotlib, jsonschema and
pyyaml (declared in `pyproject.toml`; `uv sync` or `pip install -e .`).

The skills work in two places with the same content:

| Where | Use |
|---|---|
| `.claude/` in this repository | Versioned with git; active when Claude Code is opened in this folder |
| `~/.claude/skills` and `~/.claude/agents` | Available in **any** folder, including the desktop app |

```bash
cd sessions/16-skills-enaho/Skill_Buy_Rent
python install.py              # copy the 5 skills and 4 agents to ~/.claude
python install.py --uninstall  # remove them
```

Restart Claude Code and type `/skills` to check that all five are listed. After changing anything here, run
`python install.py` again.

## Run it

The orchestrator is **`buy-vs-rent`**. In Claude Code (terminal, desktop app or VS Code), from the folder where
you want the results:

| You type | What happens |
|---|---|
| `/buy-vs-rent` | Asks the five questions, runs the four agents, reports the verdict |
| "Should I buy or rent an apartment in Surco?" | Same: the skill triggers from its description |
| `/buy-vs-rent fixture` | Full dry run on synthetic data, no internet needed |

The five questions: price range in soles; minimum m² and bedrooms; districts (one to six); down-payment percentage;
extras (parking, new or used, pets, maximum monthly payment, maximum building age).

The engine can also be called directly through its launcher, `HL` below:

| Shell | `HL` = |
|---|---|
| PowerShell | `python "$HOME\.claude\skills\buy-vs-rent\scripts\hl.py"` |
| Git Bash / macOS / Linux | `python ~/.claude/skills/buy-vs-rent/scripts/hl.py` |
| Without installing (from this folder) | `python .claude/skills/buy-vs-rent/scripts/hl.py` |

PowerShell does not expand `~` for Python, so use `$HOME` there.

| Command | What it does |
|---|---|
| `HL check-env` | Checks Python and packages |
| `HL new-run --answers answers.json` | Validates the answers and creates `outputs/<run-id>/inputs.json` |
| `HL listings --run D --raw f.csv --source-mode live\|csv\|mixed` | Cleans listings and computes realistic price and rent |
| `HL validate --run D --stage research\|analysis\|all` | Schema checks; writes `validation.txt` |
| `HL analyze --run D` | Runs the model |
| `HL summary --run D` | Short summary |
| `HL figures --run D` | Exports the PNG figures |
| `HL check-app --run D` | Tests the dashboard on a run |
| `HL fixture-run` | Complete run on synthetic data |

Tests: `python -m pytest -q` from this folder (94 tests, no network).

## Assumptions

- Horizons of 5, 10, 15, 20 and 30 years; the loan term is a separate parameter, 20 years by default.
- Mortgage rates: the market average from −2 to +2 percentage points.
- Verdict per district and horizon: "buy" when buying wins in at least 80% of the grid scenarios, "rent" at 20% or
  less, otherwise "depends".
- The S&P 500 is converted to soles with an assumed yearly USD/PEN change, 0% by default.
- The renter is assumed to pay the building fee (usual in Lima), so it cancels out.
- All modelling assumptions are commented in `.claude/skills/buy-vs-rent/scripts/housing_lima/config/defaults.yaml`.
- Housing subsidies (Bono del Buen Pagador) are not modelled; `housing_lima/subsidy.py` is the extension point.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `/buy-vs-rent` is not listed | Run `python install.py`, restart Claude Code, type `/skills` |
| The skill does not trigger by itself | Call it with `/buy-vs-rent`, or use words from its description: buy, rent, Lima |
| The agents do not start | Check `~/.claude/agents/` and type `/agents`; without agents the orchestrator runs the steps itself |
| Portals block the search | Copy `listings_template.csv` to `data/listings.csv`, paste listings with URL and date, run again (`source_mode: csv`) |
| A district shows "low confidence" | Fewer than 8 sale or rent listings were found; widen the range or drop the district |
| It does not work in the claude.ai web chat | Skills there run without internet or your Python packages; use Claude Code |

## Dashboard (Streamlit)

The dashboard runs locally, with no network calls, on any run folder. Open a terminal in the folder that holds
`outputs/` (for the example: `sessions/16-skills-enaho/Example`) and run:

```powershell
# PowerShell
python "$HOME\.claude\skills\buy-vs-rent\scripts\hl.py" dashboard --run outputs\<run-id>
```

```bash
# Git Bash / macOS / Linux
python ~/.claude/skills/buy-vs-rent/scripts/hl.py dashboard --run outputs/<run-id>
```

Replace `<run-id>` with the folder name inside `outputs/`, for example
`20261103-2350-pueblo-libre-jesus-maria-magdalena`. If the skills are not installed, point to the launcher in this
repository instead: `python <path to>\Skill_Buy_Rent\.claude\skills\buy-vs-rent\scripts\hl.py dashboard --run ...`.
For the example there is a shortcut: `python run_dashboard.py` inside `Example/`.

The browser opens http://localhost:8501; stop the server with Ctrl+C. Without `--run` it opens the newest run in
`outputs/`, or the synthetic fixture if there is none. (The command is the same as
`streamlit run <engine>/app/app.py -- --run outputs/<run-id>`.)

In the sidebar you can change the mortgage rate, the down payment, the opportunity cost (three options or a custom
rate, low / base / high), the purchase price (bounded by your range; by default the median of the listings found),
the negotiation discount, the loan term, price and rent growth, and real vs nominal terms. The page shows:

1. **Verdict by district**: who wins at 5, 10, 15, 20 and 30 years, and by how much in soles.
2. **Heat map**: buy minus rent across mortgage rates and investment returns.
3. **Wealth over time**: buyer vs renter, with the break-even year.
4. **Price check**: histogram of the listings and a table with links to each listing.
5. **Assumptions and sources**: every parameter with origin, source and date, plus all warnings.
6. **Downloads**: the current scenario as CSV.
