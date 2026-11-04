---
name: streamlit-dashboard
description: Opens, checks and updates the local Streamlit buy-vs-rent dashboard for Lima and exports the PNG figures of a run (verdicts, wealth over time, heat map) to figures/. Use when the dashboard or figures must be created, changed, debugged or checked against a run folder, or when the user asks how to open the dashboard.
---

# Streamlit dashboard and figures

The dashboard is implemented in `buy-vs-rent/scripts/housing_lima/app/`. Its purpose is not only to show the
verdict but to **explain how it was reached**, so the user can follow and challenge it. Your job: check it works
for each run, export the figures, adjust the app when asked. Layout, text and figures: [reference.md](reference.md).

`HL` means `python "${CLAUDE_SKILL_DIR}/../buy-vs-rent/scripts/hl.py"`.

## Principles (do not break)

1. **Offline.** The app reads one run folder (newest in `outputs/` by default, selectable in the sidebar, the
   synthetic fixture as last resort) and makes no network calls.
2. **One model.** Import `housing_lima.model` / `housing_lima.analysis.build_scenario`; never re-implement a formula.
   Every explanation number comes from `housing_lima.explain`, whose parts add up exactly to the model's result
   (tested in `tests/test_explain.py`), so the explanation can never contradict the verdict.
3. **Listings anchor the price.** The purchase-price slider is bounded by the user's range and defaults to the
   realistic (median) price of the listings; the P25–P75 band is shown.
4. **Plain English labels** for everything the user sees (`app/labels.py`).
5. **Explain before exploring.** Right after the verdict cards comes "How the recommendation was made": six
   numbered steps (homes from listings → same money each month → what each owns → the three comparisons that
   decide it → the scenario vote behind buy/rent/depends → the values that would flip it). Every step is a
   sentence with the actual numbers plus at most one chart. New explanations go there, in plain words.
6. **Sources visible.** Every number shows origin and date in "Assumptions and sources"; fallbacks say
   "needs your input"; the educational-use disclaimer is shown.

## Check a run and export figures

```bash
HL check-app --run <run_dir>       # AppTest: starts without errors and the sliders change the result
HL figures   --run <run_dir>       # writes to figures/ next to the outputs/ folder that holds the run
```

Figures follow the dataviz rules: buyer blue `#2a78d6`, renter orange `#eb6834`, diverging blue↔red with a gray
zero for buy-minus-rent, bars from zero, one y-axis, the title says what and when, a footnote gives source and
date, 200 dpi.

## Open the dashboard for the user

```bash
HL dashboard --run <run_dir>       # = streamlit run .../app/app.py -- --run <run_dir>
```

## Changing the app

- Add a control with a stable `key`, preset from the run (never a literal market number).
- In the repository, add an AppTest case in `tests/test_app.py` that changes it, and run `python -m pytest -q`.
- A new explanation goes into `housing_lima/explain.py` (pure, no Streamlit), with a test in
  `tests/test_explain.py` proving it adds up to `simulate`; then render it in section 2 of `app.py`.
