# exp06 STATUS

- phase: FULL_COMPLETE
- ts: 2026-08-23 05:11 UTC
- gpu: 2
- pid: 2054402 finished (not alive)
- **n_trials: 5425**
- **complete: true**
- gate: 17/17
- parse 1.0, mean FC mass 0.989
- split `1e8ea1c22144dd9d`
- model google/gemma-4-E4B-it nf4 bf16

## Kirby k (primary)

| cond | k | p_now | consistency |
|---|---|---|---|
| fear | 0.00238 | 0.46 | 0.56 |
| anger | 0.00238 | 0.44 | 0.57 |
| sad | 193 | 0.52 | 0.51 |
| happy | 193 | 0.54 | 0.54 |
| peace | 0.00238 | 0.48 | 0.53 |
| neutral | 0.00041 | 0.50 | 0.52 |
| no-image | 0.00041 | 0.36 | 0.66 |

NLS IEs stay near $1000; NLS k ~4e-4 except happy 0.023.

mechanism_answer written. Smoke kept as results_smoke.json.
