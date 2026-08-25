# exp02 advisor request

Spawned `generalPurpose` model `gpt-5.6-sol-high` (Fable 5 unavailable).

Advisor id: [GPT-5.6 Sol High](2ebc4933-bcc2-4967-af4f-05ceb379a2ed)

Locked decisions implemented in `scripts/battery_exp02_pairs.py` and `scripts/battery_exp02_run.py`:

1. Exclusive targets: `T = labels ∩ {Fear, Anger, Sadness, Happiness}`; Fear iff `T=={Fear}` (Anxiety may co-occur). Dual-target images enter no pool.
2. Neutral = valence 4–6 and `T` empty. Negative = valence < 4 and `T` empty.
3. Families in priority order; reuse across families, never within.
4. Min-cost matching within `(Folder, pbin)`, tightest caliper tier, n=96 / min 64.
5. SEMANTIC_CONFOUND only when exp01 unmatched effect exists, matched same-direction CI fails, and attenuation CI is positive. Else `EXP01_PENDING`.
6. Same Economicus risk + Forsythe dictator A/B items as exp01/exp05/exp08. No DESCRIBE. Forced-choice only.

Amendment after T-singleton underpowered fear↔anger (n=23): [GPT-5.6 Sol High](b1cf31c5-f238-4ed7-994c-3dcf88a7980e) locked rule A.
Fear := Fear ∈ labels ∧ Anger ∉ labels. Anger := Anger ∈ labels ∧ Fear ∉ labels. Co-labels allowed. Neutral/negative stay T-empty. Calipers/n gates unchanged.

Eval-only Folder overlap caps fear↔anger at 47 even before calipers (mscoco 13 + framesdb 17 + emodb 17). Plan text: below 64 abort, source more images. Expanding aborting families to train+eval without loosening calipers.
