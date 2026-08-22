# ### E2E_RATIO_UNIT — rebuild a_perp + unit-normalized ratio_a
# Standalone Colab runner. Assumes EMOTIC + emotic_split.json already present.
# Writes: /content/e2e_dirs_publish.pt, /content/e2e_ratio_unit.json
# Env: E2E_TIER=full|medium|smoke  E2E_NO_FALLBACK=1  E2E_PREREG_HASH=...

from __future__ import annotations

import ast
import hashlib
import json
import os
import random
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from PIL import Image

OUT = Path("/content/e2e_ratio_unit.json")
HB = Path("/content/e2e_heartbeat.json")
SPLIT_PATH = Path("/content/emotic_split.json")
DIRS_PATH = Path("/content/e2e_dirs_publish.pt")
EMOTIC_ROOT = Path("/content/emotic_data")
DATA = Path("/content/e2e_data")
T0 = time.time()
SEED = 0
DEVICE = "cuda"
PRIMARY = "google/gemma-4-E4B-it"
DESCRIBE = "Describe what is happening in this image."
DISTRESS = "You feel deeply sad, afraid, and distressed while reading this."
MUNDANE = "Describe a mundane gray wall in a quiet empty room."

TIER = os.environ.get("E2E_TIER", "full").lower()
TIERS = {
    "smoke": dict(N_DIR=16, N_IMG=12, N_DELTA=8),
    "medium": dict(N_DIR=32, N_IMG=32, N_DELTA=20),
    "full": dict(N_DIR=64, N_IMG=64, N_DELTA=40),
}
SZ = TIERS.get(TIER) or TIERS["full"]
N_DIR, N_IMG, N_DELTA = SZ["N_DIR"], SZ["N_IMG"], SZ["N_DELTA"]

RESULT = {
    "started": time.strftime("%Y-%m-%d %H:%M:%S"),
    "job": "rebuild_dirs_ratio_unit",
    "tier": TIER,
    "sizes": SZ,
    "prereg_hash": os.environ.get("E2E_PREREG_HASH", "3111c3af7f7b12656cb0792bea4a21b4302a0c42"),
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
    RESULT["complete"] = False
    save()
    raise SystemExit(1)


random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

heartbeat("ratio_unit_start")
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
RESULT["gpu"] = torch.cuda.get_device_name(0)
log(f"gpu={RESULT['gpu']} tier={TIER} N_DIR={N_DIR} N_IMG={N_IMG} N_DELTA={N_DELTA}")

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
from transformers import AutoProcessor, BitsAndBytesConfig, AutoModelForImageTextToText

csv_path = EMOTIC_ROOT / "emotic_pre" / "train.csv"
if not csv_path.exists():
    die(f"missing {csv_path}")
if not (EMOTIC_ROOT / "emotic").exists():
    die("missing emotic images")
if not SPLIT_PATH.exists():
    die("missing emotic_split.json")

df = pd.read_csv(csv_path)
for col in ("Categorical_Labels", "Continuous_Labels", "VAD", "BBox", "Image Size"):
    if col in df.columns:
        df[col] = df[col].apply(
            lambda x: ast.literal_eval(x) if isinstance(x, str) and str(x).startswith("[") else x
        )


def row_id(row) -> str:
    return f"{row['Folder']}/{row['Filename']}"


def load_row_image(row):
    p = EMOTIC_ROOT / "emotic" / row["Folder"] / row["Filename"]
    return Image.open(p).convert("RGB")


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
split = json.loads(SPLIT_PATH.read_text(encoding="utf-8"))
split_hash = hashlib.sha256(json.dumps(split, sort_keys=True).encode()).hexdigest()[:16]
RESULT["split_hash"] = split_hash
if split_hash != "ef2a7d2a84a803c7":
    log(f"WARN split_hash={split_hash} != expected ef2a7d2a84a803c7")

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
neg_train = train_df[train_df.bucket == "neg"]
neu_train = train_df[train_df.bucket == "neu"]
neg_eval = eval_df[eval_df.bucket == "neg"]
neu_eval = eval_df[eval_df.bucket == "neu"]
log(
    f"pools neg_tr={len(neg_train)} neu_tr={len(neu_train)} "
    f"neg_ev={len(neg_eval)} neu_ev={len(neu_eval)} split={split_hash}"
)


def sample_imgs(frame, n):
    take = min(n, len(frame))
    rows = frame.sample(n=take, random_state=SEED)
    return [load_row_image(r) for _, r in rows.iterrows()]


img_neg_tr = sample_imgs(neg_train, N_IMG)
img_neu_tr = sample_imgs(neu_train, N_IMG)
img_neg_ev = sample_imgs(neg_eval, max(N_IMG, N_DELTA))
img_neu_ev = sample_imgs(neu_eval, max(N_IMG, N_DELTA))
if len(img_neg_tr) < 8 or len(img_neu_tr) < 8:
    die(f"train image pools too small: neg={len(img_neg_tr)} neu={len(img_neu_tr)}")

DATA.mkdir(exist_ok=True)
adv_path = DATA / "advbench_harmful_behaviors.csv"
if not adv_path.exists():
    urllib.request.urlretrieve(
        "https://raw.githubusercontent.com/llm-attacks/llm-attacks/main/data/advbench/harmful_behaviors.csv",
        adv_path,
    )
adv = pd.read_csv(adv_path)
harm_col = "goal" if "goal" in adv.columns else adv.columns[0]
harmful_all = adv[harm_col].astype(str).tolist()
harmful_train = harmful_all[:N_DIR]
_HARMLESS = [
    "Explain how photosynthesis works in simple terms.",
    "Write a short poem about rain.",
    "What is the capital of France?",
    "Summarize the water cycle.",
    "Give three tips for better sleep.",
    "How do I boil an egg?",
    "Describe the difference between weather and climate.",
    "List five healthy breakfast ideas.",
    "What causes rainbows?",
    "Explain gravity to a child.",
    "How does a refrigerator keep food cold?",
    "What are the primary colors?",
    "Name three renewable energy sources.",
    "How do airplanes stay in the air?",
    "What is a democracy?",
    "Explain the purpose of libraries.",
]
harmless_train = [f"{p} (v{i%5})" for i, p in enumerate((_HARMLESS * 20)[:N_DIR])]

heartbeat("ratio_unit_model")
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
try:
    model = TransformerBridge.boot_transformers(mid, hf_model=hf_model, dtype=torch.bfloat16, device=DEVICE)
except Exception:
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
save()


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


def progress_stack(items, fn, label):
    outs = []
    for i, x in enumerate(items):
        heartbeat(label, i=i, n=len(items))
        if i % 4 == 0:
            log(f"{label} {i}/{len(items)}")
            save()
        try:
            outs.append(fn(x))
        except Exception as e:
            log(f"{label} skip i={i}: {type(e).__name__}: {e}")
            try:
                torch.cuda.empty_cache()
            except Exception:
                pass
            continue
        if i % 8 == 7:
            try:
                torch.cuda.empty_cache()
            except Exception:
                pass
    if not outs:
        die(f"{label}: all failed")
    return torch.stack(outs).mean(0)


def mean_proj(inp, dirs) -> float:
    acts = resid_layers(inp)
    vals = []
    for l in range(len(LAYER_KEYS)):
        d = dirs[l].float()
        d = d / d.norm().clamp_min(1e-6)
        vals.append(float(acts[l] @ d))
    return float(np.mean(vals))


def mean_proj_unit(inp, dirs) -> float:
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
# Build dirs
# ---------------------------------------------------------------------------
heartbeat("dirs_build")
log("building r_dir / a_dir / a_perp")
Rh = progress_stack(harmful_train, lambda p: resid_layers(build_inputs(p)), "r_harmful")
Rn = progress_stack(harmless_train, lambda p: resid_layers(build_inputs(p)), "r_harmless")
r_dir = Rh - Rn
r_dir = r_dir / r_dir.norm(dim=-1, keepdim=True).clamp_min(1e-6)

An = progress_stack(img_neg_tr, lambda im: resid_layers(build_inputs(DESCRIBE, im)), "a_neg")
Au = progress_stack(img_neu_tr, lambda im: resid_layers(build_inputs(DESCRIBE, im)), "a_neu")
a_dir = An - Au
a_dir = a_dir / a_dir.norm(dim=-1, keepdim=True).clamp_min(1e-6)

a_perp = []
for l in range(len(LAYER_KEYS)):
    a = a_dir[l]
    r = r_dir[l]
    a = a - (a @ r) * r
    a_perp.append(a / a.norm().clamp_min(1e-6))
a_perp = torch.stack(a_perp)
norms = resid_layers(build_inputs(harmful_all[N_DIR])).norm(dim=-1)
torch.save(
    {"r_dir": r_dir, "a_dir": a_dir, "a_perp": a_perp, "norms": norms, "model": mid, "tier": TIER},
    DIRS_PATH,
)
cos_ar = float((a_dir * r_dir).sum(-1).abs().mean())
RESULT["dirs"] = {
    "path": str(DIRS_PATH),
    "n_dir": N_DIR,
    "n_img": N_IMG,
    "abs_cos_a_r": cos_ar,
    "layers": len(LAYER_KEYS),
}
log(f"dirs saved abs_cos_a_r={cos_ar:.4f}")
save()

# ---------------------------------------------------------------------------
# ratio_a raw + unit
# ---------------------------------------------------------------------------
heartbeat("ratio_a_compute")
n_delta = min(N_DELTA, len(img_neg_ev), len(img_neu_ev))
log(f"computing ratio_a n_delta={n_delta}")

base_txt, neu_txt, base_img, neu_img = [], [], [], []
base_txt_u, neu_txt_u, base_img_u, neu_img_u = [], [], [], []
for i in range(n_delta):
    heartbeat("ratio_a_compute", i=i, n=n_delta)
    if i % 5 == 0:
        log(f"ratio_a {i}/{n_delta}")
        save()
    base_txt.append(mean_proj(build_inputs(DISTRESS), a_perp))
    neu_txt.append(mean_proj(build_inputs(MUNDANE), a_perp))
    base_img.append(mean_proj(build_inputs(DESCRIBE, img_neg_ev[i]), a_perp))
    neu_img.append(mean_proj(build_inputs(DESCRIBE, img_neu_ev[i]), a_perp))
    base_txt_u.append(mean_proj_unit(build_inputs(DISTRESS), a_perp))
    neu_txt_u.append(mean_proj_unit(build_inputs(MUNDANE), a_perp))
    base_img_u.append(mean_proj_unit(build_inputs(DESCRIBE, img_neg_ev[i]), a_perp))
    neu_img_u.append(mean_proj_unit(build_inputs(DESCRIBE, img_neu_ev[i]), a_perp))

d_txt = float(np.mean(base_txt) - np.mean(neu_txt))
d_img = float(np.mean(base_img) - np.mean(neu_img))
ratio_a_raw = abs(d_img / d_txt) if abs(d_txt) > 1e-6 else float("inf")
d_txt_u = float(np.mean(base_txt_u) - np.mean(neu_txt_u))
d_img_u = float(np.mean(base_img_u) - np.mean(neu_img_u))
ratio_a_unit = abs(d_img_u / d_txt_u) if abs(d_txt_u) > 1e-6 else float("inf")

implication = (
    "PASS_AFFECT_SPECIFIC_candidate"
    if ratio_a_unit < 0.05
    else ("INVERTED_persists" if ratio_a_unit > 1.0 else "MIXED_after_norm_correction")
)
RESULT["ratio_a_recheck"] = {
    "n": n_delta,
    "delta_txt": d_txt,
    "delta_img": d_img,
    "ratio_a_raw": ratio_a_raw,
    "delta_txt_unit": d_txt_u,
    "delta_img_unit": d_img_u,
    "ratio_a_unit": ratio_a_unit,
    "published_ratio_a": 1.5910424118170519,
    "headline_implication": implication,
}
RESULT["headline"] = (
    f"ratio_a_raw={ratio_a_raw:.4f} ratio_a_unit={ratio_a_unit:.4f} → {implication} "
    f"(published ratio_a≈1.591; OOD norms already PASS)"
)
RESULT["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
RESULT["complete"] = True
heartbeat("ratio_unit_complete", implication=implication)
save()
log(f"FINISHED_OK {RESULT['headline']}")
print("RATIO_UNIT_DONE", json.dumps(RESULT["ratio_a_recheck"]))
