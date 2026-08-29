# Interpretability as a Science (NeurIPS 2026) draft

Anonymous NeurIPS 2026 workshop submission (`dblblindworkshop`).
Style follows the NeurIPS 2026 instructions PDF (`neurips_2026.sty`).

**Workshop:** [Interpretability as a Science](https://interpscience.github.io/) (Sydney).
Long paper: up to 9 content pages. Deadline on the CFP: 1 September 2026 AoE
(28 August was crossed out).

## Build

```bash
python figures/make_figures.py
pdflatex -interaction=nonstopmode main
bibtex main
pdflatex -interaction=nonstopmode main
pdflatex -interaction=nonstopmode main
```

## What the paper is allowed to claim

See the six-agent audit in the parent conversation. Short version:

- Photo-present extra caution on locked XSTest (E4B and 12B). Neutral is a photo arm.
- Harmful-prompt refuse stays at ceiling (frozen v3 + Gemma-3 writeup).
- Image-built `ratio_a=1.591` is withdrawn as "images > text".
- Frozen v3: `MAGNITUDE_GAP`, `M1_causal=false`.
- Named-emotion ladders, ultimatum reject, and v2 mediation do **not** hold.
- Do not say images induce emotion. Do not pool EMOTIC and OASIS.
- Do not treat E4B vs 12B as scale. Do not treat Neutral as Peace.
- `"I"` is not refuse on the locked scorer.

## What was analyzed and is not in the main claim

- Battery v1: exploratory, no `LOCK.json`. Directionally supports exp09 only.
- OASIS v2: not on disk.
- Charlotte / Syed tensors: never exported. Writeup numbers only.
- EmoBank-VA sycophancy: aborted.
