# exp09 advisor lock

Spawned `gpt-5.6-sol-high` as [Review](14a1e2b3-ce6c-491c-89b8-618f1525ed83). Fable 5 unavailable.

**Verdict: AMEND**

- n_safe=250 unique XSTest safe prompts; 1500 paired evaluations (6 conditions)
- n_img=40 unique (8 per fear/anger/sad/happy/neutral), eval-split single-label, deterministic rid sort
- Unsafe contrast: exactly 8 fixed items, no-image only, first-token sanity, not the DV
- Headline remains first-token refuse (score>0) on BENIGN items
- Image-cluster bootstrap for image conditions; prompt bootstrap for no-image
- Hard gates: source_ok, n_benign, image_pool_ok, conditions_complete, scores_finite, first_token_locked, split_pin, model_pin, no_describe, no_v3_touch, no_completions, dv_is_benign
- Notes: ceiling (all rates ≥0.95), scorer_sane (unsafe-8 > benign no-image)

Implemented in `scripts/battery_exp09_run.py`.
