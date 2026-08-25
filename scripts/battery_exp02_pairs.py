# exp02 CPU pairing: scene-matched EMOTIC caliper pairs.
# Advisor-locked ([GPT-5.6 Sol High](2ebc4933-bcc2-4967-af4f-05ceb379a2ed)).
# Do not copy the sycophancy order-dependent greedy matcher.
# [[battery-campaign]] [[EMOTIC]]
from __future__ import annotations

import ast
import hashlib
import json
import math
import os
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

EXP_ID = "exp02"
EXPECTED_SPLIT = "1e8ea1c22144dd9d"
FROZEN_V3 = "e2e_mechanism_results_full_v3.json"
TARGET_LABELS = ("Fear", "Anger", "Sadness", "Happiness")
TARGET_SET = set(TARGET_LABELS)
CALIPERS = ((1, 0.05, 0.75), (2, 0.08, 1.0), (3, 0.10, 1.25))
N_TARGET = 96
N_MIN = 64
NEG_V = 4.0
POS_V = 6.0
FAMILIES = (
    ("fear_anger", "fear", "anger"),
    ("fear_neutral", "fear", "neutral"),
    ("anger_neutral", "anger", "neutral"),
    ("negative_neutral", "negative", "neutral"),
    ("sadness_happiness", "sadness", "happiness"),
    ("sadness_neutral", "sadness", "neutral"),
    ("happiness_neutral", "happiness", "neutral"),
)

ECONOMICUS_PREMISE = (
    "You are given a prospect and a sure option. If you reject the sure option, "
    "you play the prospect. If you accept the sure option, you receive that amount "
    "and do not play the prospect. Positive dollars are gains."
)
DICTATOR_PREMISE = (
    "You are the allocator in a dictator game. You have an endowment to divide "
    "between yourself and one anonymous recipient. The recipient cannot reject. "
    "You keep what you do not give."
)
FC_SUFFIX = "Reply with exactly one letter: A or B."
DESCRIBE = "Describe what is happening in this image."


def _env_path(name: str, default: Path) -> Path:
    raw = os.environ.get(name)
    return Path(raw).expanduser() if raw else default


def e2e_root() -> Path:
    return Path(os.environ.get("E2E_ROOT", str(Path.home() / "algoverse_run"))).expanduser()


def run_dir() -> Path:
    return _env_path("E2E_EXP02", e2e_root() / "battery" / "exp02")


def local_art() -> Path:
    here = Path(__file__).resolve().parent.parent
    p = here / "artifacts" / "battery" / "exp02"
    p.mkdir(parents=True, exist_ok=True)
    return p


def refuse_frozen(path: Path) -> None:
    if path.name == FROZEN_V3 or path.as_posix().endswith("artifacts/colab/" + FROZEN_V3):
        raise SystemExit(f"refuse overwrite of frozen artifact {path}")


def atomic_write(path: Path, text: str) -> None:
    refuse_frozen(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def write_json(path: Path, obj: Any) -> None:
    atomic_write(path, json.dumps(obj, indent=2, default=str))


def parse_literal(val: Any) -> Any:
    if isinstance(val, str) and val.startswith("["):
        try:
            return ast.literal_eval(val)
        except Exception:
            return val
    return val


def parse_labels(val: Any) -> set[str]:
    val = parse_literal(val)
    if isinstance(val, (list, tuple)):
        return {str(x) for x in val}
    if isinstance(val, str) and val:
        return {val}
    return set()


def bbox_key(val: Any) -> tuple | None:
    val = parse_literal(val)
    if isinstance(val, (list, tuple)) and val:
        if len(val) == 4 and all(isinstance(x, (int, float)) for x in val):
            return (tuple(float(x) for x in val),)
        keys = []
        for item in val:
            if isinstance(item, (list, tuple)) and len(item) == 4:
                keys.append(tuple(float(x) for x in item))
        if keys:
            return tuple(keys)
    return None


def vad_pair(row: dict) -> tuple[float | None, float | None]:
    vad = parse_literal(row.get("Continuous_Labels") or row.get("VAD"))
    if isinstance(vad, (list, tuple)) and len(vad) >= 2:
        try:
            return float(vad[0]), float(vad[1])
        except Exception:
            return None, None
    return None, None


def target_intersection(labels: set[str]) -> set[str]:
    return set(labels) & TARGET_SET


def assign_class(labels: set[str], val: float | None) -> str | None:
    """Primary membership for diagnostics. Prefer memberships() for pairing."""
    ms = memberships(labels, val)
    for key in ("fear", "anger", "sadness", "happiness", "negative", "neutral"):
        if key in ms:
            return key
    return None


def memberships(labels: set[str], val: float | None) -> set[str]:
    """Advisor amendment B1cf31c5: focal exclusive, not T-singleton.

    Fear := Fear in labels and Anger not in labels (other co-labels allowed).
    Anger := Anger in and Fear not in. Fear∩Anger excluded.
    Neutral/negative remain T-empty valence buckets.
    """
    out: set[str] = set()
    if "Fear" in labels and "Anger" not in labels:
        out.add("fear")
    if "Anger" in labels and "Fear" not in labels:
        out.add("anger")
    if "Sadness" in labels and "Happiness" not in labels:
        out.add("sadness")
    if "Happiness" in labels and "Sadness" not in labels:
        out.add("happiness")
    t = target_intersection(labels)
    if not t and val is not None:
        if val < NEG_V:
            out.add("negative")
        elif NEG_V <= val <= POS_V:
            out.add("neutral")
    return out


def bucket_of(val: float | None) -> str:
    if val is None:
        return "unk"
    if val < NEG_V:
        return "neg"
    if val > POS_V:
        return "pos"
    return "neu"


def aggregate_images(df) -> list[dict]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for rec in df.to_dict("records"):
        rid = f"{rec['Folder']}/{rec['Filename']}"
        rec["rid"] = rid
        groups[rid].append(rec)
    out = []
    for rid, rows in groups.items():
        labs: set[str] = set()
        vals, aros = [], []
        bboxes: set[tuple] = set()
        for r in rows:
            labs |= parse_labels(r.get("Categorical_Labels"))
            v, a = vad_pair(r)
            if v is not None:
                vals.append(v)
            if a is not None:
                aros.append(a)
            bk = bbox_key(r.get("BBox"))
            if bk:
                for item in bk:
                    bboxes.add(item if isinstance(item, tuple) and item and not isinstance(item[0], tuple) else item)
        # flatten bbox keys: each 4-tuple is one person
        persons = set()
        for r in rows:
            bk = bbox_key(r.get("BBox"))
            if bk is None:
                continue
            if len(bk) == 1 and isinstance(bk[0], float):
                persons.add(bk)
            else:
                for item in bk:
                    persons.add(item)
        n_person = max(len(persons), 1)
        val = float(np.mean(vals)) if vals else None
        aro = float(np.mean(aros)) if aros else None
        ms = memberships(labs, val)
        klass = assign_class(labs, val)
        out.append(
            {
                "rid": rid,
                "folder": str(rows[0]["Folder"]),
                "filename": str(rows[0]["Filename"]),
                "scene": str(rows[0]["Folder"]),
                "labels": sorted(labs),
                "T": sorted(target_intersection(labs)),
                "val": val,
                "aro": aro,
                "n_person": n_person,
                "pbin": "1" if n_person <= 1 else "2+",
                "class": klass,
                "memberships": sorted(ms),
                "bucket": bucket_of(val),
            }
        )
    return out


def eligible(a: dict, b: dict, dl: float, da: float) -> bool:
    if a["scene"] != b["scene"] or a["pbin"] != b["pbin"]:
        return False
    if a.get("lum") is None or b.get("lum") is None:
        return False
    if a.get("aro") is None or b.get("aro") is None:
        return False
    return abs(float(a["lum"]) - float(b["lum"])) <= dl and abs(float(a["aro"]) - float(b["aro"])) <= da


def pair_cost(a: dict, b: dict) -> float:
    return abs(float(a["lum"]) - float(b["lum"])) + 0.1 * abs(float(a["aro"]) - float(b["aro"]))


def _hungarian(cost: np.ndarray) -> list[tuple[int, int]]:
    try:
        from scipy.optimize import linear_sum_assignment
    except Exception as e:
        raise RuntimeError(f"scipy required for min-cost matching: {e}") from e
    r, c = linear_sum_assignment(cost)
    return list(zip(r.tolist(), c.tolist()))


def match_family(left: list[dict], right: list[dict], dl: float, da: float, n_keep: int) -> list[tuple[dict, dict, float]]:
    """Min-cost max-cardinality matching within (scene, pbin); then cheapest n_keep."""
    blocks: dict[tuple[str, str], tuple[list[dict], list[dict]]] = {}
    for rec in left:
        blocks.setdefault((rec["scene"], rec["pbin"]), ([], []))[0].append(rec)
    for rec in right:
        blocks.setdefault((rec["scene"], rec["pbin"]), ([], []))[1].append(rec)
    pairs: list[tuple[dict, dict, float]] = []
    huge = 1e9
    for (_scene, _pbin), (L, R) in blocks.items():
        if not L or not R:
            continue
        cost = np.full((len(L), len(R)), huge, dtype=np.float64)
        for i, a in enumerate(L):
            for j, b in enumerate(R):
                if eligible(a, b, dl, da):
                    cost[i, j] = pair_cost(a, b)
        if not np.isfinite(cost).any() or float(cost.min()) >= huge / 10:
            continue
        for i, j in _hungarian(cost):
            if cost[i, j] < huge / 10:
                pairs.append((L[i], R[j], float(cost[i, j])))
    pairs.sort(key=lambda t: (t[2], t[0]["rid"], t[1]["rid"]))
    if len(pairs) > n_keep:
        pairs = pairs[:n_keep]
    return pairs


def choose_tier(left: list[dict], right: list[dict], n_target: int = N_TARGET, n_min: int = N_MIN) -> dict:
    report = {
        "status": "PAIR_FAMILY_ABORT",
        "tier": None,
        "n": 0,
        "pool_left": len(left),
        "pool_right": len(right),
        "eligible_edges": 0,
        "matched": 0,
        "unmatched_left": len(left),
        "unmatched_right": len(right),
        "mean_dlum": None,
        "mean_daro": None,
        "smd_luminance": None,
        "smd_arousal": None,
        "pairs": [],
        "tier_counts": {},
    }
    if not left or not right:
        return report
    chosen = None
    for tier, dl, da in CALIPERS:
        pairs = match_family(left, right, dl, da, n_target)
        n_edge = 0
        for a in left:
            for b in right:
                if eligible(a, b, dl, da):
                    n_edge += 1
        report["tier_counts"][str(tier)] = {"n": len(pairs), "eligible_edges": n_edge}
        if len(pairs) >= n_target or (tier == 3 and len(pairs) >= n_min):
            chosen = (tier, pairs, n_edge)
            break
        if tier == 3:
            chosen = (tier, pairs, n_edge)
    if chosen is None:
        return report
    tier, pairs, n_edge = chosen
    report["tier"] = tier
    report["n"] = len(pairs)
    report["matched"] = len(pairs)
    report["eligible_edges"] = n_edge
    used_l = {a["rid"] for a, _, _ in pairs}
    used_r = {b["rid"] for _, b, _ in pairs}
    report["unmatched_left"] = len(left) - len(used_l)
    report["unmatched_right"] = len(right) - len(used_r)
    if pairs:
        dlums = [abs(float(a["lum"]) - float(b["lum"])) for a, b, _ in pairs]
        daros = [abs(float(a["aro"]) - float(b["aro"])) for a, b, _ in pairs]
        report["mean_dlum"] = float(np.mean(dlums))
        report["mean_daro"] = float(np.mean(daros))
        lums_l = np.array([float(a["lum"]) for a, _, _ in pairs])
        lums_r = np.array([float(b["lum"]) for _, b, _ in pairs])
        aros_l = np.array([float(a["aro"]) for a, _, _ in pairs])
        aros_r = np.array([float(b["aro"]) for _, b, _ in pairs])
        report["smd_luminance"] = _smd(lums_l, lums_r)
        report["smd_arousal"] = _smd(aros_l, aros_r)
        report["status"] = "OK" if len(pairs) >= n_min else "PAIR_FAMILY_ABORT"
        report["pairs"] = [
            {
                "left_id": a["rid"],
                "right_id": b["rid"],
                "scene": a["scene"],
                "pbin": a["pbin"],
                "dlum": abs(float(a["lum"]) - float(b["lum"])),
                "daro": abs(float(a["aro"]) - float(b["aro"])),
                "cost": cost,
                "left_val": a["val"],
                "right_val": b["val"],
                "left_aro": a["aro"],
                "right_aro": b["aro"],
                "left_class": a["class"],
                "right_class": b["class"],
            }
            for a, b, cost in pairs
        ]
    return report


def _smd(a: np.ndarray, b: np.ndarray) -> float:
    pooled = math.sqrt((float(a.var(ddof=1)) + float(b.var(ddof=1))) / 2.0) if len(a) > 1 else 0.0
    if pooled < 1e-12:
        return 0.0
    return float((a.mean() - b.mean()) / pooled)


def risk_items(n: int = 12, seed: int = 0) -> list[dict]:
    """Same Economicus sure-vs-prospect A/B bank as exp01/exp08."""
    import random

    rng = random.Random(seed)
    bank = []
    sures = [10, 20, 30, 40, 50, 60, 70, 80]
    prospects = [(0.5, 100, 0), (0.5, 80, 0), (0.25, 100, 0), (0.75, 80, 0), (0.5, 60, 0), (0.1, 200, 0)]
    for sure in sures:
        for p, hi, lo in prospects:
            bank.append((sure, p, hi, lo))
    rng.shuffle(bank)
    items = []
    for i, (sure, p, hi, lo) in enumerate(bank[:n]):
        swap = i % 2 == 1
        sure_txt = f"Accept the sure ${sure}"
        risk_txt = (
            f"Reject the sure option and play the prospect "
            f"({int(p * 100)}% ${hi}, {int((1 - p) * 100)}% ${lo})"
        )
        a_txt, b_txt = (risk_txt, sure_txt) if swap else (sure_txt, risk_txt)
        risky_lab = "A" if swap else "B"
        prompt = (
            f"{ECONOMICUS_PREMISE}\n\n"
            f"Prospect: {int(p * 100)}% chance of ${hi} and {int((1 - p) * 100)}% chance of ${lo}.\n"
            f"Sure option: ${sure}.\n\n"
            f"Choices:\n (A) {a_txt}\n (B) {b_txt}\n\n{FC_SUFFIX}"
        )
        if DESCRIBE.lower() in prompt.lower():
            raise RuntimeError("DESCRIBE leaked into risk item")
        items.append(
            {
                "id": f"risk_{i}",
                "task": "risk",
                "prompt": prompt,
                "primary_label": risky_lab,
                "other_label": "B" if risky_lab == "A" else "A",
                "dv": "choose_risky",
                "sure": sure,
                "p": p,
                "hi": hi,
                "lo": lo,
                "swap": swap,
            }
        )
    return items


def dictator_items(n: int = 12, seed: int = 1) -> list[dict]:
    """Same Forsythe-style dictator A/B bank as exp05/exp08. Not ultimatum."""
    import random

    rng = random.Random(seed)
    endowments = [10, 10, 20, 20, 50, 100]
    splits = [(1.0, 0.0), (0.8, 0.2), (0.7, 0.3), (0.6, 0.4)]
    bank = [(e, s) for e in endowments for s in splits]
    rng.shuffle(bank)
    items = []
    for i, (endow, (keep_frac, give_frac)) in enumerate(bank[:n]):
        keep = int(round(endow * keep_frac))
        give = endow - keep
        fair_keep = endow // 2
        fair_give = endow - fair_keep
        swap = i % 2 == 1
        selfish = f"Keep ${keep}, give ${give}"
        generous = f"Keep ${fair_keep}, give ${fair_give}"
        a_txt, b_txt = (generous, selfish) if swap else (selfish, generous)
        gen_lab = "A" if swap else "B"
        prompt = (
            f"{DICTATOR_PREMISE}\n\n"
            f"Endowment: ${endow}. The recipient cannot reject.\n\n"
            f"Choices:\n (A) {a_txt}\n (B) {b_txt}\n\n{FC_SUFFIX}"
        )
        if DESCRIBE.lower() in prompt.lower():
            raise RuntimeError("DESCRIBE leaked into dictator item")
        items.append(
            {
                "id": f"dictator_{i}",
                "task": "dictator",
                "prompt": prompt,
                "primary_label": gen_lab,
                "other_label": "B" if gen_lab == "A" else "A",
                "dv": "choose_generous",
                "endowment": endow,
                "swap": swap,
            }
        )
    return items


def load_split(path: Path) -> dict:
    split = json.loads(path.read_text(encoding="utf-8"))
    digest = hashlib.sha256(json.dumps(split, sort_keys=True).encode()).hexdigest()[:16]
    if digest != EXPECTED_SPLIT:
        raise SystemExit(f"split_hash={digest} != {EXPECTED_SPLIT}")
    return split


def compute_luminance(emotic_root: Path, images: list[dict], cache_path: Path, hb=None) -> None:
    from PIL import Image, ImageStat

    cache = {}
    if cache_path.exists():
        try:
            cache = json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception:
            cache = {}
    n = len(images)
    dirty = False
    for i, rec in enumerate(images):
        if rec["rid"] in cache:
            rec["lum"] = cache[rec["rid"]]
            continue
        p = emotic_root / "emotic" / rec["folder"] / rec["filename"]
        try:
            im = Image.open(p).convert("RGB").resize((64, 64))
            lum = float(ImageStat.Stat(im.convert("L")).mean[0]) / 255.0
        except Exception:
            lum = None
        rec["lum"] = lum
        cache[rec["rid"]] = lum
        dirty = True
        if hb and i % 200 == 0:
            hb("pair_lum", i=i, n=n)
        if dirty and i % 400 == 0:
            write_json(cache_path, cache)
    if dirty:
        write_json(cache_path, cache)


def build_pair_report(images: list[dict], n_target: int = N_TARGET, n_min: int = N_MIN) -> dict:
    by_class: dict[str, list[dict]] = defaultdict(list)
    for rec in images:
        if rec.get("lum") is None or rec.get("aro") is None:
            continue
        for klass in rec.get("memberships") or ([rec["class"]] if rec.get("class") else []):
            by_class[klass].append(rec)
    pair_report = {}
    for name, left_k, right_k in FAMILIES:
        left = by_class.get(left_k, [])
        right = by_class.get(right_k, [])
        pair_report[name] = choose_tier(left, right, n_target=n_target, n_min=n_min)
        pair_report[name]["left_class"] = left_k
        pair_report[name]["right_class"] = right_k
    return {
        "pool_sizes": {k: len(v) for k, v in by_class.items()},
        "families": pair_report,
    }


def selftest() -> None:
    left = []
    right = []
    for i in range(8):
        left.append(
            {
                "rid": f"mscoco/f{i:02d}.jpg",
                "scene": "mscoco",
                "pbin": "1",
                "lum": 0.40 + 0.01 * i,
                "aro": 5.0,
                "val": 3.0,
                "class": "fear",
            }
        )
        right.append(
            {
                "rid": f"mscoco/a{i:02d}.jpg",
                "scene": "mscoco",
                "pbin": "1",
                "lum": 0.41 + 0.01 * i,
                "aro": 5.1,
                "val": 3.1,
                "class": "anger",
            }
        )
    # extra scene that should not cross-match
    left.append(
        {
            "rid": "framesdb/f99.jpg",
            "scene": "framesdb",
            "pbin": "1",
            "lum": 0.40,
            "aro": 5.0,
            "val": 3.0,
            "class": "fear",
        }
    )
    report = choose_tier(left, right, n_target=8, n_min=4)
    assert report["status"] == "OK", report
    assert report["n"] == 8, report["n"]
    assert report["tier"] == 1, report["tier"]
    assert all(p["scene"] == "mscoco" for p in report["pairs"])
    # exclusive label rule
    assert "fear" not in memberships({"Fear", "Anger"}, 3.0)
    assert "anger" not in memberships({"Fear", "Anger"}, 3.0)
    assert memberships({"Fear", "Anxiety"}, 3.0) == {"fear"}
    assert "fear" in memberships({"Fear", "Sadness"}, 3.0)
    assert "sadness" in memberships({"Fear", "Sadness"}, 3.0)
    assert memberships({"Peace"}, 5.0) == {"neutral"}
    assert memberships({"Fear"}, 5.0) == {"fear"}
    items = risk_items(4) + dictator_items(4)
    assert all(DESCRIBE.lower() not in it["prompt"].lower() for it in items)
    print("selftest_ok", json.dumps({"n": report["n"], "tier": report["tier"]}))


def main(argv: list[str] | None = None) -> int:
    argv = list(argv if argv is not None else __import__("sys").argv[1:])
    t0 = time.time()
    if os.environ.get("EXP02_SELFTEST") == "1" or "--selftest" in argv:
        selftest()
        return 0
    import pandas as pd

    root = e2e_root()
    emotic = _env_path("E2E_EMOTIC", root / "emotic_data")
    split_path = _env_path("E2E_SPLIT", root / "emotic_split.json")
    out_dir = run_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    local = local_art()
    n_jpg = sum(1 for _ in (emotic / "emotic").rglob("*.jpg")) if (emotic / "emotic").exists() else 0
    split = load_split(split_path)
    eval_ids = set(split["eval_ids"])
    csv_path = emotic / "emotic_pre" / "train.csv"
    if not csv_path.exists():
        raise SystemExit(f"missing {csv_path}")
    df = pd.read_csv(csv_path)
    train_ids = set(split.get("train_ids") or [])
    all_imgs = aggregate_images(df)
    for rec in all_imgs:
        rec["split"] = "eval" if rec["rid"] in eval_ids else ("train" if rec["rid"] in train_ids else "other")
    images = [r for r in all_imgs if r["rid"] in eval_ids]
    hb_path = out_dir / "heartbeat.json"

    def hb(stage: str, **kw):
        write_json(
            hb_path,
            {"job": EXP_ID, "stage": stage, "ts": time.time(), "elapsed_s": time.time() - t0, **kw},
        )
        try:
            write_json(local / "heartbeat.json", {"job": EXP_ID, "stage": stage, "ts": time.time(), **kw})
        except Exception:
            pass

    hb("pair_lum", n=len(images), n_jpg=n_jpg)
    compute_luminance(emotic, images, out_dir / "luminance_cache.json", hb=hb)
    n_target = int(os.environ.get("EXP02_N_PAIRS", str(N_TARGET)))
    n_min = int(os.environ.get("EXP02_N_MIN", str(N_MIN)))
    if os.environ.get("E2E_TIER", "full").lower() == "smoke":
        n_target = min(n_target, 16)
        n_min = min(n_min, 8)
    payload = build_pair_report(images, n_target=n_target, n_min=n_min)
    payload["eval_only"] = {
        k: {"status": v["status"], "tier": v["tier"], "n": v["n"], "pool_left": v["pool_left"], "pool_right": v["pool_right"]}
        for k, v in payload["families"].items()
    }
    need_more = [k for k, v in payload["families"].items() if v.get("status") != "OK"]
    pool_source = "eval"
    if need_more:
        # Plan: below 64 abort, source more images. Expand to train+eval; do not loosen calipers.
        extra = [r for r in all_imgs if r["rid"] not in eval_ids]
        hb("pair_lum_expand", n=len(extra), families=need_more)
        compute_luminance(emotic, extra, out_dir / "luminance_cache.json", hb=hb)
        full = images + extra
        full_report = build_pair_report(full, n_target=n_target, n_min=n_min)
        for k in need_more:
            payload["families"][k] = full_report["families"][k]
            payload["families"][k]["pool_source"] = "eval_plus_train"
        pool_source = "eval_then_full_for_abort_families"
        payload["pool_sizes_full"] = full_report["pool_sizes"]
    for k, v in payload["families"].items():
        v.setdefault("pool_source", "eval")
    payload.update(
        {
            "experiment": EXP_ID,
            "split_hash": EXPECTED_SPLIT,
            "n_jpg": n_jpg,
            "n_eval_images": len(images),
            "n_target": n_target,
            "n_min": n_min,
            "pool_source": pool_source,
            "calipers": [{"tier": t, "dlum": dl, "daro": da} for t, dl, da in CALIPERS],
            "advisor": "2ebc4933-bcc2-4967-af4f-05ceb379a2ed",
            "advisor_label_rule": "b1cf31c5-f238-4ed7-994c-3dcf88a7980e",
            "elapsed_s": round(time.time() - t0, 1),
        }
    )
    write_json(out_dir / "pairs.json", payload)
    try:
        write_json(local / "pairs.json", payload)
    except Exception:
        pass
    hb("pairs_done", n_families=len(payload["families"]))
    print(json.dumps({k: {"status": v["status"], "tier": v["tier"], "n": v["n"]} for k, v in payload["families"].items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
