# Graded Sycophancy Experiment

[[sycophancy-affect-experiment]]

## Plan
- [x] Write preregistration: `docs/sycophancy_affect_plan.md` (sha256 `051e1ea79cd116fce56edeb43848ae10526e2830efc49ab0df2cd7d904a20876`)
- [x] Freeze eval-only custom claims `data/sycophancy_custom_claims.json` (n=160)
- [x] Freeze GoEmotions VA bank + affect lexicon
- [x] Implement `scripts/e2e_sycophancy_affect.py` + `scripts/_restore_sycophancy_boot.py`
- [x] Advisor [GPT-5.6 Sol High](d57c167c-11a6-4ee0-aa44-08c93a6b59cd) **AMEND** 2026-08-17 (keep all numeric thresholds; Likert endpoint-local; p-band diagnostic; detection-power not conjunction-at-boundary)
- [x] Advisor [GPT-5.6 Sol High](83939084-c3c0-4755-b2ad-37292336a71d) **AMEND-IMPLEMENTATION** 2026-08-18: fit A on V-orthogonal residuals; keep `r>=0.7`
- [ ] T4 smoke re-run (VA construction repair; cell pin `2bfc44d9…`, script pin `0a19bbfb…`) — connecting
- [ ] A100 staged full run — only if smoke VA passes and projected detection power ≥ 0.80
- [ ] Analyze / publish artifact under `artifacts/colab/` without overwriting refusal v3

## Leakage wall
Custom claims are **eval-only**. `s`, V, A never fit on them.

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
