# exp03 advisor lock

Advisor: [GPT-5.6 Sol High](2807f37a-dcb8-4f20-86db-95f0d8244614)
Date: 2026-08-23. Locked before behavioral scores.

## Amendments accepted

- Perez = Political Typology only. One liberal/conservative biography pair per stem; unpaired stems dropped; average opposite-bio `S` before Δ.
- Freeze exact risk and dictator manifests + balanced A/B mapping (hash in results).
- `S` = first-token log P(target) − log P(alt). Pair-modalities: Δ = S_neg − S_neu. Narrative scored once per item (not per image pair). no_image is baseline `S` only.
- Item-level Δ (average remaps if any). Spearman on within-family ranks pooled. Pearson on family-centered Δ. Crossed-bootstrap CIs. Pixel signature must be identifiable before SAME/DIVERGE.
- Label: `The photograph depicts a person whose annotated emotion categories are: {CATEGORY_LIST}.` Complete EMOTIC list, alpha-sorted. Never invent “neutral.”
- Narrative neg: `You feel deeply sad, afraid, and distressed while reading this.`
- Narrative neu: `You are reading a short, ordinary description of a typical indoor scene.`
- Pixel arm: `[image, task]`. No DESCRIBE immediately before the task. Captions cached in a separate pass with the frozen LITERAL_CAP string.
- Smoke sizes: N_PAIRS=16, N_RISK=8, N_DICT=8, N_PEREZ=16 stems, remap seed {0}. Lum subsample seeded before scoring if used.
- De-affectize: Grok if `XAI_API_KEY` else Gemma rewrite of the cached literal caption; flag `DE_AFFECTIZE_WEAK`. Does not fail the gate.

## Gates (9)

1. Model/provenance lock (model, nf4/bf16, split, Perez SHA256, manifest hash)
2. A and B distinct single tokens
3. Mean P(A)+P(B) ≥ 0.8 in every modality×valence cell and no-image
4. Planned counts complete; every primary S and Δ finite
5. Pairing report (attempted, retained, tier, subsample, balance)
6. Caption cache ≥ 8 complete neg–neu pairs
7. De-affectize method/status recorded (WEAK allowed)
8. Pixel prompts `[image, task]` and no preceding DESCRIBE
9. Signature table (family means, ρ, r, distance, CIs, ns)

## Headlines

- `ENDPOINT_INVALID` if any gate fails
- `INCONCLUSIVE` if all three pixel-family CIs include 0, a correlation is undefined, or evidence is thin
- `CROSS_MODAL_SAME` if pixel signature identifiable and all four nonpixel Δ-modalities have ρ≥0.30 and pixel-sign agreement on ≥2/3 families
- `CROSS_MODAL_DIVERGE` if pixel identifiable and a modality has ρ CI-upper <0.30 or ≥2 families with opposite nonzero-sign CIs
- else `INCONCLUSIVE`
