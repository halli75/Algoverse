# Advisor request — exp05 Dictator + Ultimatum

Fable 5 unavailable. Please review with gpt-5.6-sol-high.

## Locked already (do not reopen)

- Model `google/gemma-4-E4B-it` nf4/bf16, GPU 1, split `1e8ea1c22144dd9d`
- No DESCRIBE-before-task, no steer, no v3 overwrite
- Forced-choice letters (not digit Likert)
- Predictions tested vs neutral: sympathy→give more; anger→reject unfair; fear→give less
- Published stems: LLM Economicus UG proposer/responder; Microsoft Turing UG scenario; dictator = Economicus proposer minus veto

## Ask

1. Is expected-dollar = softmax over {A..F} × {0,20,40,50,60,80} the right primary for Gemma-4, vs argmax-only?
2. Keep sympathy and affection separate, or pool if exclusive n is small?
3. Should unfair rejection be pooled 90/10+80/20 or reported separately as co-primaries?
4. Any gate I should add before A100 spend (beyond mass 0.8, n≥16, split, no-DESCRIBE)?

Reply into `artifacts/battery/exp05/ADVISOR_REPLY.md` if this request is picked up after the run starts. Run will not wait: host dies Mon Aug 24 02:45 UTC.
