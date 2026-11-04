---
name: streamlit-dashboard
description: Builds, updates and tests the local Streamlit buy-vs-rent dashboard for Lima (app/app.py) that reads one run folder offline. Use when the dashboard must be created, changed, debugged or checked against a run folder, or when the user asks how to open it.
---

# Streamlit dashboard

The dashboard is already implemented in `app/`. Your job is to keep it working for each new
run, adjust it when asked, and prove it works with tests. Layout details:
[references/layout.md](references/layout.md). Spanish wording: [references/spanish-labels.md](references/spanish-labels.md).

## Principles (do not break)

1. **Offline.** The app reads one run folder (latest in `runs/` by default, selectable in the sidebar,
   synthetic fixture as last resort) and makes no network calls.
2. **One model.** Import `housing_lima.model` / `housing_lima.analysis.build_scenario`. Never re-implement a formula in `app/`.
3. **Listings anchor the price.** The purchase-price slider is bounded by the user's range and defaults
   to the realistic (median) price of the listings; the P25–P75 band is shown.
4. **Spanish labels** for everything the user sees (`app/labels.py`). Code and comments in English.
5. **Sources visible.** Every number shows its origin and date in "Supuestos y fuentes". Fallback values
   are labelled "necesita tu dato". Show the educational-use disclaimer.

## Files

| File | Role |
| --- | --- |
| `app/app.py` | Layout: sidebar controls, six sections |
| `app/state.py` | Run discovery (`--run`, `HOUSING_LIMA_RUN`, `runs/`, fixture), cached loading, control defaults |
| `app/components/cards.py` | Verdict cards (one `st.metric` per district × horizon) |
| `app/components/charts.py` | Heat map, wealth over time, price histogram (Plotly) |
| `app/labels.py` | Spanish text |

## Check a run

```bash
cd "${CLAUDE_PLUGIN_ROOT}"
python scripts/hl.py validate --run <run_dir> --stage all
python -m pytest -q tests/test_app.py                      # AppTest on the synthetic fixture, network blocked
HOUSING_LIMA_RUN=<run_dir> python -m pytest -q tests/test_app.py   # same tests on the new run
```

Then launch headless and confirm it serves:

```bash
python -m streamlit run app/app.py --server.headless true --server.port 8599 -- --run <run_dir>
curl -s http://localhost:8599/_stcore/health     # -> ok, then stop the server
```

## Launch command for the user

```bash
streamlit run "${CLAUDE_PLUGIN_ROOT}/app/app.py" -- --run "<run_dir>"
```

## Changing the app

- Add a control: give it a stable `key`, preset it from the run (never a literal market number), and add
  an AppTest case that changes it and asserts the metrics change.
- Charts follow the dataviz rules: buyer = blue `#2a78d6`, renter = orange `#eb6834`, diverging blue↔red with
  a gray zero for buy-minus-rent, one y-axis, hover tooltips, direct labels on the two lines.
