# Overnight advisor orders

[[sycophancy-affect-experiment]] [[MAGNITUDE_GAP]]

1. **Waiters:** poll `nvidia-smi` every 120 seconds (60–180 seconds with jitter is acceptable). Keep at most four live Gemma loads. Claim the first card that is actually free; prefer GPU 2 after exp06 exits because it is the only recently proven healthy scorer. Never displace exp06 or another live battery process.
2. **Zombie cleanup:** a PID may be killed only when `nvidia-smi` labels it `[Not Found]` and a fresh process check confirms it is not any live battery Python job. Otherwise, do not kill it. Do not attempt another GPU reset.
3. **Morning cuts:** protect exp06 and exp04. Cut unfinished work in this order: exp10, exp08, exp09, then exp02. Reserve the final two hours for finite-result checks, hashes, and off-host copies.
4. **Scientific guardrails:** Likert remains secondary and cannot rescue or veto a valid primary endpoint. Never overwrite `artifacts/colab/e2e_mechanism_results_full_v3.json`; exp10 may only read the frozen v3 inputs.
