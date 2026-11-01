# Included and excluded records

Included: the fresh four-model Study 1, exposure50, time200, memory4000, and the
retained version-2 Study 3 probes. All main configurations and outcomes are retained,
including low-use expressions, zero encounters, non-use/censoring and pre-exposure first uses.

Technical pilots are packaged separately and excluded from main analysis:
baseline/exposure three cycles per model; memory five cycles; semantic final pilots
24 responses. The time extension uses copied baseline history and no new LLM pilot.

Study 3 amendment 001 found option-format cues before retained inference. The
archived 313 preliminary main responses and initial 24-response pilot are preserved
under `study3_semantics/amendments/001_definition_option_cues/`, including their
earlier bank and freeze. Their archive is labelled `excluded_do_not_pool`.
No question in `reproduce.py` reads those excluded responses as retained data.

Excluded from the current scientific release: the earlier six-model IEEE Access
simulations in `revision/`, the abandoned twelve-word/three-exposure `fresh_study2/`,
reviewer letters, draft manuscripts, model weights, credential files, local
controllers, live status/lock files, and obsolete packaging outputs. These exclusions
do not remove unsuccessful cases from any retained main condition.
