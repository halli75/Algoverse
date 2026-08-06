# Agent 20m loop checklist

On every tick, record answers in `e2e_run_journal.md`.

## Pace vs plan
- [ ] Process alive OR finished
- [ ] Heartbeat age < 25 min (else hang)
- [ ] Phase matches expected order: A→B→C→D(Step2)→E(3)→F(4)→H(1)→G(5)→I(6 skip)→J(7)
- [ ] ETA still plausible; intervene if stalled

## Completeness (stop only when ALL true)
- [ ] `finished` timestamp set
- [ ] Log contains `E2E_COMPLETE`
- [ ] `phases.D_step2.decision` present
- [ ] If not STOP: E/F/G/H/J present; I may be skipped with reason
- [ ] `headline` has kill_switch, ratio_a, ratio_h, gap_ratio
- [ ] `C_validate_r`: harmless_plus_r > harmless_base (r works)
- [ ] No NaN in key ratios (or explicit documented skip)
- [ ] Journal has final verification block
