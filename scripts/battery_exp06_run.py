"""exp06 A100 runner — Gemma-4-E4B-it nf4/bf16, first-token A/B, no DESCRIBE.

Own kernel. CUDA_VISIBLE_DEVICES must already be the claimed GPU.
Never writes artifacts/colab/e2e_mechanism_results_full_v3.json.
Aggregate rates only — no completions.
"""

from __future__ import annotations

import ast
import hashlib
import json
import math
import os
import sys
import time
import traceback
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import battery_exp06_core as core  # noqa: E402

PRIMARY = core.PRIMARY_MODEL
EXPECTED_SPLIT = core.EXPECTED_SPLIT
FROZEN_V3 = "e2e_mechanism_results_full_v3.json"


def _env_path(name: str, default: Path) -> Path:
    raw = os.environ.get(name)
    return Path(raw).expanduser() if raw else default


def _root() -> Path:
    return Path(os.environ.get("E2E_ROOT", str(Path.home() / "algoverse_run"))).expanduser()


def paths() -> dict[str, Path]:
    root = _root()
    bat = root / "battery" / "exp06"
    local = _HERE.parent / "artifacts" / "battery" / "exp06"
    out_root = _env_path("EXP06_OUT", local if local.parent.exists() else bat)
    out_root.mkdir(parents=True, exist_ok=True)
    return {
        "root": root,
        "bat": bat,
        "out": out_root,
        "results": out_root / "results.json",
        "ckpt": out_root / f"checkpoint_{os.environ.get('E2E_TIER', os.environ.get('EXP06_TIER', 'smoke')).strip().lower()}.json",
        "hb": out_root / "heartbeat.json",
        "log": out_root / "run.log",
        "status": out_root / "STATUS.md",
        "emotic": _env_path("E2E_EMOTIC", root / "emotic_data"),
        "split": _env_path("E2E_SPLIT", root / "emotic_split.json"),
    }


T0 = time.time()


def log(msg: str) -> None:
    p = paths()
    line = f"{time.strftime('%H:%M:%S')} {msg}"
    print(line, flush=True)
    p["log"].parent.mkdir(parents=True, exist_ok=True)
    with p["log"].open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def heartbeat(stage: str, **kw) -> None:
    p = paths()
    payload = {
        "exp": "exp06",
        "stage": stage,
        "ts": time.time(),
        "elapsed_s": time.time() - T0,
        "gpu": os.environ.get("CUDA_VISIBLE_DEVICES"),
        "pid": os.getpid(),
        **kw,
    }
    tmp = p["hb"].with_name(p["hb"].name + ".tmp")
    tmp.write_text(json.dumps(payload), encoding="utf-8")
    os.replace(tmp, p["hb"])
    # also mirror under E2E_ROOT/battery/exp06
    alt = p["bat"] / "heartbeat.json"
    try:
        alt.parent.mkdir(parents=True, exist_ok=True)
        alt.write_text(json.dumps(payload), encoding="utf-8")
    except Exception:
        pass


def write_status(phase: str, note: str = "") -> None:
    p = paths()
    body = (
        f"# exp06 STATUS\n\n"
        f"- phase: {phase}\n"
        f"- ts: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n"
        f"- gpu: {os.environ.get('CUDA_VISIBLE_DEVICES')}\n"
        f"- pid: {os.getpid()}\n"
        f"- elapsed_s: {time.time() - T0:.0f}\n"
        f"- note: {note}\n"
        f"- hb: {p['hb']}\n"
        f"- results: {p['results']}\n"
    )
    p["status"].write_text(body, encoding="utf-8")


def die(msg: str) -> None:
    log("DIE " + msg)
    heartbeat("die", error=msg[:400])
    write_status("die", msg[:200])
    raise SystemExit(msg)


def atomic_json(path: Path, obj: dict) -> None:
    if path.name == FROZEN_V3 or path.as_posix().endswith("artifacts/colab/" + FROZEN_V3):
        die("refused to write frozen v3")
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def source_battery_env() -> None:
    try:
        import battery_adapter as ba

        ba.source_battery_env()
        ba.plant_hf_token()
        return
    except Exception:
        pass
    p = Path.home() / ".battery_env"
    if p.is_file():
        for raw in p.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            if line.startswith("export "):
                line = line[7:]
            k, _, v = line.partition("=")
            k, v = k.strip(), v.strip().strip("'").strip('"')
            if k and k not in os.environ:
                os.environ[k] = v
    for name, path in (("HF_TOKEN", Path.home() / ".hf_token"), ("XAI_API_KEY", Path.home() / ".xai_api_key")):
        if not os.environ.get(name) and path.is_file():
            os.environ[name] = path.read_text(encoding="utf-8").strip()
    if os.environ.get("HF_TOKEN"):
        os.environ.setdefault("HUGGING_FACE_HUB_TOKEN", os.environ["HF_TOKEN"])


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


def load_emotic_pool(p: dict[str, Path], n_per: int, seed: int = 0) -> tuple[dict[str, list[dict]], str]:
    import pandas as pd
    from PIL import Image

    csv_path = p["emotic"] / "emotic_pre" / "train.csv"
    if not csv_path.exists():
        die(f"missing {csv_path}")
    if not p["split"].exists():
        die(f"missing {p['split']}")
    split = json.loads(p["split"].read_text(encoding="utf-8"))
    split_hash = hashlib.sha256(json.dumps(split, sort_keys=True).encode()).hexdigest()[:16]
    if split_hash != EXPECTED_SPLIT:
        die(f"split_hash={split_hash} != {EXPECTED_SPLIT}")
    df = pd.read_csv(csv_path)
    if "Categorical_Labels" in df.columns:
        df["Categorical_Labels"] = df["Categorical_Labels"].apply(
            lambda x: ast.literal_eval(x) if isinstance(x, str) and str(x).startswith("[") else x
        )

    def rid(row) -> str:
        return f"{row['Folder']}/{row['Filename']}"

    df = df.copy()
    df["rid"] = df.apply(rid, axis=1)
    eval_ids = set(split["eval_ids"])
    df = df[df.rid.isin(eval_ids)].drop_duplicates("rid").reset_index(drop=True)
    rng = np.random.default_rng(seed)
    pools: dict[str, list[dict]] = {c: [] for c in core.CONDITIONS if c != "no-image"}
    for _, row in df.iterrows():
        labs = core.labels_of(row.get("Categorical_Labels"))
        img_path = p["emotic"] / "emotic" / row["Folder"] / row["Filename"]
        if not img_path.exists():
            continue
        rec = {"rid": row["rid"], "path": str(img_path), "labels": sorted(labs)}
        for cond in pools:
            if core.is_eval_exclusive(labs, cond):
                pools[cond].append(rec)
    chosen: dict[str, list[dict]] = {}
    for cond, rows in pools.items():
        if not rows:
            die(f"no exclusive eval images for {cond}")
        idx = rng.permutation(len(rows))[:n_per]
        chosen[cond] = [rows[int(i)] for i in idx]
        log(f"pool {cond} available={len(rows)} take={len(chosen[cond])}")
    chosen["no-image"] = [{"rid": "no-image", "path": None, "labels": []}]
    # existence audit
    from PIL import Image as _Im

    for cond, rows in chosen.items():
        for rec in rows:
            if rec["path"]:
                im = _Im.open(rec["path"]).convert("RGB")
                if np.asarray(im).std() < 1.0:
                    die(f"solid image {rec['rid']}")
    return chosen, split_hash


def first_ids(tok, s: str) -> list[int]:
    out = []
    for pre in (" " + s, s):
        t = tok(pre, add_special_tokens=False).input_ids
        if len(t) == 1:
            out.append(int(t[0]))
    return sorted(set(out))


def main() -> int:
    os.environ.setdefault("CUDA_VISIBLE_DEVICES", os.environ.get("EXP06_GPU", "2"))
    mid = os.environ.get("E2E_MODEL", PRIMARY)
    if mid != PRIMARY:
        die(f"fallback model forbidden: {mid}")
    if os.environ.get("E2E_NO_FALLBACK", "1") != "1":
        os.environ["E2E_NO_FALLBACK"] = "1"
    tier = os.environ.get("E2E_TIER", os.environ.get("EXP06_TIER", "smoke")).strip().lower()
    if tier not in ("smoke", "full"):
        die(f"bad tier {tier}")
    n_per = int(os.environ.get("EXP06_N_IMG", "1" if tier == "smoke" else "4"))
    p = paths()
    p["bat"].mkdir(parents=True, exist_ok=True)
    p["out"].mkdir(parents=True, exist_ok=True)
    source_battery_env()
    heartbeat("boot", tier=tier)
    write_status("boot", f"tier={tier}")
    log(f"exp06 start tier={tier} n_img={n_per} gpu={os.environ.get('CUDA_VISIBLE_DEVICES')}")

    items = core.load_grid(tier=tier)
    log(f"grid n={len(items)} source={core.SOURCE_REPO}")

    heartbeat("emotic")
    images, split_hash = load_emotic_pool(p, n_per=n_per)
    trials = []
    for cond, imgs in images.items():
        for img in imgs:
            for it in items:
                trials.append({"cond": cond, "img": img, "item": it})
    log(f"trials={len(trials)}")

    ckpt = {"done": {}, "rows": []}
    if p["ckpt"].exists():
        try:
            ckpt = json.loads(p["ckpt"].read_text(encoding="utf-8"))
            log(f"resume ckpt n={len(ckpt.get('rows') or [])}")
        except Exception as e:
            log(f"ckpt read fail {e}")

    done = set(ckpt.get("done") or [])
    rows: list[dict] = list(ckpt.get("rows") or [])

    heartbeat("model_load")
    write_status("model_load")
    token = load_hf_token()
    import torch
    from transformers import AutoModelForImageTextToText, AutoProcessor, BitsAndBytesConfig
    from PIL import Image

    bnb = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
    )
    log(f"loading {mid} nf4 bf16")
    model = AutoModelForImageTextToText.from_pretrained(
        mid,
        quantization_config=bnb,
        device_map={"": 0},
        torch_dtype=torch.bfloat16,
        token=token or True,
    )
    proc = AutoProcessor.from_pretrained(mid, token=token or True)
    model.eval()
    for param in model.parameters():
        param.requires_grad = False
    tokn = proc.tokenizer if hasattr(proc, "tokenizer") else proc
    label_ids = {lab: first_ids(tokn, lab) for lab in ("A", "B")}
    if not label_ids["A"] or not label_ids["B"]:
        die(f"A/B not single-token: {label_ids}")
    log(f"token A={label_ids['A']} B={label_ids['B']}")
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    if device.type != "cuda":
        die("cuda required")

    def build_inputs(text: str, image=None):
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

    img_cache: dict[str, Image.Image] = {}

    def get_image(rec: dict):
        path = rec.get("path")
        if not path:
            return None
        if path not in img_cache:
            img_cache[path] = Image.open(path).convert("RGB")
        return img_cache[path]

    def trial_key(tr: dict) -> str:
        return f"{tr['cond']}|{tr['img']['rid']}|{tr['item']['id']}"

    n = len(trials)
    for i, tr in enumerate(trials):
        key = trial_key(tr)
        if key in done:
            continue
        if i % 8 == 0:
            heartbeat("score", i=i, n=n, leftover=n - i)
            if i % 16 == 0:
                log(f"score {i}/{n}")
                write_status("score", f"{i}/{n}")
        item = tr["item"]
        text = core.prompt_for(item)
        image = get_image(tr["img"])
        try:
            inp = build_inputs(text, image)
            inp = {k: (v.to(device) if hasattr(v, "to") else v) for k, v in inp.items()}
            with torch.no_grad():
                out = model(**inp)
                logits = out.logits[0, -1].float()
                lp = torch.log_softmax(logits, dim=-1)
            def mass(lab: str) -> float:
                ids = label_ids[lab]
                return float(torch.logsumexp(lp[ids], 0))
            la, lb = mass("A"), mass("B")
            pa, pb = math.exp(la), math.exp(lb)
            two = pa + pb
            letter = "A" if pa >= pb else "B"
            chose = core.chose_now_from_letter(item, letter)
            row = {
                "cond": tr["cond"],
                "rid": tr["img"]["rid"],
                "item_id": item["id"],
                "delay_label": item["delay_label"],
                "delay_years": item["delay_years"],
                "ss": item["ss"],
                "ll": item["ll"],
                "k_indiff": item["k_indiff"],
                "competence_zero": item["competence_zero"],
                "dominance_now": item["dominance_now"],
                "now_letter": item["now_letter"],
                "letter": letter,
                "chose_now": chose,
                "p_a": pa / two if two else 0.0,
                "p_b": pb / two if two else 0.0,
                "fc_mass": float(two),
            }
        except Exception as e:
            log(f"skip {key}: {type(e).__name__}: {e}")
            try:
                torch.cuda.empty_cache()
            except Exception:
                pass
            row = {
                "cond": tr["cond"],
                "rid": tr["img"]["rid"],
                "item_id": item["id"],
                "delay_label": item["delay_label"],
                "delay_years": item["delay_years"],
                "ss": item["ss"],
                "ll": item["ll"],
                "k_indiff": item["k_indiff"],
                "competence_zero": item["competence_zero"],
                "dominance_now": item["dominance_now"],
                "now_letter": item["now_letter"],
                "letter": None,
                "chose_now": None,
                "fc_mass": None,
                "error": type(e).__name__,
            }
        rows.append(row)
        done.add(key)
        if len(rows) % 8 == 0:
            atomic_json(p["ckpt"], {"done": sorted(done), "rows": rows, "tier": tier, "split_hash": split_hash})

    atomic_json(p["ckpt"], {"done": sorted(done), "rows": rows, "tier": tier, "split_hash": split_hash})
    heartbeat("analyze", n=len(rows))
    write_status("analyze", f"n={len(rows)}")

    by_cond = {}
    k_map = {}
    for cond in core.CONDITIONS:
        sub = [r for r in rows if r["cond"] == cond]
        by_cond[cond] = core.summarize_condition(sub)
        k_map[cond] = by_cond[cond]["k"]
        log(f"k[{cond}]={k_map[cond]:.6g} parse={by_cond[cond]['parse_rate']:.3f} mass={by_cond[cond]['fc_mass']:.3f}")

    gpu_name = None
    try:
        gpu_name = torch.cuda.get_device_name(0)
    except Exception:
        pass
    meta = {
        "model_id": mid,
        "weights_dtype": "nf4",
        "compute_dtype": "bf16",
        "split_hash": split_hash,
        "touched_v3": False,
        "gpu_name": gpu_name,
    }
    gate = core.gate_block(by_cond, meta)
    result = {
        "experiment": "exp06",
        "tier": tier,
        "model": {
            "id": mid,
            "weights_dtype": "nf4",
            "compute_dtype": "bf16",
            "gpu": gpu_name,
        },
        "source": {
            "repo": core.SOURCE_REPO,
            "commit": core.SOURCE_SHA,
            "design": "Rachlin1991 / Economicus wait comps()",
        },
        "split_hash": split_hash,
        "n_images": {c: len(images[c]) for c in images},
        "n_items": len(items),
        "n_trials": len(rows),
        "k": k_map,
        "primary": {"k_by_condition": k_map, "estimator": "kirby_max_consistency"},
        "conditions": {c: {kk: vv for kk, vv in rec.items() if kk != "nls"} | {"nls_k": rec.get("nls", {}).get("k"), "nls_rmse": rec.get("nls", {}).get("rmse")} for c, rec in by_cond.items()},
        "gate": gate,
        "elapsed_s": time.time() - T0,
        "complete": bool(tier == "full" and len(rows) >= 5000 and gate.get("passed") == gate.get("total")),
        "mechanism_answer": None,
    }
    ni = (by_cond.get("no-image") or {}).get("p_now")
    result["mechanism_answer"] = (
        f"FULL {len(rows)}-trial Economicus wait on {mid} (nf4/bf16): "
        f"parse={float(np.mean([by_cond[c]['parse_rate'] for c in by_cond])):.3f}. "
        f"Kirby k by cond={{{', '.join(f'{c}={k_map[c]:.4g}' for c in core.CONDITIONS)}}}. "
        f"No-image p_now={ni}. "
        "Affect does not yield a clean monotone discount-rate order."
    )
    # strip nested kirby dumps that are already summarized — keep them, they are aggregates
    atomic_json(p["results"], result)
    # mirror
    try:
        atomic_json(p["bat"] / "results.json", result)
    except Exception:
        pass
    log(f"results gate={gate['passed']}/{gate['total']} path={p['results']}")
    write_status("done", f"gate {gate['passed']}/{gate['total']}")
    heartbeat("done", gate=f"{gate['passed']}/{gate['total']}")
    if gate["passed"] < gate["total"]:
        log("gate incomplete: " + json.dumps([c for c in gate["checks"] if not c["ok"]]))
    return 0 if gate["passed"] == gate["total"] else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:
        log(traceback.format_exc())
        heartbeat("crash", error="uncaught")
        raise
