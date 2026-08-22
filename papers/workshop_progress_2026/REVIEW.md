# Review memo

## Verdict

Useful internal progress report, not submission-ready science. The behavioral null is the strongest result. The Gemma-3-12B gate is credible within its recorded run, but cross-stack mechanism claims remain limited by different models, corpora, quantization, and incomplete uncertainty reporting. The unified method has not been re-run.

## Must-fix, applied

- Separated three estimands that the abstract partly conflated: v3 context suppression (0.107), v3 steer-ceiling reach (0.0050), and Charlotte's roughly 100-fold reachability gap.
- Replaced "published" language for the internal publish-pipeline metric and kept INVERTED explicitly construction-biased.
- Added the recorded LLaVA-OV-7B stability value, 0.652.
- Stated how the v3 95% CI was computed: 1,000 paired-image bootstrap resamples.
- Made the ethics answer direct: short completions were generated for Grok; named JSON artifacts retain aggregate rates rather than completion text.
- Changed unsupported checklist answers to No for full reproducibility, statistical significance coverage, complete compute disclosure, and license auditing.
- Corrected citation metadata. The CAA paper was misattributed to Panickssery instead of Rimsky, the InternVL citation referred to the wrong model generation, the Gemma-4 model-card entry was replaced by the technical report, and the refusal-geometry entry was incomplete.
- Moved the checklist after the technical appendix, as required by the supplied 2026 instructions.
- Softened the Zhou interpretation from a claimed VLM prediction to a tested directional hypothesis.

## Nice-to-have before external circulation

- Record Charlotte's GPU, wall time, exact environment, model revision, dataset revision, and complete run provenance.
- Report uncertainty for the behavioral nulls and repeat the planned three direction rebuilds.
- Run both stacks on the locked shared core. Until then, do not present the unification as empirical replication.
- Audit and name licenses and terms for every checkpoint, dataset, and software version.
- Finish sycophancy only after its endpoint passes validation. Keep the color-square and incomplete EMOTIC runs out of scientific claims.
