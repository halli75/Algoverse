# exp02 A100 runner — scene-matched EMOTIC caliper pairs, risk + dictator A/B.
# Gemma-4-E4B-it nf4/bf16. Own process. CUDA_VISIBLE_DEVICES=5.
# Never writes artifacts/colab/e2e_mechanism_results_full_v3.json.
# [[battery-campaign]] [[EMOTIC]]
from __future__ import annotations

import hashlib
import json
import math
import os
import random
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import battery_exp02_pairs as P  # noqa: E402

EXPERIMENT = "exp02"
PRIMARY = "google/gemma-4-E4B-it"
FROZEN_V3 = "e2e_mechanism_results_full_v3.json"
FC_MASS_MIN = 0.8
N_BOOT = 10000
SEEDS = (0, 1, 2)
SWAP_FRAC = 0.25
GPU_PREF = "5"
PRIMARY_FAMILY = "fear_anger"
T0 = time.time()


def _env_path(name: str, default: Path) -> Path:
    raw = os.environ.get(name)
    return Path(raw).expanduser() if raw else default


def paths() -> dict[str, Path]:
    root = P.e2e_root()
    bat = _env_path("E2E_EXP02", root / "battery" / "exp02")
    local = P.local_art()
    bat.mkdir(parents=True, exist_ok=True)
    return {
        "root": root,
        "bat": bat,
        "local": local,
        "results": bat / "results.json",
        "ckpt": bat / "checkpoint.json",
        "hb": bat / "heartbeat.json",
        "pairs": bat / "pairs.json",
        "partial": bat / "partial.json",
        "lock": _env_path("E2E_LOCK", root / "battery" / "A100.lock"),
        "hf_lock": _env_path("E2E_HF_LOCK", root / "battery" / "hf_download.lock"),
        "emotic": _env_path("E2E_EMOTIC", root / "emotic_data"),
        "split": _env_path("E2E_SPLIT", root / "emotic_split.json"),
        "local_results": local / "results.json",
        "local_hb": local / "heartbeat.json",
        "local_pairs": local / "pairs.json",
        "local_ckpt": local / "checkpoint.json",
    }


RESULT: dict = {
    "experiment": EXPERIMENT,
    "started": time.strftime("%Y-%m-%d %T"),
    "model_id": PRIMARY,
    "weights_dtype": "nf4",
    "compute_dtype": "bf16",
    "split_expected": P.EXPECTED_SPLIT,
    "advisor": "2ebc4933-bcc2-4967-af4f-05ceb379a2ed",
    "notes": [],
    "pair_report": {},
    "effects": {},
    "gates": {},
    "mechanism_answer": None,
    "complete": False,
}


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def heartbeat(stage: str, **kw) -> None:
    p = paths()
    payload = {
        "job": EXPERIMENT,
        "stage": stage,
        "ts": time.time(),
        "iso": time.strftime("%Y-%m-%d %T"),
        "elapsed_s": round(time.time() - T0, 1),
        "gpu": os.environ.get("CUDA_VISIBLE_DEVICES", ""),
        "pid": os.getpid(),
        **kw,
    }
    P.write_json(p["hb"], payload)
    try:
        P.write_json(p["local_hb"], payload)
    except Exception:
        pass


def save() -> None:
    p = paths()
    RESULT["updated"] = time.strftime("%Y-%m-%d %T")
    RESULT["elapsed_s"] = round(time.time() - T0, 1)
    P.write_json(p["results"], RESULT)
    try:
        P.write_json(p["local_results"], RESULT)
    except Exception:
        pass


def note(msg: str) -> None:
    log("NOTE " + msg)
    RESULT.setdefault("notes", []).append(msg)


def die(msg: str) -> None:
    log("FATAL " + msg)
    RESULT["fatal"] = msg
    RESULT["complete"] = False
    RESULT["mechanism_answer"] = RESULT.get("mechanism_answer") or f"ENDPOINT_INVALID: {msg}"
    _gate_summary()
    save()
    heartbeat("die", error=msg[:400])
    raise SystemExit(1)


FREE_MIN_MB = 18 * 1024
CANDIDATE_GPUS = ("4", "5", "2", "1", "0", "3", "6", "7")
PREFERRED_GPUS = ("4", "5", "2")


def gpu_mem() -> dict[str, dict[str, int]]:
    import subprocess

    out = subprocess.check_output(
        ["nvidia-smi", "--query-gpu=index,memory.used,memory.free", "--format=csv,noheader,nounits"],
        text=True,
    )
    rec = {}
    for line in out.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 3:
            rec[parts[0]] = {"used": int(float(parts[1])), "free": int(float(parts[2]))}
    return rec


def live_gemma() -> list[dict]:
    """Real compute processes only. Zombie [Not Found] CUDA contexts do not count."""
    import subprocess

    out = subprocess.check_output(
        ["nvidia-smi", "--query-compute-apps=gpu_bus_id,pid,process_name,used_gpu_memory", "--format=csv,noheader,nounits"],
        text=True,
    )
    bus = subprocess.check_output(
        ["nvidia-smi", "--query-gpu=index,pci.bus_id", "--format=csv,noheader"],
        text=True,
    )
    bus_to_idx = {}
    for line in bus.strip().splitlines():
        idx, pci = [p.strip() for p in line.split(",", 1)]
        bus_to_idx[pci] = idx
        bus_to_idx[pci.split(":", 1)[-1] if ":" in pci else pci] = idx
    live = []
    for line in out.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 4:
            continue
        gpu_bus, pid, name, mem = parts[0], parts[1], parts[2], parts[3]
        if "[Not Found]" in name:
            continue
        try:
            mem_i = int(float(mem))
        except Exception:
            mem_i = 0
        if mem_i < 2000:
            continue
        idx = bus_to_idx.get(gpu_bus) or bus_to_idx.get(gpu_bus.upper())
        live.append({"gpu": idx, "pid": pid, "name": name, "mb": mem_i})
    return live


def pick_gpu() -> str | None:
    mem = gpu_mem()
    live = live_gemma()
    live_gpus = {r["gpu"] for r in live if r.get("gpu") is not None}
    if len(live) >= 4:
        return None
    ranked = []
    for gid in CANDIDATE_GPUS:
        if gid not in mem:
            continue
        if gid in live_gpus:
            continue
        free = mem[gid]["free"]
        if free >= FREE_MIN_MB:
            pref = 0 if gid in PREFERRED_GPUS else 1
            ranked.append((pref, -free, gid))
    if not ranked:
        return None
    ranked.sort()
    return ranked[0][2]


def wait_gpu_free() -> None:
    t_end = time.time() + 180 * 60
    while time.time() < t_end:
        try:
            mem = gpu_mem()
            live = live_gemma()
            chosen = pick_gpu()
        except Exception as e:
            log(f"nvidia-smi skip: {e}")
            return
        if chosen is not None:
            os.environ["CUDA_VISIBLE_DEVICES"] = chosen
            os.environ["EXP02_GPU"] = chosen
            log(f"claim gpu {chosen} free={mem[chosen]['free']} live_gemma={live}")
            heartbeat("gpu_claim", gpu=chosen, free_mb=mem[chosen]["free"], n_live=len(live))
            return
        snap = {g: mem[g]["free"] for g in ("4", "5", "2", "1") if g in mem}
        log(f"waiting gpu free={snap} live_gemma={len(live)}")
        heartbeat("wait_gpu_occ", free=snap, n_live=len(live))
        time.sleep(45)
    die("no GPU with 18 GiB free after wait")


def claim_gpu_lock() -> None:
    p = paths()
    gpu = os.environ.get("CUDA_VISIBLE_DEVICES", GPU_PREF)
    lock_path = p["lock"]
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    now = time.time()
    data = {"holders": {}}
    if lock_path.exists():
        try:
            data = json.loads(lock_path.read_text(encoding="utf-8"))
        except Exception:
            data = {"holders": {}}
    holders = data.setdefault("holders", {})
    def _pid_alive(pid) -> bool:
        try:
            os.kill(int(pid), 0)
            return True
        except Exception:
            return False

    live = [
        gid
        for gid, rec in holders.items()
        if now - float(rec.get("unix") or 0) <= 20 * 60
        and rec.get("exp") != EXPERIMENT
        and _pid_alive(rec.get("pid"))
    ]
    if len(live) >= 4 and gpu not in live:
        t_end = time.time() + 90 * 60
        while time.time() < t_end:
            log(f"waiting: {len(live)} GPU jobs live {live}")
            heartbeat("wait_gpu_cap", n_live=len(live), live=live)
            time.sleep(30)
            now = time.time()
            if lock_path.exists():
                try:
                    data = json.loads(lock_path.read_text(encoding="utf-8"))
                except Exception:
                    data = {"holders": {}}
            holders = data.setdefault("holders", {})
            live = [
                gid
                for gid, rec in holders.items()
                if now - float(rec.get("unix") or 0) <= 20 * 60
                and rec.get("exp") != EXPERIMENT
                and _pid_alive(rec.get("pid"))
            ]
            if len(live) < 4 or gpu in live:
                break
        else:
            die(f"max concurrent GPU jobs still {len(live)} after wait")
    other = holders.get(gpu, {})
    if other.get("exp") and other.get("exp") != EXPERIMENT:
        age = now - float(other.get("unix") or 0)
        if age < 20 * 60 and not other.get("stale"):
            die(f"GPU {gpu} held by {other.get('exp')}")
    holders[gpu] = {"exp": EXPERIMENT, "pid": os.getpid(), "unix": time.time(), "ts": time.strftime("%Y-%m-%d %T")}
    P.write_json(lock_path, {"holders": holders})
    RESULT["phases"] = RESULT.get("phases") or {}
    RESULT["phases"]["gpu_lock"] = holders[gpu]
    log(f"claimed GPU {gpu} n_live={len(live)}")


def refresh_lock() -> None:
    p = paths()
    gpu = os.environ.get("CUDA_VISIBLE_DEVICES", GPU_PREF)
    try:
        data = json.loads(p["lock"].read_text(encoding="utf-8")) if p["lock"].exists() else {"holders": {}}
        rec = data.setdefault("holders", {}).get(gpu, {})
        rec.update({"exp": EXPERIMENT, "pid": os.getpid(), "unix": time.time(), "ts": time.strftime("%Y-%m-%d %T")})
        data["holders"][gpu] = rec
        P.write_json(p["lock"], data)
    except Exception as e:
        log(f"lock refresh skip: {e}")


def wait_hf_download() -> None:
    p = paths()
    cache = Path.home() / ".cache" / "huggingface" / "hub"
    if cache.exists() and list(cache.glob("models--google--gemma-4-E4B-it")):
        log("HF gemma-4-E4B-it cache present")
        return
    dl = p["hf_lock"]
    t_end = time.time() + 40 * 60
    while time.time() < t_end:
        if not dl.exists():
            P.write_json(dl, {"exp": EXPERIMENT, "unix": time.time()})
            log("took hf_download.lock")
            return
        try:
            rec = json.loads(dl.read_text(encoding="utf-8"))
            if time.time() - float(rec.get("unix") or 0) > 20 * 60:
                P.write_json(dl, {"exp": EXPERIMENT, "unix": time.time(), "stolen": True})
                log("stole stale hf_download.lock")
                return
        except Exception:
            return
        log("waiting for first HF download")
        heartbeat("wait_hf")
        time.sleep(20)
    note("hf download wait timed out; proceeding")


def release_hf_lock() -> None:
    p = paths()
    try:
        if p["hf_lock"].exists():
            rec = json.loads(p["hf_lock"].read_text(encoding="utf-8"))
            if rec.get("exp") == EXPERIMENT:
                p["hf_lock"].unlink()
    except Exception:
        pass


def source_battery_env() -> None:
    """Load ~/.battery_env KEY=VAL into os.environ. Never print values."""
    p = Path.home() / ".battery_env"
    if not p.is_file():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        if s.startswith("export "):
            s = s[7:].strip()
        k, _, v = s.partition("=")
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k:
            os.environ.setdefault(k, v)


def load_hf_token() -> str | None:
    source_battery_env()
    if os.environ.get("HF_TOKEN"):
        return os.environ["HF_TOKEN"].strip()
    for cand in (Path.home() / ".hf_token", Path.home() / ".cache" / "huggingface" / "token"):
        if cand.is_file():
            tok = cand.read_text(encoding="utf-8").strip()
            if tok:
                os.environ["HF_TOKEN"] = tok
                os.environ.setdefault("HUGGING_FACE_HUB_TOKEN", tok)
                return tok
    return None


def first_ids(tok, s: str) -> list[int]:
    out = []
    for pre in (" " + s, s):
        t = tok(pre, add_special_tokens=False).input_ids
        if len(t) == 1:
            out.append(int(t[0]))
    return sorted(set(out))


def crossed_bootstrap(pair_item_deltas: dict[tuple[str, str], float], n_boot: int = N_BOOT, seed: int = 0) -> dict:
    """Resample pair IDs and item IDs; mean of cell means. 95% percentile CI."""
    pairs = sorted({pid for pid, _ in pair_item_deltas})
    items = sorted({iid for _, iid in pair_item_deltas})
    if not pairs or not items:
        return {"estimate": None, "ci95": [None, None], "n": 0, "finite": False}
    cells = {(pid, iid): pair_item_deltas[(pid, iid)] for pid, iid in pair_item_deltas if math.isfinite(pair_item_deltas[(pid, iid)])}
    if not cells:
        return {"estimate": None, "ci95": [None, None], "n": 0, "finite": False}

    def stat(ps, its):
        vals = [cells[(p, i)] for p in ps for i in its if (p, i) in cells]
        return float(np.mean(vals)) if vals else None

    point = stat(pairs, items)
    rng = np.random.default_rng(seed)
    boots = []
    for _ in range(n_boot):
        ps = rng.choice(pairs, size=len(pairs), replace=True)
        its = rng.choice(items, size=len(items), replace=True)
        v = stat(list(ps), list(its))
        if v is not None:
            boots.append(v)
    if not boots or point is None:
        return {"estimate": point, "ci95": [None, None], "n": len(pairs), "finite": point is not None}
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {"estimate": float(point), "ci95": [float(lo), float(hi)], "n": len(pairs), "n_items": len(items), "finite": True}


def load_exp01(p: dict[str, Path]) -> dict | None:
    cands = [
        p["root"] / "battery" / "exp01" / "results.json",
        p["local"].parent / "exp01" / "results.json",
        Path(__file__).resolve().parent.parent / "artifacts" / "battery" / "exp01" / "results.json",
    ]
    for c in cands:
        if c.exists():
            try:
                rec = json.loads(c.read_text(encoding="utf-8"))
                rec["_source"] = str(c)
                return rec
            except Exception:
                continue
    return None


def exp01_unmatched_delta(exp01: dict | None) -> dict | None:
    if not exp01:
        return None
    if exp01.get("delta_anger_minus_fear") is not None:
        ci = exp01.get("delta_ci95_boot") or [None, None]
        return {
            "estimate": float(exp01["delta_anger_minus_fear"]),
            "ci95": [float(ci[0]) if ci[0] is not None else None, float(ci[1]) if ci[1] is not None else None],
            "source": "exp01.delta_anger_minus_fear",
        }
    for path in (
        ("effects", "risk", "fear_anger"),
        ("effects", "risk", "anger_minus_fear"),
        ("primary", "risk", "fear_vs_anger"),
        ("primary", "delta_fear_anger_risk"),
    ):
        cur = exp01
        ok = True
        for k in path:
            if not isinstance(cur, dict) or k not in cur:
                ok = False
                break
            cur = cur[k]
        if ok and isinstance(cur, dict) and cur.get("estimate") is not None:
            return cur
        if ok and isinstance(cur, (int, float)):
            return {"estimate": float(cur), "ci95": [None, None]}
    return None


def _gate_summary() -> None:
    g = RESULT.get("gates") or {}
    passed = sum(1 for v in g.values() if isinstance(v, dict) and v.get("pass") is True)
    total = sum(1 for v in g.values() if isinstance(v, dict) and "pass" in v)
    RESULT["gates"]["passed"] = passed
    RESULT["gates"]["total"] = total


def mechanism_answer(effects: dict, pair_report: dict, exp01_delta: dict | None, mass_ok: bool) -> str:
    fa = pair_report.get(PRIMARY_FAMILY) or {}
    if not mass_ok:
        return "ENDPOINT_INVALID"
    if fa.get("status") != "OK" or int(fa.get("n") or 0) < P.N_MIN:
        return "PAIR_FAMILY_ABORT"
    if exp01_delta is None:
        return "EXP01_PENDING"
    du = exp01_delta.get("estimate")
    ci_u = exp01_delta.get("ci95") or [exp01_delta.get("ci_lo"), exp01_delta.get("ci_hi")]
    if du is None or ci_u[0] is None or ci_u[1] is None:
        return "EXP01_PENDING"
    s = 1.0 if du >= 0 else -1.0
    if not (s * ci_u[0] > 0 and s * ci_u[1] > 0):
        return "NO_EXP01_EFFECT_TO_EXPLAIN"
    risk_fa = ((effects.get("risk") or {}).get("fear_anger") or {})
    dm = risk_fa.get("estimate")
    ci_m = risk_fa.get("ci95") or [None, None]
    if dm is None or ci_m[0] is None:
        return "INCONCLUSIVE"
    matched_same = s * ci_m[0] > 0
    # attenuation CI: bootstrap not available for exp01 cells here; use interval difference bound
    # s*(ΔU-ΔM) > 0 if lower bound of s*ΔU - upper bound of s*ΔM > 0
    atten = (s * ci_u[0] - s * ci_m[1]) > 0
    RESULT["gates"]["exp01_available"] = {"pass": True, "value": True}
    RESULT["gates"]["unmatched_effect"] = {"pass": True, "value": True, "delta": du, "ci95": ci_u}
    RESULT["gates"]["matched_same_direction"] = {"pass": matched_same, "value": matched_same, "delta": dm, "ci95": ci_m}
    RESULT["gates"]["attenuation"] = {"pass": atten, "value": atten}
    semantic = (not matched_same) and atten
    RESULT["gates"]["semantic_confound"] = {"pass": semantic, "value": semantic}
    if semantic:
        return "SEMANTIC_CONFOUND"
    if matched_same and not atten:
        return "PERSISTS_AFTER_MATCHING"
    if (not matched_same) and not atten:
        return "PARTIAL_ATTENUATION"
    if matched_same and atten:
        return "PARTIAL_ATTENUATION"
    return "INCONCLUSIVE"


def build_trials(families: dict, items: list[dict], seeds: tuple[int, ...]) -> list[dict]:
    trials = []
    rng_swap = random.Random(7)
    for fam_name, fam in families.items():
        if fam.get("status") != "OK":
            continue
        pairs = fam.get("pairs") or []
        for seed in seeds:
            order = list(range(len(pairs)))
            random.Random(seed).shuffle(order)
            for pi in order:
                pair = pairs[pi]
                for item in items:
                    base = {
                        "family": fam_name,
                        "pair_id": f"{pair['left_id']}::{pair['right_id']}",
                        "left_id": pair["left_id"],
                        "right_id": pair["right_id"],
                        "item_id": item["id"],
                        "task": item["task"],
                        "seed": seed,
                        "item": item,
                    }
                    trials.append({**base, "swap": False})
                    if rng_swap.random() < SWAP_FRAC:
                        trials.append({**base, "swap": True})
    return trials


def side_score_rows(rows: list[dict]) -> dict[tuple, float]:
    """Average remaps/swaps: (family, task, pair_id, item_id, side) -> S."""
    buckets: dict[tuple, list[float]] = defaultdict(list)
    for r in rows:
        if r.get("S") is None or not math.isfinite(r["S"]):
            continue
        key = (r["family"], r["task"], r["pair_id"], r["item_id"], r["side"])
        buckets[key].append(float(r["S"]))
    return {k: float(np.mean(v)) for k, v in buckets.items()}


def family_deltas(avg: dict[tuple, float], family: str, task: str) -> dict[tuple[str, str], float]:
    left = {}
    right = {}
    for (fam, tsk, pid, iid, side), val in avg.items():
        if fam != family or tsk != task:
            continue
        if side == "left":
            left[(pid, iid)] = val
        else:
            right[(pid, iid)] = val
    out = {}
    for key in left.keys() & right.keys():
        # locked estimand: anger − fear for fear_anger (right=anger, left=fear)
        out[key] = right[key] - left[key]
    return out


def main() -> int:
    os.environ.setdefault("CUDA_VISIBLE_DEVICES", os.environ.get("EXP02_GPU", GPU_PREF))
    os.environ.setdefault("E2E_NO_FALLBACK", "1")
    mid = os.environ.get("E2E_MODEL", PRIMARY)
    if mid != PRIMARY:
        die(f"fallback model forbidden: {mid}")
    tier = os.environ.get("E2E_TIER", "full").lower()
    if tier not in ("smoke", "full"):
        die(f"bad tier {tier}")
    p = paths()
    heartbeat("start", tier=tier)
    save()

    n_risk = int(os.environ.get("EXP02_N_RISK", "8" if tier == "full" else "4"))
    n_dict = int(os.environ.get("EXP02_N_DICT", "8" if tier == "full" else "4"))
    seeds = SEEDS if tier == "full" else (0, 1)
    items = P.risk_items(n_risk, seed=0) + P.dictator_items(n_dict, seed=1)
    if any(P.DESCRIBE.lower() in it["prompt"].lower() for it in items):
        die("DESCRIBE leaked into items")

    heartbeat("pairing")
    rebuild = os.environ.get("EXP02_REBUILD", "0") == "1"
    if p["pairs"].exists() and not rebuild:
        pairs_payload = json.loads(p["pairs"].read_text(encoding="utf-8"))
        fam0 = (pairs_payload.get("families") or {}).get(PRIMARY_FAMILY) or {}
        if fam0.get("status") != "OK":
            log("primary family not OK — rebuilding pairs")
            rebuild = True
        else:
            log(f"loaded pairs {p['pairs']}")
    if rebuild or not p["pairs"].exists():
        if p["pairs"].exists():
            p["pairs"].unlink()
        log("building pairs")
        rc = P.main([])
        if rc != 0:
            die("pairing failed")
        pairs_payload = json.loads(p["pairs"].read_text(encoding="utf-8"))
    try:
        P.write_json(p["local_pairs"], pairs_payload)
    except Exception:
        pass
    families = pairs_payload.get("families") or {}
    RESULT["pair_report"] = {
        k: {kk: vv for kk, vv in v.items() if kk != "pairs"} | {"n": v.get("n"), "tier": v.get("tier"), "status": v.get("status")}
        for k, v in families.items()
    }
    RESULT["pair_report_meta"] = {
        "n_jpg": pairs_payload.get("n_jpg"),
        "n_eval_images": pairs_payload.get("n_eval_images"),
        "pool_sizes": pairs_payload.get("pool_sizes"),
        "split_hash": pairs_payload.get("split_hash"),
    }
    save()
    if (families.get(PRIMARY_FAMILY) or {}).get("status") != "OK":
        RESULT["mechanism_answer"] = "PAIR_FAMILY_ABORT"
        _gate_summary()
        RESULT["complete"] = True
        save()
        log("fear_anger pairing aborted — writing PAIR_FAMILY_ABORT")
        return 0

    # prioritize primary + neg-neu, then the rest
    priority = [PRIMARY_FAMILY, "negative_neutral", "fear_neutral", "anger_neutral", "sadness_happiness", "sadness_neutral", "happiness_neutral"]
    only = [x.strip() for x in os.environ.get("EXP02_FAMILIES", "").split(",") if x.strip()]
    if only:
        priority = [k for k in priority if k in only]
    active = {k: families[k] for k in priority if k in families}
    trials = build_trials(active, items, seeds)
    log(f"trials={len(trials)} families={[k for k,v in active.items() if v.get('status')=='OK']}")

    ckpt = {"done": {}, "rows": []}
    if p["ckpt"].exists():
        try:
            ckpt = json.loads(p["ckpt"].read_text(encoding="utf-8"))
            log(f"resume ckpt n={len(ckpt.get('rows') or [])}")
        except Exception as e:
            log(f"ckpt read fail {e}")
    done = set(ckpt.get("done") or [])
    rows: list[dict] = list(ckpt.get("rows") or [])

    wait_gpu_free()
    claim_gpu_lock()
    wait_hf_download()
    heartbeat("model_load")
    token = load_hf_token()
    import torch
    from PIL import Image
    from transformers import AutoModelForImageTextToText, AutoProcessor, BitsAndBytesConfig

    if not torch.cuda.is_available():
        die("no CUDA")
    RESULT["gpu"] = torch.cuda.get_device_name(0)
    RESULT["cuda_visible"] = os.environ.get("CUDA_VISIBLE_DEVICES")
    bnb = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
    )
    log(f"loading {mid} nf4 bf16")
    model = AutoModelForImageTextToText.from_pretrained(
        mid, quantization_config=bnb, device_map={"": 0}, torch_dtype=torch.bfloat16, token=token or True,
    )
    proc = AutoProcessor.from_pretrained(mid, token=token or True)
    model.eval()
    for param in model.parameters():
        param.requires_grad = False
    release_hf_lock()
    tokn = proc.tokenizer if hasattr(proc, "tokenizer") else proc
    label_ids = {lab: first_ids(tokn, lab) for lab in ("A", "B")}
    if not label_ids["A"] or not label_ids["B"]:
        die(f"A/B not single-token: {label_ids}")
    log(f"token A={label_ids['A']} B={label_ids['B']}")
    RESULT["phases"] = RESULT.get("phases") or {}
    RESULT["phases"]["token_ids"] = label_ids
    device = torch.device("cuda:0")

    def build_inputs(text: str, image):
        content = [{"type": "image"}, {"type": "text", "text": text}]
        prompt = proc.apply_chat_template(
            [{"role": "user", "content": content}], add_generation_prompt=True, tokenize=False,
        )
        return proc(text=[prompt], images=[image], return_tensors="pt")

    img_cache: dict[str, Image.Image] = {}

    def get_image(rid: str):
        if rid not in img_cache:
            folder, fn = rid.split("/", 1)
            path = p["emotic"] / "emotic" / folder / fn
            img_cache[rid] = Image.open(path).convert("RGB")
        return img_cache[rid]

    def score_one(text: str, image, primary: str, other: str) -> tuple[float, float]:
        inp = build_inputs(text, image)
        inp = {k: (v.to(device) if hasattr(v, "to") else v) for k, v in inp.items()}
        with torch.no_grad():
            out = model(**inp)
            lp = torch.log_softmax(out.logits[0, -1].float(), dim=-1)

        def mass(lab: str) -> float:
            ids = label_ids[lab]
            return float(torch.logsumexp(lp[ids], 0))

        lm, ln = mass(primary), mass(other)
        return (lm - ln), float(math.exp(lm) + math.exp(ln))

    n = len(trials)
    scored = 0
    for i, tr in enumerate(trials):
        base_key = f"{tr['family']}|{tr['pair_id']}|{tr['item_id']}|{tr['seed']}|{int(tr['swap'])}"
        if base_key + "|L" in done and base_key + "|R" in done:
            continue
        item = tr["item"]
        prompt = item["prompt"]
        prim, oth = item["primary_label"], item["other_label"]
        if tr["swap"]:
            # swap letter semantics: rebuild prompt A/B lines
            prim, oth = oth, prim
            prompt = prompt.replace("(A) ", "(A0) ").replace("(B) ", "(A) ").replace("(A0) ", "(B) ")
        for side, rid in (("left", tr["left_id"]), ("right", tr["right_id"])):
            key = base_key + f"|{side[0].upper()}"
            if key in done:
                continue
            try:
                S, mass = score_one(prompt, get_image(rid), prim, oth)
                row = {
                    "family": tr["family"],
                    "pair_id": tr["pair_id"],
                    "item_id": item["id"],
                    "task": item["task"],
                    "seed": tr["seed"],
                    "swap": tr["swap"],
                    "side": side,
                    "rid": rid,
                    "S": S,
                    "fc_mass": mass,
                    "primary": prim,
                }
            except Exception as e:
                log(f"skip {key}: {type(e).__name__}: {e}")
                try:
                    torch.cuda.empty_cache()
                except Exception:
                    pass
                row = {
                    "family": tr["family"],
                    "pair_id": tr["pair_id"],
                    "item_id": item["id"],
                    "task": item["task"],
                    "seed": tr["seed"],
                    "swap": tr["swap"],
                    "side": side,
                    "rid": rid,
                    "S": None,
                    "fc_mass": None,
                    "error": type(e).__name__,
                }
            rows.append(row)
            done.add(key)
            scored += 1
        if i % 4 == 0:
            heartbeat("score", i=i, n=n, leftover=n - i)
            refresh_lock()
        if i % 8 == 0:
            ckpt = {"done": sorted(done), "rows": rows}
            P.write_json(p["ckpt"], ckpt)
            try:
                P.write_json(p["local_ckpt"], {"n_rows": len(rows), "i": i, "n": n})
            except Exception:
                pass
            RESULT["n_scored"] = len(rows)
            save()
            log(f"score {i}/{n} rows={len(rows)}")

    P.write_json(p["ckpt"], {"done": sorted(done), "rows": rows})
    heartbeat("stats", n_rows=len(rows))

    masses = [r["fc_mass"] for r in rows if r.get("fc_mass") is not None]
    mean_mass = float(np.mean(masses)) if masses else 0.0
    finite_ok = bool(rows) and all(r.get("S") is None or math.isfinite(r["S"]) for r in rows)
    RESULT["gates"]["forced_choice_mass"] = {
        "pass": mean_mass >= FC_MASS_MIN,
        "mean": mean_mass,
        "n": len(masses),
        "threshold": FC_MASS_MIN,
    }
    RESULT["gates"]["finite_S"] = {"pass": finite_ok, "value": finite_ok}

    # per task×condition mass
    mass_ok = mean_mass >= FC_MASS_MIN and finite_ok
    by_tc = defaultdict(list)
    for r in rows:
        if r.get("fc_mass") is not None:
            by_tc[(r["task"], r["family"], r["side"])].append(r["fc_mass"])
    RESULT["gates"]["forced_choice_mass_by_cell"] = {}
    for k, xs in by_tc.items():
        m = float(np.mean(xs))
        ok = m >= FC_MASS_MIN
        RESULT["gates"]["forced_choice_mass_by_cell"][f"{k[0]}|{k[1]}|{k[2]}"] = {"pass": ok, "mean": m, "n": len(xs)}
        if not ok:
            mass_ok = False

    avg = side_score_rows(rows)
    effects: dict[str, dict] = {"risk": {}, "dictator": {}}
    for fam in active:
        for task in ("risk", "dictator"):
            deltas = family_deltas(avg, fam, task)
            if not deltas:
                continue
            # map family name to contrast name
            contrast = fam
            if fam == PRIMARY_FAMILY:
                contrast = "fear_anger"
            rec = crossed_bootstrap(
                deltas,
                n_boot=N_BOOT if tier == "full" else 256,
                seed=int(hashlib.sha256(f"{fam}:{task}".encode()).hexdigest()[:8], 16) % 10000,
            )
            rec["n_cells"] = len(deltas)
            effects[task][contrast] = rec
    RESULT["effects"] = effects
    RESULT["n_rows"] = len(rows)
    RESULT["n_trials"] = n

    exp01 = load_exp01(p)
    RESULT["gates"]["exp01_available"] = {"pass": exp01 is not None, "value": exp01 is not None, "source": (exp01 or {}).get("_source")}
    exp01_delta = exp01_unmatched_delta(exp01)
    RESULT["exp01_unmatched"] = exp01_delta
    RESULT["mechanism_answer"] = mechanism_answer(effects, families, exp01_delta, mass_ok)
    _gate_summary()
    RESULT["complete"] = True
    RESULT["sha256_pairs"] = hashlib.sha256(p["pairs"].read_bytes()).hexdigest() if p["pairs"].exists() else None
    save()
    heartbeat("done", answer=RESULT["mechanism_answer"])
    log(f"done answer={RESULT['mechanism_answer']} gates={RESULT['gates'].get('passed')}/{RESULT['gates'].get('total')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
