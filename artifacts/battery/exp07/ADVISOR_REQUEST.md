# Advisor request — exp07 capability negative control

Status: APPLIED. Advisor [gpt-5.6-sol-high](e829ba59-4e9b-436c-a3b4-eb53f45aedb9) **AMEND**.

## Applied AMEND
- Official Jan-2025 binary TruthfulQA only (not legacy MC1 4-way). Pin n=790 sha256 `b8d8ef1e12f98b4f2a9f47abc9765da0640b182b6c5d9b92f0c1a1f2f1e02e5c` (verified against live CSV).
- Primary conditions: no_image / neutral / negative. Positive excluded from gates/headline.
- Equivalence margin ±0.05. FLAT_ACCURACY iff paired-bootstrap **90%** CIs for neg−none, neu−none, neg−neu are wholly inside [−0.05,+0.05].
- Movement iff 90% CI wholly beyond ±0.05.
- WEAK_FLAT replaced by EQUIVALENCE_INCONCLUSIVE.
- Above-chance: no-image Wilson 95% lower bound > 0.50.
- Smoke n=48 / 2000 boot (pipeline only). Full n=790 / 10000 boot.
- Power note printed in results.notes.

Fable 5 was unavailable. This file kept as the audit trail.
