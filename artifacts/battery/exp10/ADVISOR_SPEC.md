# exp10 locked identification (advisor gpt-5.6-sol-high)

Advisor: [mediation identification](d91ea330-125f-4cf1-a296-72578037c046). Fable 5 unavailable.

1. Unit = one behavioral item + one preselected negative–neutral EMOTIC science-eval pair. X=1 negative, X=0 neutral. Primary ΔY = Y_neg − Y_neu. No-image is secondary.
2. Primary M is frozen-v3 joint `a_perp` projected at the last prompt token over layers [10,25) on the **same behavioral forward**. No DESCRIBE text in that chat. DESCRIBE projection is a diagnostic only.
3. Outcomes: risk P(risky); dictator expected dollars given; Perez P(sycophantic letter). Forced-choice letter mass. No Likert.
4. Do not refit directions. Eval images must be disjoint from direction train. Freeze pairs before scoring.
5. Primary test = paired product-of-coefficients: a=mean(ΔM), c=mean(ΔY), b from ΔY ~ ΔM, indirect ab. Baron–Kenny / residualization / Pearson / Spearman are diagnostics.
6. Domain is `CORRELATIONAL_MEDIATION_SUPPORTED` only if a CI is entirely above 0, c and b and ab CIs exclude 0, sign(ab)=sign(c), Holm-survives across domains, and validity gates pass. ab without c is `INDIRECT_ASSOCIATION_ONLY`.
7. n<64 complete pairs per domain = `INSUFFICIENT_POWER`. Zero ΔM variance = `NO_MEDIATOR_MOVEMENT`. Zero ΔY variance = `NO_BEHAVIOR_CHANGE`. CI overlap at adequate n = `NO_EVIDENCE`.
8. `FROZEN_V3_EXACT` requires the original `e2e_dirs_mechanism.pt` with shape/model/cosine continuity. Any rebuild is permanently `DIAGNOSTIC_NOT_V3` and cannot be promoted. Never write `e2e_mechanism_results_full_v3.json`.

Mechanism-answer template is implemented in `scripts/battery_probe_aperp.py`.
