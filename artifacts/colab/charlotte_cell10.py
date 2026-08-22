import pandas as pd, glob
from PIL import Image
def load_prompts(f, n):
    d = pd.read_csv(f"{DATA_DIR}/{f}"); col = "prompt" if "prompt" in d.columns else d.columns[0]
    return d[col].astype(str).tolist()[:n]
def load_imgs(fold, n):
    ps = sorted(glob.glob(f"{DATA_DIR}/{fold}/*.jpg") + glob.glob(f"{DATA_DIR}/{fold}/*.png"))
    return [Image.open(p).convert("RGB") for p in ps[:n]]
harmful_train  = load_prompts("harmful_train.csv", N_DIR)
harmless_train = load_prompts("harmless_train.csv", N_DIR)
harmful_eval   = load_prompts("harmful_eval.csv", N_EVAL)
img_neg, img_neu, img_benign = load_imgs("images_negative", N_IMG), load_imgs("images_neutral", N_IMG), load_imgs("images_benign_emotional", N_IMG)
print("prompts:", len(harmful_train), len(harmless_train), len(harmful_eval), "| imgs:", len(img_neg), len(img_neu), len(img_benign))

# refusal direction r = mean(harmful) - mean(harmless), per layer
Rh = torch.stack([resid_layers(build_inputs(p)) for p in harmful_train]).mean(0)
Rn = torch.stack([resid_layers(build_inputs(p)) for p in harmless_train]).mean(0)
r_dir = (Rh - Rn); r_dir = r_dir / r_dir.norm(dim=-1, keepdim=True).clamp_min(1e-6)
# affect direction a = mean(neg images) - mean(neutral images), per layer
DESCRIBE = "Describe what is happening in this image."
An = torch.stack([resid_layers(build_inputs(DESCRIBE, im)) for im in img_neg]).mean(0)
Au = torch.stack([resid_layers(build_inputs(DESCRIBE, im)) for im in img_neu]).mean(0)
a_dir = (An - Au); a_dir = a_dir / a_dir.norm(dim=-1, keepdim=True).clamp_min(1e-6)
# a orthogonalized against r
a_perp = []
for l in range(len(LAYER_KEYS)):
    rhat = (r_dir[l]/r_dir[l].norm()).float(); v = a_dir[l].float(); vp = v - (v@rhat)*rhat
    a_perp.append(vp / vp.norm().clamp_min(1e-6))
# per-layer residual norm (for norm-scaled steering)
_i, _e = _split(build_inputs(harmful_eval[0]))
with torch.no_grad(): _, _cc = model.run_with_cache(_i, names_filter=lambda n: n in set(LAYER_KEYS), **_e)
norms = np.array([float((_cc[k][0,-1] if _cc[k].ndim==3 else _cc[k][-1]).norm()) for k in LAYER_KEYS])
def steer(dirs, a): return [(LAYER_KEYS[l], add_hook(dirs[l], a * norms[l])) for l in range(len(LAYER_KEYS))]
cos_ar = float(np.mean([abs(float(a_dir[l]@r_dir[l]/(a_dir[l].norm()*r_dir[l].norm()))) for l in range(len(LAYER_KEYS))]))
print("residual norm min/median/max: %.0f / %.0f / %.0f | mean|cos(a,r)|=%.3f" % (norms.min(), np.median(norms), norms.max(), cos_ar))