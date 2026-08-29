# Battery v2 board

GPU: NVIDIA RTX PRO 6000 Blackwell Server Edition (96 GB, $2.09/h). RTX PRO 4500 is not compatible.

Orchestrator: `scripts/battery_v2_orchestrate.py` (always terminate in finally).
15-minute ticks print `AGENT_LOOP_TICK_battery_v2`.
Results pull: `artifacts/battery_v2/from_pod/`.

Advisor: GPT-5.6 Sol High. Launch after AMEND patches (CROSS_MODAL CI rule, separate mech tracks, balanced 8-arm pools + independent pair pools, exclusive GPU pin, teardown).
