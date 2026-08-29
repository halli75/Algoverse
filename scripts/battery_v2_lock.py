# Write/check LOCK.json before scores. No GPU.
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import battery_v2_config as cfg


class LockError(RuntimeError):
    pass


REQUIRED = (
    "campaign",
    "experiment",
    "model_id",
    "weights_dtype",
    "tier",
    "split_expected",
    "script_sha256",
    "sizes",
    "primary_dv",
    "scorer",
    "seed",
    "arms",
)


def lock_path(run_dir: Path) -> Path:
    return Path(run_dir) / "LOCK.json"


def build_lock(
    *,
    experiment: str,
    model_key: str,
    tier: str,
    script_path: Path,
    primary_dv: str,
    scorer: str,
    seed: int,
    arms: list[str],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    meta = cfg.MODELS[model_key]
    payload = {
        "campaign": cfg.CAMPAIGN,
        "experiment": experiment,
        "model_key": model_key,
        "model_id": meta["id"],
        "arch": meta["arch"],
        "weights_dtype": "bf16",
        "quantize": False,
        "thinking": False,
        "chat_order": ["image", "text"],
        "describe_before_task": False,
        "tier": tier,
        "split_expected": cfg.EXPECTED_SPLIT,
        "script": str(script_path),
        "script_sha256": cfg.sha256_file(script_path) if script_path.is_file() else None,
        "sizes": cfg.sizes(tier),
        "primary_dv": primary_dv,
        "scorer": scorer,
        "seed": int(seed),
        "arms": list(arms),
        "fc_mass_min": cfg.FC_MASS_MIN,
        "frozen_v3": cfg.FROZEN_V3,
        "do_not_overwrite_v3": True,
    }
    if extra:
        payload["extra"] = extra
    return payload


def write_lock(run_dir: Path, payload: dict[str, Any]) -> Path:
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    dest = lock_path(run_dir)
    for k in REQUIRED:
        if k not in payload or payload[k] in (None, "", []):
            raise LockError(f"lock missing {k}")
    if dest.exists():
        old = json.loads(dest.read_text(encoding="utf-8"))
        if old.get("script_sha256") != payload.get("script_sha256"):
            results = run_dir / "results.json"
            complete = False
            if results.is_file():
                try:
                    complete = bool(json.loads(results.read_text(encoding="utf-8")).get("complete"))
                except Exception:
                    complete = False
            if complete:
                raise LockError("LOCK.json already exists with a different script hash")
            dest.unlink()
        else:
            return dest
    tmp = dest.with_suffix(".json.tmp")
    tmp.write_text(cfg.dumps(payload), encoding="utf-8")
    tmp.replace(dest)
    return dest


def require_lock(run_dir: Path, script_path: Path) -> dict[str, Any]:
    dest = lock_path(run_dir)
    if not dest.is_file():
        raise LockError(f"missing {dest}; write lock before scores")
    blob = json.loads(dest.read_text(encoding="utf-8"))
    for k in REQUIRED:
        if k not in blob:
            raise LockError(f"corrupt lock: missing {k}")
    if script_path.is_file():
        got = cfg.sha256_file(script_path)
        if blob.get("script_sha256") != got:
            raise LockError("script hash drifted after lock")
    if blob.get("weights_dtype") != "bf16" or blob.get("quantize"):
        raise LockError("lock must be bf16 unquantized")
    if blob.get("describe_before_task"):
        raise LockError("DESCRIBE-before-task is forbidden")
    return blob
