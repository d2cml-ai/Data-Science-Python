# Orchestrator reference

## Intake questions

Offer options where possible; the user can always answer in free text (in any language).

| # | Question | Options to offer | Answer field |
| --- | --- | --- | --- |
| 1 | What price range are you willing to pay? (minimum and maximum, in soles) | S/ 200–300k · S/ 300–450k · S/ 450–650k · S/ 650k–1M | `price_min`, `price_max`, `currency` |
| 2 | What is the minimum size in m² and the minimum number of bedrooms you would accept? | 50 m² / 1 bed · 65 m² / 2 beds · 80 m² / 3 beds · 110 m² / 3 beds | `min_area_m2`, `min_bedrooms` |
| 3 | Which districts? (one to six) | Multiple choice from the common list below + free text | `districts` |
| 4 | What percentage of the price can you pay as a down payment? | 10% · 20% · 30% · 40% | `down_payment_pct` |
| 5 | Anything else for the search? (parking, new or used, floor, pets, maximum monthly payment, maximum building age) | Nothing else · With parking · Brand new · Free text | `extras_text` |

Common districts to offer (AskUserQuestion allows 4 options per question, so split them over two
multi-select questions or offer the four most likely and let "Other" take the rest): Miraflores, San Isidro,
Santiago de Surco, San Borja, Barranco, Jesús María, Pueblo Libre, San Miguel, Lince, Magdalena del Mar,
La Molina, Surquillo. Any of the 43 districts of Lima or the 7 of Callao is accepted; aliases such as "SMP",
"Surco", "Magdalena" or "Cercado" are normalized by `new-run`.

### Answers file for `new-run`

```json
{
  "price_min": 450000,
  "price_max": 550000,
  "currency": "PEN",
  "min_area_m2": 60,
  "min_bedrooms": 2,
  "districts": ["Pueblo Libre", "Jesús María", "Magdalena del Mar"],
  "down_payment_pct": 20,
  "extras_text": "less than 10 years old"
}
```

If the user answers in dollars, set `"currency": "USD"` and add `fx_usd_pen`, `fx_as_of` and `fx_source_url`
with today's rate from an official source (SBS or BCRP). The rate is recorded in `inputs.json`.

### Normalization done by `new-run`

- Minimum below maximum, both positive; amounts converted to soles.
- Down payment 5–50% (`0.2` is read as 20%).
- Districts matched to official names; unknown names come back with suggestions.
- Free text (English or Spanish) becomes `parking_min`, `max_age_years`, `max_monthly_payment`, `is_new`,
  `pets_allowed`, `min_floor`; the full text stays in `notes` as a soft preference for the agents.

## Failure handling

| Situation | What to do |
| --- | --- |
| `check-env` not ok | List the missing packages; install only with the user's approval |
| `new-run` returns `ok: false` | Ask again only the question named by `code`; show `suggestions` for districts |
| A district has fewer than 8 sale or 8 rent listings | Tell the user; offer to widen the filters (price, m², bedrooms) or drop the district. Re-run market-data only with the new `inputs.json` (create a new run). Never fill the gap with invented data. The district stays in the results labelled low confidence if the user keeps it |
| A district has no usable listing at all | It is reported as "not analysed"; offer the same options |
| An agent's output fails `validate` | Re-run that agent once, attaching the exact validation errors to its prompt. If it fails again, stop and report the errors |
| market-data reports `source_mode: csv` or `mixed` | Continue, and say clearly in the final report that listings came (partly) from a user-supplied CSV, not a live search |
| `data/listings.csv` (in the working folder) does not exist and live search failed | Stop. Explain how to fill the fallback CSV (skill peru-listings-search, `reference.md`, section CSV fallback) |
| `analyze` stops because the mortgage rate is unknown | Ask the user for a rate (or permission to re-run market-data); do not invent one |
| Unknown parameters (`unknowns`) | Not a failure: they are carried as warnings. Mention the important ones in the report |
| Dashboard check fails | streamlit-builder fixes the app or reports; do not hand over a launch command for a broken app |

Never continue past a failed step by guessing, and never edit an agent's output file by hand to make
validation pass.
