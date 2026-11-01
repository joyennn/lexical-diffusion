# Neologism circulation

Research code and data for **Neologism circulation and semantic recognition in
language model agents**.

This repository examines how supplied English expressions recur and spread across
outputs of interacting language model agents, and how the models perform on semantic
recognition questions in the contexts preceding first use. The experiments distinguish
actual exposure, repeated output, coverage across agents, and receptive recognition.
The systems are studied as computational text-production systems; they are not proxies
for human language users.

## Studies

All simulation conditions retain 60 expressions, 10 persona instructions, and four
pinned model configurations: Llama 3 8B Instruct, Qwen3-8B, Gemma 2 9B IT, and
Mistral 7B Instruct v0.3, using community four-bit MLX conversions.

| Study | Question and design |
|---|---|
| Study 1 | Baseline circulation over 100 cycles |
| Study 2-1 | Fresh 100-cycle runs with a 50% source-recommendation branch on voluntary reads, allowing rereading |
| Study 2-2 | Continue the same baseline trajectories through cycle 200 |
| Study 2-3 | Fresh 100-cycle runs with the memory-summary trigger increased from 1,000 to 4,000 characters |
| Study 3 | Definition and novel-scenario recognition in matched initial and pre-generation contexts: 135 cases and 810 retained responses |

Each fresh simulation condition has **one exploratory trajectory per model**.
Cycles, agents, words, and semantic responses are not independent simulation repeats.
Study 2-2 extends existing trajectories rather than adding independent runs.
Semantic probes assess receptive recognition, not the correctness of each original
message or evidence of learning during interaction.

## Repository contents

The full release is in [`research/`](research/README.md):

- [`source/`](research/source/): experimental scripts, protocols, materials, frozen
  semantic questions, answer keys, amendments, and derived results.
- [`data/`](research/data/): compressed raw requests/responses, checkpoints, per-cycle
  snapshots, message/exposure tables, and separate pilot/excluded records, with checksums.
- [`results/`](research/results/): manuscript tables and reproduction/validation reports.
- [`tools/`](research/tools/): verification, data restoration, pinned-model download,
  and table/figure export tools.
- [`docs/`](research/docs/): data dictionary, provenance, exclusions, and rights notes.

Model weights, API credentials, reviewer correspondence, manuscript drafts, virtual
environments, and unrelated historical simulation outcomes are excluded. Technical
pilots and the superseded preliminary semantic responses are retained separately
for auditing and are never pooled with main results.

## Reproduce the results without a GPU

Clone with Git, then run Python 3.11+ on macOS or Linux:

```sh
git clone https://github.com/joyennn/neologism-circulation.git
cd neologism-circulation
```

Verify and regenerate the numerical results without downloading models:

```sh
python3 research/tools/verify_release.py
python3 research/reproduce.py --workspace work/reproduction
```

The second command restores about 4.05 GiB of uncompressed records into a **new**
workspace, runs tests and independent audits, and compares 15 regenerated numerical
CSVs with the retained results. It performs **no LLM inference**. Numerical
reproduction uses Python's standard library; fresh model inference and optional
plotting have separate dependencies.

Fresh inference on Apple Silicon is documented in the
[research README](research/README.md#fresh-inference-on-apple-silicon). It requires
explicit execution, the pinned model downloads, and a separate destination; supplied
observations are not overwritten.

## Interpretation and reuse

These findings describe the recorded configurations and exploratory trajectories.
Literal frequency, user coverage, and semantic recognition are distinct outcomes.
Some semantic-test contexts retain source definitions, and the AI-assisted question
bank has not received independent human validation. See the
[interpretation limits](research/README.md#interpretation) and
[data dictionary](research/docs/DATA_DICTIONARY.md) before drawing conclusions.

Citation metadata are provided in [`CITATION.cff`](research/CITATION.cff).
No DOI or unrestricted third-party license is claimed. Consult
[NOTICE](research/docs/NOTICE.md) for model and source-material rights.

**한국어 안내:** 실험별 코드·데이터와 재현 설명서를 포함한 저장소입니다.
기존 결과 재분석은 GPU나 모델 다운로드 없이 가능하며, 새 실험 실행은 별도
환경에서 명시적으로 시작해야 합니다. 이전 실험과 폐기 조건은 현재 결과에
포함하지 않습니다.
