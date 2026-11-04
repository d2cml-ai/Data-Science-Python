# Failure handling

| Situation | What to do |
| --- | --- |
| `check-env` not ok | List the missing packages; install only with the user's approval |
| `new-run` returns `ok: false` | Ask again only the question named by `code`, in Spanish; show `suggestions` for districts |
| A district has fewer than 8 sale or 8 rent listings | Tell the user; offer to widen the filters (price, m², bedrooms) or drop the district. Re-run market-data only with the new `inputs.json` (create a new run). Never fill the gap with invented data. The district stays in the results labelled low confidence if the user keeps it |
| A district has no usable listing at all | It is reported as "not analysed"; offer the same options |
| An agent's output fails `validate` | Re-run that agent once, attaching the exact validation errors to its prompt. If it fails again, stop and report the errors |
| market-data reports `source_mode: csv` or `mixed` | Continue, and say clearly in the final report that listings came (partly) from a user-supplied CSV, not a live search |
| `data/fallback/listings.csv` does not exist and live search failed | Stop. Explain how to fill the fallback CSV (skill peru-listings-search, `references/fallback-csv.md`) |
| `analyze` stops because the mortgage rate is unknown | Ask the user for a rate (or permission to re-run market-data); do not invent one |
| Unknown parameters (`unknowns`) | Not a failure: they are carried as warnings. Mention the important ones in the report |
| Dashboard tests fail | streamlit-builder fixes `app/` or reports; do not hand over a launch command for a broken app |

Never continue past a failed step by guessing, and never edit an agent's output file by hand to make
validation pass.
