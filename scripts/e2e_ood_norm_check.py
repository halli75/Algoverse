# ### E2E_OOD — residual-norm / color-square artifact diagnostic (plan gate 6)
# Standalone Colab runner. Does NOT re-run kill/gap/γ.
# Outputs: /content/e2e_ood_norm.json
# Decision: PASS / FAIL_COLORLIKE / FAIL_NORM_INFLATION
# Also recomputes ratio_a on unit-normalized activations (ratio_a_unit).
#
# Env: E2E_OOD_N=16  E2E_PREREG_HASH=...  E2E_NO_FALLBACK=1

from __future__ import annotations

import hashlib
import json
import os
import random
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np
import torch
from PIL import Image

OUT = Path("/content/e2e_ood_norm.json")
HB = Path("/content/e2e_heartbeat.json")
SPLIT_PATH = Path("/content/emotic_split.json")
DIRS_PATH = Path("/content/e2e_dirs_publish.pt")
EMOTIC_ROOT = Path("/content/emotic_data")
T0 = time.time()
SEED = 0
N = int(os.environ.get("E2E_OOD_N", "16"))
DEVICE = "cuda"
PRIMARY = "google/gemma-4-E4B-it"
DESCRIBE = "Describe what is happening in this image."
DISTRESS = "You feel deeply sad, afraid, and distressed while reading this."
MUNDANE = "Describe a mundane gray wall in a quiet empty room."

RESULT = {
    "started": time.strftime("%Y-%m-%d %H:%M:%S"),
    "plan_gate": 6,
    "prereg_hash": os.environ.get("E2E_PREREG_HASH", "3111c3af7f7b12656cb0792bea4a21b4302a0c42"),
    "n": N,
}


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def heartbeat(stage: str, **kw) -> None:
    payload = {
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "unix": time.time(),
        "stage": stage,
        "elapsed_s": time.time() - T0,
        **kw,
    }
    HB.write_text(json.dumps(payload), encoding="utf-8")


def save() -> None:
    RESULT["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    OUT.write_text(json.dumps(RESULT, indent=2, default=str), encoding="utf-8")
    log(f"saved {OUT}")


def die(msg: str) -> None:
    log(f"FATAL: {msg}")
    RESULT["fatal"] = msg
    RESULT["decision"] = "FAIL"
    save()
    raise SystemExit(1)


def summarize(vals):
    a = np.asarray(vals, dtype=float)
    if a.size == 0:
        return {"n": 0}
    return {
        "n": int(a.size),
        "median": float(np.median(a)),
        "mean": float(np.mean(a)),
        "p90": float(np.percentile(a, 90)),
        "max": float(np.max(a)),
        "min": float(np.min(a)),
    }


# ---------------------------------------------------------------------------
# Secrets + GPU
# ---------------------------------------------------------------------------
heartbeat("ood_start")
try:
    from google.colab import userdata  # type: ignore

    for k in ("HF_TOKEN", "XAI_API_KEY"):
        if not os.environ.get(k):
            try:
                os.environ[k] = userdata.get(k)
            except Exception:
                pass
except Exception:
    pass

if not torch.cuda.is_available():
    die("no CUDA")
gpu = torch.cuda.get_device_name(0)
log(f"gpu={gpu}")
RESULT["gpu"] = gpu

# ---------------------------------------------------------------------------
# Deps (minimal; match publish pipeline)
# ---------------------------------------------------------------------------
import subprocess

log("pip ensure")
subprocess.check_call(
    [
        sys.executable,
        "-m",
        "pip",
        "install",
        "-q",
        "git+https://github.com/TransformerLensOrg/TransformerLens.git",
        "bitsandbytes>=0.46.1",
        "accelerate",
        "pillow",
        "pandas",
        "huggingface_hub",
    ],
)
try:
    from transformers.utils.import_utils import is_bitsandbytes_available

    is_bitsandbytes_available.cache_clear()
except Exception:
    pass
from transformer_lens.model_bridge import TransformerBridge  # noqa: E402

# ---------------------------------------------------------------------------
# EMOTIC pools from existing split
# ---------------------------------------------------------------------------
import pandas as pd
import ast

csv_path = EMOTIC_ROOT / "emotic_pre" / "train.csv"
if not csv_path.exists():
    die(f"missing {csv_path} — restore EMOTIC annotations first")
if not (EMOTIC_ROOT / "emotic").exists():
    die("missing /content/emotic_data/emotic images")

df = pd.read_csv(csv_path)
# light parse of labels if needed
if "Categorical_Labels" in df.columns and isinstance(df.iloc[0]["Categorical_Labels"], str):
    df["Categorical_Labels"] = df["Categorical_Labels"].apply(
        lambda x: ast.literal_eval(x) if isinstance(x, str) and x.startswith("[") else x
    )


def row_id(row) -> str:
    return f"{row['Folder']}/{row['Filename']}"


def load_row_image(row):
    p = EMOTIC_ROOT / "emotic" / row["Folder"] / row["Filename"]
    return Image.open(p).convert("RGB")


for col in ("Categorical_Labels", "Continuous_Labels", "VAD", "BBox", "Image Size"):
    if col in df.columns:
        df[col] = df[col].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) and str(x).startswith("[") else x)

NEG = {"Anger", "Sadness", "Fear", "Disgust", "Suffering", "Anxiety", "Embarrassment", "Pain"}
POS = {"Happiness", "Pleasure", "Excitement", "Affection", "Esteem", "Anticipation"}
NEU = {"Peace", "Engagement", "Confidence", "Doubt/Confusion", "Sympathy", "Yearning"}


def _labs(row) -> set:
    lab = row.get("Categorical_Labels", [])
    return set(lab) if isinstance(lab, (list, tuple, set)) else set()


def _valence(row) -> str:
    vad = row.get("Continuous_Labels") or row.get("VAD")
    if isinstance(vad, (list, tuple)) and vad:
        try:
            v = float(vad[0])
            if v < 4.0:
                return "neg"
            if v > 6.0:
                return "pos"
            return "neu"
        except Exception:
            pass
    labs = _labs(row)
    n_neg, n_pos, n_neu = len(labs & NEG), len(labs & POS), len(labs & NEU)
    if n_neg == n_pos == n_neu == 0:
        return "neu"
    best = max([("neg", n_neg), ("pos", n_pos), ("neu", n_neu)], key=lambda t: t[1])
    ties = [k for k, v in [("neg", n_neg), ("pos", n_pos), ("neu", n_neu)] if v == best[1]]
    if len(ties) > 1:
        for pref in ("neu", "neg", "pos"):
            if pref in ties:
                return pref
    return best[0]


df = df.copy()
df["rid"] = df.apply(row_id, axis=1)
if not SPLIT_PATH.exists():
    die("missing emotic_split.json — need same split as full run")
split = json.loads(SPLIT_PATH.read_text(encoding="utf-8"))
split_hash = hashlib.sha256(json.dumps(split, sort_keys=True).encode()).hexdigest()[:16]
RESULT["split_hash"] = split_hash
# Match publish image_bucket_v1: one bucket per image id
_img_buckets = {}
for rid, g in df.groupby("rid", sort=False):
    vals = []
    for _, row in g.iterrows():
        vad = row.get("Continuous_Labels") or row.get("VAD")
        if isinstance(vad, (list, tuple)) and vad:
            try:
                vals.append(float(vad[0]))
            except Exception:
                pass
    if vals:
        mv = sum(vals) / len(vals)
        if mv < 4.0:
            _img_buckets[rid] = "neg"
        elif mv > 6.0:
            _img_buckets[rid] = "pos"
        else:
            _img_buckets[rid] = "neu"
    else:
        _img_buckets[rid] = _valence(g.iloc[0])
df["bucket"] = df["rid"].map(_img_buckets)
df = df.drop_duplicates(subset=["rid"], keep="first").reset_index(drop=True)
train_df = df[df.rid.isin(set(split["train_ids"]))]
eval_df = df[df.rid.isin(set(split["eval_ids"]))]
neg_eval = eval_df[eval_df.bucket == "neg"]
neu_eval = eval_df[eval_df.bucket == "neu"]
pos_eval = eval_df[eval_df.bucket == "pos"]
neu_train = train_df[train_df.bucket == "neu"]
log(f"pools neg_ev={len(neg_eval)} neu_ev={len(neu_eval)} pos_ev={len(pos_eval)} neu_tr={len(neu_train)}")
if len(neg_eval) < 4 or len(neu_eval) < 4 or len(neu_train) < 4:
    die(f"pools too small for OOD check: neg_ev={len(neg_eval)} neu_ev={len(neu_eval)} neu_tr={len(neu_train)}")


def sample_imgs(frame, n):
    take = min(n, len(frame))
    rows = frame.sample(n=take, random_state=SEED)
    return [load_row_image(r) for _, r in rows.iterrows()]


img_ref = sample_imgs(neu_train, N)
img_neg = sample_imgs(neg_eval, N)
img_neu = sample_imgs(neu_eval, N)
img_pos = sample_imgs(pos_eval, N) if len(pos_eval) else img_neu

# synthetic solid-color OOD controls (the known failure mode)
solids = []
for rgb in [(0, 0, 0), (128, 128, 128), (255, 220, 0), (180, 0, 0), (0, 0, 180), (255, 255, 255)]:
    solids.append(Image.new("RGB", (512, 512), rgb))

# ---------------------------------------------------------------------------
# Load model (nf4, same as publish)
# ---------------------------------------------------------------------------
heartbeat("ood_model_load")
try:
    from transformers.utils.import_utils import is_bitsandbytes_available

    is_bitsandbytes_available.cache_clear()
except Exception:
    pass
from transformers import AutoProcessor, BitsAndBytesConfig, AutoModelForImageTextToText

mid = os.environ.get("E2E_MODEL", PRIMARY)
log(f"loading {mid} nf4")
bnb = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
)
token = os.environ.get("HF_TOKEN") or True
hf_model = AutoModelForImageTextToText.from_pretrained(
    mid,
    quantization_config=bnb,
    device_map={"": 0},
    torch_dtype=torch.bfloat16,
    token=token,
)
# TransformerBridge bootstrap — match publish pipeline
try:
    model = TransformerBridge.boot_transformers(mid, hf_model=hf_model, dtype=torch.bfloat16, device=DEVICE)
except Exception:
    # fallback: wrap via HookedTransformer if bridge API differs
    from transformer_lens import HookedTransformer

    model = HookedTransformer.from_pretrained(mid, hf_model=hf_model, dtype=torch.bfloat16, device=DEVICE)

try:
    model.processor = AutoProcessor.from_pretrained(mid, token=token)
except Exception as e:
    log(f"processor attach failed: {e}")
model.eval()
for p in model.parameters():
    p.requires_grad = False
proc = getattr(model, "processor", None)
tokn = model.tokenizer
n_layers = int(model.cfg.n_layers)
d_model = int(model.cfg.d_model)
RESULT["model"] = {"id": mid, "n_layers": n_layers, "d_model": d_model}
log(f"model ready layers={n_layers} d={d_model}")


def build_inputs(text, image=None):
    p = proc or getattr(model, "processor", None)
    if image is not None and p is not None and hasattr(p, "apply_chat_template"):
        content = [{"type": "image"}, {"type": "text", "text": text}]
        prompt = p.apply_chat_template(
            [{"role": "user", "content": content}],
            add_generation_prompt=True,
            tokenize=False,
        )
        return dict(p(text=[prompt], images=[image], return_tensors="pt"))
    if p is not None and hasattr(p, "apply_chat_template") and image is None:
        prompt = p.apply_chat_template(
            [{"role": "user", "content": [{"type": "text", "text": text}]}],
            add_generation_prompt=True,
            tokenize=False,
        )
        return dict(p(text=[prompt], return_tensors="pt"))
    return {"input_ids": tokn(text, return_tensors="pt").input_ids}


def _split(inp):
    ids = inp["input_ids"].to(DEVICE)
    return ids, {k: (v.to(DEVICE) if torch.is_tensor(v) else v) for k, v in inp.items() if k != "input_ids"}


_ids, _ex = _split(build_inputs("hello"))
with torch.no_grad():
    _, _c = model.run_with_cache(_ids, names_filter=lambda n: "resid_post" in n, **_ex)


def _blk(k):
    part = k.split("blocks.")[-1].split(".")[0]
    return int(part) if part.isdigit() else -1


_dims = [_c[k].shape[-1] for k in _c]
D = d_model if d_model in _dims else max(set(_dims), key=_dims.count)
LAYER_KEYS = sorted([k for k in _c if "resid_post" in k and _c[k].shape[-1] == D], key=_blk)
if not LAYER_KEYS:
    die("no resid_post hooks")


def resid_layers(inp):
    ids, ex = _split(inp)
    with torch.no_grad():
        _, c = model.run_with_cache(ids, names_filter=lambda n: "resid_post" in n, **ex)
    return torch.stack([(c[k].float()[0] if c[k].ndim == 3 else c[k].float())[-1].cpu() for k in LAYER_KEYS])


def mean_resid_norm(inp) -> float:
    acts = resid_layers(inp)
    return float(acts.norm(dim=-1).mean())


def layer_resid_norms(inp):
    return resid_layers(inp).norm(dim=-1).tolist()


def mean_proj(inp, dirs) -> float:
    acts = resid_layers(inp)
    vals = []
    for l in range(len(LAYER_KEYS)):
        d = dirs[l].float()
        d = d / d.norm().clamp_min(1e-6)
        vals.append(float(acts[l] @ d))
    return float(np.mean(vals))


def mean_proj_unit(inp, dirs) -> float:
    """Projection after unit-normalizing each layer activation (norm-invariant)."""
    acts = resid_layers(inp)
    vals = []
    for l in range(len(LAYER_KEYS)):
        a = acts[l].float()
        a = a / a.norm().clamp_min(1e-6)
        d = dirs[l].float()
        d = d / d.norm().clamp_min(1e-6)
        vals.append(float(a @ d))
    return float(np.mean(vals))


# ---------------------------------------------------------------------------
# Norm sweep
# ---------------------------------------------------------------------------
heartbeat("ood_norms")
log("computing residual norms")
sets = {
    "text_distress": [build_inputs(DISTRESS) for _ in range(N)],
    "text_mundane": [build_inputs(MUNDANE) for _ in range(N)],
    "photo_ref_neu_train": [build_inputs(DESCRIBE, im) for im in img_ref],
    "science_neg_eval": [build_inputs(DESCRIBE, im) for im in img_neg],
    "science_neu_eval": [build_inputs(DESCRIBE, im) for im in img_neu],
    "science_pos_eval": [build_inputs(DESCRIBE, im) for im in img_pos],
    "solid_color_ood": [build_inputs(DESCRIBE, im) for im in solids],
}

norm_raw = {}
for name, inps in sets.items():
    vals = []
    for i, inp in enumerate(inps):
        heartbeat("ood_norms", set=name, i=i, n=len(inps))
        try:
            vals.append(mean_resid_norm(inp))
        except Exception as e:
            log(f"norm fail {name}[{i}]: {e}")
    norm_raw[name] = vals
    log(f"  {name}: {summarize(vals)}")

norm_summary = {k: summarize(v) for k, v in norm_raw.items()}
RESULT["norm_summary"] = norm_summary

ref_med = norm_summary["photo_ref_neu_train"].get("median") or float("nan")
solid_med = norm_summary["solid_color_ood"].get("median") or float("nan")
sci_vals = (
    norm_raw["science_neg_eval"]
    + norm_raw["science_neu_eval"]
    + norm_raw["science_pos_eval"]
)
sci_med = float(np.median(sci_vals)) if sci_vals else float("nan")
txt_med = float(
    np.median(norm_raw["text_distress"] + norm_raw["text_mundane"])
)

# color-like: science median closer to solid than to photo_ref, OR any science > 0.8*solid_med
# when solid >> photo, OR science/photo_ref > 4x (inflation)
ratio_sci_ref = sci_med / ref_med if ref_med and ref_med > 0 else float("inf")
ratio_solid_ref = solid_med / ref_med if ref_med and ref_med > 0 else float("inf")
dist_sci_ref = abs(sci_med - ref_med)
dist_sci_solid = abs(sci_med - solid_med)
n_colorlike = 0
if solid_med and ref_med and solid_med > 1.5 * ref_med:
    thresh = 0.8 * solid_med
    n_colorlike = int(sum(1 for v in sci_vals if v >= thresh))

fail_colorlike = bool(
    (solid_med > 1.5 * ref_med and dist_sci_solid < dist_sci_ref)
    or (n_colorlike > max(1, len(sci_vals) // 10))
)
fail_inflation = bool(ratio_sci_ref > 4.0)

if fail_colorlike:
    decision = "FAIL_COLORLIKE"
elif fail_inflation:
    decision = "FAIL_NORM_INFLATION"
else:
    decision = "PASS"

RESULT["norm_ratios"] = {
    "ref_median": ref_med,
    "science_median": sci_med,
    "solid_median": solid_med,
    "text_median": txt_med,
    "ratio_science_over_ref": ratio_sci_ref,
    "ratio_solid_over_ref": ratio_solid_ref,
    "n_science_colorlike": n_colorlike,
    "fail_colorlike": fail_colorlike,
    "fail_inflation": fail_inflation,
}
RESULT["decision"] = decision
log(f"OOD_DECISION={decision} sci/ref={ratio_sci_ref:.3f} solid/ref={ratio_solid_ref:.3f}")
save()

# ---------------------------------------------------------------------------
# Corrected ratio_a (unit-normalized activations) if dirs exist
# Prefer /content/e2e_dirs_publish.pt from publish or e2e_rebuild_dirs_ratio_unit.py
# ---------------------------------------------------------------------------
heartbeat("ood_ratio_unit")
if DIRS_PATH.exists():
    blob = torch.load(DIRS_PATH, map_location="cpu", weights_only=False)
    a_perp = blob["a_perp"]
    n_delta = min(N, len(img_neg), len(img_neu))
    base_txt = [mean_proj(build_inputs(DISTRESS), a_perp) for _ in range(n_delta)]
    neu_txt = [mean_proj(build_inputs(MUNDANE), a_perp) for _ in range(n_delta)]
    base_img = [mean_proj(build_inputs(DESCRIBE, im), a_perp) for im in img_neg[:n_delta]]
    neu_img = [mean_proj(build_inputs(DESCRIBE, im), a_perp) for im in img_neu[:n_delta]]
    d_txt = float(np.mean(base_txt) - np.mean(neu_txt))
    d_img = float(np.mean(base_img) - np.mean(neu_img))
    ratio_a_raw = abs(d_img / d_txt) if abs(d_txt) > 1e-6 else float("inf")

    base_txt_u = [mean_proj_unit(build_inputs(DISTRESS), a_perp) for _ in range(n_delta)]
    neu_txt_u = [mean_proj_unit(build_inputs(MUNDANE), a_perp) for _ in range(n_delta)]
    base_img_u = [mean_proj_unit(build_inputs(DESCRIBE, im), a_perp) for im in img_neg[:n_delta]]
    neu_img_u = [mean_proj_unit(build_inputs(DESCRIBE, im), a_perp) for im in img_neu[:n_delta]]
    d_txt_u = float(np.mean(base_txt_u) - np.mean(neu_txt_u))
    d_img_u = float(np.mean(base_img_u) - np.mean(neu_img_u))
    ratio_a_unit = abs(d_img_u / d_txt_u) if abs(d_txt_u) > 1e-6 else float("inf")

    RESULT["ratio_a_recheck"] = {
        "n": n_delta,
        "delta_txt": d_txt,
        "delta_img": d_img,
        "ratio_a_raw": ratio_a_raw,
        "delta_txt_unit": d_txt_u,
        "delta_img_unit": d_img_u,
        "ratio_a_unit": ratio_a_unit,
        "headline_implication": (
            "PASS_AFFECT_SPECIFIC_candidate"
            if ratio_a_unit < 0.05
            else ("INVERTED_persists" if ratio_a_unit > 1.0 else "MIXED_after_norm_correction")
        ),
    }
    log(
        f"ratio_a_raw={ratio_a_raw:.4f} ratio_a_unit={ratio_a_unit:.4f} "
        f"→ {RESULT['ratio_a_recheck']['headline_implication']}"
    )
else:
    RESULT["ratio_a_recheck"] = {
        "skipped": True,
        "reason": "missing e2e_dirs_publish.pt — run e2e_rebuild_dirs_ratio_unit.py",
    }
    log("dirs missing — skip ratio_a_unit recheck (norms-only decision still valid; use rebuild script)")

RESULT["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
RESULT["complete"] = True
heartbeat("ood_complete", decision=decision)
save()
log(f"FINISHED_OK decision={decision}")
print("OOD_NORM_DONE", json.dumps({"decision": decision, "ratio": RESULT.get("ratio_a_recheck")}))
