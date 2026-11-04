# Dashboard reference

## Sidebar controls

| Control | Key | Range and default |
| --- | --- | --- |
| Run | `run` | Runs found; `--run` first |
| District for the detail view | `district` | Districts of the run with a realistic price and rent |
| Mortgage rate (annual effective) | `mortgage_rate` | Grid min −1 pp to grid max +1 pp; default market average |
| Down payment | `down_payment` | 5–50%; default the user's answer |
| Opportunity cost | `option` | The three options (by risk) + "Custom rate" |
| Return scenario | `level_<option>` | Low / Base / High from `opportunity_costs.json` |
| USD/PEN change | `fx_change` | Only for options with `return_usd_*`; default `fx_change_assumption` |
| Return | `ret_<option>_<level>_<preset>` / `ret_custom` | −5% to 20%; preset from the scenario |
| Purchase price | `price_<district>` | User's price range; default realistic price; P25–P75 in the caption |
| Negotiation discount | `discount` | 0–20%; default from the run (0%) |
| Loan term | `loan_term` | 10/15/20/25/30; default `defaults.yaml` (20) |
| Price growth / rent growth | `price_growth_<district>`, `rent_growth_<district>` | −5% to 10%; preset from params; "needs your input" when a fallback is used |
| Real vs nominal | `real` | Toggle; deflates by CPI inflation |

District-specific keys reset the slider to that district's defaults when the district changes. The price and
growth sliders apply to the detail district only; the cards for the other districts use their own realistic
price and parameters with the shared controls (rate, down payment, return, discount, term).

## Main page

1. **Verdict by district**: one row per district, five `st.metric` (5–30 years), value "Buying wins" /
   "Renting wins" with ▲/▼, delta in soles. The help text shows the grid verdict of the original analysis.
2. **Heat map**: buy − rent over mortgage rate (current ±2 pp, 0.5 pp steps) × return (0–14% plus the current
   value) for the detail district at the chosen horizon. Open circle = current scenario.
3. **Wealth over time**: buyer vs renter, 0–30 years, dotted break-even line, loan summary, warning if the
   renter's portfolio goes negative.
4. **Price check**: histogram of clean in-range sale listings with the P25–P75 band and the chosen price; table
   of all listings of the district with links (`LinkColumn`) and dates.
5. **Assumptions and sources**: parameter table (value, origin, source, date), banks, option risks, every
   warning, the disclaimer.
6. **Downloads**: current scenario per district × horizon, and the yearly path of the detail district.

## Text

All user-facing text lives in `buy-vs-rent/scripts/housing_lima/app/labels.py`. Keep it plain and short.
The disclaimer comes from `housing_lima.DISCLAIMER`. Numbers: soles as `S/ 350,000`; rates as `8.50%`.

## Figures (`HL figures`)

| File | Content |
| --- | --- |
| `figures/verdicts.png` | Share of grid scenarios where buying wins, by district and horizon, with the 80% / 20% thresholds |
| `figures/<district>_wealth.png` | Buyer vs renter wealth, 0–30 years, at the market rate and the lowest-risk option |
| `figures/<district>_heatmap_20y.png` | Buy − rent after 20 years: mortgage rate × opportunity-cost option |
