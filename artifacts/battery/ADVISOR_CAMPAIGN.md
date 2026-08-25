# Campaign advisor ruling

[[EMOTIC]] [[OASIS]] [[MAGNITUDE_GAP]] [[sycophancy-affect-experiment]]

## Verdict

**Not yet confirmatory-valid as a ten-experiment set.** `queue.json` and `STATUS.md` are execution records, not a preregistration. Any score produced before an experiment-level lock manifest is written must be labeled exploratory.

The set can become paper-valid as a battery of **image-conditioned behavior**, with these limits:

- Say that images *depict* or are *normed for* affect. Do not say Gemma felt, experienced, or was induced into fear, anger, or another emotion.
- `MAGNITUDE_GAP` motivates the battery but does not validate it. Do not reuse the v3 result as evidence for a battery hypothesis tested on the same model and EMOTIC split.
- Behavioral DVs are not circular merely because image labels selected the conditions. Representational claims are circular when evaluated on an axis partly built from those images.
- Pre-specify one primary contrast per experiment and a battery-level multiplicity rule or ordered testing hierarchy. Do not market ten uncorrected tests as ten confirmations.
- Report heterogeneous DVs separately. Do not pool letter log-odds, dollars, acceptance, accuracy, and refusal rates into one effect without a frozen common estimand.

Use “fear-depicting versus anger-depicting images condition risk choices,” not “fear versus anger changes risk.”

## Lock before the first confirmatory score

Write one immutable `LOCK.json` per experiment, plus a campaign manifest, before scoring outcomes. Each must contain:

1. Git commit and SHA256 of the experiment script, prompt file, lock file, and analysis code.
2. Exact model revision, tokenizer revision, nf4/bf16 settings, chat template, `[image, text]` order, and package versions.
3. EMOTIC split hash `1e8ea1c22144dd9d`, exact image IDs and relative paths, file-manifest hash, labels used, deduplication rules, exclusions, pair/caliper output, and assignment/remapping seeds.
4. For OASIS, exact release/source, license status, norm table hash, image-manifest hash, selected IDs, and any matching strata.
5. Raw task-data revision and SHA256, exact item IDs, item-list hash, train/calibration/eval split lists, grouping key, ordering, and all exclusions.
6. Frozen prompt strings, options, label/side counterbalancing, primary DV and contrast, sample size, stopping rule, missing-data rule, CI/bootstrap unit, random seeds, validity gates, and multiplicity procedure.
7. For null controls such as exp07, a frozen equivalence/non-inferiority margin. Failure to reject zero is not evidence of no capability change.
8. For exp10, SHA256 of frozen v3 and every loaded direction/tensor, layer/window choices, and a hard assertion that no direction is refit.

The lock writer must run before the scorer and refuse to continue if a source hash changes. Preserve the pre-score lock and append results separately.

## Confirmatory status by experiment

- **Confirmatory candidates:** exp01, exp02, exp04, exp05, exp06, exp07, exp09, but only after the locks above. Exp02 is a matched-design robustness test. Exp07 is a negative control, not positive affect evidence.
- **exp04:** valid only as a new, behavior-only Perez contrast. It is not completion or rescue of the aborted VA sycophancy preregistration. Do not fit VA or `s`, apply the old `r>=0.7` gate, or reopen that run.
- **exp03:** exploratory-only as currently named. It can be confirmatory only if the tested direction/readout is built independently of all evaluated images, for example text-built then image-tested or fully cross-fit. Caption, label, and narrative arms also test information format, not emotion induction.
- **exp08:** exploratory-only. EMOTIC versus OASIS confounds corpus, content, visual style, annotation target, and human norming protocol. It can support stimulus-set generalization after pre-score matching, not a causal “depicted versus elicited emotion” claim about Gemma.
- **exp10:** exploratory diagnostic only. Joint v3 `a_perp` includes an image-built component, and projection mediation is not causal mediation. It may test consistency with frozen v3, not intrinsic image affect or a new confirmatory mechanism.

## GPU and deadline order

There is a clock inconsistency: campaign start `2026-08-23 00:25 ET` is `04:25 UTC`, so destruction at `2026-08-24 02:45 UTC` leaves **22 h 20 min**, not 44 h. Plan to the 22-hour hard limit unless the wipe time is independently corrected. Treat any extra time as reserve.

Keep at most four persistent model loads:

1. Wave A: exp01, exp05, exp06, exp04.
2. Wave B: exp07, exp02, exp03, exp09.
3. Wave C: exp08, exp10.
4. Reserve the final 2 hours for finite-result checks, lock/result hash verification, and off-host copies. Do not spend the reserve enlarging samples or adding analyses.

Start the next queued experiment when a slot frees; do not wait for an entire wave. If time dies, cut strictly from the queue tail: **exp10, exp08, exp09, exp03, exp02, exp07**, then stop. Preserve exp01, exp05, exp06, and exp04 first. Never issue a mechanism headline from partial exp03/exp10 prerequisites.

## OASIS retrieval failure

Run retrieval off the GPU critical path now:

1. Check for an authorized complete host/cache copy, then the official release source. Record source and license.
2. Verify image count, unique IDs, image-to-norm joins, readable files, and hashes before condition selection.
3. Freeze the selected list and matching output before any Gemma score.
4. If a complete authorized copy cannot be verified before Wave C, emit `DATA_UNAVAILABLE`, keep exp08 unrun, and release the slot.

Do not substitute EMOTIC, the earlier incomplete corpus, synthetic images, screenshots, or norm rows without images. A failed retrieval is cleaner than a changed construct.

## Likert ruling

The old Gemma-4 Likert failure does **not** force a battery-wide DV redesign, because the campaign already makes forced-choice letters and dollar/accept amounts primary. Mark Likert secondary and unavailable when its condition-specific digit mass is invalid; it cannot rescue or veto a valid primary endpoint.

For dollar allocations or delays, freeze a finite option set and score counterbalanced labels or candidate sequence log-probabilities. Validate finite scores and candidate mass before outcomes. If any experiment currently has Likert as its only primary DV, redesign and lock it before scoring; never replace the DV after seeing condition effects.
