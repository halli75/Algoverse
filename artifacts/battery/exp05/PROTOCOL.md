# exp05 — Dictator + Ultimatum (locked)

[[battery-campaign]] [[EMOTIC]] [[LLM-Economicus]]

Not a VA/sycophancy amendment. No `v3` overwrite. No DESCRIBE-before-task. No steer.

## Model / data

- `google/gemma-4-E4B-it` nf4 weights, bf16 compute. GPU 1. No fallback.
- EMOTIC eval split `1e8ea1c22144dd9d` only.
- Chat `[image, text]`. Natural prepend. Conditions: fear, anger, sadness, sympathy, affection (if labeled n ok), happiness, neutral, no-image.

## Items

Frozen in `items.json`. Ultimatum stems from LLM Economicus + Microsoft Turing. Dictator is the Economicus proposer line with the veto removed (Forsythe/Engel).

Primary DVs are forced-choice letters mapped to dollars or accept/reject. Digit Likert is not used.

6-way letter+dollar (A–F amounts) failed FC mass (~0.26–0.31). Locked repair: A/B amount pairs `$0` vs `$50` and `$50` vs `$80`. Reject A/B was already valid (mass 0.999). Threshold stays 0.8. Run1/run2 kept as `results_run1.json` / `results_run2.json`.

## Predictions (test, do not assume)

- sympathy/affection → give more (dictator EV vs neutral)
- anger → reject unfair (90/10 and 80/20 vs neutral)
- fear → give/trust less (dictator EV vs neutral)

## Gates (do not retune)

- split hash, model/dtype, no-DESCRIBE, eval-only images
- mean forced-choice letter mass ≥ 0.8
- n ≥ 16 per primary cell
- finite means + 95% bootstrap CIs
- `results.json` has `gates.passed` / `gates.total` and `mechanism_answer`
