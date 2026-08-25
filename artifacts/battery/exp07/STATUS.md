# exp07 capability negative control

phase: done
updated: 2026-08-23 04:54 UTC
gpu: 4
tier: full
dataset: truthfulqa_mc_binary_2025 n=790 sha256 pin matched
complete: True
mechanism_answer: EQUIVALENCE_INCONCLUSIVE
gates: 10/11

accuracy:
- no_image 0.718 [0.685, 0.748]
- neutral  0.678 [0.645, 0.710]
- negative 0.696 [0.663, 0.727]

deltas (paired bootstrap 90% CI, margin ±0.05):
- neg−none −0.022 [−0.043, 0.000] inside
- neu−none −0.039 [−0.061, −0.019] not inside
- neg−neu  +0.018 [0.003, 0.034] inside

FC mass 0.90–0.96. Split 1e8ea1c22144dd9d. Sourced ~/.battery_env. GPU lock released.
