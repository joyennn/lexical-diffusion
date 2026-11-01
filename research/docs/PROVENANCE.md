# Provenance and release adaptations

The simulation runners, analysis rules, prompts, seeds, and retained raw observations
are preserved. Materialized raw files must match their original uncompressed SHA-256
hashes. Gzip/tar wrappers use deterministic metadata; decompression changes no bytes.

The original internal freezes and amendments document decisions made during the
research program. They are not a public preregistration of the entire program.
`RELEASE_ADAPTATIONS.json` records host-path normalization only. Two metadata
files need relative paths for execution from the restored study directory:

- `time200/lineage.json`: `baseline_root` and each `source_checkpoint` point to
  `../../fresh_study1/...`.
- `memory4000/provenance.json`: `baseline_root` is `../../fresh_study1`.

Their original before/after hashes are recorded. In each affected directory,
`provenance_release/historical_freeze.json` preserves the original freeze record;
the public `freeze.json` updates only the normalized metadata file hash and labels
this release adjustment. Existing scientific amendments retain their original
before/after code hashes. No public freeze is represented as a new pre-inference registration.

Other host paths in non-scientific metadata are replaced by `${WORKSPACE}`.
Prompts, raw model outputs, events, checkpoints, material content, and per-task
request hashes are not rewritten. Controllers, PID/status files, download caches,
logs, environment directories and private local paths are not publication inputs.

New release helpers provide isolated unpacking, original-analysis invocation,
paper-table export, and fresh-inference orchestration. They are separate from the
historical experimental source, and are tested as release infrastructure. Original
report generators are retained where freeze verification requires them, but the
old IEEE manuscript/template is not part of this release.

The source material provenance is retained in each study's materials metadata.
The input spreadsheet hash is `03d6fe55e6b9092668b3fd75a9e753a7c4a2b0776ef60a7ea485a98310288818`.
The recovered original materials came from
https://github.com/joyennn/information-diffusion at revision
`852ea2bf9f6e79523145c61b925f5665d79d9165`. Its older simulation outcomes are excluded.

Successful numerical reproduction does not establish independent human validation
of semantic items, independent simulation replication, or hardware-independent
bitwise generation. It establishes recovery of the distributed numerical findings
from the retained records using the documented rules.
