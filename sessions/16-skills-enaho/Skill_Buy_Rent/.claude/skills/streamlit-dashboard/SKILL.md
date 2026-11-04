---
name: streamlit-dashboard
description: Opens, checks and updates the local Streamlit buy-vs-rent dashboard for Lima and exports the PNG figures of a run (veredictos, patrimonio, mapa de calor) to figuras/. Use when the dashboard or figures must be created, changed, debugged or checked against a run folder, or when the user asks how to open the dashboard.
---

# Streamlit dashboard and figures

The dashboard is implemented in `buy-vs-rent/scripts/housing_lima/app/`. Your job: check it works for each run,
export the figures, adjust the app when asked. Layout and Spanish wording: [reference.md](reference.md).

`HL` means `python "${CLAUDE_SKILL_DIR}/../buy-vs-rent/scripts/hl.py"`.

## Principles (do not break)

1. **Offline.** The app reads one run folder (newest in `salidas/` by default, selectable in the sidebar, the
   synthetic fixture as last resort) and makes no network calls.
2. **One model.** Import `housing_lima.model` / `housing_lima.analysis.build_scenario`; never re-implement a formula.
3. **Listings anchor the price.** The purchase-price slider is bounded by the user's range and defaults to the
   realistic (median) price of the listings; the P25–P75 band is shown.
4. **Spanish labels** for everything the user sees (`app/labels.py`). Code and comments in English.
5. **Sources visible.** Every number shows origin and date in "Supuestos y fuentes"; fallbacks say "necesita tu dato";
   the educational-use disclaimer is shown.

## Check a run and export figures

```bash
HL check-app --run <run_dir>       # AppTest: starts without errors and the sliders change the result
HL figures   --run <run_dir>       # figuras/veredictos.png, <distrito>_patrimonio.png, <distrito>_mapa_calor_20a.png
```

Figures follow the dataviz rules: buyer blue `#2a78d6`, renter orange `#eb6834`, diverging blue↔red with a gray
zero for buy-minus-rent, bars from zero, one y-axis, title says what and when, footnote with source and date,
200 dpi.

## Open the dashboard for the user

```bash
HL dashboard --run <run_dir>       # = streamlit run .../app/app.py -- --run <run_dir>
```

## Changing the app

- Add a control with a stable `key`, preset from the run (never a literal market number).
- In the repository, add an AppTest case in `tests/test_app.py` that changes it, and run `python -m pytest -q`.
