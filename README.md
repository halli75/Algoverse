# algoverse

Read-only affect experiments (VLM emotional-image vs text affect).

This repo mirrors Colab results (tables, ratios, thresholds). Tensors are downloaded manually; Drive mount via the MCP bridge does not work.

## Behavioral battery (2026-08-23, exploratory)

Ten A100 experiments on `google/gemma-4-E4B-it` with natural EMOTIC prepend. Protocol: [`docs/battery_campaign.md`](docs/battery_campaign.md). Per-experiment SUCCESS/FAILED labels: [`docs/battery_results.md`](docs/battery_results.md). Scores are exploratory (no pre-score lock). Do not overwrite `artifacts/colab/e2e_mechanism_results_full_v3.json`.

## Locked for this phase

- Model: Gemma-3-4B (Qwen at Step 6)
- Today: Step 0 + Step 2 kill switch only
- Judge: Grok via xAI API (`XAI_API_KEY` in `.env`; never commit)
- Affect protocol: **match Charlotte** — mean-over-layers projection + multi-layer norm-scaled steer (`ALPHA_JB=0.008`); gate window `[8,20)`
- Ethics: mentor OK; aggregate refusal rates only — no harmful completions saved
- MM-SafetyBench pairs: curate in Colab
- Order if Step 2 passes: 2 → 3 → 4 → 1 → 5 → 6 → 7
- Arnav Colab: https://colab.research.google.com/drive/1zAoSyYTIfTEER56WJU0KN2iklYYVNtXi
- Extracts: `docs/teammate-findings.md`, `docs/charlotte-colab-extract.md`

## Do not commit

- API keys
- Harmful model completions (aggregate rates only)
- Large tensors / EMOTIC images
