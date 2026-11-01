# Research release

This release supports the manuscript **Neologism circulation and semantic
recognition in language model agents**. It contains observed outputs, not simulated
placeholder data. Four pinned configurations are retained throughout:
Meta-Llama-3-8B-Instruct, Qwen3-8B, Gemma-2-9B-IT, and Mistral-7B-Instruct-v0.3,
using the exact community four-bit MLX revisions in `source/fresh_study1/models.json`.

## Included studies

| Directory below `source/` | Design | Independent trajectories per model |
|---|---|---|
| `fresh_study1` | 60 expressions, 10 personas, baseline 100 cycles | 1 |
| `study2_mechanisms/exposure50` | Same materials, fresh 100 cycles; 50% recommendation branch on a non-source voluntary read; rereading allowed | 1 |
| `study2_mechanisms/time200` | Continue the original baseline state through cycles 101–200 | Same baseline trajectory, not another replicate |
| `study2_mechanisms/memory4000` | Fresh 100 cycles; summary trigger changes from >1000 to >4000 characters | 1 |
| `study3_semantics` | Matched initial/pre-generation definition and scenario probes on all 135 first-use cases from exposure50 | 810 retained responses nested within existing trajectories |

There is one source agent with persistent private glossary access and nine
non-source agents. The source's initial introductions and generated messages are
separated from primary non-source output measures. A cycle gives ten agents one
turn each; it is not an independent experiment. The source recommendation branch
is **not** a fixed word-level exposure dose. Actual source-reading shares can
exceed 50%. The 4000-character condition delays compression but retains the
100-token summary generation and 500-character stored-summary limits.

## Files

- `source/`: verbatim experimental Python source, fixed materials and protocols,
  existing analytical CSVs, freeze records and amendments. Host-path-only metadata
  changes are listed in `RELEASE_ADAPTATIONS.json`.
- `data/*.tar.gz`: raw calls, final checkpoints, all retained cycle snapshots,
  exported messages/exposures, and separate pilot records. No weights are included.
- `data/archives.json`: every compressed archive and every uncompressed member,
  with byte counts and SHA-256 hashes.
- `data/source_files.json`: hashes of distributed source/material/result files.
- `results/`: the main paper tables exported as CSV, plus the successful release
  reproduction report.
- `tools/`: verification, unpacking, pinned model download, and table/figure export.
- `reproduce.py`: numerical reproduction from completed observations.
- `new_run.py`: explicit, isolated fresh inference; dry-run by default.
- `docs/`: data dictionary, exclusions, portability, provenance, and licensing notes.

## Reproduce retained results without inference

Use Python 3.11+ on macOS or Linux. Numerical reproduction uses Python's standard
library; the archived inference controllers import Unix `fcntl`. No MLX, model
download, GPU, API key, TeX installation, or manuscript generator is needed.

From the repository root:

```sh
python3 research/tools/verify_release.py
python3 research/reproduce.py --workspace work/reproduction
```

The destination must be absent or empty and outside `research/`. The command
verifies compressed and uncompressed hashes, restores data and source into that
new directory, executes original tests/analysis/independent checks, and compares
15 numerical CSVs to the release. It writes `work/reproduction/reproduction_report.json`
and `work/reproduction/paper_results/`. Audit timestamps and review-code hashes
are not numerical results and are not expected to match historical timestamps.
The distributed data remain untouched.

To restore only, without analysis:

```sh
python3 research/tools/materialize.py --destination work/restored
```

To make the paper figures after reproduction, install the optional plotting
dependency and use the restored workspace:

```sh
python3 -m pip install -r research/requirements-plotting.txt
python3 research/tools/make_paper_figures.py --workspace work/reproduction --output work/figures
```

## Fresh inference on Apple Silicon

Fresh generation is distinct from reproducing the retained numerical observations.
Stochastic/MLX/hardware differences may change new outputs even with matching seeds.
The recorded runs used an M1 Pro with 16 GB unified memory, loading one model at a time.

```sh
python3 -m venv .venv
.venv/bin/pip install -r research/requirements-inference.txt
.venv/bin/python research/tools/download_models.py --destination work/models
.venv/bin/python research/new_run.py --condition baseline --destination work/new-baseline --seed 2026103010
```

The last command only prints a plan. Add the following options to explicitly run:

```sh
.venv/bin/python research/new_run.py --condition baseline --destination work/new-baseline --seed 2026103010 --model-store work/models --hours 96 --execute
```

Other supported condition names are `exposure50`, `memory4000`, `time200`, and
`semantics`. The first three 100-cycle conditions run separate technical pilots
before their main runs. Seeds ending in zero preserve the source persona while
varying feed/generation randomness. For the time extension, supply a completed
100-cycle baseline directory; the original first hundred cycles are copied as
history and are never counted as new inference:

```sh
.venv/bin/python research/new_run.py --condition time200 --baseline-dir work/reproduction/fresh_study1 --destination work/new-time200 --model-store work/models --hours 96 --execute
```

`semantics` regenerates fresh answers to the **retained frozen 810 jobs** with
their original paired task-specific seeds; it does not select new first-use cases
or validate the item bank. The original `prepare.py` is included for provenance,
but cannot overwrite a frozen bank. Building a new study's questions/cases needs
an explicit new protocol and instrument review.

`new_run.py` never copies retained response caches into fresh conditions. Only
`time200` copies its explicit baseline history. Inference results go to an isolated
subtree matching the original study layout. An interrupted new run retains calls
and checkpoints; resume its copied low-level runner with matching model, stage,
cycles, and `MODEL_STORE`, rather than trying to create the same destination again.
The archived legacy manuscript-generating pipeline is not the entry point for this
release. New trajectories need separate analysis and review; do not pool them with
the retained results without documenting the new design.

## Interpretation

All simulation conditions are exploratory, with one trajectory per configuration.
There are no model-population significance tests. Normalized frequency, target-bearing
messages, expression diversity, agent coverage, first-use timing, and actual encounters
are different measurements. Literal matches do not identify the intended sense.
The 810 semantic responses are not 810 independent simulation replications.
Probes assess receptive recognition; some use prefixes contain source definitions.
They do not establish acquisition, retention after source removal, appropriate
spontaneous use, or a policy-specific semantic benefit versus baseline. The bank
was AI-assisted and has not received independent human validation. These systems
are not proxies for human language users.

See [the data dictionary](docs/DATA_DICTIONARY.md), [provenance and portability](docs/PROVENANCE.md),
and [excluded records](docs/EXCLUSIONS.md). Licensing and third-party material notes
are in [NOTICE](docs/NOTICE.md). No public repository, DOI, or external validation
is claimed solely by the presence of this local release.
