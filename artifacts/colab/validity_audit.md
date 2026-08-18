# Validity audit — master verdict

**Date:** 2026-08-10  
**Question:** Is the Gemma-4 E2E experiment invalidated by image-built affect-axis circularity?  
**Answer:** The **geometry / INVERTED mechanism story is not valid as framed**. The **behavioral “images don’t jailbreak” result still holds**. The experiment is not worthless; several claims must be withdrawn or rewritten.

**Hard truth:** Nothing is “100% perfect.” This is a staff-engineer claim triage + fix list.

**Auditors (Cursor Grok 4.5):**
- [Codebase validity audit](4f4150a4-a223-41f1-a1f6-846d6b5a725b) — done
- [Literature construct validity](0658d61e-6308-4452-b7a5-cfb2f6188e4f) — done
- [Charlotte research audit](09665b36-0a1d-413d-a555-de3e616ee9fa) — done
- [Syed research audit](b58ede07-94e5-47a7-b326-a425d6379215) — done

---

## 1. Core methodological finding (all auditors agree)

| Fact | Implication |
|------|-------------|
| `a` / `a⟂` built from **images only** (EMOTIC/OASIS neg−neu + DESCRIBE) | Image Δ on that axis ≈ reconstructing the defining contrast |
| `ratio_a = \|Δ_img\| / \|Δ_txt\|` on that axis | **Biased toward images by construction** |
| `ratio_a ≈ 1.59` labeled INVERTED | Valid as a **metric outcome**; **invalid** as “photos are more emotional than text” |
| OOD-norm PASS + `ratio_a_unit ≈ 1.39` | Rule out color-square / ‖act‖ artifacts only — **do not** fix construction bias |

**One-line ruthlessness ([Literature](0658d61e-6308-4452-b7a5-cfb2f6188e4f)):**  
Current `ratio_a` answers “how well does an image-defined contrast reconstruct itself relative to a mismatched text contrast?” — not “is emotion appraisal shared across modalities?”

---

## 2. Claim ledger (merged)

| Claim | Verdict | Notes |
|-------|---------|-------|
| Images don’t jailbreak (refuse ~1.0 / 1.0 / 0.98, Grok) | **HOLDS** | Independent of how `a` was built |
| OOD residual-norm PASS (science/ref ≈ 1.003) | **HOLDS** | Not color-square inflation |
| Unit-norm inversion persists | **HOLDS as narrow measurement** | Still on image-built dir |
| `r` steering competence (harmless → refuse) | **HOLDS** | Text-built refusal axis |
| γ=100 collapse is generic (random worse) | **HOLDS** | Not emotion-specific jailbreak |
| Gap B/A ≈ 1.13 (caption ≈ photo on `a⟂`) | **PARTIALLY HOLDS** | Relative A vs B OK; both on image-built axis |
| INVERTED ⇒ images intrinsically > text on affect | **INVALID** | Construction bias |
| INVERTED as primary mechanism paper claim | **WITHDRAW** | Plan itself said withhold mechanism on INVERTED |
| INVERTED kills “shared text↔image affect” | **OVERCLAIMED** | Need Syed-style text→image transfer |
| Charlotte SHARED killed by your INVERTED | **NO** | Different metrics/models ([Charlotte](09665b36-0a1d-413d-a555-de3e616ee9fa)) |
| `ratio_h ≈ 0.036` ⇒ clean “harm is text-dominant” | **WEAK / SUSPECT** | [Codebase](4f4150a4-a223-41f1-a1f6-846d6b5a725b): `h` built as harmful-text − DESCRIBE(eval EMOTIC-neg), then remeasured with overlap — not MM-SafetyBench train pairs |
| Gap C as clean text-emotion upper bound | **SUSPECT** | Baseline subtracts image-neu, not mundane text |
| Text distress diversity in `ratio_a` | **WEAK** | `[DISTRESS] * N_DELTA` — one string repeated |
| Pre-reg 3 direction rebuilds / null power | **NOT DONE** | Plan required; only seed 0 |

---

## 3. Teammate comparison

### Syed ([Syed research audit](b58ede07-94e5-47a7-b326-a425d6379215))
- **Question:** Do text-learned appraisal directions transfer to image activations?
- **Method:** Stage A text gate → Stage C **frozen text → image** (+ caption / random-null controls) → Stage D causal steer under images.
- **Key numbers (Gemma-3-4B):** Stage C full test n=7280 — pleasantness vs valence Spearman **+0.507**, retention **~0.66**; unique(image\|captions) residual **+0.201**; Stage D slopes +0.329 / −0.309 vs random −0.027.
- **Prompt matching is load-bearing:** Syed got transfer only with parallel emotion Qs; mismatched prompted-image vs bare-text is Charlotte’s null mode, not Syed’s failure.
- **Vs Arnav:** Syed **reframes** INVERTED — predicts large image Δ on image-built DESCRIBE axis + weak mismatched text Δ without endorsing “images > text.” Shared geometry can coexist with your INVERTED metric.
- **Adopt:** text→image cross-build; matched framing; random-dir null *distribution*; semipartial caption vs valence GT; demote INVERTED from mechanism headline.

### Charlotte ([Charlotte research audit](09665b36-0a1d-413d-a555-de3e616ee9fa))
- Also builds `a` from **images**.
- Her “~100× too little” = natural image Δ under **harmful** prompts vs **steering ceiling** to jailbreak — **not** Arnav’s `|Δ_img|/|Δ_txt|`.
- **Not the same circularity** as Arnav’s modality ratio.
- **Agree with you:** images don’t jailbreak.
- **Disagree / non-comparable:** “images barely move affect” (her steer-gap ≠ your INVERTED).
- INVERTED does **not** refute her behavioral null or deck SHARED; it **does** kill using her 100× as evidence for PASS_AFFECT_SPECIFIC on Gemma-4.

---

## 4. Extra code issues ([Codebase](4f4150a4-a223-41f1-a1f6-846d6b5a725b))

1. **`h` plan violation:** eval EMOTIC-neg + DESCRIBE stand-in, not MM-SafetyBench; build/measure overlap → `ratio_h` hard to trust.  
2. **Gap C baseline:** text distress minus **image** neu — mismatched.  
3. **Single distress/mundane strings** × N.  
4. **Mean-over-layers** while layer curves flip sign for text.  
5. **Framing contradiction:** plan withholds mechanism on INVERTED; `summary.md` / framing led with trusted INVERTED geometry.

---

## 5. What you can still say (no new runs)

**Allowed**
- On Gemma-4-E4B-it (nf4), under this AdvBench + EMOTIC protocol: emotional images do **not** lower refuse (~ceiling, Grok 100%).
- Image-built `a` generalizes to held-out images (large Δ); not an OOD-norm artifact.
- Text distress has **nonzero** projection on that image-built axis (transfer exists in one direction, not quantified fairly).
- Caption ≈ photo on that axis (gap≈1.13); pure distress text still larger under gap C (interpret cautiously).
- Huge γ collapse is nonspecific (random worse).
- Pre-reg label INVERTED correctly describes the **asymmetric metric**, not a discovery of intrinsic image>text affect.

**Forbidden without redesign**
- “Images have stronger emotion appraisal than text.”
- “`a⟂` is pure / refusal-independent affect” (Wollschläger: ortho ≠ independence).
- “INVERTED means visual affect dominates text.”
- Using INVERTED alone to accept/reject SHARED appraisal.
- Equating Charlotte’s 100× with your `ratio_a`.

---

## 6. Minimal fix (make shared-axis claim valid)

1. Build `a_text` = DoM(diverse emotion texts − neutral texts); ortho to `r` if needed.  
2. Build `a_img` as now (train images only).  
3. **Transfer matrix** on held-out data: text→text, text→image, image→image, image→text.  
4. Primary shared stats = **text→image** and **image→text** (Syed direction + reverse).  
5. Matched ontology / prompt regime (Syed lesson).  
6. Fix or drop `h` from kill geometry until MM train pairs + held-out eval.  
7. Fix Gap C baseline to mundane text.  
8. Nulls: shuffled labels + random dirs; 3 direction seeds.  
9. Causal: steer `a_text` on images and `a_img` on text; measure affect reports + refuse.

---

## 7. Immediate actions for the writeup

1. **Rewrite** `summary.md` / framing: lead with behavioral null; demote INVERTED to “biased metric outcome.”  
2. **Do not** claim mechanism paper from current `ratio_a`.  
3. **Next science run:** Syed-style text→image transfer on Gemma-4 (smallest high-value experiment).  
4. Treat `ratio_h` as provisional until `h` rebuilt cleanly.

---

## 8. Bottom line

Your instinct was right: the circularity is **decisive for the geometry headline**.  
It does **not** trash the whole project — **“images don’t jailbreak” remains the robust result**, aligned with Charlotte.  
Syed already shows how to test SHARED properly (text→image); that is the experiment you still need for the appraisal question.
