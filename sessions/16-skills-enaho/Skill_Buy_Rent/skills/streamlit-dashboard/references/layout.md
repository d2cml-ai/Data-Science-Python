# Layout

## Sidebar controls

| Control | Key | Range and default |
| --- | --- | --- |
| Run | `run` | Runs found; `--run` first |
| District for the detail | `district` | Districts of the run with a realistic price and rent |
| Mortgage rate (TEA) | `mortgage_rate` | Grid min −1 pp to grid max +1 pp; default market average |
| Down payment | `down_payment` | 5–50%; default the user's answer |
| Opportunity cost | `option` | The three options (by risk) + "Tasa personalizada" |
| Return level | `level_<option>` | Bajo / Base / Alto from `opportunity_costs.json` |
| USD/PEN change | `fx_change` | Only for options with `return_usd_*`; default `fx_change_assumption` |
| Return | `ret_<option>_<level>_<preset>` / `ret_custom` | −5% to 20%; preset from the level |
| Purchase price | `price_<district>` | User's price range; default realistic price; P25–P75 in caption |
| Negotiation discount | `discount` | 0–20%; default from the run (0%) |
| Loan term | `loan_term` | 10/15/20/25/30; default `defaults.yaml` (20) |
| Price growth / rent growth | `price_growth_<district>`, `rent_growth_<district>` | −5% to 10%; preset from params; "necesita tu dato" when a fallback |
| Real vs nominal | `real` | Toggle; deflates by CPI inflation |

The district-specific keys reset the slider to that district's defaults when the district changes.
The price and growth sliders apply to the detail district only; the cards for other districts use their
own realistic price and parameters with the shared controls (rate, down payment, return, discount, term).

## Main page

1. **Veredicto por distrito**: one row per district, five `st.metric` (5–30 years), value "Comprar gana" /
   "Alquilar gana" with ▲/▼, delta in soles. Help text shows the grid verdict of the original analysis.
2. **Mapa de calor**: buy − rent over mortgage rate (current ±2 pp, 0.5 pp steps) × return (0–14% plus the
   current value) for the detail district at the chosen horizon. Open circle = current scenario.
3. **Patrimonio en el tiempo**: buyer vs renter, 0–30 years, break-even dotted line, loan summary caption,
   warning if the renter's portfolio goes negative.
4. **Revisión de precios**: histogram of clean in-range sale listings with the P25–P75 band and the chosen
   price; table of all listings of the district with links (`LinkColumn`) and dates.
5. **Supuestos y fuentes**: parameter table (value, origin, source, date), banks, option risks, every warning,
   the disclaimer.
6. **Descargas**: current scenario per district × horizon, and the yearly path of the detail district.
