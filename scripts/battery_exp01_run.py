# exp01: fear vs anger vs sadness vs happiness vs peace/confidence vs
# neutral vs no-image on forced-choice A/B lotteries (Economicus converted).
# Gemma-4-E4B-it nf4/bf16. GPU from CUDA_VISIBLE_DEVICES. No image DESCRIBE.
from __future__ import annotations

import ast
import hashlib
import json
import math
import os
import random
import sys
import time
from pathlib import Path

import numpy as np

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
import battery_adapter as ad

EXP = "exp01"
PRIMARY = ad.PRIMARY
EXPECTED_SPLIT = ad.EXPECTED_SPLIT
SEED = 20260823
T0 = time.time()

CATS_IMG = ["fear", "anger", "sadness", "happiness", "peace_confidence", "neutral"]
ALL_CATS = CATS_IMG + ["no_image"]
ANCHOR = {
    "fear": {"Fear"},
    "anger": {"Anger"},
    "sadness": {"Sadness"},
    "happiness": {"Happiness"},
    "peace_confidence": {"Peace", "Confidence"},
    "neutral": {"Engagement", "Sympathy"},
}
EXCLUSIVE = {
    "fear": {"Fear", "Disquietment", "Doubt/Confusion"},
    "anger": {"Anger", "Annoyance", "Aversion", "Disapproval"},
    "sadness": {"Sadness", "Suffering", "Pain", "Fatigue", "Disconnection", "Embarrassment", "Yearning", "Sensitivity"},
    "happiness": {"Happiness", "Pleasure", "Excitement", "Affection", "Esteem", "Anticipation", "Surprise"},
    "peace_confidence": {"Peace", "Confidence"},
    "neutral": {"Engagement", "Sympathy"},
}
FALLBACK_OK = {
    "fear": {"Fear"},
    "anger": {"Anger"},
    "sadness": {"Sadness"},
    "happiness": {"Happiness"},
    "peace_confidence": {"Peace", "Confidence"},
    "neutral": {"Engagement"},
}
# Competing labels that break exclusive admission on fallback
BAN = {
    "fear": {"Anger"},
    "anger": {"Fear"},
    "sadness": {"Fear", "Anger", "Happiness"},
    "happiness": {"Fear", "Anger", "Sadness"},
    "peace_confidence": {"Fear", "Anger", "Sadness"},
    "neutral": {"Fear", "Anger", "Sadness", "Happiness"},
}


def work_root() -> Path:
    return Path(os.environ.get("E2E_EXP01", str(ad.e2e_root() / "battery" / EXP))).expanduser()


def local_mirror() -> Path | None:
    raw = os.environ.get("EXP01_LOCAL_MIRROR")
    if raw:
        return Path(raw)
    # on the Windows checkout when present
    p = Path(__file__).resolve().parents[1] / "artifacts" / "battery" / "exp01"
    return p if p.exists() or os.name == "nt" else None


HB = work_root() / "heartbeat.json"
OUT = Path(os.environ.get("E2E_OUT", str(work_root() / "results.json")))
TRIALS = work_root() / "trials.jsonl"
PARTIAL = work_root() / "results.partial.json"


def log(msg: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    lp = work_root() / "run.log"
    lp.parent.mkdir(parents=True, exist_ok=True)
    with lp.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def heartbeat(stage: str, **kw) -> None:
    payload = {
        "exp": EXP,
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "unix": time.time(),
        "elapsed_s": round(time.time() - T0, 1),
        "stage": stage,
        "gpu": os.environ.get("CUDA_VISIBLE_DEVICES", ""),
        **kw,
    }
    HB.parent.mkdir(parents=True, exist_ok=True)
    tmp = HB.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload), encoding="utf-8")
    os.replace(tmp, HB)
    mir = local_mirror()
    if mir is not None:
        try:
            mir.mkdir(parents=True, exist_ok=True)
            (mir / "heartbeat.json").write_text(json.dumps(payload), encoding="utf-8")
        except Exception:
            pass


def atomic_write(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, default=str), encoding="utf-8")
    os.replace(tmp, path)


def load_items() -> list[dict]:
    cands = [
        Path(os.environ["EXP01_LOTTERIES"]).expanduser() if os.environ.get("EXP01_LOTTERIES") else None,
        ad.e2e_root() / "battery" / "exp01" / "exp01_lotteries.json",
        Path(__file__).resolve().parents[1] / "data" / "battery" / "exp01_lotteries.json",
        Path.home() / "Algoverse" / "data" / "battery" / "exp01_lotteries.json",
    ]
    path = next((p for p in cands if p is not None and p.exists()), None)
    if path is None:
        raise SystemExit("missing exp01_lotteries.json")
    blob = json.loads(path.read_text(encoding="utf-8"))
    return list(blob["items"]), str(path)


def fmt_money(x: float) -> str:
    return f"${int(x)}" if float(x) == int(x) else f"${x:.2f}"


def item_prompt(item: dict, risky_is_a: bool) -> str:
    sure = f"Receive {fmt_money(item['sure'])} for certain."
    risky = (
        f"{int(round(item['p'] * 100))}% chance of {fmt_money(item['prize'])}, "
        f"otherwise {fmt_money(item.get('other', 0))}."
    )
    if risky_is_a:
        a, b = risky, sure
    else:
        a, b = sure, risky
    text = (
        "You must choose exactly one option. Reply with only the letter A or B.\n\n"
        f"A. {a}\n"
        f"B. {b}"
    )
    if "describe what is happening" in text.lower() or "look at the image" in text.lower():
        raise RuntimeError("image description leaked into prompt")
    return text


def labs_of(row) -> set[str]:
    raw = row.get("Categorical_Labels", [])
    if isinstance(raw, str) and raw.startswith("["):
        raw = ast.literal_eval(raw)
    return set(raw) if isinstance(raw, (list, tuple, set)) else set()


def vad_of(row) -> tuple[float | None, float | None, float | None]:
    raw = row.get("Continuous_Labels") or row.get("VAD")
    if isinstance(raw, str) and raw.startswith("["):
        raw = ast.literal_eval(raw)
    if isinstance(raw, (list, tuple)) and len(raw) >= 3:
        try:
            return float(raw[0]), float(raw[1]), float(raw[2])
        except Exception:
            return None, None, None
    return None, None, None


def classify_union(union: set[str]) -> str | None:
    if not union:
        return None
    for cat, allowed in EXCLUSIVE.items():
        if union <= allowed and (union & ANCHOR[cat]):
            return cat
    return None


def classify_fallback(union: set[str]) -> str | None:
    if not union:
        return None
    for cat, anchors in FALLBACK_OK.items():
        if union & anchors and not (union & BAN[cat]):
            return cat
    return None


def load_pools(n_need: int) -> tuple[dict[str, list[dict]], dict]:
    import pandas as pd

    emotic, split_path = ad.discover_emotic()
    csv_path = emotic / "emotic_pre" / "train.csv"
    img_root = emotic / "emotic"
    split = json.loads(split_path.read_text(encoding="utf-8"))
    split_hash = hashlib.sha256(json.dumps(split, sort_keys=True).encode()).hexdigest()[:16]
    if split_hash != EXPECTED_SPLIT:
        raise SystemExit(f"split_hash={split_hash} != {EXPECTED_SPLIT}")
    eval_ids = set(split["eval_ids"])
    df = pd.read_csv(csv_path)
    for col in ("Categorical_Labels", "Continuous_Labels", "VAD", "BBox"):
        if col in df.columns:
            df[col] = df[col].apply(
                lambda x: ast.literal_eval(x) if isinstance(x, str) and str(x).startswith("[") else x
            )
    df = df.copy()
    df["rid"] = df.apply(lambda r: f"{r['Folder']}/{r['Filename']}", axis=1)
    groups: dict[str, dict] = {}
    for _, row in df.iterrows():
        rid = row["rid"]
        g = groups.setdefault(rid, {"rid": rid, "folder": row["Folder"], "filename": row["Filename"], "labs": set(), "vads": []})
        g["labs"] |= labs_of(row)
        v, a, d = vad_of(row)
        if v is not None:
            g["vads"].append((v, a, d))
    exclusive: dict[str, list[dict]] = {c: [] for c in CATS_IMG}
    fallback: dict[str, list[dict]] = {c: [] for c in CATS_IMG}
    for rid, g in groups.items():
        if rid not in eval_ids:
            continue
        if g["vads"]:
            v = float(np.mean([x[0] for x in g["vads"]]))
            a = float(np.mean([x[1] for x in g["vads"]]))
            d = float(np.mean([x[2] for x in g["vads"]]))
        else:
            v = a = d = None
        rec = {"rid": rid, "folder": g["folder"], "filename": g["filename"], "labs": sorted(g["labs"]), "V": v, "A": a, "D": d}
        cat = classify_union(g["labs"])
        if cat:
            exclusive[cat].append(rec)
        fb = classify_fallback(g["labs"])
        if fb:
            fallback[fb].append(rec)

    used_fallback = False
    pools: dict[str, list[dict]] = {}
    for cat in CATS_IMG:
        pool = exclusive[cat]
        if len(pool) < n_need:
            used_fallback = True
            have = {x["rid"] for x in pool}
            extra = [x for x in fallback[cat] if x["rid"] not in have]
            pool = pool + extra
        pool = sorted(pool, key=lambda x: hashlib.sha256(f"{SEED}:{x['rid']}".encode()).hexdigest())
        pools[cat] = pool[: max(n_need, 12)]
    meta = {
        "split_hash": split_hash,
        "n_eval": len(eval_ids),
        "n_jpg": sum(1 for _ in img_root.rglob("*.jpg")),
        "exclusive_n": {c: len(exclusive[c]) for c in CATS_IMG},
        "fallback_n": {c: len(fallback[c]) for c in CATS_IMG},
        "used_n": {c: len(pools[c]) for c in CATS_IMG},
        "used_fallback": used_fallback,
        "emotic": str(emotic),
        "img_root": str(img_root),
    }
    return pools, meta


def smd(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return float("nan")
    sa, sb = float(np.std(a, ddof=1) or 0), float(np.std(b, ddof=1) or 0)
    sp = math.sqrt(((len(a) - 1) * sa ** 2 + (len(b) - 1) * sb ** 2) / max(len(a) + len(b) - 2, 1))
    if sp < 1e-9:
        return 0.0
    return (float(np.mean(a)) - float(np.mean(b))) / sp


def select_matched(pools: dict[str, list[dict]], n: int) -> dict[str, list[dict]]:
    out = {c: list(pools[c][:n]) for c in CATS_IMG}
    fear, anger = [x for x in pools["fear"] if x["V"] is not None], [x for x in pools["anger"] if x["V"] is not None]
    if len(fear) >= n and len(anger) >= n:
        best = None
        rng = random.Random(SEED)
        for _ in range(400):
            fs = rng.sample(fear, n)
            an = rng.sample(anger, n)
            dv = abs(smd([x["V"] for x in fs], [x["V"] for x in an]))
            da = abs(smd([x["A"] for x in fs], [x["A"] for x in an]))
            dgap = float(np.mean([x["D"] for x in an])) - float(np.mean([x["D"] for x in fs]))
            score = dv + da - 0.25 * dgap
            if best is None or score < best[0]:
                best = (score, fs, an, dv, da, dgap)
        if best:
            out["fear"], out["anger"] = best[1], best[2]
    return out


def schedule(items: list[dict], pools: dict[str, list[dict]], n_blocks: int) -> list[dict]:
    trials = []
    cat_idx = {c: i for i, c in enumerate(CATS_IMG)}
    for i, item in enumerate(items):
        for c, cat in enumerate(CATS_IMG):
            imgs = pools[cat]
            m = len(imgs)
            if m == 0:
                continue
            for b in range(n_blocks):
                j = (i + b + cat_idx[cat]) % m
                rec = imgs[j]
                risky_is_a = ((i + j + c) % 2) == 0
                trials.append(
                    {
                        "tid": f"{cat}|{item['id']}|{b}|{rec['rid']}",
                        "cat": cat,
                        "item_id": item["id"],
                        "block": b,
                        "rid": rec["rid"],
                        "folder": rec["folder"],
                        "filename": rec["filename"],
                        "risky_is_a": risky_is_a,
                        "item": item,
                    }
                )
        risky_is_a = (i % 2) == 0
        trials.append(
            {
                "tid": f"no_image|{item['id']}|0|none",
                "cat": "no_image",
                "item_id": item["id"],
                "block": 0,
                "rid": None,
                "folder": None,
                "filename": None,
                "risky_is_a": risky_is_a,
                "item": item,
            }
        )
    rng = random.Random(SEED)
    rng.shuffle(trials)
    return trials


def done_tids() -> set[str]:
    if not TRIALS.exists():
        return set()
    out = set()
    for line in TRIALS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            out.add(json.loads(line)["tid"])
        except Exception:
            pass
    return out


def append_trial(rec: dict) -> None:
    with TRIALS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, default=str) + "\n")


def read_trials() -> list[dict]:
    if not TRIALS.exists():
        return []
    rows = []
    for line in TRIALS.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                rows.append(json.loads(line))
            except Exception:
                pass
    return rows


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float, float]:
    if n <= 0:
        return float("nan"), float("nan"), float("nan")
    p = k / n
    den = 1 + z ** 2 / n
    centre = (p + z ** 2 / (2 * n)) / den
    half = (z * math.sqrt((p * (1 - p) + z ** 2 / (4 * n)) / n)) / den
    return p, max(0.0, centre - half), min(1.0, centre + half)


def crra_u(w: float, rho: float) -> float:
    w = max(w, 1e-9)
    if abs(rho - 1.0) < 1e-6:
        return math.log(w)
    return (w ** (1.0 - rho) - 1.0) / (1.0 - rho)


def fit_crra(rows: list[dict], conds: tuple[str, str] = ("fear", "anger")) -> dict:
    # secondary: condition-specific rho, shared inverse-temp, A-side bias
    sub = [r for r in rows if r.get("valid") and r.get("cat") in conds and r.get("chose_risky") is not None]
    if len(sub) < 8:
        return {"ok": False, "n": len(sub)}

    def nll(theta):
        rho_f, rho_a, beta, a_coef = theta
        s = 0.0
        for r in sub:
            rho = rho_f if r["cat"] == "fear" else rho_a
            it = r["item"] if isinstance(r["item"], dict) else {}
            sure, p, prize = float(it.get("sure", 50)), float(it.get("p", 0.5)), float(it.get("prize", 100))
            du = p * crra_u(100 + prize, rho) + (1 - p) * crra_u(100.0, rho) - crra_u(100 + sure, rho)
            # logit for choosing risky
            side = 1.0 if r.get("risky_is_a") else -1.0
            z = float(np.clip(beta * du + a_coef * side, -20, 20))
            pr = 1.0 / (1.0 + math.exp(-z))
            y = 1.0 if r["chose_risky"] else 0.0
            s -= y * math.log(max(pr, 1e-12)) + (1 - y) * math.log(max(1 - pr, 1e-12))
        return s

    best = None
    for rho_f in np.linspace(-1, 3, 9):
        for rho_a in np.linspace(-1, 3, 9):
            for beta in (0.5, 1.5, 4.0):
                for ac in (-0.2, 0.0, 0.2):
                    val = nll((rho_f, rho_a, beta, ac))
                    if best is None or val < best[0]:
                        best = (val, (float(rho_f), float(rho_a), float(beta), float(ac)))
    return {
        "ok": True,
        "n": len(sub),
        "rho_fear": best[1][0],
        "rho_anger": best[1][1],
        "beta": best[1][2],
        "a_side": best[1][3],
        "nll": best[0],
    }


def analyze(rows: list[dict], meta: dict, n_expect: int) -> dict:
    by_cat: dict[str, list[dict]] = {c: [] for c in ALL_CATS}
    for r in rows:
        if r.get("cat") in by_cat:
            by_cat[r["cat"]].append(r)
    rates = {}
    for c, rs in by_cat.items():
        valid = [r for r in rs if r.get("valid")]
        k = sum(1 for r in valid if r.get("chose_risky"))
        p, lo, hi = wilson(k, len(valid))
        rates[c] = {
            "n": len(rs),
            "n_valid": len(valid),
            "p_risky": p,
            "ci95_wilson": [lo, hi],
            "letter_mass_mean": float(np.mean([r.get("ab_mass") or 0 for r in rs])) if rs else float("nan"),
        }
    # crossed bootstrap
    rng = np.random.default_rng(SEED)
    items = sorted({r["item_id"] for r in rows})
    boot = {c: [] for c in ALL_CATS}
    deltas = []
    n_boot = 2000 if os.environ.get("E2E_TIER", "full") == "smoke" else 10000
    grouped = {}
    for r in rows:
        if not r.get("valid"):
            continue
        grouped.setdefault((r["cat"], r["item_id"]), []).append(r)
    for _ in range(n_boot):
        bi = rng.choice(items, size=len(items), replace=True)
        pc = {}
        for c in ALL_CATS:
            vals = []
            for it in bi:
                pool = grouped.get((c, int(it)), [])
                if not pool:
                    continue
                pick = pool[int(rng.integers(0, len(pool)))]
                vals.append(1.0 if pick.get("chose_risky") else 0.0)
            pc[c] = float(np.mean(vals)) if vals else float("nan")
            boot[c].append(pc[c])
        if math.isfinite(pc.get("anger", float("nan"))) and math.isfinite(pc.get("fear", float("nan"))):
            deltas.append(pc["anger"] - pc["fear"])

    def pct(xs):
        xs = [x for x in xs if math.isfinite(x)]
        if not xs:
            return [float("nan"), float("nan")]
        return [float(np.percentile(xs, 2.5)), float(np.percentile(xs, 97.5))]

    for c in ALL_CATS:
        rates[c]["ci95_boot"] = pct(boot[c])
    delta = rates["anger"]["p_risky"] - rates["fear"]["p_risky"]
    dci = pct(deltas)

    valid_all = [r for r in rows if r.get("valid")]
    letter_rate = (len(valid_all) / len(rows)) if rows else 0.0
    risky_a = [r for r in valid_all if r.get("risky_is_a")]
    risky_b = [r for r in valid_all if not r.get("risky_is_a")]
    p_a = float(np.mean([r["chose_risky"] for r in risky_a])) if risky_a else float("nan")
    p_b = float(np.mean([r["chose_risky"] for r in risky_b])) if risky_b else float("nan")
    side = abs(p_a - p_b) if math.isfinite(p_a) and math.isfinite(p_b) else float("nan")
    a_frac = float(np.mean([1.0 if r.get("risky_is_a") else 0.0 for r in rows])) if rows else float("nan")
    pooled = None
    fa = [r for r in valid_all if r.get("cat") in ("fear", "anger")]
    if fa:
        pooled = float(np.mean([r["chose_risky"] for r in fa]))

    g = []
    g.append(("G1_lock", meta.get("split_hash") == EXPECTED_SPLIT and meta.get("model") == PRIMARY))
    g.append(("G2_images", all(meta.get("used_n", {}).get(c, 0) >= (2 if meta.get("tier") == "smoke" else 12) for c in CATS_IMG)))
    g.append(("G3_match", bool(meta.get("g3_ok"))))
    g.append(("G4_complete", len(rows) >= n_expect and letter_rate >= 0.0))
    g.append(("G5_letter", letter_rate >= 0.95 and all(rates[c]["n_valid"] / max(rates[c]["n"], 1) >= 0.95 or rates[c]["n"] == 0 for c in ALL_CATS)))
    g.append(("G6_balance", abs(a_frac - 0.5) <= 0.15 if math.isfinite(a_frac) else False))
    g.append(("G7_side", (side <= 0.10) if math.isfinite(side) else False))
    n_fa = {c: rates[c]["n_valid"] for c in ("fear", "anger")}
    need = 8 if meta.get("tier") == "smoke" else 114
    g.append(("G8_range", (pooled is not None and 0.10 <= pooled <= 0.90 and n_fa["fear"] >= need and n_fa["anger"] >= need)))
    passed = sum(1 for _, ok in g if ok)

    supported = bool(math.isfinite(delta) and dci[0] > 0)
    mechanism = (
        f"The appraisal-tendency prediction was {'supported' if supported else 'not supported'}: "
        f"P(risky|anger)={rates['anger']['p_risky']:.3f}, P(risky|fear)={rates['fear']['p_risky']:.3f}, "
        f"delta anger-fear={delta:.3f} (95% crossed-bootstrap CI [{dci[0]:.3f},{dci[1]:.3f}]; gates {passed}/8)."
    )
    return {
        "rates": rates,
        "delta_anger_minus_fear": delta,
        "delta_ci95_boot": dci,
        "letter_valid_rate": letter_rate,
        "risky_letter_side_effect": side,
        "risky_is_a_frac": a_frac,
        "pooled_fear_anger": pooled,
        "crra": fit_crra(rows),
        "gates": {k: bool(v) for k, v in g},
        "gates_passed": passed,
        "gates_total": 8,
        "mechanism_answer": mechanism,
        "n_trials": len(rows),
        "n_expect": n_expect,
        "n_boot": n_boot,
    }


def open_image(img_root: Path, folder: str, filename: str):
    from PIL import Image

    return Image.open(img_root / folder / filename).convert("RGB")


def main() -> int:
    work_root().mkdir(parents=True, exist_ok=True)
    gpu = os.environ.get("EXP01_GPU", os.environ.get("CUDA_VISIBLE_DEVICES", "0"))
    os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu).split(",")[0]
    ad.plant_hf_token()
    heartbeat("boot", gpu=os.environ["CUDA_VISIBLE_DEVICES"])
    try:
        ad.claim_gpu(EXP, os.environ["CUDA_VISIBLE_DEVICES"])
    except SystemExit as e:
        log(f"gpu wait: {e}")
        time.sleep(30)
        ad.claim_gpu(EXP, os.environ["CUDA_VISIBLE_DEVICES"])
    ad.wait_for_first_download(EXP)

    tier = os.environ.get("E2E_TIER", "full").lower()
    if tier not in ("smoke", "full"):
        tier = "full"
    items_all, items_path = load_items()
    if tier == "smoke":
        keep = {1, 4, 7, 10}
        items = [x for x in items_all if x["id"] in keep]
        n_img, n_blocks = 2, 2
    else:
        items = items_all
        n_img, n_blocks = 12, 12
    n_expect = len(items) * len(CATS_IMG) * n_blocks + len(items)

    heartbeat("emotic", tier=tier, n_expect=n_expect)
    pools_all, emeta = load_pools(n_img)
    pools = select_matched(pools_all, n_img)
    fear_v = [x["V"] for x in pools["fear"] if x["V"] is not None]
    anger_v = [x["V"] for x in pools["anger"] if x["V"] is not None]
    fear_a = [x["A"] for x in pools["fear"] if x["A"] is not None]
    anger_a = [x["A"] for x in pools["anger"] if x["A"] is not None]
    fear_d = [x["D"] for x in pools["fear"] if x["D"] is not None]
    anger_d = [x["D"] for x in pools["anger"] if x["D"] is not None]
    g3 = False
    g3_stats = {}
    if fear_v and anger_v and fear_a and anger_a and fear_d and anger_d:
        dv, da = abs(smd(fear_v, anger_v)), abs(smd(fear_a, anger_a))
        dgap = float(np.mean(anger_d) - np.mean(fear_d))
        pair_ok = True
        for f, a in zip(pools["fear"], pools["anger"]):
            if f["V"] is None or a["V"] is None:
                pair_ok = False
                break
            if abs(f["V"] - a["V"]) > 1 or abs((f["A"] or 0) - (a["A"] or 0)) > 1:
                pair_ok = False
        g3 = pair_ok and dv <= 0.25 and da <= 0.25 and dgap >= 0.5
        g3_stats = {"smd_v": dv, "smd_a": da, "d_gap": dgap, "pair_ok": pair_ok}
    emeta.update({"g3_ok": g3, "g3": g3_stats, "tier": tier, "model": PRIMARY, "used_n": {c: len(pools[c]) for c in CATS_IMG}})
    atomic_write(work_root() / "pools.json", {c: [{"rid": x["rid"], "V": x["V"], "A": x["A"], "D": x["D"], "labs": x["labs"]} for x in pools[c]] for c in CATS_IMG} | {"meta": emeta})
    log(f"pools {emeta['used_n']} fallback={emeta['used_fallback']} g3={g3} {g3_stats}")

    trials = schedule(items, pools, n_blocks)
    done = done_tids()
    log(f"schedule {len(trials)} done={len(done)} expect={n_expect}")
    heartbeat("model_load", n_done=len(done), n_expect=n_expect)
    model, processor = ad.load_gemma4_nf4(PRIMARY)
    ad.mark_download_ready(EXP)
    emeta["model"] = PRIMARY
    emeta["weights"] = "nf4"
    emeta["compute"] = "bf16"
    img_root = Path(emeta["img_root"])
    log("model ready")

    pending = [t for t in trials if t["tid"] not in done]
    for i, t in enumerate(pending):
        ad.refresh_lock(EXP, os.environ["CUDA_VISIBLE_DEVICES"])
        prompt = item_prompt(t["item"], t["risky_is_a"])
        image = None
        if t["cat"] != "no_image":
            try:
                image = open_image(img_root, t["folder"], t["filename"])
            except Exception as e:
                log(f"img fail {t['rid']}: {e}")
                rec = {**t, "valid": False, "error": str(e), "chose_risky": None}
                append_trial(rec)
                continue
        try:
            gen = ad.generate_choice(model, processor, prompt, image)
        except Exception as e:
            log(f"gen fail {t['tid']}: {e}")
            rec = {**t, "valid": False, "error": type(e).__name__, "chose_risky": None}
            append_trial(rec)
            continue
        letter = gen["letter"]
        valid = letter in ("A", "B")
        chose_risky = None
        if valid:
            chose_risky = (letter == "A") if t["risky_is_a"] else (letter == "B")
        rec = {
            "tid": t["tid"],
            "cat": t["cat"],
            "item_id": t["item_id"],
            "block": t["block"],
            "rid": t["rid"],
            "risky_is_a": t["risky_is_a"],
            "item": t["item"],
            "letter": letter,
            "ab_mass": gen["ab_mass"],
            "valid": valid,
            "chose_risky": chose_risky,
            "gen": gen["text"],
        }
        append_trial(rec)
        if i % 5 == 0 or i + 1 == len(pending):
            rows = read_trials()
            partial = analyze(rows, emeta, n_expect)
            atomic_write(PARTIAL, {"meta": emeta, **partial, "complete": False})
            heartbeat("generate", i=len(done) + i + 1, n=n_expect, p_fear=partial["rates"]["fear"]["p_risky"], p_anger=partial["rates"]["anger"]["p_risky"])
            log(f"gen {len(done)+i+1}/{n_expect} letter={letter} cat={t['cat']} item={t['item_id']}")

    rows = read_trials()
    result = {
        "experiment": EXP,
        "started": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(T0)),
        "elapsed_s": round(time.time() - T0, 1),
        "complete": True,
        "items_path": items_path,
        "meta": emeta,
        **analyze(rows, emeta, n_expect),
    }
    atomic_write(OUT, result)
    mir = local_mirror()
    if mir is not None:
        try:
            atomic_write(mir / "results.json", result)
            if TRIALS.exists():
                (mir / "trials.jsonl").write_text(TRIALS.read_text(encoding="utf-8"), encoding="utf-8")
        except Exception as e:
            log(f"local mirror skip: {e}")
    heartbeat("done", gates=f"{result['gates_passed']}/{result['gates_total']}")
    log(result["mechanism_answer"])
    try:
        repo_id = os.environ.get("EXP01_HF_REPO", "halli75/algoverse-battery-exp01")
        from huggingface_hub import HfApi

        api = HfApi(token=os.environ.get("HF_TOKEN"))
        api.create_repo(repo_id, repo_type="dataset", exist_ok=True, private=True)
        for name in ("results.json", "results.partial.json", "heartbeat.json", "pools.json", "trials.jsonl"):
            p = work_root() / name
            if p.exists():
                api.upload_file(path_or_fileobj=str(p), path_in_repo=f"exp01/{name}", repo_id=repo_id, repo_type="dataset")
        result["hf_dataset"] = repo_id
        atomic_write(OUT, result)
        log(f"hf push {repo_id}")
    except Exception as e:
        log(f"hf push skip: {type(e).__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
