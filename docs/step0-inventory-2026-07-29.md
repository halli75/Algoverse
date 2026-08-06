# Step 0 inventory — 2026-07-29

Colab: https://colab.research.google.com/drive/1zAoSyYTIfTEER56WJU0KN2iklYYVNtXi  
Runtime: T4 GPU connected. Cell `# ### STEP0_INVENTORY` executed ~3:38 PM (~4.4s).

```
STEP0_INVENTORY
python 3.12.13
torch 2.11.0+cu128 cuda True
gpu Tesla T4
vram_free_gb 15.53 / 15.64
mm_model: NO
train_df: NO
recog_vecs: NO
own_vecs: NO
single_pools: NO
neutral_rows: NO
make_add_hook: NO
get_logits: NO
STEER_HOOK: NO
EMOTION_TO_WORD: NO
load_row_image: NO
Annotations.zip False
emotic_data False
```

## Verdict

Kernel is cold: no model, no EMOTIC tables/helpers, no `Annotations.zip` / `emotic_data` on the runtime filesystem. VRAM almost fully free confirms Gemma is not loaded.

**Blocked on user decision before Step 2 kill switch:** rebuild (~40 min) requires re-upload of `Annotations.zip` (and any other local data) after reset/re-run of setup cells.
