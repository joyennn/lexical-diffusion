# Data dictionary

Archive members restore to their historical relative paths. Consult `data/archives.json`
for their exact identities, checksums, and category. UTF-8 JSON/JSONL and CSV are used.

## Simulation records

| File | Contents |
|---|---|
| `runs/{pilot,main}/{model}/calls.jsonl` | One request/response attempt per line: task key, request hash, prompt content, sampling/model settings, raw output, status, token counts, elapsed seconds, timestamp |
| `checkpoint.json` | Complete final simulator state: seed, source agent, target horizon, completion/cursor fields, agents, posts, comments, events, exposures |
| `snapshots/cycle_NNN.json` | Full state at each completed cycle; duplicates parts of earlier histories intentionally |
| `posts.csv`, `comments.csv` | Generated/public content with agent, cycle, task identifiers, raw and transmitted text, and literal target IDs; initial posts are flagged |
| `events.csv` | Ordered turns, decisions, selected parent, incoming/generated content, memory before/after, and summary task references |
| `exposures.csv` | Content actually entering another agent's input, with source kind/identity and matched target IDs |
| `completed.json` | Completion metadata, cycles, seed, model, stage |
| `backend.json` | Recorded model/configuration and device information |

Agent IDs are 0–9; source ID is stored explicitly in each checkpoint. Term IDs are
0–59 and map to `materials/terms.json`. Mutable memories and source-private glossary
are distinct. `text` is the transmitted prefix; `raw_text` is the full completion.
Public posts have 100-character/40-token ceilings and comments 50-character/20-token
ceilings. Exact generation requests are the authoritative record of prompts.

`time200/runs/main/*/calls.jsonl` includes copied cycles 1–100 plus new cycles
101–200. `origin/*/calls_1_100.jsonl` and `checkpoint_100.json` preserve the baseline
prefix. These copied records are not additional independent observations.

## Materials and semantic jobs

`terms.json` contains the expression, supplied meaning, example (nullable), usage
notes, and retained labels. The missing `shadow banning` example stays null.
`personas.json` contains the ten fixed instruction profiles, not recruited participants.

| Semantic file/field | Meaning |
|---|---|
| `cases.json` | Every selected first non-source agent–expression use, original task/hash, cycle/action and exact `initial_prefix`/`use_prefix` |
| `earlier_or_same_turn_exposure` | Recorded external encounter occurred no later than the first output; false cases are retained |
| `exact_source_definition_in_prefix` | Verbatim supplied definition remains in the use prefix; absence does not exclude paraphrases/examples |
| `item_bank.json` | Fixed definition/scenario questions, keyed answer, three distractors |
| `item_content.tsv` | Source-based authored semantic content used to construct the bank |
| `jobs.json` | 810 retained model/case/item/state requests, shuffled options, fixed answer index, paired seed |
| `runs/main/*/calls.jsonl` | Actual digit responses to retained jobs; correctness is recomputed from the fixed key |

`meaning` denotes definition recognition; `application` denotes novel-scenario
selection, also a receptive task. `use` means immediately before original generation,
not after observing the generated message. There are 135 cases and 45 expressions
in the union, with 15 expressions untested. Initial and use jobs share options/order/seed.

## Derived outputs

`occurrences_per100messages` = 100 × literal occurrences / generated messages;
`occurrences_per1000characters` = 1000 × occurrences / transmitted characters.
`term_bearing_message_percent` counts each message at most once.
`distinct_used_words` counts expressions; `unique_user_word_pairs` counts agent–expression
pairs. `exposure_linked_first_users` requires an earlier/same-turn encounter before
the first literal output, not a proven causal or semantic adoption event.
Non-source denominators are nine agents × sixty expressions = 540 potential pairs.

Unreached timing endpoints are censored/null with an event indicator, not imputed as
an event at the final cycle. Twenty-cycle outputs describe one evolving trajectory.
For semantics, word-macro accuracy averages within expression before averaging
across expressions; micro accuracy weights each response equally. Paired transitions
and leave-one-word/agent-out ranges are descriptive, not independent-run confidence intervals.
