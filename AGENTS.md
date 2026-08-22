# algoverse

Read-only affect experiments (VLM emotional-image vs text affect). The repo mirrors
Colab/GPU results; see `README.md` for the locked scientific protocol.

## Cursor Cloud specific instructions

### What is runnable in this environment (no GPU)

The heavy end-to-end pipelines (`scripts/e2e_*.py`) are **Colab/GPU-only**: they import
`google.colab`, `transformer_lens`, `transformers`, `torch`, do a Hugging Face login, and
load Gemma/Qwen VLMs on a GPU with manually-uploaded tensors/EMOTIC images. They cannot run
here and are not part of local dev — treat their outputs under `artifacts/colab/` as frozen
mirrors of Colab runs.

Locally the testable/runnable surface is pure-numpy and tiny:

- `scripts/affect_core.py` — the locked shared affect/refusal method (numpy only).
- `tests/test_affect_core.py` — 19 unit tests for that core (no GPU, no network).
- `src/judge.py` — Grok judge over the external xAI API; needs `XAI_API_KEY` (from `.env`
  or env). Without the key it raises `RuntimeError` by design; that is expected, not a setup
  failure.

### Commands

- Tests: `python3 -m unittest discover -s tests` (or `python3 -m pytest tests/ -q`).
- Lint: no linter is configured in the repo. Use `python3 -m py_compile <files>` as a syntax
  check.
- Core smoke: `import affect_core` from `scripts/` and call e.g. `core_pin()`,
  `gate_window(34)`, `calibrate_gate_on_split(...)` — see `tests/test_affect_core.py` for
  usage patterns.

### Gotchas

- Only `numpy` is required for tests/core; `torch` is intentionally absent. Do not add torch
  to make the e2e scripts import — they still need a GPU/Colab.
- `pip install --user` puts `pytest` in `~/.local/bin`, which is not on `PATH`. Invoke it as
  `python3 -m pytest` or `~/.local/bin/pytest`.
- Frozen artifacts are guarded: `affect_core` refuses to overwrite
  `artifacts/colab/e2e_mechanism_results_full_v3.json` (`FrozenArtifactError`). A test asserts
  that file exists, so do not delete it.
- Never commit API keys or harmful model completions (aggregate rates only) — see `README.md`.
