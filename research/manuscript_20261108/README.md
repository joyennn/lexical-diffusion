# Manuscript code and Study 3 questions

This package supplements the original single-run release with the code, fixed
semantic questions, scored responses, descriptive inputs, and Bayesian analysis
used for the two-run manuscript. No new model inference was performed for this upload.

## Quick links

- [All 180 questions and answer keys — readable version](study3_questions/QUESTIONS_AND_KEYS.md)
- [Questions, correct answers, and distractors — CSV](study3_questions/items_and_answer_keys.csv)
- [Frozen 180-item bank — JSON](study3_questions/item_bank_180.json)
- [Original 135-item bank — JSON](study3_questions/item_bank_original_135.json)
- [Actual option orders and answer indices for 1,482 presentations](study3_questions/actual_item_presentations_1482.json)
- [Study 1 inference runner](replication_check/rep02/fresh_study1/run_study1.py)
- [Source-access inference runner](replication_check/rep02/study2_mechanisms/exposure50/run_exposure.py)
- [Time-extension inference runner](replication_check/rep02/study2_mechanisms/time200/run_study1.py)
- [Memory-condition inference runner](replication_check/rep02/study2_mechanisms/memory4000/run_study1.py)
- [Study 3 inference runner](replication_check/rep02/study3_semantics/run.py)
- [Independent raw-data audit and descriptive analysis](replication_check/analyze_replications.py)
- [Bayesian count analysis](output/LV_two_run_statistics/fit_count_long.R)
- [Bayesian semantic analysis with context slopes](output/LV_two_run_statistics/fit_semantic_slopes.R)
- [Complete posterior contrasts and diagnostics](output/LV_two_run_statistics/statistics/)
- [Study 2 three-measure means and sample SDs](results/study2_three_metrics_mean_sd.json)

## Scope and provenance

The manuscript combines two independently seeded trajectories per model and fresh
condition (seeds 2026103000 and 2026110300). Continuation extends each baseline
trajectory through cycle 200; it is not another independent trajectory. Technical
pilots are excluded from main outcomes. The four models, 60 supplied expressions,
10 fixed persona instructions, and three distinct Study 2 comparisons are retained.
The source-recommendation condition changes prioritization and permits rereading.

The original inference source and first-run raw observations remain in
[`../source/`](../source/) and [`../data/`](../data/). This supplementary package
contains the additional-run source, protocols, materials, analysis-ready observations
and statistical results. It **does not contain the second-run raw generation logs,
full checkpoints, model weights, manuscript drafts, or reviewer correspondence**.
Consequently, analysis from the supplied CSVs is possible, but independent replay
of every second-run raw generation is not provided by this package. Existing audit
reports document checks previously performed against the retained local raw data;
their inclusion is not a claim that those raw data are distributed here.

[`PROVENANCE.json`](PROVENANCE.json) records original/released file hashes and any
host-workspace path substitutions. No questions, responses, scientific rules,
scores, priors, or fitted estimates were changed. Historical freeze hashes refer
to original experiment files; the release-wide checksums describe distributed files.

## Study 3 instrument

The original 135 items (45 expressions) are preserved verbatim in the expanded
180-item bank. Forty-five items covering the other 15 expressions were fixed before
the additional simulation. Each expression has one `meaning` item (definition)
and two `application` items (novel scenarios). The bank includes items not used
in a particular run: assessment cases depend on the expressions actually first
produced by non-source agents under source access.

There are 135 first-use cases and 810 answers in the original run, and 112 cases
and 672 answers in the additional run: 247 cases and 1,482 responses overall.
Each case is assessed in an initial and a saved pre-generation context. Questions
are paired with the same options/order and sampling seed across these contexts.

In the bank JSON, `correct` is the **correct answer text**. In the actual-presentation
JSON, `correct` is the **zero-based correct option index (0–3)**, not the model's
accuracy. `run` identifies Run1 or Run2. The scored-response CSV instead uses
`correct` for binary model accuracy (0/1). The readable bank does not claim to show
the randomized administered order; use the presentation JSON for that purpose.

The supplied source senses define the answer keys. The AI-assisted question bank
has not received independent human validation; distractor difficulty was not
calibrated. Recognition scores do not establish appropriate spontaneous use,
interaction-induced learning, or human language behavior.

## Verification and analysis

Run from the repository root, with Python 3.11+ and no model dependencies:

```sh
python3 research/manuscript_20261108/verify_package.py
```

This verifies file hashes, retained-bank identity, item/option keys, actual paired
presentations, score-record alignment, and the three-measure descriptive table.
It performs no LLM inference and no posterior sampling.

Analysis inputs are in `replication_check/analysis/`. The count model uses 32
model–condition–run observations with message-count offsets; the logistic model
uses 1,482 binary answers with dependence terms and context slopes. Full model
code, primary and wider-prior contrasts, diagnostic tables and the recorded R
session are in `output/LV_two_run_statistics/`. Reported intervals are 95%
equal-tailed Bayesian credible intervals. Posterior increase probabilities are
not frequentist p-values. Expression and agent–expression coverage are descriptive;
the count model estimates occurrence-rate contrasts only. The analysis was post hoc.

For posterior refitting, first copy this package to a new working directory to
preserve the published outputs. Install R, CmdStan, and the R packages `cmdstanr`,
`posterior`, and `jsonlite`. From that copy's root, run:

```sh
Rscript output/LV_two_run_statistics/fit_count_long.R
Rscript output/LV_two_run_statistics/fit_semantic_slopes.R
Rscript output/LV_two_run_statistics/verify_statistics.R
```

Refitting performs substantial computation and writes new posterior output;
small numerical differences may occur. Full saved posterior draws/RDS objects
are not included, but the scripts regenerate them from the supplied inputs.
No posterior sampling is needed to inspect the retained estimates.

Fresh model inference is separate: see the [original documented entry point](../README.md#fresh-inference-on-apple-silicon).
The copied experiment controllers are provenance records, not a one-command,
portable release entry point; raw-data audits require the corresponding run trees.
Do not run historical preparation scripts to overwrite a frozen instrument.

All Study 2 measures exclude the source agent. Expression coverage divides the
number of used expressions by 60; agent–expression coverage divides used pairs
by 540. Continuation counts all uses within cycles 101–200, including expressions
and combinations previously used in cycles 1–100. It does not count only new types.
Means and sample SDs are computed from run-specific measurements, not by pooling
messages. Additional seeds require recomputing summaries and statistical models.

Source-material and model-rights notes in [NOTICE](../docs/NOTICE.md) also apply.
