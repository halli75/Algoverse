# Pipeline unification decision

## 1. Verdict

Arnav and Charlotte should share one implementation of the causal affect/refusal method, not average their existing results or collapse their scientific programs. The locked default is a depth-scaled mid-gate intervention, last-prompt-token residual directions, gate-window mean projection, and residual-norm-scaled steering at the fixed reference dose `alpha=0.008`. The joint primary affect arrow is the construction-safer text+image axis orthogonalized to refusal; Charlotte's successful image-only gate remains a required named replication variant. Both confirmatory stacks remain: Gemma-4-E4B NF4 + EMOTIC for Arnav and Gemma-3-12B bf16 + OASIS for Charlotte. The method_compare result rejects the old `coeff=20`/late-layer encoding; it does not reject Arnav's current science, which already uses norm-scaled steering and a fractional gate. Headline behavior is generation-free first-token behavior, with generations used only for coherence and secondary validation. Existing numeric validity gates are immutable, and `artifacts/colab/e2e_mechanism_results_full_v3.json` is read-only forever.

## 2. Locked CORE

There must be one shared library, imported by both pipelines and pinned by commit/hash. Dataset/model adapters may differ; direction algebra, layer selection, hooks, steering, projections, controls, split discipline, metrics, and outcome labels may not.

```python
CORE_METHOD = dict(
    layers="fractional_gate",       # [floor(0.25 * L), floor(0.60 * L))
    token_pool="last_prompt",       # direction construction and input geometry
    proj="window_mean",             # mean of per-layer scalar projections in the gate
    steer="normscaled",             # alpha * ||resid_l|| * unit(direction_l)
    alpha=0.008,                    # fixed shared reference dose
)
```

For `L=34`, `42`, and `48`, the locked windows are respectively `[8,20)`, `[10,25)`, and `[12,28)`. These are formula-derived, not selected after looking at effects. The historical Charlotte `[8,20)` is therefore exactly recovered on the 34-layer model without fitting a gate to data.

The shared run must implement all of the following:

1. **Representations and signs.** Extract `resid_post` at the final prompt token. Build and unit-normalize every direction independently at every layer. `r` is harmful minus harmless. Image affect is negative minus neutral under the exact prompt `Describe what is happening in this image.` Text affect is distress minus neutral. Affect points toward negative/distressed affect, so `-a` is the benign/positive steering sign.
2. **Directions.**
   - `r_l = unit(mean(harmful_train_l) - mean(harmless_train_l))`
   - `a_img,l = unit(mean(negative_image_train_l) - mean(neutral_image_train_l))`
   - `a_text,l = unit(mean(distress_text_train_l) - mean(neutral_text_train_l))`
   - Joint primary: `a_joint,l = unit(a_img,l + a_text,l)`
   - Primary intervention: `a_perp,l = unit((I - r_l r_l^T) a_joint,l)`
3. **Joint projection.** For an input, compute `h[l, last_prompt] · unit(d[l])` and take the arithmetic mean only over the locked gate. “Mean” never means mean-pooling prompt tokens. Multi-token continuation pooling is a separate tone diagnostic and cannot change the core projection.
4. **Steering.** At every gate layer, add `alpha * ||resid_l|| * unit(d_l)` to the full residual stream. The norm is taken from the first item of a versioned, disjoint calibration manifest; its ID, hash, per-layer norms, actual coefficients, hook backend, and layer window are saved. No bare-unit or fixed-coefficient path is permitted in a default.
5. **Reference dose and causal-gate curve.** Every run evaluates the fixed common point `alpha=0.008`. The causal-gate analysis additionally uses Charlotte's already-declared grid `[.004, .006, .008, .010, .012, .016, .020, .030, .040, .050]` and unchanged strict criteria: affect refusal `<=.20`, matched-random refusal `>=.80`, and coherence. Select the smallest passing dose on the calibration split and evaluate it once on held-out evaluation data. Failure to cross the gate is `NO_GATE`, not permission to change the grid or thresholds. Arnav's larger-alpha and gamma curves are stress tests, not calibration.
6. **Matched control.** The primary random control is a seeded isotropic vector projected off `r` per layer, unit-normalized, and given the identical gate, norm scale, sign, and dose. Additional isotropic and covariance-aware/whitened null distributions remain validity panels.
7. **Generation-free headline.** Use the shared refusal token sets, next-token log-sum-exp refusal-minus-compliance score, `score > 0` refusal threshold, and first-token option-logit scores for batteries. Generated responses, VADER/RoBERTa tone, regex, and Grok are secondary checks only. No LLM judge result may replace or be mixed into the headline endpoint.
8. **Leakage wall.** Each corpus gets hashed, disjoint direction-train, dose-calibration, and final-evaluation manifests. Directions use train only; dose/coherence selection uses calibration only; all headline estimates use evaluation only. Reusing direction images or alpha-selection prompts in evaluation is forbidden in the core.
9. **Validity union.** Run both programs' nonredundant controls: manifest and overlap checks, corpus integrity, held-out effects, split-half direction stability, residual-norm/OOD checks, construction-circularity audit, matched `random_perp_r`, isotropic and covariance-aware/whitened nulls, massive-dimension robustness, hook existence/shape plus a zero-ablation firing test, bootstrap uncertainty, and independent direction rebuilds where already preregistered. Existing thresholds—including `r >= 0.7`, token-mass gates, coherence gates, and projected power `>= 0.80`—must remain unchanged. If two existing hard gates apply to the same quantity, use the stricter one; never weaken either from observed results.
10. **Outcome taxonomy.** Emit distinct statuses for `PASS`, `NO_GATE`, `WEAK_REFUSER`, `INVALID_AXIS`, `OOD_INPUT`, `INSUFFICIENT_POWER`, and `PIPELINE_ERROR`. A failed validity gate is not a scientific null.
11. **Artifact immutability.** Unified runs write new, versioned files such as `artifacts/unified/<stack>/<run_id>/core_results_v1.json` with create-only semantics. They may read but must never modify, truncate, rename, or reuse `artifacts/colab/e2e_mechanism_results_full_v3.json`.

## 3. Decision table

| ID | Issue | Locked choice | Reason | Kept from Arnav | Kept from Charlotte | Named variant if any |
|---|---|---|---|---|---|---|
| D01 | METHOD cell | `layers="fractional_gate"`, `proj="window_mean"`, `steer="normscaled"`, `alpha=.008` | It preserves the current shared steering formula and uses the configuration family that moved tone. The old comparison tested obsolete Arnav code, not Arnav's current mechanism. | Current fractional window and norm-scaled hooks | Mid-gate placement, mean projection, and `.008` reference | `charlotte_fixed_8_20_localization`; `arnav_late_layer_stress` is diagnostic only |
| D02 | Layer scope | Steer only `[floor(.25L), floor(.60L))` in the core | It is depth-portable, preregistered independently of observed effects, and exactly equals `[8,20)` at 34 layers. All-layer dose is not commensurate with window dose. | Gemma-4 `[10,25)` mechanism | Historical `[8,20)` gate and causal localization idea | `charlotte_all_layer_steer`; `charlotte_depth_thirds_localization` |
| D03 | Token and layer pooling | Last prompt token at each layer, then gate-window mean of scalar projections | Direction extraction already matches. Window averaging aligns the measured estimand with the intervened circuit and avoids all-layer dilution. | Last-token extraction and mechanism window mean | Mean aggregation rather than a single late-layer score | `charlotte_all_layer_projection`; `charlotte_generated_token_mean_tone` |
| D04 | Refusal direction `r` | Per-layer unit harmful-minus-harmless difference of means | This is already an exact algebraic match and should not be reopened. | AdvBench/local-benign stack input | AdvBench/Alpaca stack input | `arnav_local_benign_pole` and `charlotte_alpaca_benign_pole` remain corpus-stack factors |
| D05 | Image contrast | Negative minus neutral is the shared core contrast | It matches both refusal-gate implementations and isolates departure from neutral without doubling valence span. | EMOTIC negative-neutral | OASIS gate notebook negative-neutral | `charlotte_low_high_valence` for lighting, reachability, and soft behavior |
| D06 | Primary affect arrow | `a_perp = orth_r(unit(a_text + a_img))` is joint primary | It reduces image-construction circularity and directly tests a cross-modal construct. An image-built axis cannot headline an image-vs-text comparison. | Combined text+image mechanism arrow and circularity audit | Image component, cross-modal induction tests, and gate intervention | `image_only_a_perp` is a required Charlotte replication and Arnav publish-reproduction variant |
| D07 | Orthogonalization | Per-layer projection off `r`; use QR/joint projection for more than one nuisance direction | Sequential subtraction against nonorthogonal `r` and `j` can reintroduce removed components. | `a_perp` and multi-axis mechanism goals | Same single-axis Gram-Schmidt and live `r` mediation | `arnav_sequential_orth_legacy` for artifact reproduction only |
| D08 | Steering scale | Add `alpha * ||resid_l|| * unit(d_l)`; save actual coefficients | This is the current exact match and makes alpha dimensionless across layers. | Current publish/mechanism implementation | Successful norm-scaled gate/tone implementation | `fixed_coeff_reproduction` may reproduce old dry runs but can never be a default |
| D09 | Norm probe | First item in a hashed, disjoint calibration manifest, identically processed in both stacks | A recorded fixed probe prevents prompt drift and evaluation leakage while preserving the current formula. | Recorded per-layer norm path | Explicit norm-scaled calibration | `task_specific_norm_probe` for Charlotte battery; `single_train_prompt_norm_legacy` for old Arnav artifact reproduction |
| D10 | Dose selection and coherence | Fixed `.008` common point plus frozen Charlotte strict grid selected on calibration only | The fixed point makes methods comparable; disjoint calibration retains Charlotte's coherent causal-gate logic without tuning on final evaluation. | Fixed `.008` scale and stress curves | Smallest strict coherent/random-controlled dose | `arnav_gamma_generic_collapse`; `arnav_large_alpha_reachability`; `charlotte_eval_selected_alpha_legacy` |
| D11 | Primary random control | Seeded `random_perp_r`, matched in layer, norm, sign, and dose | It controls accidental direct refusal movement and is the closest geometric match to `a_perp`. | Seeded random/null infrastructure | Explicit random projection off `r` | `arnav_isotropic_null`; `arnav_covariance_aware_null`; `charlotte_single_random_legacy` |
| D12 | Behavioral endpoint | First-token refusal score/rate and option logits are headline | They are deterministic, shared, generation-free, and avoid judge drift or mixed fallback sources. | Existing FT scores and completion-based secondary audit | Generation-free refusal and battery metrics | `arnav_grok_completion_secondary`; `arnav_regex_fallback_audit`; `generation_examples_coherence_only` |
| D13 | Image and prompt splits | Hashed train/calibration/evaluation manifests for both corpora | Charlotte's pool reuse makes axis-aligned image estimates partly in-sample; method unification requires the same leakage wall. | Hashed held-out EMOTIC discipline | OASIS acquisition/integrity and split-half stability | `charlotte_reused_pool_legacy` for exact old-result reproduction |
| D14 | Construct validity | Union of held-out/OOD/null/circularity/massive-dimension checks; no threshold retuning | These controls catch different failures and are additive, not substitutes. | OOD norm gate, covariance-aware null floor, construction audit | Data-starvation gate, split-half stability, massive-dimension check | Stack-specific validation panels retain their names and frozen thresholds |
| D15 | Model and image corpus | Keep two confirmatory stacks; do not pool raw effect sizes | Model generation, quantization, corpus semantics, and sample design are scientific factors, not method settings. | Gemma-4-E4B NF4 + EMOTIC | Gemma-3-12B bf16 + OASIS | `arnav_confirmatory_stack`; `charlotte_confirmatory_stack`; Charlotte's wider cross-model roster is secondary |
| D16 | Hook backend | TransformerLens `resid_post` is the reference backend; HF block hooks require backend-labeled replication | HF decoder outputs are only approximately equivalent to TL residual hooks. A zero-ablation test is mandatory for both. | Hook discovery and shape checks | HF fallback and zero-ablation sanity | `hf_block_output_backend`; no cross-backend pooling |
| D17 | Refusal-axis validation | Compare harmless baseline with `+0.25r` under the core gate and enforce the stricter existing delta requirement | A post-steer rate without a baseline is uninformative. Weak `r` must invalidate interpretation rather than trigger retuning. | Baseline-to-steered causal validation and fallback taxonomy | Same `+0.25r` intervention | `charlotte_postrate_only_legacy`; mechanism's softer warning path is removed from defaults |
| D18 | Layer localization | Core gate is fixed; localization runs early/mid/late, fixed `[8,20)`, all-layer, and observational curves as labeled modules | Causal window restriction and observational layer curves answer different questions. | Full observational context curves | Interventional window localization | `arnav_observational_layer_curve`; `charlotte_depth_thirds_localization`; `charlotte_fixed_8_20_localization` |
| D19 | Causal mediation | Keep Charlotte `r`-restore and Arnav clean-displacement/`j` interventions as separate tests | Restoring refusal projection tests mediation; injecting an image displacement tests sufficiency. Neither substitutes for the other. | M1 clean/raw/random restore, independent `j`, C2/C3 | Live `r` ablation and clean-`r` projection restoration | `arnav_displacement_sufficiency`; `charlotte_r_restore_mediation` |
| D20 | Context reachability | Run DESCRIBE, task/opinion, harmful, borderline, and caption-framed contexts with the same core scorer | The strongest joint result is context-dependent reachability, while captions test whether it is vision-specific. | M1-M5 contexts, borderline bank, caption gap | Describe/task/harmful matrix and white-box ceiling | `arnav_suppression_ratio`; `charlotte_natural_to_whitebox_ratio` must remain separately named |
| D21 | Generated tone experiment | Use the locked gate/norm-scaled `.008` steer; VADER and RoBERTa are secondary tone endpoints | These endpoints established that the viable steer changes tone, but they do not validate refusal or determine the projection convention. | Shared image-effect sanity and current norm-scaled method | Successful gate-steered tone effect and continuation-mean diagnostic | `shared_generation_tone`; old “Arnav” coeff-20 result is labeled `obsolete_dry_run` |
| D22 | Statistical discipline | Preserve each frozen sample-size, mass, CI, power, and seed gate; run independent direction rebuilds rather than relabeling mapping seeds | Mapping/bootstrap uncertainty does not include direction-estimation uncertainty. Failed power is not a null result. | Held-out hashes, bootstraps, whitened controls, power gates | Split-half stability, bootstraps, cross-model status | Corpus-specific `N` remains in the two stack configs; it is not silently harmonized after effects |
| D23 | Output and provenance | Create-only, versioned unified artifacts containing config/data/code hashes and full status taxonomy | This prevents accidental overwrite and makes historical and unified results distinguishable. | Frozen refusal-v3 provenance discipline | Checkpoint/result tables and model-status rows | `legacy_artifact_reader` is read-only |

## 4. What code to change first

1. **Create the single source of truth:** `scripts/affect_core.py`.
   - Add `CoreMethodConfig`, `fractional_gate_layers`, `extract_last_prompt_residuals`, `build_difference_direction`, `orthogonalize_span` (QR, not sequential subtraction), `window_mean_projection`, `residual_norms`, `make_normscaled_hooks`, `make_random_perp`, `first_token_refusal_score`, `calibrate_gate_on_split`, `validate_hook_path`, and create-only artifact writing.
   - Put the exact refusal/compliance token lists, DESCRIBE prompt, status taxonomy, frozen calibration grid, and numeric gates in versioned config. Callers must not redefine them.
   - Add `tests/test_affect_core.py` first for windows (`34 -> [8,20)`, `42 -> [10,25)`, `48 -> [12,28)`), unit scaling, span orthogonality, random-off-`r`, projection scope, split overlap rejection, and artifact overwrite rejection.

2. **Move Arnav's current mechanism onto the core:** `scripts/e2e_mechanism_context_suppress.py`.
   - In `main`, replace nested `resid_layers`, `add_hook`, `steer`, `mean_proj`, refusal-token construction, and sequential `orth_to` with shared functions.
   - Keep the current `a_text + a_img` construction as the core primary.
   - Replace alpha selection from `[0.1, 0.25, 0.4, 0.6, 0.9]` in the default path with fixed `.008` plus the shared calibration-split curve. Retain the old list only under `arnav_large_alpha_reachability`.
   - Keep M1-M5, `j`, caption, null, and restore phases as modules. Correct multi-direction cleaning to project off the joint span of `{r,j}`.
   - Add an explicit guard that refuses any output path resolving to `artifacts/colab/e2e_mechanism_results_full_v3.json`.

3. **Move Charlotte's gate notebook onto the same core:** `vendor/charlotte-affect-control-axis/notebooks/affect_gate_replication.ipynb`.
   - In `run_model`, replace local `RL`, `add`, `st`, `rsc`, `rproj`, and `aproj` with the pinned core.
   - Change default all-layer steering to the fractional gate and default all-layer projection to gate-window mean.
   - Add hashed OASIS train/calibration/evaluation manifests. Move alpha selection off `harmful_eval[:30]` and onto calibration; final `affect_gate_refuse` is evaluation-only.
   - Construct both `a_joint_perp` (core primary) and `a_img_perp` (`image_only_a_perp` replication). Preserve all-layer, thirds, detector, clamp, mediation, and no-massive-dimension outputs under explicit module names.
   - The notebook wrapper should download/import a commit-pinned `affect_core.py` and record its SHA, not copy editable helper cells.

4. **Then update the companion/common analyses.**
   - `scripts/e2e_publish_pipeline.py`: replace `resid_layers`, `add_hook`, `steer`, `mean_proj`, direction construction, and the data-dependent gamma hook loop with core calls. Preserve image-only geometry and gamma only as named reproduction/stress modules.
   - `vendor/charlotte-affect-control-axis/notebooks/emotional_image_effects.ipynb`: route `RL`, `add`, `st`, `aproj`, `rsc`, and reachability through the core while retaining low-high, lighting, soft-task, and agentic modules.
   - `vendor/charlotte-affect-control-axis/notebooks/behavior_battery.ipynb`: use core hooks/projections and retain its option-logit endpoint as a Charlotte module.
   - `artifacts/charlotte/colab_live_dump.ipynb` / the Drive `method_compare.ipynb`: set the displayed default to the locked `CORE_METHOD`; preserve both historical rows only in a section titled `obsolete_dry_run_reproduction`.

5. **Clean obsolete defaults last:** `scripts/e2e_colab_pipeline.py`.
   - It is a historical dry run. Remove it from every launcher/default import path and require `--variant legacy_colab_dry_run` to execute it.
   - Do not rewrite historical result JSONs or notebooks merely to make old outputs look unified.

Commit and pin the shared core before either person's confirmatory rerun. A copied implementation in two notebooks is not unification.

## 5. What NOT to merge

- **Arnav-only:** graded sycophancy (`S_label`, native sequence score, Likert diagnostic, V/A and `s` directions, Perez/custom claims, mass and power gates); M1-M5; independent jailbreak direction `j`; clean displacement sufficiency; caption/de-affectization gap; extreme-gamma generic-collapse; contagion; Grok completion audit; `h` kill-switch history and its validity audit.
- **Charlotte-only:** detector and one-sided clamp; lighting interventions; six-probe behavior battery; cross-model/fusion roster; agentic helplessness and survival-threat sign flip; soft-task image behavior; user-empathy legacy branch; mechanism-guided affective rewriter.
- **Do not merge endpoints:** sycophancy, refusal, sentiment tone, option logits, and agentic choice remain separately named outcomes.
- **Do not merge ratios:** Arnav's context-suppression and `R_jail/R_affect` ratios are not Charlotte's natural-image-to-white-box reachability ratio.
- **Do not merge axes:** joint text+image `a`, image-only `a`, low-high valence, emotion-specific text vectors, V/A, `r`, `j`, `h`, and sycophancy `s` retain distinct names and provenance.
- **Do not merge evidence status:** completed result, notebook-only analysis, failed smoke, and planned module must remain separate.
- **Do not merge model/corpus effects:** Gemma-4 NF4/EMOTIC and Gemma-3-12B bf16/OASIS are dual confirmatory stacks, not pooled observations.

Modules may import the shared core primitives, but their scientific estimands and frozen gates remain owner-specific.

## 6. Obsolete Arnav encodings to delete from defaults

“Delete from defaults” means remove from launchers, default configs, and unlabeled code paths; retain only an explicit named reproduction/stress variant where scientifically useful.

1. `coeff=20.0` fixed-coefficient steering.
2. Bare `resid + coeff * unit(d)` with a coefficient not computed as `alpha * ||resid_l||`.
3. Late-only (`~70%-100%`) layers as the default causal intervention.
4. `proj="last"` as the old generation-tone METHOD default. Final-prompt-token extraction remains required; the obsolete part is using one final generated-token score as the shared projection method.
5. All-layer steering as the default in `e2e_colab_pipeline.py` or Charlotte's gate notebook.
6. All-layer projection as the default in `e2e_publish_pipeline.py` or Charlotte's gate notebook.
7. Fixed `GATE_LO=8, GATE_HI=20` placeholders in default configuration. Keep exact `[8,20)` only as `charlotte_fixed_8_20_localization`; derive the core window from model depth.
8. The data-dependent gamma coefficient `gamma * .008 * ||resid_l|| * min(abs(d_img)/50, 2)` as a causal/default dose. Keep it only as `arnav_gamma_generic_collapse`.
9. The large direct-alpha list `[.1, .25, .4, .6, .9]` as the default gate search. Keep it only as `arnav_large_alpha_reachability`.
10. Unprojected isotropic random as the sole matched control. It remains an additional null family; `random_perp_r` is primary.
11. Image-only `a_perp` as the unlabeled joint primary. Keep it as `image_only_a_perp`.
12. Sequential `orth_to(delta, r, j)` while claiming joint orthogonality. Use projection off the QR span; keep sequential behavior only for exact frozen-artifact reproduction.
13. Silent regex substitution for a missing Grok judge and any generated-answer judge as headline refusal.
14. Weak-`r` or OOD warnings that continue into a causal headline. They must emit a non-PASS status without changing thresholds.
15. Any default output path that can overwrite `artifacts/colab/e2e_mechanism_results_full_v3.json`.

The old method_compare “Arnav” row must be labeled `obsolete_dry_run`, never “Arnav current.” Arnav's current norm-scaled fractional-gate mechanism remains scientifically active.
