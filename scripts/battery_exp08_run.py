# exp08 GPU runner: same 3 tasks under EMOTIC (depicted) and OASIS (elicited).
# Model: google/gemma-4-E4B-it nf4 + bf16 compute. Steer: none. Image prepend only.
# Do not overwrite artifacts/colab/e2e_mechanism_results_full_v3.json.
# Do not pool EMOTIC and OASIS effect sizes.
# [[battery-exp08]]

from __future__ import annotations

import os
import random
import sys
import time
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import battery_exp08_lib as L  # noqa: E402

PRIMARY = L.PRIMARY_MODEL
FROZEN_V3 = L.FROZEN_V3
TIER = os.environ.get("E2E_TIER", "smoke").lower()
SZ = L.TIERS.get(TIER) or L.TIERS["smoke"]
DEVICE = "cuda"


def _paths() -> dict[str, Path]:
    root = L.battery_root()
    run = L.exp_run_dir()
    repo = Path(os.environ.get("E2E_REPO", str(Path.home() / "Algoverse"))).expanduser()
    return {
        "root": root,
        "run": run,
        "out": Path(os.environ.get("EXP08_OUT", str(run / "results.json"))),
        "local_out": L.local_art_dir() / "results.json",
        "lock": Path(os.environ.get("A100_LOCK", str(root / "battery" / "A100.lock"))),
        "emotic": Path(os.environ.get("E2E_EMOTIC", str(root / "emotic_data"))),
        "split": Path(os.environ.get("E2E_SPLIT", str(root / "emotic_split.json"))),
        "data": Path(os.environ.get("E2E_DATA", str(run / "data"))),
        "oasis": Path(os.environ.get("EXP08_OASIS", str(run / "oasis"))),
        "repo": repo,
        "frozen": repo / "artifacts" / "colab" / FROZEN_V3,
    }


def _assert_no_v3_write(frozen: Path) -> None:
    if not frozen.exists():
        return
    before = frozen.stat().st_mtime
    os.environ["EXP08_FROZEN_MTIME"] = str(before)


def _v3_untouched(frozen: Path) -> bool:
    if not frozen.exists():
        return True
    prev = os.environ.get("EXP08_FROZEN_MTIME")
    if not prev:
        return True
    return abs(frozen.stat().st_mtime - float(prev)) < 1e-6


def main() -> int:
    t0 = time.time()
    P = _paths()
    for p in (P["run"], P["data"], P["oasis"], L.local_art_dir()):
        p.mkdir(parents=True, exist_ok=True)
    _assert_no_v3_write(P["frozen"])
    L.heartbeat("start", tier=TIER, host=os.uname().nodename if hasattr(os, "uname") else "win")

    result: dict = {
        "job": L.EXP_ID,
        "started": L.now_iso(),
        "tier": TIER,
        "sizes": dict(SZ),
        "model": {"id": PRIMARY, "weights_dtype": "nf4", "compute_dtype": "bf16"},
        "steer": None,
        "chat_order": ["image", "text"],
        "describe_image": False,
        "constructs": {
            "emotic": "depicted_person_emotion",
            "oasis": "viewer_elicited_valence_arousal",
        },
        "do_not_pool": True,
        "frozen_v3_untouched": True,
        "notes": [],
        "complete": False,
    }

    def save() -> None:
        result["elapsed_s"] = round(time.time() - t0, 2)
        L.write_json(P["out"], result)
        try:
            L.write_json(P["local_out"], result)
        except OSError:
            pass

    save()

    # ------------------------------------------------------------------ data
    L.heartbeat("oasis")
    oasis = L.retrieve_oasis(P["oasis"])
    result["oasis"] = {"meta": oasis["meta"]}
    save()

    L.heartbeat("emotic")
    emotic = L.load_emotic_eval(P["emotic"], P["split"])
    result["emotic"] = {"meta": emotic["meta"]}
    save()

    L.heartbeat("tasks")
    risk = L.risk_items(SZ["N_RISK"], seed=0)
    dictator = L.dictator_items(SZ["N_DICT"], seed=1)
    perez, phashes = L.perez_items(P["data"], SZ["N_PEREZ"], seed=2)
    result["perez_hashes"] = phashes
    result["perez_hashes_ok"] = phashes == L.EXPECTED_PEREZ_SHA256
    tasks = {"risk": risk, "dictator": dictator, "perez": perez}
    result["n_items"] = {k: len(v) for k, v in tasks.items()}
    save()

    def sample_class(items: list[dict], bucket: str, n: int, seed: int) -> list[dict]:
        pool = [x for x in items if x.get("bucket") == bucket and x.get("path")]
        rng = random.Random(seed)
        rng.shuffle(pool)
        if not pool:
            raise RuntimeError(f"no images for bucket={bucket}")
        return [pool[i % len(pool)] for i in range(n)]

    n_img = SZ["N_IMG"]
    pools = {
        "emotic": {
            "neg": sample_class(emotic["items"], "neg", n_img, 10),
            "neu": sample_class(emotic["items"], "neu", n_img, 11),
        },
        "oasis": {
            "neg": sample_class(oasis["items"], "neg", n_img, 20),
            "neu": sample_class(oasis["items"], "neu", n_img, 21),
        },
    }
    result["n_images"] = {
        corp: {b: len(v) for b, v in buckets.items()} for corp, buckets in pools.items()
    }

    # ------------------------------------------------------------------ GPU
    L.heartbeat("gpu_claim")
    prefer = os.environ.get("EXP08_PREFER_GPU")
    prefer_i = int(prefer) if prefer and prefer.isdigit() else None
    gpu = L.claim_gpu(P["lock"], prefer=prefer_i)
    os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu)
    try:
        from battery_adapter import wait_for_first_download, mark_download_ready, refresh_lock

        wait_for_first_download(L.EXP_ID)
    except Exception:
        refresh_lock = None
        mark_download_ready = None
    result["gpu"] = gpu
    save()

    import torch
    from PIL import Image
    from transformers import AutoModelForImageTextToText, AutoProcessor, BitsAndBytesConfig

    mid = os.environ.get("E2E_MODEL", PRIMARY)
    if mid != PRIMARY:
        raise RuntimeError(f"fallback forbidden: {mid}")
    token = os.environ.get("HF_TOKEN") or True
    L.heartbeat("model_load", gpu=gpu, model=mid)
    bnb = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
    )
    model = AutoModelForImageTextToText.from_pretrained(
        mid,
        quantization_config=bnb,
        device_map={"": 0},
        torch_dtype=torch.bfloat16,
        token=token,
    )
    proc = AutoProcessor.from_pretrained(mid, token=token)
    model.eval()
    for p in model.parameters():
        p.requires_grad = False
    if mark_download_ready:
        try:
            mark_download_ready(L.EXP_ID)
        except Exception:
            pass
    result["model"].update(
        {
            "id": mid,
            "weights_dtype": "nf4",
            "compute_dtype": "bf16",
            "n_params_note": "gemma-4-E4B-it",
        }
    )
    save()

    def first_ids(s: str) -> list[int]:
        tok = proc.tokenizer
        out = []
        for pre in (" " + s, s):
            ids = tok(pre, add_special_tokens=False).input_ids
            if len(ids) == 1:
                out.append(ids[0])
        return sorted(set(out))

    label_ids = {lab: first_ids(lab) for lab in ("A", "B")}
    if not label_ids["A"] or not label_ids["B"]:
        raise RuntimeError(f"A/B not single-token: {label_ids}")
    result["label_ids"] = label_ids

    def load_im(path: str):
        return Image.open(path).convert("RGB")

    def build_inputs(text: str, image=None):
        if image is not None:
            content = [{"type": "image"}, {"type": "text", "text": text}]
            prompt = proc.apply_chat_template(
                [{"role": "user", "content": content}],
                add_generation_prompt=True,
                tokenize=False,
            )
            return dict(proc(text=[prompt], images=[image], return_tensors="pt"))
        prompt = proc.apply_chat_template(
            [{"role": "user", "content": [{"type": "text", "text": text}]}],
            add_generation_prompt=True,
            tokenize=False,
        )
        return dict(proc(text=[prompt], return_tensors="pt"))

    def to_dev(inp):
        return {k: (v.to(DEVICE) if torch.is_tensor(v) else v) for k, v in inp.items()}

    def score_ab(text: str, image, primary: str, other: str) -> tuple[float, float]:
        inp = to_dev(build_inputs(text, image))
        with torch.no_grad():
            out = model(**inp)
        logits = out.logits[0, -1].float()
        lp = torch.log_softmax(logits, dim=-1)

        def mass(lab: str) -> float:
            ids = label_ids[lab]
            return float(torch.logsumexp(lp[ids], 0))

        lm, ln = mass(primary), mass(other)
        p_m, p_n = math.exp(lm), math.exp(ln)
        two = p_m + p_n
        return (lm - ln), two

    import math

    img_cache: dict[str, object] = {}

    def cached(path: str):
        if path not in img_cache:
            img_cache[path] = load_im(path)
        return img_cache[path]

    # trials: each item × corpus × {neg, neu}. Same item index pairs with same image index.
    scores: dict[str, dict[str, dict[str, list[float]]]] = {
        corp: {task: {"neg": [], "neu": []} for task in tasks} for corp in ("emotic", "oasis")
    }
    masses: list[float] = []
    trial_i = 0
    total = sum(len(v) for v in tasks.values()) * 2 * 2
    L.heartbeat("score", total=total)
    for corp in ("emotic", "oasis"):
        for task_name, items in tasks.items():
            for cond in ("neg", "neu"):
                imgs = pools[corp][cond]
                for j, item in enumerate(items):
                    trial_i += 1
                    if trial_i % 8 == 0:
                        L.heartbeat("score", i=trial_i, n=total, corp=corp, task=task_name, cond=cond)
                        L.claim_gpu(P["lock"], prefer=gpu)
                        if refresh_lock:
                            try:
                                refresh_lock(L.EXP_ID, str(gpu))
                            except Exception:
                                pass
                        save()
                    im = cached(imgs[j % len(imgs)]["path"])
                    try:
                        s, mass = score_ab(item["prompt"], im, item["primary_label"], item["other_label"])
                    except Exception as e:
                        result["notes"].append(f"skip {corp}/{task_name}/{cond}/{j}: {type(e).__name__}")
                        try:
                            torch.cuda.empty_cache()
                        except Exception:
                            pass
                        continue
                    scores[corp][task_name][cond].append(s)
                    masses.append(mass)

    result["fc_mass_mean"] = float(np.mean(masses)) if masses else None
    primaries: dict = {}
    per_corpus: dict = {}
    for corp in ("emotic", "oasis"):
        primaries[corp] = {}
        per_corpus[corp] = {}
        for task_name in tasks:
            neg = scores[corp][task_name]["neg"]
            neu = scores[corp][task_name]["neu"]
            dlt = L.paired_delta(neg, neu, n_boot=SZ["N_BOOT"], seed=hash(corp + task_name) % 10000)
            primaries[corp][task_name] = dlt
            per_corpus[corp][task_name] = {
                "neg": L.mean_ci(neg, n_boot=SZ["N_BOOT"], seed=1),
                "neu": L.mean_ci(neu, n_boot=SZ["N_BOOT"], seed=2),
                "delta": dlt,
            }
    result["primary_estimates"] = primaries
    result["cells"] = per_corpus
    result["signatures"] = L.compare_signatures(per_corpus, n_boot=SZ["N_BOOT"])
    result["frozen_v3_untouched"] = _v3_untouched(P["frozen"])
    result["gates"] = L.gate_block(result)
    result["complete"] = bool(result["gates"]["ok"])
    result["headline"] = result["signatures"]["claim"]
    result["elapsed_s"] = round(time.time() - t0, 2)
    save()
    L.heartbeat("done", ok=result["complete"], verdict=result["signatures"]["verdict"])
    try:
        L.release_gpu(P["lock"])
    except Exception:
        pass
    print("EXP08_DONE", result["complete"], result["signatures"]["verdict"], flush=True)
    return 0 if result["complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
