# Exclusive EMOTIC pools and OASIS valence pools. CPU only.
from __future__ import annotations

import ast
import hashlib
import json
import random
from pathlib import Path
from typing import Any

import battery_v2_config as cfg

try:
    import affect_core as ac
except ImportError:
    ac = None  # type: ignore


class InsufficientPool(RuntimeError):
    pass


def _labels(raw: Any) -> set[str]:
    if raw is None:
        return set()
    if isinstance(raw, str) and raw.startswith("["):
        try:
            raw = ast.literal_eval(raw)
        except Exception:
            return {raw} if raw else set()
    if isinstance(raw, (list, tuple, set)):
        return {str(x) for x in raw}
    return {str(raw)} if raw else set()


def exclusive_rids(rows: list[dict], target: str, rivals: set[str]) -> list[str]:
    out = []
    seen = set()
    for row in rows:
        labs = _labels(row.get("cats") or row.get("Categorical_Labels"))
        if target not in labs:
            continue
        if labs & (rivals - {target}):
            continue
        rid = row["rid"]
        if rid in seen:
            continue
        seen.add(rid)
        out.append(rid)
    return out


def neutral_rids(rows: list[dict], targets: set[str]) -> list[str]:
    out = []
    seen = set()
    for row in rows:
        labs = _labels(row.get("cats") or row.get("Categorical_Labels"))
        if labs & targets:
            continue
        rid = row["rid"]
        if rid in seen:
            continue
        seen.add(rid)
        out.append(rid)
    return out


def build_emotic_pools(
    rows: list[dict],
    science_ids: set[str],
    n_per: int,
    seed: int,
    min_n: dict[str, int] | None = None,
    n_calib: int = 8,
) -> dict[str, Any]:
    sci = [r for r in rows if r["rid"] in science_ids]
    rivals = set(cfg.EMOTIC_CATS.values())
    rng = random.Random(seed)
    pools: dict[str, list[str]] = {}
    calib: dict[str, list[str]] = {}
    exclusive_n: dict[str, int] = {}
    mins = min_n or cfg.POOL_MIN
    raw: dict[str, list[str]] = {}
    for arm, cat in cfg.EMOTIC_CATS.items():
        rids = exclusive_rids(sci, cat, rivals)
        exclusive_n[arm] = len(rids)
        need = int(mins.get(arm, 4))
        if len(rids) < need:
            raise InsufficientPool(f"{arm} exclusive={len(rids)} < {need}")
        rng.shuffle(rids)
        raw[arm] = rids
    neu = neutral_rids(sci, rivals)
    exclusive_n["neutral"] = len(neu)
    if len(neu) < int(mins.get("neutral", 4)):
        raise InsufficientPool(f"neutral exclusive={len(neu)} < {mins.get('neutral', 4)}")
    rng.shuffle(neu)
    raw["neutral"] = neu
    n_eval = min(n_per, min(len(v) for v in raw.values()))
    if n_eval < min(int(v) for v in mins.values()):
        raise InsufficientPool(f"balanced n_eval={n_eval}")
    for arm, rids in raw.items():
        pools[arm] = rids[:n_eval]
        calib[arm] = rids[n_eval : n_eval + n_calib]
    pair_n = max(int(cfg.sizes("budget3h")["n_pairs_03"]), int(cfg.sizes("budget3h")["n_pairs_10"]))
    pair_pools = {arm: raw[arm][:pair_n] for arm in ("anger", "sadness", "neutral") if arm in raw}
    pools["no_image"] = []
    calib["no_image"] = []
    return {
        "pools": pools,
        "calib_pools": calib,
        "pair_pools": pair_pools,
        "exclusive_n": exclusive_n,
        "n_science": len(sci),
        "n_eval": n_eval,
    }


def load_emotic_rows(csv_path: Path) -> list[dict]:
    import pandas as pd

    df = pd.read_csv(csv_path)
    if "Categorical_Labels" in df.columns:
        df["cats"] = df["Categorical_Labels"].apply(_labels)
    else:
        df["cats"] = [set() for _ in range(len(df))]
    df["rid"] = df["Folder"].astype(str) + "/" + df["Filename"].astype(str)
    df = df.drop_duplicates(subset=["rid"], keep="first")
    return df[["rid", "cats"]].to_dict("records")


def load_split(split_path: Path) -> dict:
    split = json.loads(split_path.read_text(encoding="utf-8"))
    h = hashlib.sha256(json.dumps(split, sort_keys=True).encode()).hexdigest()[:16]
    if h != cfg.EXPECTED_SPLIT:
        raise ValueError(f"split hash {h} != {cfg.EXPECTED_SPLIT}")
    train, ev = set(split["train_ids"]), set(split["eval_ids"])
    eval_sorted = sorted(ev)
    rng = random.Random(0)
    calib_n = max(1, int(0.15 * len(eval_sorted)))
    calib = set(rng.sample(eval_sorted, calib_n))
    science = ev - calib
    if ac is not None:
        ac.assert_disjoint_manifests(train, calib, science, label="emotic_images")
    return {
        "hash": h,
        "train_ids": train,
        "eval_ids": ev,
        "calib_ids": calib,
        "science_ids": science,
    }


def oasis_valence_pools(items: list[dict], n_per: int, seed: int) -> dict[str, Any]:
    import battery_exp08_lib as o8

    meta = o8.attach_oasis_tertiles(items, q=cfg.OASIS_Q)
    rng = random.Random(seed)
    pools = {"no_image": []}
    calib = {"no_image": []}
    for lab in ("neg", "neu", "pos"):
        rids = [x.get("theme") or x.get("id") for x in items if x.get("bucket") == lab]
        rids = [r for r in rids if r]
        rng.shuffle(rids)
        if len(rids) < 4:
            raise InsufficientPool(f"oasis {lab} n={len(rids)}")
        pools[lab] = rids[:n_per]
        calib[lab] = rids[n_per : n_per + 8]
    return {"pools": pools, "calib_pools": calib, "meta": meta}
