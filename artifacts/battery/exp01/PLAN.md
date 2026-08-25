# exp01 plan — fear vs anger on risk

Advisor: [design lock](5fcddd21-3be9-4520-bcb6-c863b588975e) (gpt-5.6-sol-high). Fable 5 unavailable.

**Question:** Does depicted fear vs anger (same valence/arousal class, different dominance) shift Gemma-4 P(risky) on forced-choice lotteries?

**Lock**
- Model: `google/gemma-4-E4B-it` nf4 / bf16. GPU 0. No fallback. No steer.
- Images: EMOTIC eval, split hash `1e8ea1c22144dd9d`. Chat `[image, text]`. Do not describe the image.
- DV: P(risky). Secondary: CRRA ρ on fear vs anger.
- Forced-choice A/B only. Economicus gambling CE lists converted to one A/B per item (`data/battery/exp01_lotteries.json`).
- Latin square: image `j = (i + b + c) mod m`. Risky is A iff `(i + j + c) mod 2 == 0`. Seed `20260823`.

**Size**
- smoke: 4 items (1,4,7,10) × 2 images × 6 cats + 4 no-image = 52
- full: 10 items × 12 images × 6 cats + 10 no-image = 730

**Gates (8):** model/hash lock; ≥12 exclusive images/cat (full); fear–anger V/A match + D gap; completion; A/B valid ≥0.95; unique cells + A/B balance; side-letter |Δ|≤0.10; 0.10≤P(risky|fear+anger)≤0.90.

**Inference:** crossed bootstrap 10k (items shared; images within cond). Δ = P(anger) − P(fear).

Host wipe Mon Aug 24 02:45 UTC. Checkpoint `~/algoverse_run/battery/exp01` and `artifacts/battery/exp01/`.
