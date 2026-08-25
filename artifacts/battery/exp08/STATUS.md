# exp08 STATUS — complete

Tick: 2026-08-23 01:25 ET. Host `results.json` has `complete: true`.

## Run
- GPU 4 (exp04 had released). Elapsed 73.3s smoke.
- Model `google/gemma-4-E4B-it` nf4 / bf16. Steer none. Chat `[image, text]`.
- Sizes: 12 images × 12 risk × 12 dictator × 16 Perez. N_BOOT=64.
- Gates 9/9. `frozen_v3_untouched`. OASIS official `OASIS.csv` n_rated=900. EMOTIC split `1e8ea1c22144dd9d`.
- `do_not_pool: true`. `pooled_effect_size: null`. Constructs kept separate.

## Signatures (smoke only)
All six primary CIs include 0 (`both_null` per task). Locked matcher therefore reports `signatures_match_visual_affect`. That is not a same-sign effect; it is an underpowered smoke. Point estimates differ in sign (EMOTIC slightly negative, OASIS slightly positive). Do not treat this as a full-n visual-affect claim. Do not pool the two corpora.

## Queue note
A leftover `battery_exp08_run.py` (pid 2052748) kept writing the old waiter heartbeat and holding the max-4 queue. Killed it, then the new claimer took GPU 4.
