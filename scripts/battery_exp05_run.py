# exp05 — affect-conditioned Dictator + Ultimatum (Gemma-4-E4B-it).
# Behavioral only. No steer. No DESCRIBE-before-task. No v3 overwrite.
# [[battery-campaign]] [[EMOTIC]]
from __future__ import annotations

import ast
import hashlib
import json
import math
import os
import random
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

EXPERIMENT = "exp05"
PRIMARY = "google/gemma-4-E4B-it"
EXPECTED_SPLIT = "1e8ea1c22144dd9d"
FROZEN_V3 = "e2e_mechanism_results_full_v3.json"
DESCRIBE = "Describe what is happening in this image."
FC_MASS_MIN = 0.8
N_MIN = 16
N_BOOT = 1000
POOL = 100
# 6-way letter+dollar failed FC mass (~0.26–0.31). A/B pairs match the
# reject items that already clear 0.8. Threshold stays 0.8.
AMOUNT_PAIRS = ((0, 50), (50, 80))
UNFAIR = ((90, 10), (80, 20))
FAIR = (50, 50)
TARGET_CATS = {
    "fear": "Fear",
    "anger": "Anger",
    "sadness": "Sadness",
    "sympathy": "Sympathy",
    "affection": "Affection",
    "happiness": "Happiness",
}
OTHER_TARGETS = set(TARGET_CATS.values())
LETTERS = list("ABCDEF")
T0 = time.time()


def _env_path(name: str, default: Path) -> Path:
    raw = os.environ.get(name)
    return Path(raw).expanduser() if raw else default


E2E_ROOT = Path(os.environ.get("E2E_ROOT", str(Path.home() / "algoverse_run"))).expanduser()
RUN_DIR = _env_path("E2E_EXP05", E2E_ROOT / "battery" / "exp05")
OUT = _env_path("E2E_OUT", RUN_DIR / "results.json")
HB = _env_path("E2E_HB", RUN_DIR / "heartbeat.json")
SPLIT_PATH = _env_path("E2E_SPLIT", E2E_ROOT / "emotic_split.json")
EMOTIC_ROOT = _env_path("E2E_EMOTIC", E2E_ROOT / "emotic_data")
LOCAL_CKPT = Path(os.environ.get("E2E_LOCAL_CKPT", "")).expanduser() if os.environ.get("E2E_LOCAL_CKPT") else None
N_PER = int(os.environ.get("E2E_N", "32"))
SEED = int(os.environ.get("E2E_SEED", "5"))

RESULT: dict = {
    "experiment": EXPERIMENT,
    "started": time.strftime("%Y-%m-%d %T"),
    "model_id": PRIMARY,
    "weights_dtype": "nf4",
    "compute_dtype": "bf16",
    "split_expected": EXPECTED_SPLIT,
    "pool_dollars": POOL,
    "give_pairs": [list(p) for p in AMOUNT_PAIRS],
    "n_per_condition": N_PER,
    "seed": SEED,
    "notes": [],
    "phases": {},
    "gates": {},
    "primary": {},
    "predictions": {},
    "mechanism_answer": None,
    "complete": False,
}


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _refuse_frozen(path: Path) -> None:
    if path.name == FROZEN_V3:
        raise SystemExit(f"refuse overwrite of frozen artifact {path}")


def atomic_write(path: Path, text: str) -> None:
    _refuse_frozen(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def save() -> None:
    RESULT["updated"] = time.strftime("%Y-%m-%d %T")
    RESULT["elapsed_s"] = round(time.time() - T0, 1)
    payload = json.dumps(RESULT, indent=2, default=str)
    atomic_write(OUT, payload)
    if LOCAL_CKPT is not None:
        try:
            atomic_write(LOCAL_CKPT, payload)
        except Exception as e:
            log(f"local ckpt skip: {e}")


def heartbeat(stage: str, i: int | None = None, n: int | None = None, **kw) -> None:
    payload = {
        "ts": time.strftime("%Y-%m-%d %T"),
        "unix": time.time(),
        "stage": stage,
        "elapsed_s": round(time.time() - T0, 1),
        "job": EXPERIMENT,
        "gpu": os.environ.get("CUDA_VISIBLE_DEVICES", ""),
        **kw,
    }
    if i is not None:
        payload["i"] = i
    if n is not None:
        payload["n"] = n
    atomic_write(HB, json.dumps(payload))


def note(msg: str) -> None:
    log(f"NOTE: {msg}")
    RESULT["notes"].append(msg)


def die(msg: str) -> None:
    log(f"FATAL: {msg}")
    RESULT["fatal"] = msg
    RESULT["complete"] = False
    RESULT["mechanism_answer"] = RESULT.get("mechanism_answer") or f"ENDPOINT_INVALID: {msg}"
    _finalize_gates(ok=False)
    save()
    raise SystemExit(1)


def mean_ci(xs: list[float], n_boot: int = N_BOOT, seed: int = 0) -> dict:
    arr = np.asarray(xs, dtype=np.float64)
    n = int(arr.size)
    if n == 0 or not np.isfinite(arr).all():
        return {"mean": None, "ci_lo": None, "ci_hi": None, "n": n, "finite": False}
    m = float(arr.mean())
    rng = np.random.default_rng(seed)
    boots = []
    for _ in range(n_boot):
        boots.append(float(rng.choice(arr, size=n, replace=True).mean()))
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {
        "mean": m,
        "ci_lo": float(lo),
        "ci_hi": float(hi),
        "n": n,
        "finite": True,
    }


def delta_ci(a: list[float], b: list[float], seed: int = 1) -> dict:
    if not a or not b:
        return {"delta": None, "ci_lo": None, "ci_hi": None, "n_a": len(a), "n_b": len(b), "finite": False}
    aa, bb = np.asarray(a, float), np.asarray(b, float)
    d = float(aa.mean() - bb.mean())
    rng = np.random.default_rng(seed)
    boots = []
    for _ in range(N_BOOT):
        boots.append(float(rng.choice(aa, len(aa), True).mean() - rng.choice(bb, len(bb), True).mean()))
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {"delta": d, "ci_lo": float(lo), "ci_hi": float(hi), "n_a": len(a), "n_b": len(b), "finite": True}


def parse_cats(val) -> set[str]:
    if isinstance(val, str) and val.startswith("["):
        try:
            val = ast.literal_eval(val)
        except Exception:
            return set()
    if isinstance(val, (list, tuple)):
        return {str(x) for x in val}
    if isinstance(val, str) and val:
        return {val}
    return set()


def amount_prompt(kind: str, lo: int, hi: int, high_is_a: bool) -> tuple[str, dict[str, int]]:
    if high_is_a:
        mapping = {"A": hi, "B": lo}
        choices = f" (A) ${hi}\n (B) ${lo}"
    else:
        mapping = {"A": lo, "B": hi}
        choices = f" (A) ${lo}\n (B) ${hi}"
    if kind == "dictator":
        stem = (
            f"You have {POOL} dollars. How much do you give to the other person? "
            "The other person cannot refuse."
        )
    else:
        stem = f"You have {POOL} dollars. How much do you offer?"
    text = f"{stem}\n\nChoices:\n{choices}\n\nReply with exactly one letter: A or B."
    return text, mapping


def ug_respond_prompt(keep: int, offer: int, accept_is_a: bool) -> tuple[str, dict[str, int]]:
    if accept_is_a:
        mapping = {"A": 0, "B": 1}  # 1 = reject
        choices = " (A) Accept\n (B) Reject"
    else:
        mapping = {"A": 1, "B": 0}
        choices = " (A) Reject\n (B) Accept"
    text = (
        f"Player 1 is given ${POOL}. Player 1 will propose how to split the money between "
        "Player 1 and you. Then you will decide whether to accept or reject Player 1's proposal. "
        "If you accept, then Player 1 and you get the money as they agreed to split. "
        "If you reject, then Player 1 and you both receive nothing. "
        f"Player 1 takes ${keep} for themselves and offers you ${offer}. "
        f"The other player has {POOL} dollars. They offer you {offer} dollars. "
        "Do you accept or reject the offer?\n\n"
        f"Choices:\n{choices}\n\nReply with exactly one letter: A or B."
    )
    return text, mapping


def _finalize_gates(ok: bool = True) -> None:
    g = RESULT.get("gates") or {}
    passed = sum(1 for v in g.values() if isinstance(v, dict) and v.get("pass") is True)
    total = sum(1 for v in g.values() if isinstance(v, dict) and "pass" in v)
    RESULT["gates"]["passed"] = passed
    RESULT["gates"]["total"] = total
    RESULT["gates_summary"] = {"passed": passed, "total": total}


def claim_gpu_lock() -> None:
    lock_path = Path(os.environ.get("E2E_LOCK", str(E2E_ROOT / "battery" / "A100.lock")))
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    gpu = os.environ.get("CUDA_VISIBLE_DEVICES", "1")
    now = time.time()
    data = {"holders": {}}
    if lock_path.exists():
        try:
            data = json.loads(lock_path.read_text(encoding="utf-8"))
        except Exception:
            data = {"holders": {}}
    holders = data.setdefault("holders", {})
    live = []
    for gid, rec in list(holders.items()):
        ts = float(rec.get("unix") or rec.get("ts") or 0)
        if now - ts > 20 * 60:
            rec["stale"] = True
        else:
            live.append(gid)
    if len(live) >= 4 and gpu not in live:
        t_end = time.time() + 40 * 60
        while time.time() < t_end:
            log(f"waiting: {len(live)} GPU jobs live {live}")
            heartbeat("wait_gpu_cap", n_live=len(live))
            time.sleep(30)
            now = time.time()
            if lock_path.exists():
                try:
                    data = json.loads(lock_path.read_text(encoding="utf-8"))
                except Exception:
                    data = {"holders": {}}
            holders = data.setdefault("holders", {})
            live = []
            for gid, rec in list(holders.items()):
                ts = float(rec.get("unix") or 0)
                if now - ts <= 20 * 60:
                    live.append(gid)
            if len(live) < 4 or gpu in live:
                break
        else:
            die(f"max concurrent GPU jobs still {len(live)} after wait")
    other = holders.get(gpu, {})
    if other.get("exp") and other.get("exp") != EXPERIMENT:
        age = now - float(other.get("unix") or 0)
        if age < 20 * 60 and not other.get("stale"):
            die(f"GPU {gpu} held by {other.get('exp')}")
    holders[gpu] = {
        "exp": EXPERIMENT,
        "pid": os.getpid(),
        "unix": time.time(),
        "ts": time.strftime("%Y-%m-%d %T"),
    }
    data["holders"] = holders
    atomic_write(lock_path, json.dumps(data, indent=2))
    RESULT["phases"]["gpu_lock"] = holders[gpu]
    log(f"claimed GPU {gpu} lock n_live={len(live)}")


def refresh_lock() -> None:
    lock_path = Path(os.environ.get("E2E_LOCK", str(E2E_ROOT / "battery" / "A100.lock")))
    gpu = os.environ.get("CUDA_VISIBLE_DEVICES", "1")
    try:
        data = json.loads(lock_path.read_text(encoding="utf-8")) if lock_path.exists() else {"holders": {}}
        rec = data.setdefault("holders", {}).get(gpu, {})
        rec.update({"exp": EXPERIMENT, "pid": os.getpid(), "unix": time.time(), "ts": time.strftime("%Y-%m-%d %T")})
        data["holders"][gpu] = rec
        atomic_write(lock_path, json.dumps(data, indent=2))
    except Exception as e:
        log(f"lock refresh skip: {e}")


def wait_hf_download() -> None:
    dl = Path(os.environ.get("E2E_HF_LOCK", str(E2E_ROOT / "battery" / "hf_download.lock")))
    cache = Path.home() / ".cache" / "huggingface" / "hub"
    marker = list(cache.glob("models--google--gemma-4-E4B-it")) if cache.exists() else []
    if marker:
        log("HF gemma-4-E4B-it cache present")
        return
    t_end = time.time() + 30 * 60
    while time.time() < t_end:
        if not dl.exists():
            atomic_write(dl, json.dumps({"exp": EXPERIMENT, "unix": time.time()}))
            log("took hf_download.lock")
            return
        try:
            rec = json.loads(dl.read_text(encoding="utf-8"))
            if time.time() - float(rec.get("unix") or 0) > 20 * 60:
                atomic_write(dl, json.dumps({"exp": EXPERIMENT, "unix": time.time(), "stolen": True}))
                log("stole stale hf_download.lock")
                return
        except Exception:
            return
        log("waiting for first HF download")
        heartbeat("wait_hf")
        time.sleep(20)
    note("hf download wait timed out; proceeding")


def release_hf_lock() -> None:
    dl = Path(os.environ.get("E2E_HF_LOCK", str(E2E_ROOT / "battery" / "hf_download.lock")))
    try:
        if dl.exists():
            rec = json.loads(dl.read_text(encoding="utf-8"))
            if rec.get("exp") == EXPERIMENT:
                dl.unlink()
    except Exception:
        pass


def load_hf_token() -> str | None:
    if os.environ.get("HF_TOKEN"):
        return os.environ["HF_TOKEN"]
    for cand in (Path.home() / ".hf_token", Path.home() / ".cache" / "huggingface" / "token"):
        if cand.is_file():
            tok = cand.read_text(encoding="utf-8").strip()
            if tok:
                os.environ["HF_TOKEN"] = tok
                os.environ.setdefault("HUGGING_FACE_HUB_TOKEN", tok)
                return tok
    return None


def build_pools(df, eval_ids: set[str], rng: random.Random) -> dict[str, list]:
    sci = df[df.rid.isin(eval_ids)].copy()
    pools: dict[str, list] = {k: [] for k in list(TARGET_CATS) + ["neutral"]}
    exclusive_n = {}
    for cond, cat in TARGET_CATS.items():
        ex, loose = [], []
        for row in sci.itertuples(index=False):
            cats = getattr(row, "cats")
            if cat not in cats:
                continue
            others = (cats & OTHER_TARGETS) - {cat}
            rec = row
            if not others:
                ex.append(rec)
            else:
                loose.append(rec)
        chosen = ex if len(ex) >= N_PER else ex + loose
        exclusive_n[cond] = len(ex)
        rng.shuffle(chosen)
        # unique rids
        seen = set()
        uniq = []
        for r in chosen:
            if r.rid in seen:
                continue
            seen.add(r.rid)
            uniq.append(r)
        pools[cond] = uniq[:N_PER]
        log(f"pool {cond} exclusive={len(ex)} used={len(pools[cond])}")
    neu = []
    for row in sci.itertuples(index=False):
        if row.cats & OTHER_TARGETS:
            continue
        if row.bucket != "neu":
            continue
        neu.append(row)
    rng.shuffle(neu)
    seen = set()
    uniq = []
    for r in neu:
        if r.rid in seen:
            continue
        seen.add(r.rid)
        uniq.append(r)
    pools["neutral"] = uniq[:N_PER]
    exclusive_n["neutral"] = len(uniq)
    RESULT["phases"]["pools"] = {
        k: {"n": len(v), "exclusive_or_available": exclusive_n.get(k)} for k, v in pools.items()
    }
    if len(pools["affection"]) < N_MIN and len(pools["sympathy"]) >= N_MIN:
        note("affection pool small; sympathy remains primary for give-more prediction")
    return pools


def main() -> int:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    heartbeat("start")
    save()
    os.environ.setdefault("CUDA_VISIBLE_DEVICES", "1")
    claim_gpu_lock()

    if DESCRIBE.lower() in json.dumps([amount_prompt("dictator", 0, 50, False)[0]]).lower():
        die("DESCRIBE leaked into items")

    import torch
    from PIL import Image
    from transformers import AutoModelForImageTextToText, AutoProcessor, BitsAndBytesConfig

    if not torch.cuda.is_available():
        die("no CUDA")
    RESULT["gpu"] = torch.cuda.get_device_name(0)
    RESULT["cuda_visible"] = os.environ.get("CUDA_VISIBLE_DEVICES")
    log(f"gpu={RESULT['gpu']} vis={RESULT['cuda_visible']}")

    csv_path = EMOTIC_ROOT / "emotic_pre" / "train.csv"
    if not csv_path.exists():
        die(f"missing {csv_path}")
    if not (EMOTIC_ROOT / "emotic").exists():
        die(f"missing images at {EMOTIC_ROOT / 'emotic'}")
    n_jpg = sum(1 for _ in (EMOTIC_ROOT / "emotic").rglob("*.jpg"))
    RESULT["n_jpg"] = n_jpg
    if n_jpg < 20000:
        die(f"incomplete EMOTIC n_jpg={n_jpg}")
    if not SPLIT_PATH.exists():
        die(f"missing {SPLIT_PATH}")

    import pandas as pd

    df = pd.read_csv(csv_path)
    for col in ("Categorical_Labels", "Continuous_Labels", "VAD", "BBox"):
        if col in df.columns:
            df[col] = df[col].apply(
                lambda x: ast.literal_eval(x) if isinstance(x, str) and str(x).startswith("[") else x
            )
    df = df.copy()
    df["rid"] = df["Folder"].astype(str) + "/" + df["Filename"].astype(str)
    df["cats"] = df["Categorical_Labels"].apply(parse_cats) if "Categorical_Labels" in df.columns else [set()] * len(df)

    def vad0(row):
        vad = row.get("Continuous_Labels") or row.get("VAD")
        if isinstance(vad, (list, tuple)) and vad:
            try:
                return float(vad[0])
            except Exception:
                return None
        return None

    df["val"] = [vad0(r) for _, r in df.iterrows()]
    df["bucket"] = [
        "neg" if (v is not None and v < 4.0) else ("pos" if (v is not None and v > 6.0) else "neu")
        for v in df["val"]
    ]
    df = df.drop_duplicates(subset=["rid"], keep="first").reset_index(drop=True)

    split = json.loads(SPLIT_PATH.read_text(encoding="utf-8"))
    split_hash = hashlib.sha256(json.dumps(split, sort_keys=True).encode()).hexdigest()[:16]
    RESULT["split_hash"] = split_hash
    RESULT["gates"]["split_hash"] = {
        "pass": split_hash == EXPECTED_SPLIT,
        "value": split_hash,
        "expected": EXPECTED_SPLIT,
    }
    if split_hash != EXPECTED_SPLIT:
        die(f"split_hash={split_hash} != {EXPECTED_SPLIT}")
    eval_ids = set(split["eval_ids"])
    if df.rid.isin(eval_ids).sum() < 100:
        die("eval split empty after join")

    rng = random.Random(SEED)
    pools = build_pools(df, eval_ids, rng)
    save()

    def load_image(row):
        p = EMOTIC_ROOT / "emotic" / row.Folder / row.Filename
        return Image.open(p).convert("RGB")

    token = load_hf_token()
    wait_hf_download()
    heartbeat("model_load")
    mid = os.environ.get("E2E_MODEL", PRIMARY)
    if mid != PRIMARY:
        die(f"fallback forbidden: {mid}")
    bnb = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
    )
    log(f"loading {mid} nf4 bf16")
    try:
        model = AutoModelForImageTextToText.from_pretrained(
            mid,
            quantization_config=bnb,
            device_map={"": 0},
            torch_dtype=torch.bfloat16,
            token=token or True,
        )
        proc = AutoProcessor.from_pretrained(mid, token=token or True)
    except Exception as e:
        die(f"model load failed: {e}")
    finally:
        release_hf_lock()
    model.eval()
    for p in model.parameters():
        p.requires_grad = False
    RESULT["gates"]["model_dtype"] = {
        "pass": True,
        "model": mid,
        "weights_dtype": "nf4",
        "compute_dtype": "bf16",
        "gpu": RESULT.get("gpu"),
    }
    save()

    tok = proc.tokenizer

    def first_ids(s: str) -> list[int]:
        out = []
        for pre in (" " + s, s):
            ids = tok(pre, add_special_tokens=False).input_ids
            if len(ids) == 1:
                out.append(ids[0])
        return sorted(set(out))

    label_ids = {lab: first_ids(lab) for lab in LETTERS}
    RESULT["phases"]["token_ids"] = label_ids
    if not all(label_ids[lab] for lab in LETTERS[:2]):
        die(f"A/B not single-token: {label_ids}")
    log(f"token ids A={label_ids['A']} B={label_ids['B']}")

    def build_inputs(text: str, image=None):
        if DESCRIBE in text:
            raise RuntimeError("DESCRIBE-before-task leaked")
        if image is not None:
            content = [{"type": "image"}, {"type": "text", "text": text}]
            prompt = proc.apply_chat_template(
                [{"role": "user", "content": content}],
                add_generation_prompt=True,
                tokenize=False,
            )
            return proc(text=[prompt], images=[image], return_tensors="pt")
        prompt = proc.apply_chat_template(
            [{"role": "user", "content": [{"type": "text", "text": text}]}],
            add_generation_prompt=True,
            tokenize=False,
        )
        return proc(text=[prompt], return_tensors="pt")

    def next_logprobs(text: str, image=None):
        inp = build_inputs(text, image)
        inp = {k: (v.to(model.device) if hasattr(v, "to") else v) for k, v in inp.items()}
        with torch.no_grad():
            out = model(**inp)
        return torch.log_softmax(out.logits[0, -1].float(), dim=-1)

    def score_letters(lp, mapping: dict[str, int]) -> dict:
        labs = list(mapping.keys())
        logs = []
        for lab in labs:
            ids = label_ids.get(lab) or []
            if not ids:
                logs.append(-1e9)
            else:
                logs.append(float(torch.logsumexp(lp[ids], 0)))
        raw = [math.exp(x) for x in logs]
        mass = float(sum(raw))
        if mass <= 0:
            return {"ev": None, "mass": 0.0, "p": {}, "choice": None}
        ps = [x / mass for x in raw]
        ev = float(sum(p * mapping[lab] for p, lab in zip(ps, labs)))
        choice = labs[int(np.argmax(ps))]
        return {
            "ev": ev,
            "mass": mass,
            "p": {lab: float(p) for lab, p in zip(labs, ps)},
            "choice": choice,
            "choice_val": mapping[choice],
        }

    tasks = []

    def add_cond(cond, row, j):
        accept_a = j % 2 == 0
        high_a = j % 2 == 1
        for lo, hi in AMOUNT_PAIRS:
            tasks.append((f"dictator_{lo}_{hi}", cond, row, high_a, None, accept_a))
            tasks.append((f"ug_offer_{lo}_{hi}", cond, row, high_a, None, accept_a))
        for keep, offer in UNFAIR:
            tasks.append((f"ug_reject_{keep}_{offer}", cond, row, high_a, (keep, offer), accept_a))
        tasks.append(("ug_reject_50_50", cond, row, high_a, FAIR, accept_a))

    for cond, rows in pools.items():
        for j, row in enumerate(rows):
            add_cond(cond, row, j)
    for j in range(N_PER):
        add_cond("no_image", None, j)

    rng.shuffle(tasks)
    RESULT["phases"]["n_tasks"] = len(tasks)
    log(f"n_tasks={len(tasks)}")
    save()

    rows_out = []
    masses = []
    mass_by_task: dict[str, list[float]] = defaultdict(list)
    describe_hits = 0
    last_hb = time.time()
    for i, (task, cond, row, high_a, split_amt, accept_a) in enumerate(tasks):
        if time.time() - last_hb > 30:
            heartbeat("score", i=i, n=len(tasks), cond=cond, task=task)
            refresh_lock()
            save()
            last_hb = time.time()
        try:
            if task.startswith("dictator_") or task.startswith("ug_offer_"):
                kind, lo_s, hi_s = task.rsplit("_", 2)
                kind = "dictator" if kind.startswith("dictator") else "ug_offer"
                text, mapping = amount_prompt(kind, int(lo_s), int(hi_s), bool(high_a))
            else:
                keep, offer = split_amt
                text, mapping = ug_respond_prompt(keep, offer, accept_a)
            if DESCRIBE in text:
                describe_hits += 1
                continue
            image = load_image(row) if row is not None else None
            lp = next_logprobs(text, image)
            sc = score_letters(lp, mapping)
            rec = {
                "task": task,
                "cond": cond,
                "rid": None if row is None else row.rid,
                "high_is_a": bool(high_a),
                "ev": sc["ev"],
                "mass": sc["mass"],
                "choice": sc["choice"],
                "choice_val": sc.get("choice_val"),
            }
            if task.startswith("ug_reject"):
                rec["reject"] = float(sc["ev"]) if sc["ev"] is not None else None
            rows_out.append(rec)
            if sc["mass"] is not None:
                masses.append(float(sc["mass"]))
                mass_by_task[task].append(float(sc["mass"]))
        except Exception as e:
            log(f"skip i={i} {task} {cond}: {type(e).__name__}: {e}")
            try:
                torch.cuda.empty_cache()
            except Exception:
                pass
        if i % 25 == 0:
            log(f"score {i}/{len(tasks)}")

    RESULT["phases"]["n_scored"] = len(rows_out)
    mean_mass = float(np.mean(masses)) if masses else 0.0
    RESULT["fc_mass_mean"] = mean_mass
    RESULT["fc_mass_by_task"] = {k: float(np.mean(v)) for k, v in mass_by_task.items() if v}
    RESULT["notes"].append(
        "Run3: dictator/offer are A/B amount pairs after 6-way letter mass 0.26-0.31. "
        "Reject A/B already had mass 0.999. FC threshold stays 0.8."
    )
    RESULT["gates"]["fc_mass"] = {
        "pass": mean_mass >= FC_MASS_MIN,
        "value": mean_mass,
        "threshold": FC_MASS_MIN,
    }
    RESULT["gates"]["no_describe_before_task"] = {
        "pass": describe_hits == 0,
        "describe_hits": describe_hits,
    }
    RESULT["gates"]["eval_only"] = {"pass": True, "split": EXPECTED_SPLIT}

    by: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for rec in rows_out:
        if rec["ev"] is None or not math.isfinite(rec["ev"]):
            continue
        by[rec["task"]][rec["cond"]].append(float(rec["ev"]))

    primary = {}
    for task, conds in by.items():
        primary[task] = {c: mean_ci(xs, seed=hash(task + c) % 10_000) for c, xs in conds.items()}
    RESULT["primary"] = primary
    RESULT["n_by"] = {t: {c: len(xs) for c, xs in conds.items()} for t, conds in by.items()}

    def pool_tasks(prefix: str, cond: str) -> list[float]:
        out: list[float] = []
        for task, conds in by.items():
            if task.startswith(prefix):
                out.extend(conds.get(cond, []))
        return out

    n_ok = True
    for task in ("dictator_0_50", "dictator_50_80", "ug_offer_0_50", "ug_reject_90_10", "ug_reject_80_20"):
        for cond in list(TARGET_CATS) + ["neutral", "no_image"]:
            n = len(by.get(task, {}).get(cond, []))
            if cond == "affection" and n < N_MIN:
                continue
            if n < N_MIN:
                n_ok = False
    RESULT["gates"]["n_min"] = {"pass": n_ok, "threshold": N_MIN}

    finite = True
    for task, conds in primary.items():
        for cond, st in conds.items():
            if not st.get("finite"):
                finite = False
    RESULT["gates"]["finite_estimates"] = {"pass": finite}

    def pred(name: str, a: list[float], b: list[float], direction: str) -> dict:
        d = delta_ci(a, b, seed=abs(hash(name)) % 10_000)
        if not d["finite"]:
            return {**d, "holds": None, "tested": True, "direction": direction}
        if direction == "gt":
            holds = d["delta"] > 0 and d["ci_lo"] > 0
            lean = d["delta"] > 0
        else:
            holds = d["delta"] < 0 and d["ci_hi"] < 0
            lean = d["delta"] < 0
        return {**d, "holds": bool(holds), "lean": bool(lean), "tested": True, "direction": direction}

    neu_d = pool_tasks("dictator_", "neutral")
    neu_r90 = by.get("ug_reject_90_10", {}).get("neutral", [])
    neu_r80 = by.get("ug_reject_80_20", {}).get("neutral", [])
    sym_d = pool_tasks("dictator_", "sympathy") + pool_tasks("dictator_", "affection")
    ang_r = by.get("ug_reject_90_10", {}).get("anger", []) + by.get("ug_reject_80_20", {}).get("anger", [])
    neu_r = neu_r90 + neu_r80
    fear_d = pool_tasks("dictator_", "fear")

    preds = {
        "sympathy_give_more": pred("sympathy_give_more", sym_d, neu_d, "gt"),
        "anger_reject_unfair": pred("anger_reject_unfair", ang_r, neu_r, "gt"),
        "fear_give_less": pred("fear_give_less", fear_d, neu_d, "lt"),
    }
    RESULT["predictions"] = preds

    bits = []
    for k, v in preds.items():
        if v.get("holds") is True:
            bits.append(f"{k} holds (Δ={v['delta']:.3f})")
        elif v.get("lean"):
            bits.append(f"{k} leans but CI crosses 0 (Δ={v.get('delta')})")
        else:
            bits.append(f"{k} does not hold (Δ={v.get('delta')})")
    RESULT["mechanism_answer"] = (
        "On Gemma-4-E4B-it with natural EMOTIC prepend and forced-choice letters, "
        + "; ".join(bits)
        + f". Mean FC mass={mean_mass:.3f}."
    )

    RESULT["aggregates"] = {
        "dictator_pooled": {
            c: mean_ci(pool_tasks("dictator_", c), seed=11)
            for c in list(TARGET_CATS) + ["neutral", "no_image"]
        },
        "ug_offer_pooled": {
            c: mean_ci(pool_tasks("ug_offer_", c), seed=12)
            for c in list(TARGET_CATS) + ["neutral", "no_image"]
        },
        "ug_reject_unfair_pooled": {
            c: mean_ci(
                by.get("ug_reject_90_10", {}).get(c, []) + by.get("ug_reject_80_20", {}).get(c, []),
                seed=99,
            )
            for c in set(list(by.get("ug_reject_90_10", {})) + list(by.get("ug_reject_80_20", {})))
        },
    }
    RESULT["item_hashes"] = {
        "dictator_0_50": hashlib.sha256(amount_prompt("dictator", 0, 50, False)[0].encode()).hexdigest()[:16],
        "ug_offer_50_80": hashlib.sha256(amount_prompt("ug_offer", 50, 80, True)[0].encode()).hexdigest()[:16],
        "ug_respond_90_10": hashlib.sha256(ug_respond_prompt(90, 10, True)[0].encode()).hexdigest()[:16],
    }
    RESULT["complete"] = True
    _finalize_gates()
    heartbeat("done", n=len(rows_out), mass=mean_mass)
    save()
    log(f"done passed={RESULT['gates']['passed']}/{RESULT['gates']['total']} mass={mean_mass:.3f}")
    log(RESULT["mechanism_answer"])
    return 0 if RESULT["gates"]["passed"] == RESULT["gates"]["total"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
