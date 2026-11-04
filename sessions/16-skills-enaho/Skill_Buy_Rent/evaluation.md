# Evaluation: with and without skills

Run each request twice, with and without skills, and note which skills were triggered, whether real listings with
URL and date were used, whether the numbers come from the model, and what the output looks like.

```bash
claude -p "<request>"                                  # with skills
claude -p --disallowedTools Skill "<request>"          # without skills
```

| # | Request | Skills that should trigger | Expected result |
|---|---|---|---|
| 1 | `/buy-vs-rent fixture` | `buy-vs-rent` (+ `streamlit-dashboard`) | Complete synthetic run; `outputs/validation.txt` with `RESULT: OK`; figures in `figures/` |
| 2 | Should I buy or rent a 2-bedroom apartment in Pueblo Libre with a S/ 500k budget? | `buy-vs-rent` → the four agents | First the missing questions (size, down payment, extras); then listings with URLs and a verdict for 5–30 years |
| 3 | What would the monthly payment be on a S/ 280,000 loan at 8.5% over 20 years? | `rent-vs-buy-model` | About S/ 2,375 per month, from the constant-payment formula on the annual effective rate |
| 4 | How does a fixed-term deposit in soles compare with the S&P 500? | `peru-safe-investments` | Rates by bank with URL and date; S&P 500 converted to soles; educational-use note |

## Results

| # | With skills: what triggered? | Number | Sources and dates? | Without skills: what happened | Note |
|---|---|---|---|---|---|
| 1 | | | | | |
| 2 | | | | | See `../Example` for a full real run of this kind of request |
| 3 | | | | | |
| 4 | | | | | |

What to look for without skills: invented prices or rates with no source, missing buying and selling costs, a rent
comparison that forgets to invest the down payment, a single answer with no horizon or assumptions.

If a skill does not trigger, add the words of the request to its `description` and try again.
