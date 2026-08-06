# Teammate findings (ingested 2026-07-29)

Source: Arnav paste of Syed Stages A–D + Charlotte Exp 2/3 writeups.
Links only — tensors were never Drive-checkpointed.

## Syed — appraisal-research-algoverse

- **Repo:** https://github.com/syedmahdi30/appraisal-research-algoverse
- **Colab:** https://colab.research.google.com/drive/1ddCgMVMM-bN9mTXXVE9uIoXCjAGUyFjx
- **Model:** Gemma-3-4B-it, critical layer **18** (`blocks.18.hook_attn_out` for Stage C read-out)
- **Lesson:** probe direction ≠ steering direction → use **difference-of-means**
- **Stage C:** text pleasantness probe → image valence ρ≈0.51; not just captioning (unique 0.31→0.26→0.20)
- **Stage D:** text DoM pleasantness steers image emotion output (β −3..+3); random ~12× smaller; suddenness ~4.5× smaller
- **Captions (needed for Step 3):** generated in Colab, persisted as
  - `results/stage_c/caption_readout.parquet` (plain/neutral)
  - `results/stage_c/caption_readout_rich.parquet` (detailed)
  - **Not in GitHub** (only `.gitkeep` under `results/stage_c/`). Must export from his Colab/local run.

## Charlotte — affect × refusal (Exp 3)

- **Colab:** https://colab.research.google.com/drive/1Ffb3Mca34LN3irJEBknHdD2_4OQNXKjN
- **`r`:** Arditi-style refusal; validated (harmless +α → refuse 0.12→1.00)
- **`a` pre-ortho:** mean `|cos(a,r)| = 0.358`
- **`a⟂`:** orthogonalized to `r`; jailbreak toward **positive/benign** affect (negative α)
- **Coherent jailbreak window:** roughly α ∈ [−0.01, −0.005]; outside → “yummy yummy…” collapse
- **Mechanism:** `a⟂` works **through** `r` (r-proj 19967→14656 under steer; jailbreak dies if `r` ablated)
- **KEY NULL (images):**

  | condition | refuse | a⟂-proj | r-proj |
  |---|---:|---:|---:|
  | no image | 0.99 | 694 | 19967 |
  | neutral | 0.98 | 937 | 19521 |
  | negative | 0.99 | 915 | 19549 |
  | positive | 0.99 | 926 | 19519 |

  Coherent text jailbreak moves a⟂-proj by ~−265/layer → images ~100× too weak.

- **Operative layer for `a⟂`/`r`:** **still unknown** — not stated in the writeup paste. Must read her Colab cells or ask her.
- **Tensors `a⟂`, `r`:** **not exported.** Re-derive from her Colab or ask her to download `.pt`.

## Implications for our kill switch

- Do **not** use `r` as the “images drive this” geometric control — `a⟂` is causally routed through `r`.
- Control axis = harmfulness axis from harmful-image vs matched text (MM-SafetyBench).
- Behavioral readout = refusal / AdvBench (may still involve `r`).
- Canonical projection layer for Steps 2–4 = **Charlotte’s operative layer** (TBD), not Arnav-22 or Syed-18.

## Still missing before Step 2

1. Charlotte data on Drive (`affect_refusal/data`) **or** rebuild matched sets, then re-run Cell 10 recipe (no `.pt` exists — confirmed in Colab)
2. Decide projection/steer convention: her mean-over-layers + window `[8,20)` vs single mid-layer (see `docs/charlotte-colab-extract.md`)
3. Syed: copy `results/stage_c/caption_readout{,_rich}.parquet` from his runtime (or regenerate) — not in notebook, not on GitHub
4. Fresh Colab MCP token+port for Arnav notebook
5. Grok API key in `.env` (judge)
