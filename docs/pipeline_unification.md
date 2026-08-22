# Pipeline unification (what landed)

Arnav and Charlotte now share one implementation of the causal affect/refusal
**method**. Their scientific programs stay separate. Binding decisions and
per-difference reasons are in [`docs/pipeline_unification_advisor.md`](pipeline_unification_advisor.md)
(GPT-5.6 advisor lock). This file records what the code does.

## Shared core

`scripts/affect_core.py` is the single source of truth. Tests:
`python3 -m unittest tests.test_affect_core`.

Locked default:

```python
CORE_METHOD = dict(
    layers="fractional_gate",   # [floor(0.25 L), floor(0.60 L))
    token_pool="last_prompt",
    proj="window_mean",
    steer="normscaled",         # alpha * ||resid_l|| * unit(d_l)
    alpha=0.008,
)
```

Windows: L=34 → `[8,20)`; L=42 → `[10,25)`; L=48 → `[12,28)`.

Joint primary axis: `a_perp = orth_span(unit(a_text + a_img), r)`.
Image-only `a_perp` is the required named variant `image_only_a_perp`.

## Who imports it

| Stack | File | Primary `a` | Model / corpus |
|---|---|---|---|
| Arnav confirmatory | `scripts/e2e_mechanism_context_suppress.py` | joint text+image | Gemma-4-E4B NF4 + EMOTIC |
| Arnav publish geometry | `scripts/e2e_publish_pipeline.py` | `image_only_a_perp` | Gemma-4-E4B NF4 + EMOTIC |
| Charlotte notebooks | `scripts/charlotte_notebook_core.py` | joint + image-only named | Gemma-3-12B bf16 + OASIS |

`scripts/e2e_colab_pipeline.py` is **not** a default launcher. It requires
`--variant legacy_colab_dry_run`.

`artifacts/colab/e2e_mechanism_results_full_v3.json` is read-only forever.

## Resolution reasons (short)

Full table: advisor D01–D23. Summary of the conflicts that actually change code:

| Difference | Locked choice | Why |
|---|---|---|
| METHOD cell | fractional gate + window mean + normscaled `.008` | That family moved tone; coeff=20/late was an obsolete dry run, not Arnav's current mechanism. |
| Layer scope | `[floor(.25L), floor(.60L))` | Depth-portable, preregistered, equals Charlotte `[8,20)` at 34 layers. |
| Projection | gate-window mean of last-token scalars | Matches the intervened circuit; all-layer mean dilutes the gate. |
| Primary `a` | `orth_r(unit(a_text+a_img))` | Cross-modal construct; image-only cannot headline an image-vs-text claim. Image-only kept as named replication. |
| Orthogonalization | QR span, not sequential GS | Sequential subtraction against non-orthogonal `{r,j}` can put `r` back. |
| Steering | `alpha * \|\|resid\|\| * unit(d)` | Already the exact match; makes alpha dimensionless across layers. |
| Dose | fixed `.008` plus Charlotte's frozen grid on **calibration** | Comparable common point without tuning on eval. Large alphas / gamma stay named stress tests. |
| Random | seeded `random_perp_r` | Closest geometric match to `a_perp`; isotropic remains an extra null. |
| Headline | first-token refusal / option logits | Shared, generation-free; Grok/VADER/RoBERTa stay secondary. |
| Splits | hashed train / calib / eval | Charlotte pool reuse made some image estimates in-sample. |
| Models / corpora | dual confirmatory stacks | Generation, quantization, and image semantics are science factors, not method knobs. Do not pool effect sizes. |
| Weak `r` | `INVALID_AXIS`, delta `0.15` | Stricter existing gate; do not retune or headline through a warning. |

## Explicitly not merged

Arnav-only: graded sycophancy; M1–M5; independent `j`; caption gap; gamma collapse; Grok as headline.
Charlotte-only: detector/clamp; lighting; six-probe battery; agentic/protective modules; cross-model roster.

Those modules may **import** the core. They must not overwrite it.
