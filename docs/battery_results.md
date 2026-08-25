# Battery campaign results (exploratory)

[[sycophancy-affect-experiment]] [[EMOTIC]] [[VA-subspace]]

Protocol: [`docs/battery_campaign.md`](battery_campaign.md).
Raw scores: `artifacts/battery/exp0X/results.json`.
Board: [`artifacts/battery/STATUS.md`](../artifacts/battery/STATUS.md).

**Model:** `google/gemma-4-E4B-it`, nf4 weights, bf16 compute.
**Images:** EMOTIC split `1e8ea1c22144dd9d` (OASIS only in exp08).
**Host:** 8× A100-SXM4-40GB JupyterHub; wiped 2026-08-24 02:45 UTC.
**All ten runs finished** (`complete: true`). Frozen refusal artifact `artifacts/colab/e2e_mechanism_results_full_v3.json` was not overwritten.

These scores are **exploratory**. There was no per-experiment `LOCK.json` before scoring. Do not say the photos induce emotion in the model. Do not reopen the aborted EmoBank-VA sycophancy confirmatory.

## How SUCCESS / FAILED is labeled

- **Run:** every experiment completed on the A100. That is not the scientific label.
- **SUCCESS:** we saw a behavioral difference worth reporting (with the caveats in that section).
- **FAILED:** no reliable behavioral difference of the kind we went looking for. A FAILED test can still be a clean null. It is not “the code crashed.”

Percents are a subjective chance that a **rerun on this same model with new photos and new items** would show the same difference — not a p-value inverted, and not a claim about humans.

| Chance at least one of the five moves is real | Chance all five are real |
|---|---|
| ~90% | ~15% |

## Scoreboard

| ID | Scientific label | What we asked | What we actually saw | Chance real, not noise |
|---|---|---|---|---|
| exp01 | **FAILED** | Fear vs anger on risky bets | Δ ≈ −0.09; interval includes 0 | — (null) |
| exp02 | **FAILED** | Matched-scene pairs to explain exp01 | Nothing from exp01 to explain | — (null) |
| exp03 | **SUCCESS** (weak) | Photos vs captions vs labels | Pixel dictator moved; captions did not copy it. n=8 pairs | ~45% |
| exp04 | **FAILED** | Perez sycophancy, behavior only | Mean Δ vs neutral interval includes 0 | — (null) |
| exp05 | **SUCCESS** (partial) | Dictator + Ultimatum | Anger → more unfair-reject vs other photos. Give-more / give-less did not hold | ~65% contrast; ~35% “anger causes fairness” story |
| exp06 | **SUCCESS** (partial) | Temporal discounting by emotion | No emotion ladder. Any photo → more “money now” than no photo | ~75% photo vs none; ~15% emotion-specific k |
| exp07 | **FAILED** | Trivia as a negative control | Accuracy ~0.68–0.72. Equivalence test inconclusive. Not an emotion-collapses-knowledge finding | — (null for affect) |
| exp08 | **FAILED** | EMOTIC vs OASIS on the same tasks | All three tasks `both_null`. Matching nulls, not matching effects. Do not pool | — (null) |
| exp09 | **SUCCESS** | Over-refusal on benign XSTest | No photo ~66% refuse; any photo ~91–94%. Neutral photos too | ~85% the score jumped; ~60% it is real extra caution |
| exp10 | **SUCCESS** (partial) | Does an internal affect direction mediate answers? | Risk changed and correlational mediation held. Dictator invalid. Perez null. Dirs are `DIAGNOSTIC_NOT_V3` | ~70% risk shift; ~40% mediation story |

**If only one finding goes in a paper as more than a hint:** exp09 (photo vs no photo, extra caution).
**Worth a locked rerun:** exp05 anger-reject and exp06 photo-vs-none.
**Too small / too rebuilt:** exp03 (n=8), exp10 (not frozen v3).

---

## exp01 — Fear vs anger on risky lotteries

**Scientific label: FAILED**

**Question.** Do fear photos make the model pick the safe lottery more than anger photos (appraisal-tendency)?

**Result.** Anger risky rate 0.375 vs fear 0.467; delta anger−fear ≈ −0.092. 95% bootstrap CI **[−0.50, 0.30]** includes 0. Gates 6/8 (pool match and letter-side bias failed). Fear pool used fallback labels. Exclusive fear n was tiny (9).

**Not noise vs real.** This is a failed prediction, not a hidden success. A small real fear/anger gap could still exist; this run did not find one.

**Artifact.** `artifacts/battery/exp01/results.json`

---

## exp02 — Scene-matched EMOTIC caliper pairs

**Scientific label: FAILED**

**Question.** If exp01’s fear/anger gap was a scene confound (different objects/lighting), matched pairs should shrink it.

**Result.** Headline `NO_EXP01_EFFECT_TO_EXPLAIN`. Pairs were built (fear–anger n=96 at tier 2), but there was no exp01 effect to attribute to semantics.

**Not noise vs real.** Downstream of a null. Does not revive exp01.

**Artifact.** `artifacts/battery/exp02/results.json`

---

## exp03 — Cross-modal: pixels vs caption vs de-affectized vs label vs narrative

**Scientific label: SUCCESS (weak)**

**Question.** If photos change answers, do captions / “feel sad” / labels copy that pattern?

**Result.** Headline `CROSS_MODAL_DIVERGE`. Pixel identifiable. **Dictator + actual photos:** negative vs neutral Δ ≈ −0.98, CI **excludes 0** (n=8). Risk and Perez pixel CIs include 0. Caption / de-affectized / label dictator CIs include 0. Narrative Perez moved the other way (CI excludes 0). Smoke tier, 14 pairs (target 16).

**Chance this is real, not noise: ~45%.** Among 5 modalities × 3 task families, a couple of intervals will miss 0 by luck. Winner’s curse on n=8. Captions leaned the same way as pixels but were noisier.

**Artifact.** `artifacts/battery/exp03/results.json`

---

## exp04 — Perez sycophancy, behavior only

**Scientific label: FAILED**

**Question.** Do negative photos change how much the model plays along with a wrong user opinion? This is **not** the aborted VA prereg. No EmoBank, no `s` fit, `N_CUSTOM=0`.

**Result.** Headline mean((fear+anger+sad)/3 − neutral) ΔS ≈ −0.065, CI95 **[−0.22, 0.09]** includes 0. Per-emotion vs-neutral CIs all include 0. Gates 6/6. Do **not** claim `NATURAL_AFFECT_SYCOPHANCY`.

**Not noise vs real.** No trustworthy shift. Does not rescue the VA-gated confirmatory.

**Artifact.** `artifacts/battery/exp04/results.json`

---

## exp05 — Dictator + Ultimatum

**Scientific label: SUCCESS (partial)**

**Question.** Sympathy → give more? Anger → reject unfair splits? Fear → give less?

**Result.**

| Prediction | Holds? | Delta | 95% CI |
|---|---|---|---|
| sympathy give more | no (leans) | 0.095 | **includes 0** (very wide) |
| **anger reject unfair** | **yes** | **+0.073** | **[0.032, 0.123]** |
| fear give less | no | 0.132 | **includes 0** |

Giving stayed ~flat across emotion types (~$44 pooled dictator). Unfair-reject: anger ~8.4% vs neutral ~1.1%, but **no-image was ~9.8%** — similar to anger. So the contrast is anger vs other photos, not “anger vs no picture.”

**Chance the anger-vs-other-photos contrast is real: ~65%.**
**Chance the story “anger made it punish unfairness” is the right one: ~35%.** Alternative: most photos make it swallow unfair deals; anger photos do that less. Three money predictions were tested; one landed.

**Artifact.** `artifacts/battery/exp05/results.json`

---

## exp06 — Temporal discounting (money now vs later)

**Scientific label: SUCCESS (partial)**

**Question.** Does fear / anger / sad produce a clean impatience order (Kirby k)?

**Result.** 5425 trials. Parse rate 1.0. Kirby consistency only 0.51–0.66, so emotion-specific k is weakly identified (sad/happy k exploded to ~193; others ~0.002). **No-image p(now)=0.36**; every photo arm **0.44–0.54**.

**Chance photo vs no-photo is real: ~75%.**
**Chance fear/anger/sad each have their own discount rate: ~15%.** The “a picture is attached” effect is the only one I would keep.

**Artifact.** `artifacts/battery/exp06/results.json`

---

## exp07 — TruthfulQA capability negative control

**Scientific label: FAILED** (as an affect-changes-knowledge finding; equivalence **inconclusive**)

**Question.** If photos change bets or sycophancy, does ordinary knowledge stay flat (±5pp)?

**Result.** Accuracy: no-image 0.718, negative 0.696, neutral 0.678 (n=790). Negative vs no-image and negative vs neutral sit inside the ±5pp window; **neutral vs no-image misses it slightly** (Δ ≈ −0.039). Headline `EQUIVALENCE_INCONCLUSIVE`. Tiny generic photo cost, not affect-specific collapse.

**Not noise vs real.** Do not report “emotion made it worse at trivia.” The negative-control *proof* of flatness did not fully pass.

**Artifact.** `artifacts/battery/exp07/results.json`

---

## exp08 — EMOTIC depicted vs OASIS elicited

**Scientific label: FAILED**

**Question.** Do depicted-person emotion (EMOTIC) and viewer-elicited ratings (OASIS) produce the same task signature?

**Result.** Smoke n. All three tasks (risk, dictator, Perez) `both_null` — negative−neutral CIs include 0 on **both** corpora. Headline “signatures match” means **matching nulls**, not matching big effects. Do not pool EMOTIC and OASIS.

**Not noise vs real.** No trustworthy corpus-specific or shared effect on these small tasks.

**Artifact.** `artifacts/battery/exp08/results.json`

---

## exp09 — XSTest over-refusal on benign asks

**Scientific label: SUCCESS** (strongest finding)

**Question.** Do photos make the model refuse harmless questions that only *sound* sensitive?

**Result.** First-token refuse on 250 official XSTest safe items:

| Condition | Refuse rate | 95% CI | Δ vs no-image |
|---|---|---|---|
| no image | 0.656 | [0.596, 0.716] | — |
| fear | 0.920 | [0.880, 0.956] | +0.264 [0.224, 0.302] |
| anger | 0.936 | [0.916, 0.956] | +0.280 |
| sad | 0.908 | [0.859, 0.952] | +0.252 |
| happy | 0.924 | [0.892, 0.956] | +0.268 |
| **neutral** | **0.944** | [0.916, 0.972] | **+0.288** |

All five photo types jump. Neutral is highest. This is **photo vs no photo**, not fear vs anger.

**Chance the first-token score really jumped: ~85%.** Five independent arms, ~+26pp, clustered bootstrap still far from 0.
**Chance this is genuine extra caution rather than a scoring quirk: ~60%.** Refuse words include “I”; a Grok judge agreed with the first-token label only ~53% on a 32-item subsample. Locked rerun should not treat “I” as refuse.

**Artifact.** `artifacts/battery/exp09/results.json`

---

## exp10 — Representation mediation (exploratory; not frozen v3)

**Scientific label: SUCCESS (partial)**

**Question.** Do negative vs calm photos change answers *through* an internal affect direction?

**Result.** Dirs labeled `DIAGNOSTIC_NOT_V3` (rebuilt; cosine to frozen v3 did not match). Frozen v3 file not written.

| Domain | Verdict | Behavior (neg−neu) CI |
|---|---|---|
| **risk** | correlational mediation supported | **[−0.113, −0.031]** excludes 0; indirect **[−0.083, −0.016]** |
| dictator | endpoint invalid (letter mass ~0.27) | ignore |
| Perez | no evidence | includes 0 |

1/3 valid domains. Correlation, not causal mediation.

**Chance the risk behavior shift is real: ~70%** (n=64 pairs).
**Chance “the rebuilt affect direction caused it”: ~40%.** Would likely drop if we required the frozen v3 arrow.

**Artifact.** `artifacts/battery/exp10/results.json`

---

## What this battery does *not* show

- Photos do not jailbreak this model (prior work; not reopened here).
- Fear vs anger does not reliably change betting.
- Natural photos do not rescue Perez sycophancy without VA.
- Trivia skill does not collapse under negative photos.
- EMOTIC and OASIS cannot be pooled.
- Images do not “make Gemma feel.” At most they change some answers, often whenever *any* picture is present.
