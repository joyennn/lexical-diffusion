# Neologism circulation and semantic recognition in language model agents

Code, retained observations, frozen materials, and reproducibility tools for the
four-model exploratory study. The complete public-release tree is in [`research/`](research/README.md).

**수록 범위:** 새 Study 1, Study 2-1 노출 정책, Study 2-2 시간 연장,
Study 2-3 기억 요약 시점, Study 3 의미 인식 평가. 이전 IEEE Access 실험과
폐기된 12단어 조건은 현재 결과에 포함하지 않습니다.

No model weights, API credentials, manuscript drafts, reviewer correspondence,
virtual environments, or unrelated historical outcomes are included.

Recompute the retained numerical results without downloading a model:

```sh
python3 research/tools/verify_release.py
python3 research/reproduce.py --workspace work/reproduction
```

The second command restores about 4 GiB of uncompressed records into a **new**
workspace, runs tests and independent audits, and compares the regenerated CSVs
with the retained results. It performs **no LLM inference**.

Read [scope and limitations](research/README.md#interpretation) before using the results.
