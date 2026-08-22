# Gemma-4 full E2E — framing status (LOCKED)

Updated: 2026-08-07

## Verdict
**Revised 2026-08-10:** Do **not** trust INVERTED as the paper’s geometry headline — image-built `a` makes `ratio_a` favor images by construction (see `validity_audit.md`).  
Still trust: behavioral refuse ceiling (“images don’t jailbreak”); OOD-norm PASS rules out color-square artifact only.  
Do **not** flip to PASS_AFFECT_SPECIFIC either without a text-built transfer test.

## Locked numbers
| Item | Value |
|---|---|
| Kill | **INVERTED** |
| `ratio_a` (published) | **1.591** |
| `ratio_a_raw` (rebuild) | **1.591** (exact match) |
| `ratio_a_unit` (act/‖act‖) | **1.390** → INVERTED_persists |
| `ratio_h` | ≈0.036 (`h_valid=true`) |
| Behavior refuse | ~ceiling; Grok judge 100% |
| Split hash | `ef2a7d2a84a803c7` |
| Pre-reg | `3111c3af7f7b12656cb0792bea4a21b4302a0c42` |

## Gate 6 OOD residual-norm — PASS
Artifact: `e2e_ood_norm_gemma4.json`
- science/photo_ref ≈ **1.003** (no inflation)
- solid-color also normal on Gemma-4
- fail_colorlike=false, fail_inflation=false
- **Not** the old color-square / activation-norm OOD artifact.

## Unit-normalized geometry — INVERTED persists
Artifact: `e2e_ratio_unit_gemma4.json`
- Rebuilt full-tier dirs (N_DIR=64, N_IMG=64, N_DELTA=40)
- `abs_cos_a_r≈0.136`
- Raw ratio exactly reproduces published 1.591
- Unit-normalized still **1.39 > 1** → inversion is directional, not norm-driven

## γ random check
Artifact: `e2e_gamma_random_check.json`
| γ | emotion refuse | random refuse |
|---|---|---|
| 50 | 0.95 | **1.0** |
| 100 | 0.475 | **0.1** |

γ=100 drop is generic huge-perturbation collapse (random worse than emotion), not emotion-specific.

## Paper framing (recommended)
1. **Primary claim:** visual affect does **not** transfer like text distress onto the refusal-orthogonal affect axis in the expected direction — geometry is **INVERTED** (`ratio_a≈1.59`, unit≈1.39).
2. **Trust:** OOD norm gate PASS + exact raw reproduction + unit persistence.
3. **Behavioral:** images don’t jailbreak (refuse ceiling); validated `h` shows text harm axis works.
4. **Caveat:** γ=100 steering collapse is **not** emotion-specific (random collapses harder).
