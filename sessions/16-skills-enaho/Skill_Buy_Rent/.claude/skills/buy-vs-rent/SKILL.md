---
name: buy-vs-rent
description: Answers "is buying a home better than renting in Lima?" for the user's own search (buy vs rent, mortgage vs rent, apartment in Lima or Callao). Asks the intake questions, validates them, runs the market-data and opportunity-cost agents in parallel, then financial-analysis and streamlit-builder, and reports the verdict per district and horizon with figures and the dashboard. Use for any buy-vs-rent question about Lima or Callao.
argument-hint: "[fixture]"
---

# Buy vs rent in Lima (orchestrator)

You are the single entry point. You ask, validate, run the four agents in order and report. **You never do
the heavy work yourself**: no web research, no model maths, no dashboard code. Agents exchange files in a run
folder; you pass only the run folder path and read only small summary output.

`HL` means `python "${CLAUDE_SKILL_DIR}/scripts/hl.py"`. Run it from the user's working folder: run folders go to
`outputs/<run-id>/`, figures to `figures/`, user files (the listings CSV fallback) live in `data/`.

If the argument is `fixture`, skip to **Dry run**.

## 1. Intake (before anything else)

Ask the five questions in [reference.md](reference.md) (section "Intake questions"), in the user's language. Use
the AskUserQuestion tool for the multiple-choice parts (it allows free text through "Other"); group them in at
most two rounds. Skip any question the user already answered. Do not start any agent until every answer is in.

## 2. Validate and create the run

1. `HL check-env`. If `ok` is false, list what is missing and ask before installing anything.
2. Write the answers to a temporary JSON file (fields in reference.md) and run `HL new-run --answers <file>`.
3. If it returns `ok: false`, use `code` to ask again **only** the question concerned (`price_range`, `size`,
   `district` with `suggestions`, `down_payment_out_of_range`, `fx_needed`, `currency`). A down payment outside
   5–50% is a warning and a new question, never a refusal.
4. On success keep `run_dir` (it holds a valid `inputs.json`) and show the normalized search in two lines.

## 3. Research agents, in parallel

Launch **both in the same message** (two Agent tool calls in one turn), each with only the run folder path:
`market-data` and `opportunity-cost`. Prompt: `Run folder: <absolute run_dir>. Follow your skill. Return only the
short summary.` Then `HL validate --run <run_dir> --stage research`.

## 4. Analysis, dashboard check and figures

1. Launch `financial-analysis` with the run folder path.
2. Then launch `streamlit-builder` with the run folder path (it checks the app and writes the figures).
3. `HL validate --run <run_dir> --stage all` (this also writes `outputs/validation.txt`).

If the Agent tool or these agents are not available, do the four steps yourself in the same order, loading
each skill: peru-listings-search, peru-safe-investments, rent-vs-buy-model, streamlit-dashboard.

## 5. Report (a few lines)

Run `HL summary --run <run_dir>` and tell the user:

- What was found per district (sale and rent counts, realistic price and rent). Say clearly if `source_mode` is
  `csv` or `mixed` (data came from a user file, not a live search).
- The headline verdict per horizon (5, 10, 15, 20, 30 years) per district: buy / rent / depends.
- The most important warnings (unknown parameters, low-confidence districts).
- Where `analysis_report.md`, `outputs/validation.txt` and `figures/` are, and the dashboard command from the
  summary (`HL dashboard --run <run_dir>`).
- The educational-use disclaimer, in one sentence.

## Failure handling

See [reference.md](reference.md) (section "Failure handling"). In short: fewer than 8 listings per side in a
district → tell the user and offer to widen filters or drop the district; schema failure → re-run that agent once
with the error attached, then stop and report; never continue past a failed step by guessing; never invent data.

## Dry run

`HL fixture-run` builds a complete run from the SYNTHETIC fixture (the research outputs are copied, the listings go
through the real CSV pipeline, the analysis runs for real). Then `HL figures --run <run_dir>` and report as in
step 5, saying clearly that the data is synthetic.
