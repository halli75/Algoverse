# Affect-conditioned behavioral battery — A100 campaign

[[sycophancy-affect-experiment]] [[EMOTIC]] [[VA-subspace]]

New campaign. Not an amendment of the aborted EmoBank-VA sycophancy confirmatory.
Do not overwrite `artifacts/colab/e2e_mechanism_results_full_v3.json`.
Do not relaunch the VA-gated sycophancy full run. Do not retune frozen refusal/sycophancy gates.

**Model:** `google/gemma-4-E4B-it` only. nf4 weights, bf16 compute. No fallback.
**Images:** EMOTIC eval split `1e8ea1c22144dd9d` unless the experiment is the OASIS contrast (exp08).
**Steer:** none in main arms. Natural image prepend only. Chat order `[image, text]`.
**Do not DESCRIBE the image in the main behavioral prompt.**
**Primary DVs:** forced-choice letters or dollar/accept amounts. Likert is secondary; Gemma-4 digit mass has already failed.
**Deadline:** A100 host is destroyed Mon Aug 24 02:45 UTC. Checkpoint off-box continuously.

**Results (exploratory):** all ten runs finished. Scientific SUCCESS/FAILED labels, numbers, and “real vs noise” percents are in [`docs/battery_results.md`](battery_results.md). Do not treat this protocol table as confirmatory.

## Experiments

| ID | Experiment | Extra data beyond EMOTIC | Scientific |
|---|---|---|---|
| exp01 | Fear vs anger on risk (Economicus Gambling / lottery A/B) | LLM Economicus prompts (GitHub) | FAILED |
| exp02 | Scene-matched EMOTIC caliper pairs | None (EMOTIC metadata) | FAILED |
| exp03 | Cross-modal signature (pixels / caption / de-affectized / label / narrative) | Existing caption prompts | SUCCESS (weak) |
| exp04 | Perez sycophancy as behavior only (no VA / no `s` fit) | Perez JSONL (pinned SHA256) | FAILED |
| exp05 | Dictator + Ultimatum | Published game instructions | SUCCESS (partial) |
| exp06 | Temporal discounting (Economicus Waiting) | LLM Economicus Waiting | SUCCESS (partial) |
| exp07 | Capability negative control | TruthfulQA MC (fallback MMLU-CF) | FAILED |
| exp08 | EMOTIC depicted vs OASIS elicited | OASIS (required; EMOTIC cannot stand in) | FAILED |
| exp09 | Soft safety / over-refusal | XSTest (fallback: existing border items) | SUCCESS |
| exp10 | Representation mediation on frozen v3 `a_perp` | Frozen v3 dirs; do not refit (run used DIAGNOSTIC_NOT_V3) | SUCCESS (partial) |

## Shared A100 lock

Host has **8× NVIDIA A100-SXM4-40GB**. Still cap **4 concurrent** Gemma-4 loads so the first HF download and host RAM do not stampede.

GPU file: `$E2E_ROOT/battery/A100.lock` (default `~/algoverse_run/battery/A100.lock`).
Local board: `artifacts/battery/STATUS.md` and `artifacts/battery/queue.json`.

Claim a GPU id before load (`CUDA_VISIBLE_DEVICES`). Preferred ids in `queue.json`.
If 4 jobs are already `running`, wait. Serialize the first `google/gemma-4-E4B-it` download.
Heartbeat every 5 minutes. Stale lock (>20 min, no heartbeat) may be stolen after writing `STALE_LOCK` to STATUS.
Do not take over the overseer's JupyterLab UI tab. Start your own kernel or `nohup` process.

## 15-minute loops

Each experiment agent: work 15 min, check A100/heartbeat/logs, fix stalls, continue. Do not stop until `artifacts/battery/<id>/results.json` exists with finite primary estimates and a `passed/total` gate block.
Overseer (this chat): same cadence across all ten.

## Advisor

Complex design/architecture: spawn `generalPurpose` with model `gpt-5.6-sol-high`.
**Fable 5 is not available** in this Cursor session. Do not request it.
If spawn fails, write `artifacts/battery/<id>/ADVISOR_REQUEST.md`; the overseer will spawn the advisor.

## Outputs

Each experiment writes only under `artifacts/battery/<id>/` and `scripts/battery_<id>_*.py`.
Shared adapter only: `scripts/battery_adapter.py`, `scripts/battery_a100_boot.py`.
Never commit tokens, passwords, or harmful completions. Aggregate rates only.
