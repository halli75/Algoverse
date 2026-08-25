# Night orders (do not stop)

Laptop stays on. Overseer 15-min loop stays on until all ten `results.json` have `complete: true` and a `mechanism_answer`.

Done (do not relaunch): exp01, exp03, exp05, exp07.
Must finish: exp02, exp04, exp06, exp08, exp09, exp10.

Rules:
- Do not exit because you are waiting on GPU. Sleep 60–180s, recheck `nvidia-smi`, retry.
- Max 4 live Gemma loads. If RAM/VRAM is full, wait. Do not kill other battery jobs.
- Zombie `[Not Found]` CUDA contexts exist. `nvidia-smi -r` is denied. Wait for a card to actually free, then load.
- Preserve order: exp06 and exp04 first, then exp02, exp09, then exp08, then exp10.
- Advisor: spawn Task `generalPurpose` model `gpt-5.6-sol-high` on any construct, gate, or stall >30 min. Fable 5 unavailable.
- Never overwrite `artifacts/colab/e2e_mechanism_results_full_v3.json`.
- Checkpoint to `artifacts/battery/<id>/` and hub `~/algoverse_run/battery/<id>/` after every slice.
