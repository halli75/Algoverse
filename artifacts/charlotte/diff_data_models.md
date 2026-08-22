# Arnav vs Charlotte pipelines: data, models, dtype, and evaluation sets

## Scope and reading rule

This audit compares:

- **Arnav publish/refusal pipeline:** `docs/colab_publish_experiment_plan.md`, `scripts/e2e_publish_pipeline.py`, and `artifacts/colab/summary.md`.
- **Arnav context-suppression pipeline:** `docs/context_suppression_mechanism_plan.md`, `scripts/e2e_mechanism_context_suppress.py`, and the frozen result `artifacts/colab/e2e_mechanism_results_full_v3.json` (read only).
- **Arnav sycophancy pipeline:** `docs/sycophancy_affect_plan.md`, `scripts/e2e_sycophancy_affect.py`, and the frozen banks under `data/`.
- **Charlotte confirmed pipeline:** `vendor/charlotte-affect-control-axis/` and the extracted notebook text under `artifacts/charlotte/extracted_nb/`.

“Conflict” below means the difference changes the estimand, population, representation, or measurement enough that results should not be pooled or treated as a direct replication. “Compatible” means the designs can coexist as complementary evidence; it does not mean their numerical effect sizes are directly exchangeable. Some entries are marked “compatible only after stratification” where a meta-analysis could preserve the difference as a factor.

## Executive comparison

| Dimension | Arnav | Charlotte |
|---|---|---|
| Flagship | `google/gemma-4-E4B-it` | `google/gemma-3-12b-it` |
| Gemma-3-4B role | Publish fallback / optional smoke | Legacy/provisional result and one roster member |
| Precision | NF4 4-bit weights + bf16 compute | Full bf16 |
| Confirmed image corpus | EMOTIC | OASIS |
| Image labels | Per-person categorical multi-label emotion + VAD | Normative scalar valence/arousal |
| Main image split | Hashed EMOTIC train/eval; mechanism also carves calibration | No held-out OASIS science split; split-half is a stability check |
| Refusal text | AdvBench + local benign prompts | AdvBench + Alpaca |
| Affect text | 64 distress + 64 neutral; sycophancy also uses a 62-item GoEmotions-style bank | Small Claude-generated emotion/valence stories and probes |
| Main refusal sizes | `N_DIR=64`, harmful eval 100, image direction 64/class | `N_DIR=128`, eval 60 or 100, image direction 60 or 200/class |
| Evaluation | Generated responses + Grok for behavioral headlines; first-token scores also used | First-token option/refusal logits; generation-free headline; no LLM judge |
| Unique scope | Graded sycophancy with public Perez sets and custom claims | Six-probe behavior battery, lighting, agentic/survival probes |

## Enumerated differences

### D01 — Flagship model generation and scale

- **Arnav:** The flagship and completed full mechanism run use `google/gemma-4-E4B-it`, a 42-layer, `d_model=2560` model. The sycophancy contract is Gemma-4 only.
- **Charlotte:** The confirmed affect-gate and behavior results center `google/gemma-3-12b-it`.
- **File cites:** `docs/colab_publish_experiment_plan.md:3-6,31-32`; `artifacts/colab/e2e_mechanism_results_full_v3.json:407-420`; `docs/sycophancy_affect_plan.md:26-33`; `vendor/charlotte-affect-control-axis/README.md:72-84`; `vendor/charlotte-affect-control-axis/docs/AFFECT_REFUSAL_RESULTS.md:8-16`.
- **Scientific stake:** Model generation and scale jointly alter architecture, residual geometry, refusal calibration, and the causal gate. Charlotte explicitly finds the gate in Gemma-3-12B but not Gemma-3-4B, so transferring it to Gemma-4 is not licensed.
- **Classification:** **Conflict** for direct replication; **compatible** as cross-generation evidence.

### D02 — The role of `google/gemma-3-4b-it`

- **Arnav:** Gemma-3-4B is a fallback only if Gemma-4 load/hooks/emotion/steering gates fail or Step 0 exceeds two hours; the completed publish run did not fall back. The later sycophancy protocol forbids fallback entirely.
- **Charlotte:** Gemma-3-4B is both a roster member and the source of older EMOTIC-era/legacy results; Charlotte marks those results provisional and reports no confirmed gate on the valid OASIS axis.
- **File cites:** `docs/colab_publish_experiment_plan.md:5,31-33,51-60`; `artifacts/colab/summary.md:83-94`; `docs/sycophancy_affect_plan.md:28-33`; `artifacts/charlotte/extracted_nb/affect_gate_replication.py.txt:42-49`; `vendor/charlotte-affect-control-axis/docs/AFFECT_REFUSAL_RESULTS.md:1-14,33-38`.
- **Scientific stake:** “Gemma-3-4B” does not denote the same evidentiary role in the two projects: it is an unexercised contingency for Arnav but an observed, confounded scale point for Charlotte.
- **Classification:** **Conflict** if 4B is described as a shared replication; otherwise **compatible** provenance.

### D03 — Single-model causal claim versus cross-model roster

- **Arnav:** The publish and mechanism claims are deliberately single-model; the sycophancy run is hard-pinned to Gemma-4. Gemma-3-4B is only a fallback/smoke option outside sycophancy.
- **Charlotte:** The replication notebook defines a broad roster across Gemma-3, LLaVA-OneVision, Qwen, InternVL, Phi, Idefics, and MiniCPM, using TransformerLens and Hugging Face backends. The committed combined table contains successful, weak-refuser, no-gate, and error rows.
- **File cites:** `docs/colab_publish_experiment_plan.md:69-73`; `docs/context_suppression_mechanism_plan.md:433-459`; `docs/sycophancy_affect_plan.md:28-34`; `artifacts/charlotte/extracted_nb/affect_gate_replication.py.txt:42-49,91-112,535-568,743-808`; `vendor/charlotte-affect-control-axis/results/replication_combined.csv:1-11`.
- **Scientific stake:** Charlotte can test family/fusion dependence; Arnav has stronger within-model controls but cannot estimate model heterogeneity.
- **Classification:** **Compatible** and complementary, but do not call Arnav cross-model.

### D04 — Numeric precision and quantization

- **Arnav:** Actual Gemma-4 weights are NF4 4-bit with bf16 compute and double quantization. The publish loader may attempt full bf16 on larger-memory hardware, but the completed T4/A100 artifacts record NF4.
- **Charlotte:** The core notebooks load model weights directly in bf16; no 4-bit quantization is used for the confirmed 12B results.
- **File cites:** `scripts/e2e_publish_pipeline.py:439-488,491-524`; `scripts/e2e_mechanism_context_suppress.py:464-505`; `artifacts/colab/summary.md:83-93`; `vendor/charlotte-affect-control-axis/README.md:36-40,82-84`; `artifacts/charlotte/extracted_nb/emotional_image_effects.py.txt:132-136`; `artifacts/charlotte/extracted_nb/affect_gate_replication.py.txt:299-310`.
- **Scientific stake:** Quantization can rotate or attenuate residual directions and alter logit margins. Same-dtype direction construction/intervention protects Arnav internally, but NF4 versus bf16 remains a between-pipeline confound.
- **Classification:** **Conflict** for numerical effect-size comparison; **compatible only after a dtype replication**.

### D05 — Confirmed image corpus

- **Arnav:** Uses real EMOTIC pixels and annotations; the full runs report 23,185 JPGs and reject incomplete or solid-color substitutes.
- **Charlotte:** Uses OASIS as the confirmed image source. EMOTIC is optional/legacy because Charlotte’s local EMOTIC download had only about 184 images and produced a poisoned one-image negative set.
- **File cites:** `docs/colab_publish_experiment_plan.md:19-20,83-107`; `scripts/e2e_mechanism_context_suppress.py:249-260`; `artifacts/colab/summary.md:95-118`; `vendor/charlotte-affect-control-axis/README.md:65-70`; `vendor/charlotte-affect-control-axis/docs/PROJECT_OVERVIEW.md:48-57`; `vendor/charlotte-affect-control-axis/docs/AFFECT_REFUSAL_RESULTS.md:8-14`.
- **Scientific stake:** EMOTIC is people-centered and labels depicted emotion per person; OASIS is a normative affective-photo set. Corpus differences can change scene content, social salience, and model visual competence.
- **Classification:** **Conflict** for a corpus-controlled replication; **compatible** as cross-corpus robustness.

### D06 — Image data-integrity policy

- **Arnav:** Hard-fails below 20,000 EMOTIC JPGs, checks for missing/solid images, records pool counts, and runs a photo-versus-solid residual-norm OOD check.
- **Charlotte:** The current OASIS builder hard-fails below 100 negative images and self-heals a starved image directory; this policy was introduced after the incomplete-EMOTIC failure. It does not use Arnav’s 20,000-file EMOTIC gate.
- **File cites:** `scripts/e2e_publish_pipeline.py:299-320,735-826`; `scripts/e2e_mechanism_context_suppress.py:249-260,830-849`; `artifacts/charlotte/extracted_nb/affect_gate_replication.py.txt:34-40,115-125,248-290`.
- **Scientific stake:** Both address the same validity risk, but against different corpus failure modes. Passing one gate does not imply passing the other.
- **Classification:** **Compatible** validation philosophy; corpus-specific thresholds must stay separate.

### D07 — Affect contrast encoded by the image direction

- **Arnav:** Publish builds image affect as EMOTIC **negative minus neutral**. The context-suppression run combines a negative-minus-neutral image vector with a distress-minus-neutral text vector.
- **Charlotte:** The replication/refusal notebook builds OASIS **negative minus neutral**, while the emotional-image notebook defines a broader low-valence-minus-high-valence axis. Charlotte therefore has two image contrasts across notebooks.
- **File cites:** `docs/colab_publish_experiment_plan.md:113-120`; `scripts/e2e_mechanism_context_suppress.py:697-708`; `artifacts/charlotte/extracted_nb/affect_gate_replication.py.txt:369-383`; `artifacts/charlotte/extracted_nb/emotional_image_effects.py.txt:181-190`.
- **Scientific stake:** Negative-vs-neutral isolates departure from neutrality; low-vs-high spans both ends of valence and generally yields a larger, different direction. The directions should not be treated as identical.
- **Classification:** **Conflict** unless the contrast is explicitly stratified and rebuilt.

### D08 — EMOTIC thresholds versus OASIS valence “tertiles”

- **Arnav:** Buckets EMOTIC using mean VAD valence where available: `<4` negative, `>6` positive, otherwise neutral; categorical labels backfill missing VAD.
- **Charlotte:** OASIS uses empirical valence quantiles. The current replication sets `OASIS_Q=0.30`, placing the bottom 30% in negative, top 30% in positive, and middle 40% in neutral; the public prep document uses 0.33/0.67 tertiles.
- **File cites:** `scripts/e2e_publish_pipeline.py:230-285`; `scripts/e2e_mechanism_context_suppress.py:270-307`; `artifacts/charlotte/extracted_nb/affect_gate_replication.py.txt:34-39,218-245`; `vendor/charlotte-affect-control-axis/docs/AFFECT_REFUSAL_DATASETS.md:71-90`.
- **Scientific stake:** Arnav uses absolute annotation-scale thresholds; Charlotte uses corpus-relative ranks. “Negative” and “neutral” therefore have different prevalence and severity.
- **Classification:** **Conflict** for class-conditioned effects; **compatible** after continuous-valence harmonization.

### D09 — Multi-label emotion handling

- **Arnav:** EMOTIC can attach several labels and several annotated people to one frame. Arnav aggregates to one image ID, averages available person-level valence, assigns exactly one bucket, diagnoses multi-label/Peace∩Happiness overlap, and aborts if assigned negative and positive IDs overlap.
- **Charlotte:** Confirmed OASIS classes derive from one normative scalar valence per image; there is no multi-label categorical collision to resolve. Charlotte’s optional EMOTIC exporter instead uses distress/sympathy and anger exclusion rules.
- **File cites:** `docs/colab_publish_experiment_plan.md:92-103`; `scripts/e2e_publish_pipeline.py:230-345`; `artifacts/colab/summary.md:102-118`; `artifacts/charlotte/extracted_nb/affect_gate_replication.py.txt:163-190,218-245`.
- **Scientific stake:** Arnav’s labels mix depicted categories and VAD across people; Charlotte’s OASIS labels are aggregate viewer ratings. Label noise and construct validity differ.
- **Classification:** **Conflict** at the label level; **compatible** only through a shared continuous-valence analysis.

### D10 — `N_IMG` and per-class image sample sizes

- **Arnav:** Publish full tier uses `N_IMG=64` per negative/neutral direction pool; mechanism full evaluates 64 negative and 64 neutral images; sycophancy targets 96 matched negative-neutral pairs.
- **Charlotte:** Emotional-image effects uses `N_IMG=60`; cross-model replication uses `N_IMG=200` per class and a minimum of 100 negatives.
- **File cites:** `scripts/e2e_publish_pipeline.py:68-83,728-733`; `artifacts/colab/e2e_mechanism_results_full_v3.json:6-23,153-169`; `docs/sycophancy_affect_plan.md:105-125`; `artifacts/charlotte/extracted_nb/emotional_image_effects.py.txt:39-68`; `artifacts/charlotte/extracted_nb/affect_gate_replication.py.txt:34-39,270-290`.
- **Scientific stake:** Charlotte’s 200/class direction has lower sampling variance than Arnav’s 64/class direction, while Arnav’s matched 96-pair sycophancy design has stronger paired control for behavior.
- **Classification:** **Compatible only after uncertainty/power adjustment**; raw variances are not comparable.

### D11 — Held-out image train/eval discipline

- **Arnav:** Uses a fixed 60/40 EMOTIC split. Direction construction is train-only and science is eval-only; mechanism further removes 15% of eval IDs for calibration. The sycophancy experiment uses eval images for behavior and train images only for continuity/OOD diagnostics.
- **Charlotte:** The OASIS builder writes one set of up to 200 images/class. The same `img_neg`/`img_neu` arrays build `a` and are later used for image refusal and other image evaluations. Split-half is used to estimate direction stability, not to create a held-out science set.
- **File cites:** `docs/colab_publish_experiment_plan.md:81-100`; `scripts/e2e_publish_pipeline.py:348-390`; `scripts/e2e_mechanism_context_suppress.py:341-396`; `scripts/e2e_sycophancy_affect.py:520-529,615-630`; `artifacts/charlotte/extracted_nb/affect_gate_replication.py.txt:270-290,369-418`; `artifacts/charlotte/extracted_nb/emotional_image_effects.py.txt:181-200,247-283`.
- **Scientific stake:** Charlotte’s image-conditioned projection and refusal measurements are partly in-sample with respect to the affect direction, which can inflate axis-aligned separation. Arnav’s held-out image estimates target generalization.
- **Classification:** **Conflict** and a major reason not to compare projection magnitudes directly.

### D12 — Matched image pairs and repeated remapping

- **Arnav:** Sycophancy matches EMOTIC negative↔neutral images on exact scene folder, person-count bin, luminance, and arousal calipers; it targets 96 pairs and remaps task-to-image assignments with seeds 0/1/2.
- **Charlotte:** OASIS class images are shuffled and truncated by class, but no one-to-one scene/person/luminance/arousal matching is imposed. Emotional-image behavior generally cycles or averages independently selected class images.
- **File cites:** `docs/sycophancy_affect_plan.md:105-127`; `scripts/e2e_sycophancy_affect.py:548-613`; `artifacts/charlotte/extracted_nb/affect_gate_replication.py.txt:227-245`; `artifacts/charlotte/extracted_nb/emotional_image_effects.py.txt:55-68,311-324`.
- **Scientific stake:** Arnav estimates a within-matched-pair affect effect with assignment uncertainty; Charlotte estimates a between-class image-set effect that can retain scene/content imbalance.
- **Classification:** **Conflict** for natural-image causal attribution.

### D13 — Split hashing and provenance

- **Arnav:** Serializes and SHA256-hashes the EMOTIC split, records preregistration/file hashes, and asserts disjointness. Two artifact generations exist: publish summary hash `ef2a7d2a84a803c7` and the later mechanism/sycophancy hash `1e8ea1c22144dd9d`; analyses must name which revision they use.
- **Charlotte:** Uses fixed CSV files, sorted filenames, seeded shuffles, and result checkpoints, but the notebook evidence does not pin a hash of the OASIS image manifest or the train/eval CSV contents.
- **File cites:** `scripts/e2e_publish_pipeline.py:348-380`; `artifacts/colab/summary.md:21-27,120-129`; `artifacts/colab/e2e_mechanism_results_full_v3.json:25-45`; `docs/sycophancy_affect_plan.md:288-299`; `vendor/charlotte-affect-control-axis/docs/AFFECT_REFUSAL_DATASETS.md:50-92`; `artifacts/charlotte/extracted_nb/affect_gate_replication.py.txt:227-245`.
- **Scientific stake:** Arnav can identify exact split revisions and detect accidental drift. Charlotte’s seed alone cannot reconstruct a corpus if directory contents/order change.
- **Classification:** **Conflict** in reproducibility guarantees; scientifically compatible if Charlotte adds manifest hashes.

### D14 — Harmful text corpus

- **Arnav:** Uses AdvBench goals for refusal direction/evaluation and for mechanism calibration. Sycophancy uses separate Perez/Anthropic sets, not AdvBench, for its primary behavior.
- **Charlotte:** Uses AdvBench for refusal direction and evaluation.
- **File cites:** `scripts/e2e_publish_pipeline.py:691-707`; `scripts/e2e_mechanism_context_suppress.py:400-425`; `docs/sycophancy_affect_plan.md:68-104`; `vendor/charlotte-affect-control-axis/README.md:65-70`; `vendor/charlotte-affect-control-axis/docs/AFFECT_REFUSAL_DATASETS.md:24-31`.
- **Scientific stake:** The refusal substudies share the harmful benchmark family, which aids conceptual comparison; Arnav’s sycophancy estimand is a different behavior with different public sources.
- **Classification:** **Compatible** for refusal, **not applicable/directly incompatible** for sycophancy.

### D15 — Harmless text corpus used to build refusal direction `r`

- **Arnav:** Uses a fixed local list of 16 benign prompts, repeated with suffix variants to reach `N_DIR`.
- **Charlotte:** Uses instruction-only Alpaca examples; the prep takes the first 200 eligible items.
- **File cites:** `scripts/e2e_publish_pipeline.py:708-726`; `scripts/e2e_mechanism_context_suppress.py:426-444`; `vendor/charlotte-affect-control-axis/docs/AFFECT_REFUSAL_DATASETS.md:28-30,60-69`; `vendor/charlotte-affect-control-axis/README.md:65-70`.
- **Scientific stake:** Difference-of-means refusal directions depend on both poles. Repeated near-duplicate benign prompts can yield a narrower baseline than diverse Alpaca instructions.
- **Classification:** **Conflict** for direct `r`, `a⊥`, or cosine comparison.

### D16 — Affect text banks

- **Arnav:** Context suppression uses 64 distinct distress and 64 roughly length-matched neutral sentences from `data/mechanism_text_banks.json`. Sycophancy fits V/A from a fixed 62-item, single-label GoEmotions-style bank with train/held-out flags.
- **Charlotte:** Cross-modal emotion vectors and behavior probes use small Claude-generated banks: typically four stories per emotion and five neutral sentences, plus five negative and five positive valence sentences in the battery.
- **File cites:** `data/mechanism_text_banks.json:1-5,71-137`; `data/sycophancy_goemotions_bank.json:1-21`; `docs/sycophancy_affect_plan.md:101-104,188-198`; `artifacts/charlotte/extracted_nb/emotional_image_effects.py.txt:203-244`; `artifacts/charlotte/extracted_nb/behavior_battery.py.txt:115-147`; `vendor/charlotte-affect-control-axis/docs/PROVENANCE.md:55-60`.
- **Scientific stake:** Arnav’s larger bank supports held-out V/A validation and lowers lexical-template variance; Charlotte’s small, hand-authored contrasts may be more prompt-specific.
- **Classification:** **Conflict** for text-axis equality; **compatible** as independent prompt-bank robustness.

### D17 — GoEmotions, Perez sycophancy sets, and custom claims

- **Arnav:** Uses a GoEmotions-style direction-fit bank; downloads PhilPapers, Political Typology, and NLP Survey sycophancy JSONL; and reserves 160 paired custom factual/plan claims strictly for evaluation.
- **Charlotte:** Uses none of those datasets in the implemented affect/refusal or behavior-battery pipelines. Charlotte mentions sycophancy in literature/context, not as the measured battery endpoint.
- **File cites:** `docs/sycophancy_affect_plan.md:68-104`; `scripts/e2e_sycophancy_affect.py:55-80,419-451,994-1052`; `data/sycophancy_custom_claims.json:1-23,143-163`; `data/sycophancy_goemotions_bank.json:1-21`; `artifacts/charlotte/extracted_nb/behavior_battery.py.txt:3-26,160-185`.
- **Scientific stake:** Arnav estimates affect-conditioned agreement/matching; Charlotte estimates other affect-congruent judgments. These are different behavioral constructs and eval populations.
- **Classification:** **Compatible** as non-overlapping behavior coverage; **conflict** if presented as the same eval set.

### D18 — `N_DIR`

- **Arnav:** Publish/context mechanism uses `N_DIR=64`; sycophancy uses 192 direction-train stems.
- **Charlotte:** Both major image/refusal notebooks use `N_DIR=128`.
- **File cites:** `scripts/e2e_publish_pipeline.py:68-83`; `artifacts/colab/e2e_mechanism_results_full_v3.json:6-18,35-45`; `docs/sycophancy_affect_plan.md:78-88`; `artifacts/charlotte/extracted_nb/emotional_image_effects.py.txt:39-40`; `artifacts/charlotte/extracted_nb/affect_gate_replication.py.txt:34-35`.
- **Scientific stake:** Direction estimation variance and corpus diversity differ. Arnav’s sycophancy `N_DIR` is not a refusal-direction sample and should not be compared numerically to Charlotte’s `N_DIR`.
- **Classification:** **Compatible only with endpoint-specific labels and uncertainty**.

### D19 — `N_EVAL` and behavioral sample sizes

- **Arnav:** Publish evaluates 100 harmful prompts; mechanism full uses 100 harmful plus 80 borderline prompts and 64 images for projection deltas. Sycophancy public confirmatory sets are 160 PhilPapers + 136 Political, with 64 NLP and 160 custom secondary items.
- **Charlotte:** Emotional-image effects uses `N_EVAL=60`; cross-model replication uses `N_EVAL=100`. The behavior battery has six probe prompts rather than a large item sample.
- **File cites:** `scripts/e2e_publish_pipeline.py:68-83`; `artifacts/colab/e2e_mechanism_results_full_v3.json:6-23,79-169`; `docs/sycophancy_affect_plan.md:78-94`; `artifacts/charlotte/extracted_nb/emotional_image_effects.py.txt:39-68`; `artifacts/charlotte/extracted_nb/affect_gate_replication.py.txt:34-35`; `artifacts/charlotte/extracted_nb/behavior_battery.py.txt:165-185`.
- **Scientific stake:** Precision and unit of analysis differ: prompts/images for refusal, stems for sycophancy, and only six constructs for the battery.
- **Classification:** **Conflict** for pooled standard errors; **compatible** as separate endpoint families.

### D20 — Text train/eval/calibration splits

- **Arnav:** Context mechanism slices AdvBench into disjoint direction (64), evaluation (100), and calibration (240) segments. Sycophancy groups by normalized question-stem hash before allocating direction/calibration/eval sets.
- **Charlotte:** Data prep writes AdvBench rows 0:200 to train and 200:400 to eval and writes Alpaca train separately. Notebooks then take the first 128 train and first 60 or 100 eval rows. Charlotte has no dedicated text calibration set for the core direction; per-model alpha selection examines the first 30 harmful-eval prompts.
- **File cites:** `scripts/e2e_mechanism_context_suppress.py:400-425`; `docs/context_suppression_mechanism_plan.md:130-143`; `docs/sycophancy_affect_plan.md:70-89`; `vendor/charlotte-affect-control-axis/docs/AFFECT_REFUSAL_DATASETS.md:60-69`; `artifacts/charlotte/extracted_nb/affect_gate_replication.py.txt:396-408`.
- **Scientific stake:** Arnav separates calibration from headline evaluation. Charlotte’s alpha sweep on eval prompts can optimistically select steering strength for that eval distribution.
- **Classification:** **Conflict** in calibration leakage control.

### D21 — Generation-free versus generated-response evaluation

- **Arnav:** Uses first-token refusal scores for internal/calibration analyses but generates responses for behavioral refusal and uses generation-based coherence. Sycophancy’s confirmatory endpoints are token/sequence probabilities, with free-form generation exploratory.
- **Charlotte:** Headline behavioral measures are generation-free first-token refusal or option logits. Short generation appears only as a validation/coherence check, not as the principal score.
- **File cites:** `scripts/e2e_publish_pipeline.py:644-688,1133-1161`; `docs/context_suppression_mechanism_plan.md:247-257,372-386`; `docs/sycophancy_affect_plan.md:36-66`; `vendor/charlotte-affect-control-axis/README.md:14-18`; `artifacts/charlotte/extracted_nb/behavior_battery.py.txt:3-26`; `artifacts/charlotte/extracted_nb/affect_gate_replication.py.txt:832-839`.
- **Scientific stake:** First-token proxies measure immediate policy preference; judged generations measure realized behavior after decoding. They can disagree, especially near refusal ceilings.
- **Classification:** **Compatible** as convergent endpoints, but **conflict** if one is substituted for the other.

### D22 — LLM judge

- **Arnav:** Grok is primary for publish/mechanism behavioral refusal, with regex fallback tracked; the sycophancy pipeline also has a capped, blinded Grok-4.6 High exploratory branch and Grok de-affectization.
- **Charlotte:** Uses no LLM judge for headline measures; the repository explicitly describes all behavioral measures as generation-free.
- **File cites:** `docs/colab_publish_experiment_plan.md:175-191`; `scripts/e2e_publish_pipeline.py:1107-1161`; `docs/sycophancy_affect_plan.md:60-66,155-176`; `vendor/charlotte-affect-control-axis/README.md:14-18`; `vendor/charlotte-affect-control-axis/docs/PROVENANCE.md:1-4`.
- **Scientific stake:** Arnav introduces judge-model validity, API drift, and fallback-rate concerns but evaluates full completions. Charlotte avoids judge subjectivity but relies on token-set construction.
- **Classification:** **Conflict** in measurement; **compatible** as a deliberate triangulation opportunity.

### D23 — Lighting manipulation

- **Arnav:** Publish scope explicitly defers Charlotte’s lighting experiment. Sycophancy measures luminance only as a negative-neutral matching covariate; it does not relight images as an intervention.
- **Charlotte:** Creates normal/dark/bright/warm/cool variants of the same 30 neutral images via brightness/color transforms and evaluates affect-axis shifts. A committed lighting result exists.
- **File cites:** `docs/colab_publish_experiment_plan.md:69-73`; `docs/sycophancy_affect_plan.md:105-123`; `artifacts/charlotte/extracted_nb/emotional_image_effects.py.txt:111-127,274-284`; `vendor/charlotte-affect-control-axis/results/expA2_lighting_gemma-3-12b-it.json:1-7`; `vendor/charlotte-affect-control-axis/docs/PROVENANCE.md:27-41`.
- **Scientific stake:** Charlotte tests a content-preserving low-level causal knob; Arnav controls brightness confounding but does not estimate a lighting effect.
- **Classification:** **Compatible** and Charlotte-only.

### D24 — MM-SafetyBench and harm-scene pairs

- **Arnav:** The publish plan names MM-SafetyBench SD/TYPO/OCR matched image-text pairs as primary. The actual publish script does **not** load MM-SafetyBench: it labels an AdvBench-text versus held-out EMOTIC-negative-image construction as a stand-in and builds at most 32 pairs by default.
- **Charlotte:** Does not use MM-SafetyBench or matched harmful-scene image/text pairs. Its image-jailbreak test pairs AdvBench requests with OASIS valence images that are affect stimuli, not visual encodings of the harmful request.
- **File cites:** `docs/colab_publish_experiment_plan.md:27-39,105-107,122-125`; `scripts/e2e_publish_pipeline.py:1050-1068`; `artifacts/charlotte/extracted_nb/emotional_image_effects.py.txt:327-353`; `vendor/charlotte-affect-control-axis/docs/AFFECT_REFUSAL_DATASETS.md:24-35`.
- **Scientific stake:** Arnav’s executed `h` contrast is a degraded modality/content contrast, not the preregistered matched harm-scene test. Charlotte has no corresponding harm-image axis. Neither executed pipeline supports a clean cross-pipeline MM-SafetyBench comparison.
- **Classification:** **Conflict**, including an **Arnav plan-versus-implementation deviation** that must remain labeled.

### D25 — Affect-axis construction

- **Arnav:** Publish uses image `a`, then removes `r`; context mechanism’s primary `a_perp` is `orth(unit(a_text+a_img), r)` with equal-weight unit text and image components. Sycophancy discards this construct and fits separate V/A axes from GoEmotions-style ratings.
- **Charlotte:** Refusal/image notebooks primarily build an OASIS image valence axis and orthogonalize against `r`; the behavior battery’s committed result instead uses a text-valence axis (`images_used=false`).
- **File cites:** `docs/colab_publish_experiment_plan.md:111-120`; `scripts/e2e_mechanism_context_suppress.py:697-708`; `artifacts/colab/e2e_mechanism_results_full_v3.json:61-70`; `docs/sycophancy_affect_plan.md:188-208`; `artifacts/charlotte/extracted_nb/emotional_image_effects.py.txt:181-190`; `artifacts/charlotte/extracted_nb/behavior_battery.py.txt:115-147`; `vendor/charlotte-affect-control-axis/results/behavior_battery_gemma-3-12b-it.json:1-8`.
- **Scientific stake:** These axes answer different questions: image affect, cross-modal shared affect, two-dimensional V/A, and text valence. Axis names alone are insufficient to establish equivalence.
- **Classification:** **Conflict** unless each axis is rebuilt and cross-projected on common data.

### D26 — Evaluation contexts

- **Arnav:** Context mechanism compares DESCRIBE, single-person EMOTION_Q, harmful, borderline, harmless, and caption-framed contexts; it also tests causal restoration, jailbreak subspace, and reachability. Publish adds gap A/B/C, gamma, contagion, and layer curves.
- **Charlotte:** Emotional-image effects compares neutral description, a task/opinion prompt, and one harmful context; then tests simple decisions, image/text pairing, agentic/survival scenarios, and lighting. The replication notebook focuses on gate dose response, mediation, detection/defense, localization, and cross-model status.
- **File cites:** `docs/context_suppression_mechanism_plan.md:234-352`; `scripts/e2e_publish_pipeline.py:1164-1268`; `artifacts/charlotte/extracted_nb/emotional_image_effects.py.txt:247-284,286-353,355-444`; `vendor/charlotte-affect-control-axis/docs/PROVENANCE.md:27-51`.
- **Scientific stake:** Context is itself the proposed moderator. Different prompt speech acts and answer spaces can reverse or suppress affect expression.
- **Classification:** **Compatible** as a broader context matrix; **conflict** for one-to-one cell comparison.

### D27 — Sycophancy experiment (Arnav-only)

- **Arnav:** Runs a preregistered graded sycophancy study with counterbalanced single-token matching log-odds, native-completion replication, Likert diagnostics, image relevance, shuffled images, literal/de-affectized captions, matched EMOTIC pairs, V/A and sycophancy directions, power gates, and optional Grok scoring.
- **Charlotte:** Has no implemented graded sycophancy experiment or Perez/custom-claim eval. Sycophancy appears only as related literature or a possible behavioral consequence.
- **File cites:** `docs/sycophancy_affect_plan.md:26-66,68-127,165-254`; `scripts/e2e_sycophancy_affect.py:67-104,419-451,994-1099,1473-1579`; `vendor/charlotte-affect-control-axis/docs/NOVEL_DIRECTIONS_REPORT.md:53-56`; `artifacts/charlotte/extracted_nb/behavior_battery.py.txt:3-26`.
- **Scientific stake:** Arnav directly tests whether affect changes deference to a user’s belief; Charlotte cannot support or refute that claim.
- **Classification:** **Compatible** and Arnav-only.

### D28 — Six-probe behavior battery (Charlotte-only)

- **Arnav:** Does not run Charlotte’s six-probe battery.
- **Charlotte:** Measures interpretation bias, risk estimation, prosocial helping, moral harshness, confidence, and sentiment using first-token option-logit scores under steering, text primes, random controls, and an optional image arm. The committed result used a text-valence axis and no images.
- **File cites:** `docs/colab_publish_experiment_plan.md:69-73`; `docs/context_suppression_mechanism_plan.md:457-460`; `artifacts/charlotte/extracted_nb/behavior_battery.py.txt:3-26,115-185,194-252`; `vendor/charlotte-affect-control-axis/results/behavior_battery_gemma-3-12b-it.json:1-8`.
- **Scientific stake:** Charlotte demonstrates breadth across low-stakes judgments, but the committed result is not evidence that natural images moved those six behaviors because `images_used=false`.
- **Classification:** **Compatible** and Charlotte-only, with the image-arm caveat.

### D29 — Agentic and survival-threat behavior

- **Arnav:** The compared pipelines do not include Charlotte’s agentic-misalignment and survival-threat scenario battery; Arnav’s unique behavior extension is sycophancy.
- **Charlotte:** Scores four hypothetical agentic choices and a survival-threat sign-flip test using first-token option logits, distress images, and text-derived desperation directions.
- **File cites:** `artifacts/charlotte/extracted_nb/emotional_image_effects.py.txt:355-444`; `vendor/charlotte-affect-control-axis/docs/PROVENANCE.md:27-41`; `docs/context_suppression_mechanism_plan.md:433-460`.
- **Scientific stake:** These probe self-preservation/deception tendencies, not refusal or user-agreement. They enlarge behavior coverage but cannot be substituted for Arnav’s sycophancy endpoint.
- **Classification:** **Compatible** and Charlotte-only.

### D30 — Positive-image and image-plus-text conditions

- **Arnav:** Publish includes positive EMOTIC as a refusal-table condition, but mechanism headline contrasts negative versus neutral. Sycophancy’s confirmatory natural-image contrast is negative versus neutral versus no image.
- **Charlotte:** Uses low, neutral, and high OASIS valence and explicitly tests high-valence image plus a positive text prefix against no image and white-box steering.
- **File cites:** `scripts/e2e_publish_pipeline.py:1040-1048`; `docs/context_suppression_mechanism_plan.md:247-266`; `docs/sycophancy_affect_plan.md:105-127`; `artifacts/charlotte/extracted_nb/emotional_image_effects.py.txt:327-353`.
- **Scientific stake:** Charlotte tests multimodal affect congruence/amplification; Arnav’s principal causal contrasts are not designed around a congruent positive image-text pair.
- **Classification:** **Compatible** extra condition, not a matched headline cell.

### D31 — Null distributions, seeds, and uncertainty

- **Arnav:** Mechanism uses isotropic and activation-whitened nulls (100 each), bootstrap CIs, three task-image remapping seeds, and planned independent direction rebuilds. The frozen mechanism artifact records seeds 0/1/2 for mappings but the saved primary direction uses the first direction seed. Sycophancy uses crossed bootstraps and multiple random families.
- **Charlotte:** Uses seeded random controls, a split-half affect-direction stability metric, and per-model alpha sweeps. The emotional-image notebook uses 20 random directions for a robustness panel; the behavior battery bootstraps over only six behaviors.
- **File cites:** `docs/context_suppression_mechanism_plan.md:57-75,175-182,272-288,345-368`; `artifacts/colab/e2e_mechanism_results_full_v3.json:6-23,61-70`; `docs/sycophancy_affect_plan.md:210-232`; `artifacts/charlotte/extracted_nb/affect_gate_replication.py.txt:369-408`; `artifacts/charlotte/extracted_nb/emotional_image_effects.py.txt:447-497`; `artifacts/charlotte/extracted_nb/behavior_battery.py.txt:255-279`.
- **Scientific stake:** Arnav emphasizes anisotropy-aware nulls and repeated mappings; Charlotte emphasizes direction stability and cross-model replication. These quantify different uncertainties.
- **Classification:** **Compatible** but non-interchangeable uncertainty analyses.

### D32 — Caption controls

- **Arnav:** Publish regenerates rich image captions for a pixel-versus-caption gap. Context mechanism compares caption-only and caption-plus-harmful framing. Sycophancy adds literal captions, Grok de-affectization, lexical-content retention, V/A neutrality gates, shuffled images, and claim relevance.
- **Charlotte:** Uses Claude-generated emotion stories and a positive text prefix, but the implemented image-effect pipeline does not contain Arnav’s literal/de-affectized caption mediation design.
- **File cites:** `docs/colab_publish_experiment_plan.md:150-163`; `scripts/e2e_mechanism_context_suppress.py:1193-1226`; `docs/sycophancy_affect_plan.md:147-186`; `scripts/e2e_sycophancy_affect.py:1473-1579`; `artifacts/charlotte/extracted_nb/emotional_image_effects.py.txt:203-244,327-353`.
- **Scientific stake:** Arnav can distinguish affect from scene semantics and pixel-specific from language-mediated effects more directly; Charlotte’s image/content confounding remains less separated.
- **Classification:** **Compatible** extension, Arnav-only in its full form.

### D33 — Direct comparability of headline findings

- **Arnav:** The frozen Gemma-4 mechanism result is a magnitude-gap/context-suppression study on hashed EMOTIC with NF4 and Grok-assisted behavioral validation; the earlier publish artifact reports an image-derived-axis inversion but warns against simple Charlotte-style interpretation.
- **Charlotte:** The headline is an affect gate on Gemma-3-12B bf16 using OASIS and generation-free scores, with cross-model evidence that the gate is model-specific.
- **File cites:** `artifacts/colab/e2e_mechanism_results_full_v3.json:386-424`; `artifacts/colab/summary.md:1-13,374-395`; `vendor/charlotte-affect-control-axis/README.md:1-18,72-84`; `vendor/charlotte-affect-control-axis/docs/AFFECT_REFUSAL_RESULTS.md:16-46`.
- **Scientific stake:** Model, precision, corpus, image split, harmless pole, axis construction, and endpoint all change simultaneously. A difference in outcome cannot be assigned to any one of them.
- **Classification:** **Conflict** for causal attribution across pipelines; **compatible** only as a factorial research agenda requiring harmonized reruns.

## Bottom line

The strongest shared core is: last-token residual directions, AdvBench refusal tasks, norm-scaled interventions, real affective images, negative/neutral or low/high contrasts, random controls, and the finding that natural affective images do not straightforwardly jailbreak the tested model. The strongest non-shared factors are the model generation/scale, NF4 versus bf16, EMOTIC versus OASIS, explicit held-out/hashing discipline, harmless-prompt source, image-axis contrast, judge/generation policy, and the behavior target.

Therefore:

1. Do not describe Arnav as an exact Charlotte replication.
2. Do not compare projection or steering magnitudes without rebuilding both pipelines on the same model, dtype, corpus split, text banks, and endpoint.
3. Treat Charlotte’s cross-model roster and behavior/lighting battery as complementary breadth.
4. Treat Arnav’s held-out EMOTIC split, matched-pair sycophancy design, hashing, caption controls, and Grok completion scoring as complementary depth.
5. Label Arnav’s executed harm-axis data as an MM-SafetyBench **stand-in**, because the script does not execute the preregistered matched MM-SafetyBench pairs.
