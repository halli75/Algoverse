# Graded Sycophancy Experiment

[[sycophancy-affect-experiment]]

## Plan
- [x] Write preregistration: `docs/sycophancy_affect_plan.md` (original freeze sha256 `051e1ea79cd116fce56edeb43848ae10526e2830efc49ab0df2cd7d904a20876`)
- [x] Freeze eval-only custom claims `data/sycophancy_custom_claims.json` (n=160) — **dropped from eval 2026-08-22; file kept as provenance**
- [x] Freeze GoEmotions VA bank + affect lexicon — GoEmotions bank is provenance only after 2026-08-22
- [x] Implement `scripts/e2e_sycophancy_affect.py` + `scripts/_restore_sycophancy_boot.py`
- [x] Advisor [GPT-5.6 Sol High](d57c167c-11a6-4ee0-aa44-08c93a6b59cd) **AMEND** 2026-08-17 (keep all numeric thresholds; Likert endpoint-local; p-band diagnostic; detection-power not conjunction-at-boundary)
- [x] Advisor [GPT-5.6 Sol High](83939084-c3c0-4755-b2ad-37292336a71d) **AMEND-IMPLEMENTATION** 2026-08-18: fit A on V-orthogonal residuals; keep `r>=0.7`
- [x] Advisor **AMEND 2026-08-22** (dataset/path lock; do not retune gates):
  - Confirmatory: Perez PhilPapers + Political Typology only; pin Perez SHA256; die on mismatch
  - Secondary: Perez NLP; Sharma `answer.jsonl` + `are_you_sure.jsonl` (native/Grok only). Smoke `N_FREEFORM=0`
  - `N_CUSTOM=0`; drop custom claims from eval/calibration/relevance; keep file as provenance
  - Drop Sharma `feedback.jsonl`
  - VA: JULIELab EmoBank human VAD (commit `248ce2a43e165a66d31aeaed83cff9641d6654e0`); fit train, gate test; same estimator; `r>=0.7`
  - Env paths: `E2E_ROOT` (default `/content`; JupyterHub `~/algoverse_run`), `E2E_OUT`, `E2E_HB`, `E2E_DIRS`, `E2E_SPLIT`, `E2E_EMOTIC`, `E2E_DATA`
  - Never overwrite `artifacts/colab/e2e_mechanism_results_full_v3.json`
  - Original prereg hash unchanged
  - Plan file hash `bb892bbdddf9be5965f8a583a7682ad2a8019b265b088be8bc97df7db9978fc3`
  - Amendment hash `e7fb263a24cd8db0cfd3e3616c18f66167b0d54f6bd84bbd189598b0788137d1` (2026-08-22 section including HTML markers)
- [x] A100 JupyterHub boot: `scripts/a100_sycophancy_boot.py` + cell `scripts/a100_sycophancy_cell.py` (clone/pull `halli75/Algoverse`; no Colab userdata)
- [ ] T4/A100 smoke with EmoBank VA + Perez pins (`N_CUSTOM=0`, `N_FREEFORM=0`)
- [ ] A100 staged full run — only if smoke VA `r>=0.7` and projected detection power ≥ 0.80
- [ ] Analyze / publish artifact under `artifacts/colab/` without overwriting refusal v3

## Frozen gates (do not retune)
FC mass 0.8 → `ENDPOINT_INVALID`. Likert 0.8 → `LIKERT_INVALID` only. `r_v`/`r_a` ≥ 0.7. `s` ρ ≥ 0.3. Power 0.80. ΔS ≥ 0.20.

## A100 JupyterHub
1. Set `HF_TOKEN` (and `XAI_API_KEY` if full Grok).
2. `E2E_ROOT=~/algoverse_run` `E2E_TIER=smoke` (or `full`).
3. Run `scripts/a100_sycophancy_cell.py` in the notebook (prints `nvidia-smi`, execs boot).
4. Boot clones/pulls `halli75/Algoverse`, restores EMOTIC if needed, runs `e2e_sycophancy_affect.py`.

## Leakage wall
Custom claims are **not used**. `s` fits on public direction-train only. V/A fit on EmoBank `train`, gated on EmoBank `test`.

## Review
- Protocol frozen 2026-08-15 before confirmatory scores. Prereg sha256 `051e1ea79cd116fce56edeb43848ae10526e2830efc49ab0df2cd7d904a20876`.
- Advisor [GPT-5.6 Sol High](d57c167c-11a6-4ee0-aa44-08c93a6b59cd): first review NO-GO. Smoke-blocker fixes applied (opposite bios, native scorer+masks, single-token IDs, stem rule, person-count aggregation, Likert/FC mass abort, VA/s residualize+spearman+abort, power SD).
- Gist pinned `34eb7bc8e3f185478a9b438750da40321a5ad662`.
- This run replaces remaining optional refusal robustness phases.
- Refusal v3 artifact stays frozen: `artifacts/colab/e2e_mechanism_results_full_v3.json`
- Colab tab recovered. Cell 0 injected (gist `c03a3447…/_sycophancy_colab_cell.py`). T4 selected and saved.
- User bought Colab credits 2026-08-17. T4 connected; cell 0 sycophancy smoke executed ~21:47–22:06 ET.
- Tick 2 (22:17 ET): smoke **aborted**. FC mass 0.989 pass; Likert mass 0.181 fail; headroom 0.183 < 0.25. Model/gist/split pins held. Cell 0 spinner stale; kernel idle. Not re-run.
- Advisor [GPT-5.6 Sol High](d57c167c-11a6-4ee0-aa44-08c93a6b59cd) 2026-08-17 **AMEND**: do not lower 0.8/0.20/0.25/0.80. Likert mass failure is `LIKERT_INVALID` only. Probability-band `p_in_band` is `CEILING_NOTE`, not a hard stop (confirmatory estimand is log-odds). Detection power = Pr(CI low>0 and both benchmarks and native positive) at true ΔS=0.20; do not require simulated mean≥0.20. Original prereg hash preserved; plan-file hash `834cd895…`. T4 smoke re-launched on pin `b8bdcca2…` / cell `05e6258b…`.
- Advisor 2026-08-22 **AMEND**: dataset/path lock for JupyterHub A100. Custom claims and invented GoEmotions V/A out of the experiment. EmoBank human VAD in. Perez SHA256 pins. Sharma feedback dropped. Thresholds unchanged.
