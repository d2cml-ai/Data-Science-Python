---
name: buy-vs-rent
description: Answers "is buying a home better than renting in Lima?" for the user's own search (¿me conviene comprar o alquilar un departamento en Lima?). Asks the intake questions, validates them, runs the market-data and opportunity-cost agents in parallel, then financial-analysis and streamlit-builder, and reports the verdict per district and horizon with the dashboard command. Use for any buy-vs-rent, comprar vs alquilar, or mortgage-vs-rent question about Lima or Callao.
argument-hint: "[fixture]"
---

# Buy vs rent in Lima (orchestrator)

You are the single entry point. You ask, validate, run the four agents in order and report. **You never do
the heavy work yourself**: no web research, no model maths, no dashboard code. Agents exchange files in a run
folder; you pass only the run folder path and read only small summary output.

`HL` below means `python "${CLAUDE_PLUGIN_ROOT}/scripts/hl.py"`.

If the argument is `fixture`, skip to **Dry run**.

## 1. Intake (Spanish, before anything else)

Ask the five questions in [references/intake-questions.md](references/intake-questions.md). Use the
AskUserQuestion tool for the multiple-choice parts (it allows free text through "Other"); group them in at most
two rounds. Do not start any agent until every answer is in.

## 2. Validate and create the run

1. Check the environment: `HL check-env`. If `ok` is false, list what is missing and ask before installing
   anything (`pip install -e "${CLAUDE_PLUGIN_ROOT}"`).
2. Write the answers to a temporary JSON file (fields in intake-questions.md) and run
   `HL new-run --answers <file>`.
3. If it returns `ok: false`, use `code` to ask again **only** the question concerned, in Spanish
   (`price_range`, `size`, `district` with `suggestions`, `down_payment_out_of_range`, `fx_needed`, `currency`).
   A down payment outside 5–50% is a warning and a new question, never a refusal.
4. On success, keep `run_dir`. It contains a valid `inputs.json`. Show the user, in two lines, the normalized
   search (districts with official names, price range in soles, structured extras).

## 3. Research agents, in parallel

Launch **both in the same message** (two Agent tool calls in one turn), each with only the run folder path:

- `market-data` (plugin agent `housing-lima:market-data`)
- `opportunity-cost` (plugin agent `housing-lima:opportunity-cost`)

Prompt for each: `Run folder: <run_dir>. Follow your skill. Return only the short summary.`

When both finish: `HL validate --run <run_dir> --stage research`.

## 4. Analysis, then dashboard

1. Launch `financial-analysis` (`housing-lima:financial-analysis`) with the run folder path.
2. Then launch `streamlit-builder` (`housing-lima:streamlit-builder`) with the run folder path.
3. `HL validate --run <run_dir> --stage all`.

## 5. Report (a few lines, Spanish)

Run `HL summary --run <run_dir>` and tell the user:

- What was found per district (sale and rent counts, realistic price and rent). Say clearly if
  `source_mode` is `csv` or `mixed` (data came from a user file, not a live search).
- The headline verdict per horizon (5, 10, 15, 20, 30 years) per district: comprar / alquilar / depende.
- The most important warnings (unknown parameters, low-confidence districts).
- Where the run folder and `analysis_report.md` are, and the launch command:
  `streamlit run "${CLAUDE_PLUGIN_ROOT}/app/app.py" -- --run "<run_dir>"`.
- The educational-use disclaimer, in one sentence.

## Failure handling

Follow [references/failure-handling.md](references/failure-handling.md). In short: fewer than 8 listings per
side in a district → tell the user and offer to widen filters or drop the district; schema failure → re-run that
agent once with the error attached, then stop and report; never continue past a failed step by guessing;
never fill gaps with invented data.

## Dry run

`HL fixture-run` builds a complete run from the SYNTHETIC fixture (research agents in fixture mode: their
outputs are copied, the listings go through the real CSV pipeline, the analysis runs for real). Then launch
`streamlit-builder` on the returned `run_dir` and report as in step 5, saying clearly that the data is synthetic.
