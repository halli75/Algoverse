# Colab publish journal

## 2026-08-06

- EMOTIC PAMI images on Colab: 23185 jpg, solids=0; Annotations.mat present.
- Implemented `scripts/e2e_publish_pipeline.py` with **primary `google/gemma-4-E4B-it`** (Gemma-3 fallback only on Step-0 gate fail / >2h).
- T4 smoke first (`E2E_TIER=smoke`); A100 only after T4 proves pipeline.
- Monitor loop: every 15 minutes.
