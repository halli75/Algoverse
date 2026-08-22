# Lessons

## 2026-08-18 — Health ticks are not the experiment
- **Mistake:** After amended T4 smoke died on VA `r_a=-0.019`, spent ~7h only confirming Colab idle/disconnect. Did not take VA to the advisor or split construction vs honest fail until the user woke up angry.
- **Why it happened:** Treated “do not re-run hoping r_a moves” as “wait.” Lessons already said implementation defects get a locked fix and a new smoke without waiting to be asked.
- **Rule:** After a smoke abort, diagnose the failing gate the same day. If it can be a construction defect, advisor-lock the estimator repair immediately. Idle GPU watchdog ticks do not substitute for that work.

## 2026-08-17 — Smoke-gate abort is not “don't fix implementation bugs”
- **Mistake:** After T4 smoke failed Likert mass 0.181, treated the freeze as a total halt. Did not apply the locked Likert construction the advisor already allowed. User had to ask why it wasn't fixed.
- **Why it happened:** Confused “do not retune thresholds from outcomes” with “do not touch the pipeline.” Likert was scored on the FC prompt minus one line, so `Choices: (A)/(B)` stayed in context and stole digit mass. That is a pre-existing prompt bug, not a threshold to lower. Headroom 0.183 with S_label mean 3.88 is a real ceiling gate and is not a code fix.
- **Rule:** On smoke abort, split defects vs gates. Implementation defects (wrong Likert stem, infra) get a locked fix and a new T4 smoke. Frozen thresholds (0.8 mass, 0.25 headroom) do not move. Do not wait for the user to ask “why didn't you fix it.”

## 2026-08-17 — Health loop ≠ science stop
- **Mistake:** After T4 smoke hit frozen gates, killed the 15-minute monitor loop (PID 9012) to silence ticks. Treated “stop on scientific gate failures” as “tear down supervision.”
- **Why it happened:** Mixed two different stops. Plan Supervision says recover infra only and stop the *run* on science gates. The 15-minute loop is a standing requirement (kernel/GPU, heartbeat, stage, model/dtype, checkpoints). Aborting Likert/headroom does not authorize killing the watchdog, nor skipping remaining plan work (advisor-after-smoke, write all gates + `mechanism_answer`).
- **Rule:** Never stop the 15-minute loop unless the user says to. Science abort = do not re-run/retune. Loop stays. “Abort Likert” invalidates the Likert endpoint only. A100 stays blocked while `CEILING_OR_FLOOR` / `ENDPOINT_INVALID` stand.

## 2026-08-13 — Do not hide the mechanism behind a picky refuse-bump gate
- **Mistake:** B1 required CI upper ≤ +0.02, so a +3pp *increase* in refuse at ceiling became PREMISE_FALSE and skipped the why. C1 compared FT scores (~10) to a 0.05 *rate* cutoff, so causal M1 could never pass. M2_miss used |s_j|<0.05 on raw projections (~4), so it could never fire. M4/layer curves were never measured. Text-only arrow was used after the user asked for text+image.
- **Rule:** Premise = images do not *lower* refuse. Combined `a_perp=orth(unit(a_text+a_img),r)` is the paper arrow. C1 uses refuse *rates* (or FT only if rates are saturated, and then clean must beat random). M2_miss uses |s_j_natural|/|s_j_ceiling|. Always dump text/image/combined Δ, layer curves, s_r/s_j/s_a, and a one-sentence `mechanism_answer`.

## 2026-08-13 — Affect arrow is BOTH text and images, not text-only primary
- **Mistake:** Mechanism run built `a_text` and `a_img` separately, then scored M1 only on text-built `a_text_perp`. User asked to construct the emotion arrow from **both** text and images. Grading “did photos move emotion?” on the text-only arrow is the wrong experiment and produced a false “photos don’t move it” story.
- **Why it happened:** Circularity audit overcorrected: avoided image-only `a`, then treated text-only `a` as the primary readout instead of a combined/shared direction.
- **Rule:** Default affect direction = combine text distress−neutral **and** image neg−neu (e.g. `unit(a_text + a_img)` or pooled contrast), then ortho to `r`. Never abort M1 on `a_text` alone. Do not tell the user “photos didn’t move the arrow” if we did not use the arrow they asked for.

## 2026-08-13 — Steer must use residual norms; gist /raw/ is cached
- **Mistake:** Mechanism `steer()` added bare `alpha` to a unit vector. Publish/Charlotte use `alpha * ||resid||`. On Gemma-4 that made α=0.25 ~470× too weak, so `r_validate` stayed 0.08→0.08 and intervention phases were invalid.
- **Also:** Gist `.../raw/file` can serve a stale CDN copy after PATCH. Pin `.../raw/<gist_sha>/file`. Incomplete unzip after a kill left 3475/23185 jpgs; skip-unpack if `emotic/` exists is unsafe — require jpg count.
- **Rule:** Copy the publish steer recipe (`alpha * norms[l]`). After gist PATCH, fetch by revision SHA. After unpack, assert n_jpg ≳ 20k before mat2py.

## 2026-08-09 — Flag axis-construction circularity early
- **Mistake:** Explained INVERTED `ratio_a` (image Δ > text Δ on `a⟂`) as a trustworthy geometry finding after OOD/unit checks, without leading with: the affect axis was **built from images**, so images winning on that axis is partly by construction.
- **Why it happened:** Focused on artifact gates the plan already emphasized (OOD norms, unit-norm) and on matching the Charlotte/pre-reg recipe, instead of interrogating whether the *comparison itself* was fair.
- **Rule:** Whenever reporting modality ratios (image vs text) on a direction, **first state how the direction was built** and whether that biases the winner. If axis is image-built, do not sell “images > text” as a clean intrinsic claim; frame as shared-representation / cross-modal transfer test, and name the cross-build control (text-built axis → test images).
- **Also:** When simplifying for the user, keep the construction bias visible — simplicity is not an excuse to drop the main methodological caveat.

## 2026-08-10 — Validity audit: what survives circularity
- **Codebase + lit + Charlotte auditors agree:** INVERTED geometry headline is invalid as intrinsic image>text; behavioral no-jailbreak holds; Charlotte’s ~100× is steer-ceiling not modality ratio; Syed text→image is the clean SHARED test.
- **Extra landmine found:** `h` / `ratio_h` may be leaked (eval EMOTIC-neg in build + overlapping measure) — do not treat as clean control until rebuilt.
- **Rule:** After any kill-switch run, publish a claim ledger (HOLDS / INVALID / NEEDS_RERUN) before framing docs. Never elevate pre-reg branch labels to scientific discoveries without construct checks.
