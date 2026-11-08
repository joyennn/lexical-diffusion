# Lexical diffusion

Execution code and Study 3 semantic evaluation questions for the lexical-circulation
experiments with four language model agent configurations. This repository contains
**code and input materials only**. Results, generated responses, saved interaction
contexts, checkpoints, statistical outputs, manuscript drafts, and model weights
are not included in the current published tree.

## Find what you need

| Folder | Contents |
|---|---|
| [`code/`](code/) | Simulation runners, run preparation, model download, and Study 3 job preparation/inference |
| [`evaluation/`](evaluation/) | Study 3 questions, correct answers, and distractors — readable, CSV, and JSON |
| [`materials/`](materials/) | Shared 60 expressions, 10 personas, and pinned model identifiers |

**Start here:** [Read all Study 3 questions and answer keys](evaluation/QUESTIONS_AND_KEYS.md)

- [Download question/answer CSV](evaluation/questions_and_keys.csv)
- [Machine-readable question bank](evaluation/questions.json)
- [Study 1 baseline runner](code/runners/baseline.py)
- [Study 2-1 source-access runner](code/runners/source_access.py)
- [Study 2-2 continuation preparation](code/prepare_run.py)
- [Study 2-3 delayed-summary runner](code/runners/memory4000.py)
- [Study 3 context and question preparation](code/study3/prepare.py)
- [Study 3 inference runner](code/study3/run.py)

## Experimental conditions

All fresh simulations retain 60 expressions, ten fixed persona instructions, four
pinned model configurations, and 100 cycles. Model configurations are Llama 3 8B
Instruct, Qwen3-8B, Gemma 2 9B IT, and Mistral 7B Instruct v0.3 (four-bit MLX).

| Condition | Change relative to baseline |
|---|---|
| Study 1 — `baseline` | Ordinary unread-post selection; summary trigger >1,000 characters |
| Study 2-1 — `source_access` | On a voluntary non-source read, a 50% branch samples a source introduction with replacement; the other branch uses baseline selection |
| Study 2-2 — `continuation` | Preserve a completed baseline state and continue cycles 101–200 |
| Study 2-3 — `memory4000` | Fresh 100 cycles; change only the summary trigger to >4,000 characters |
| Study 3 | Probe the initial and exact pre-generation contexts for each first non-source agent–expression use under source access |

Study 2-1 combines recommendation priority and rereading; it does not impose a
fixed word-level exposure count. Continuation uses the same baseline trajectory,
not an independent repeat. The delayed summary retains the same 100-token summary
generation limit and maximum 500 stored characters.

## Run locally

Inference requires Apple Silicon/macOS, Python, sufficient model memory and access
to the pinned weights. Read the scripts before starting long computations. Commands
below prepare fresh local outputs; they do not reproduce historical observations
byte-for-byte or download any published results.

```sh
python3 -m venv .venv
.venv/bin/pip install -r code/requirements.txt
.venv/bin/python code/download_models.py --output work/models
export MODEL_STORE="$PWD/work/models"

.venv/bin/python code/prepare_run.py --condition baseline --seed 2026110300 --output work/baseline
```

Preparation prints four commands, one per model. Run these sequentially using the
same virtual-environment Python. For example:

```sh
.venv/bin/python work/baseline/run.py --model llama --stage main --cycles 100 --hours 96
```

Replace `llama` with `qwen`, `gemma`, and `mistral` to run the remaining models.
For a different independent seed, create another output directory. The recorded
seed values were 2026103000 and 2026110300. Seeds end in zero to retain source identity.

Prepare the other conditions with:

```sh
.venv/bin/python code/prepare_run.py --condition source_access --seed 2026110300 --output work/source_access
.venv/bin/python code/prepare_run.py --condition memory4000 --seed 2026110300 --output work/memory4000
.venv/bin/python code/prepare_run.py --condition continuation --seed 2026110300 --baseline-dir work/baseline --output work/continuation
```

Run the printed commands; continuation requires all four baseline checkpoints to
be complete. It copies their history locally and adds only cycles 101–200. The
original baseline folder is preserved. Interrupted runs can resume with the same
copied runner command. Avoid simultaneous runs of the same model/output directory.
Technical pilots were separate from main observations; these minimal commands
launch main inference only. To conduct a local technical check first, the copied
simulation runner also accepts `--stage pilot --cycles 3` in a separate pilot tree.

### Study 3

After all four source-access trajectories are complete:

```sh
.venv/bin/python code/study3/prepare.py --exposure-dir work/source_access --output work/study3
.venv/bin/python work/study3/run.py
```

The preparation code preserves the additional-run case-selection and paired-option
logic, using the fixed published 180-item bank. It creates case-specific contexts,
jobs, and a hash freeze locally before semantic inference. Both contexts share
options/order and sampling seed. The runner uses `MODEL_STORE` to locate weights;
it generates new local pilot/main responses. Neither generated contexts nor answers
are uploaded by these scripts. The portable wrappers change file locations and
execution setup, not the inference rules. Simulation runner files retain the
original experimental implementation; continuation reuses the baseline runner.

## Study 3 evaluation sheet

The bank contains **180 items**: one definition and two scenario questions for each
of 60 expressions. It preserves the original 135 items and the 45 items added before
the additional simulation. Each question has one keyed answer and three distractors.
The CSV and JSON show the correct answer separately; they do not represent the
randomized option order used in any particular assessment. In JSON, `correct` is
answer text. Locally prepared job files use `correct` as a zero-based option index.

The source senses define the keys. AI-assisted questions have not received independent
human validation or calibrated distractor difficulty. The probes assess recognition
in supplied contexts, not the appropriateness of spontaneous output or evidence
of human language learning.

**한국어 안내:** 실행 코드는 `code`, 평가 문항·정답은 `evaluation`, 공통 입력자료는
`materials`에 있습니다. 결과·응답·통계표는 현재 공개 파일에 포함하지 않습니다.
평가 문항은 원문을 유지했고, 보기 순서는 실제 평가 실행 시 코드에서 구성합니다.

See [NOTICE](NOTICE.md) for source-material and model rights. No unrestricted
third-party license or human validation is claimed.
