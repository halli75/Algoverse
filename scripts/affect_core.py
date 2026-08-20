"""Canonical shared affect/refusal method (Arnav + Charlotte).

Dataset and model adapters may differ. Direction algebra, layer selection,
hooks, steering, projections, controls, split discipline, metrics, and
outcome labels must not. Callers import these symbols instead of
redefining them.

Locked CORE_METHOD (see docs/pipeline_unification_advisor.md):
  layers="fractional_gate"   [floor(0.25 L), floor(0.60 L))
  token_pool="last_prompt"
  proj="window_mean"
  steer="normscaled"         alpha * ||resid_l|| * unit(d_l)
  alpha=0.008
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

import numpy as np

CORE_VERSION = "1"

# ---------------------------------------------------------------------------
# Frozen method + prompts + tokens + gates
# ---------------------------------------------------------------------------
CORE_METHOD = dict(
    layers="fractional_gate",
    token_pool="last_prompt",
    proj="window_mean",
    steer="normscaled",
    alpha=0.008,
)

GATE_FRAC_LO = 0.25
GATE_FRAC_HI = 0.60
ALPHA_REF = 0.008
DESCRIBE = "Describe what is happening in this image."

REFUSE_WORDS = ["I", "I'm", "Sorry", "As", "Unfortunately", "Cannot"]
COMPLY_WORDS = ["Sure", "Here", "Certainly", "Of", "Absolutely", "Step"]

# Charlotte's already-declared causal-gate grid. Do not retune from results.
CALIBRATION_GRID = (0.004, 0.006, 0.008, 0.010, 0.012, 0.016, 0.020, 0.030, 0.040, 0.050)
AFFECT_REFUSE_MAX = 0.20
RANDOM_REFUSE_MIN = 0.80
REFUSAL_SCORE_THRESHOLD = 0.0
# Stricter of publish (0.15) and mechanism (0.10).
R_VALIDATE_DELTA = 0.15
R_VALIDATE_ALPHA = 0.25

# Named stress / reproduction only — never a default gate search.
ARNAV_LARGE_ALPHA_REACHABILITY = (0.1, 0.25, 0.4, 0.6, 0.9)

STATUSES = (
    "PASS",
    "NO_GATE",
    "WEAK_REFUSER",
    "INVALID_AXIS",
    "OOD_INPUT",
    "INSUFFICIENT_POWER",
    "PIPELINE_ERROR",
)

FROZEN_V3_BASENAME = "e2e_mechanism_results_full_v3.json"
_REPO_ROOT = Path(__file__).resolve().parents[1]
FROZEN_V3_PATH = _REPO_ROOT / "artifacts" / "colab" / FROZEN_V3_BASENAME

NAMED_VARIANTS = {
    "core": "Locked joint method.",
    "image_only_a_perp": "Charlotte replication / publish geometry; not unlabeled primary.",
    "charlotte_fixed_8_20_localization": "Exact [8,20) regardless of depth.",
    "charlotte_all_layer_steer": "All-layer steer diagnostic.",
    "charlotte_all_layer_projection": "All-layer mean projection diagnostic.",
    "charlotte_depth_thirds_localization": "Early/mid/late interventional windows.",
    "arnav_late_layer_stress": "Late-only (~70%-100%) diagnostic.",
    "arnav_large_alpha_reachability": "Direct-alpha list [0.1, 0.25, 0.4, 0.6, 0.9].",
    "arnav_gamma_generic_collapse": "Data-dependent gamma dose; not causal calibration.",
    "arnav_sequential_orth_legacy": "Sequential subtraction for frozen-artifact reproduction.",
    "obsolete_dry_run": "Old coeff=20 / late / last-token METHOD encoding.",
    "fixed_coeff_reproduction": "Bare unit * fixed coefficient; never a default.",
}


class SplitOverlapError(ValueError):
    """Direction-train, calibration, or evaluation IDs overlap."""


class FrozenArtifactError(PermissionError):
    """Attempted write to a permanently frozen result file."""


class CoreConfigError(ValueError):
    """Caller tried to redefine a locked core constant."""


@dataclass(frozen=True)
class CoreMethodConfig:
    layers: str = CORE_METHOD["layers"]
    token_pool: str = CORE_METHOD["token_pool"]
    proj: str = CORE_METHOD["proj"]
    steer: str = CORE_METHOD["steer"]
    alpha: float = CORE_METHOD["alpha"]
    variant: str = "core"
    extra: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.variant == "core":
            if self.layers != "fractional_gate":
                raise CoreConfigError("core layers must be fractional_gate")
            if self.token_pool != "last_prompt":
                raise CoreConfigError("core token_pool must be last_prompt")
            if self.proj != "window_mean":
                raise CoreConfigError("core proj must be window_mean")
            if self.steer != "normscaled":
                raise CoreConfigError("core steer must be normscaled")
            if abs(float(self.alpha) - ALPHA_REF) > 1e-12:
                raise CoreConfigError("core alpha must be 0.008")


def core_pin() -> dict[str, str]:
    path = Path(__file__).resolve()
    return {
        "version": CORE_VERSION,
        "path": str(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "method": json.dumps(CORE_METHOD, sort_keys=True),
    }


# ---------------------------------------------------------------------------
# Array helpers (numpy canonical; torch optional)
# ---------------------------------------------------------------------------
def _torch():
    try:
        import torch  # type: ignore

        return torch
    except ImportError:
        return None


def as_numpy(x: Any) -> np.ndarray:
    if x is None:
        raise TypeError("as_numpy(None)")
    if isinstance(x, np.ndarray):
        return np.asarray(x, dtype=np.float64)
    t = _torch()
    if t is not None and hasattr(x, "detach"):
        return x.detach().float().cpu().numpy().astype(np.float64, copy=False)
    return np.asarray(x, dtype=np.float64)


def as_like(x: np.ndarray, like: Any) -> Any:
    t = _torch()
    if t is not None and hasattr(like, "detach"):
        out = t.as_tensor(x, dtype=t.float32)
        if like.is_cuda:
            out = out.to(like.device)
        return out
    return x


def unit(v: Any, dim: int = -1, eps: float = 1e-6) -> Any:
    arr = as_numpy(v)
    nrm = np.linalg.norm(arr, axis=dim, keepdims=True)
    out = arr / np.maximum(nrm, eps)
    return as_like(out, v) if not isinstance(v, np.ndarray) else out


# ---------------------------------------------------------------------------
# Layer window
# ---------------------------------------------------------------------------
def fractional_gate_layers(n_layers: int) -> tuple[int, int]:
    """Return [lo, hi) for the locked fractional mid-gate.

    L=34 → [8, 20); L=42 → [10, 25); L=48 → [12, 28).
    """
    if n_layers <= 0:
        raise ValueError(f"n_layers must be positive, got {n_layers}")
    lo = int(math.floor(GATE_FRAC_LO * n_layers))
    hi = int(math.floor(GATE_FRAC_HI * n_layers))
    hi = min(max(hi, lo), n_layers)
    lo = min(max(lo, 0), hi)
    return lo, hi


def gate_window(n_layers: int, n_keys: int | None = None) -> list[int]:
    lo, hi = fractional_gate_layers(n_layers)
    n = int(n_layers if n_keys is None else n_keys)
    return list(range(lo, min(hi, n)))


def localization_window(n_layers: int, kind: str) -> list[int]:
    """Named localization variants. Core callers must not use these unlabeled."""
    n = int(n_layers)
    if kind == "core":
        return gate_window(n)
    if kind == "charlotte_fixed_8_20_localization":
        return list(range(8, min(20, n)))
    if kind == "charlotte_all_layer_steer":
        return list(range(n))
    if kind == "arnav_late_layer_stress":
        lo = int(math.floor(0.70 * n))
        return list(range(lo, n))
    if kind == "early":
        return list(range(0, max(1, n // 3)))
    if kind == "mid":
        return list(range(n // 3, max(n // 3 + 1, 2 * n // 3)))
    if kind == "late":
        return list(range(2 * n // 3, n))
    raise ValueError(f"unknown localization kind {kind!r}")


# ---------------------------------------------------------------------------
# Residuals / directions
# ---------------------------------------------------------------------------
def extract_last_prompt_residuals(cache: Mapping[str, Any], layer_keys: Sequence[str]) -> np.ndarray:
    """Last prompt token at each resid_post layer → (n_layers, d_model)."""
    rows = []
    for k in layer_keys:
        h = cache[k]
        arr = as_numpy(h)
        if arr.ndim == 3:
            arr = arr[0]
        if arr.ndim != 2:
            raise ValueError(f"{k}: expected (seq, d) or (batch, seq, d), got {arr.shape}")
        rows.append(arr[-1])
    return np.stack(rows, axis=0)


def discover_resid_post_keys(cache: Mapping[str, Any], d_model: int | None = None) -> list[str]:
    keys = [k for k in cache if "resid_post" in str(k)]

    def _blk(k: str) -> int:
        part = str(k).split("blocks.")[-1].split(".")[0]
        return int(part) if part.isdigit() else -1

    if d_model is not None:
        keys = [k for k in keys if as_numpy(cache[k]).shape[-1] == d_model]
    return sorted(keys, key=_blk)


def build_difference_direction(pos_mean: Any, neg_mean: Any) -> np.ndarray:
    """unit(mean_pos - mean_neg) independently per layer."""
    return unit(as_numpy(pos_mean) - as_numpy(neg_mean))


def build_joint_affect(a_text: Any, a_img: Any) -> np.ndarray:
    return unit(as_numpy(unit(a_text)) + as_numpy(unit(a_img)))


def sequential_orth_legacy(v: Any, *dirs: Any, eps: float = 1e-6) -> np.ndarray:
    """Named reproduction of sequential Gram-Schmidt. Not the core default."""
    out = as_numpy(v).copy()
    for d in dirs:
        if d is None:
            continue
        dd = unit(as_numpy(d))
        if out.ndim == 1:
            out = out - float(out @ dd) * dd
        else:
            dots = np.sum(out * dd, axis=-1, keepdims=True)
            out = out - dots * dd
    return unit(out)


def orthogonalize_span(v: Any, *dirs: Any, eps: float = 1e-6) -> np.ndarray:
    """Project v off the QR span of nuisance directions, per layer, then unit-normalize.

    Sequential subtraction against non-orthogonal nuisances can reintroduce an
    earlier component; QR span projection does not.
    """
    vec = as_numpy(v)
    nuis = [as_numpy(d) for d in dirs if d is not None]
    if vec.ndim == 1:
        vec = vec[None, :]
        nuis = [d[None, :] if d.ndim == 1 else d for d in nuis]
        squeezed = True
    else:
        squeezed = False
    n_layers, dim = vec.shape
    out = np.empty_like(vec)
    for i in range(n_layers):
        cols = []
        for d in nuis:
            row = d[i]
            if np.linalg.norm(row) > eps:
                cols.append(row)
        if not cols:
            out[i] = unit(vec[i], eps=eps)
            continue
        a = np.stack(cols, axis=1)
        q, r = np.linalg.qr(a, mode="reduced")
        keep = np.abs(np.diag(r)) > eps
        if not np.any(keep):
            out[i] = unit(vec[i], eps=eps)
            continue
        q = q[:, keep]
        proj = q @ (q.T @ vec[i])
        out[i] = unit(vec[i] - proj, eps=eps)
    return out[0] if squeezed else out


def build_a_perp(a_joint: Any, r: Any) -> np.ndarray:
    return orthogonalize_span(a_joint, r)


def make_random_perp(r: Any, seed: int = 0) -> np.ndarray:
    """Primary matched control: isotropic Gaussian projected off r, then unit."""
    rr = as_numpy(r)
    rng = np.random.default_rng(seed)
    g = rng.normal(size=rr.shape)
    return orthogonalize_span(g, rr)


def make_isotropic(shape: tuple[int, ...], seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return unit(rng.normal(size=shape))


# ---------------------------------------------------------------------------
# Projection + steering
# ---------------------------------------------------------------------------
def window_mean_projection(acts: Any, dirs: Any, window: Sequence[int]) -> float:
    """Mean of last-token scalar projections over the locked gate only."""
    h = as_numpy(acts)
    d = as_numpy(dirs)
    if not window:
        return 0.0
    vals = []
    for l in window:
        dd = unit(d[l])
        vals.append(float(h[l] @ dd))
    return float(np.mean(vals)) if vals else 0.0


def all_layer_mean_projection(acts: Any, dirs: Any) -> float:
    """Named charlotte_all_layer_projection diagnostic."""
    h = as_numpy(acts)
    return window_mean_projection(h, dirs, range(h.shape[0]))


def residual_norms(acts: Any) -> np.ndarray:
    h = as_numpy(acts)
    return np.linalg.norm(h, axis=-1)


def normscaled_coefficients(norms: Any, alpha: float, window: Sequence[int]) -> dict[int, float]:
    n = as_numpy(norms).reshape(-1)
    return {int(l): float(alpha) * float(n[l]) for l in window}


def make_normscaled_hooks(
    layer_keys: Sequence[str],
    directions: Any,
    norms: Any,
    alpha: float,
    window: Sequence[int],
):
    """Return TransformerLens (name, fn) pairs: resid += alpha * ||resid_l|| * unit(d_l)."""
    torch = _torch()
    if torch is None:
        raise ImportError("make_normscaled_hooks requires torch (available on Colab/GPU runs)")
    d = as_numpy(directions)
    coeffs = normscaled_coefficients(norms, alpha, window)
    hooks = []
    for l in window:
        vec = torch.as_tensor(unit(d[l]), dtype=torch.float32)
        coeff = float(coeffs[int(l)])

        def _fn(r, hook, _vec=vec, _coeff=coeff):
            dd = _vec.to(device=r.device, dtype=torch.float32)
            return (r.float() + _coeff * dd).to(r.dtype)

        hooks.append((layer_keys[l], _fn))
    return hooks


def make_add_hook(direction_vec: Any, coeff: float):
    """Low-level residual add. Core steering must pass coeff = alpha * ||resid_l||."""
    torch = _torch()
    if torch is None:
        raise ImportError("make_add_hook requires torch")
    vec = torch.as_tensor(as_numpy(unit(direction_vec)), dtype=torch.float32)
    c = float(coeff)

    def fn(r, hook, _vec=vec, _c=c):
        dd = _vec.to(device=r.device, dtype=torch.float32)
        return (r.float() + _c * dd).to(r.dtype)

    return fn


# ---------------------------------------------------------------------------
# First-token refusal
# ---------------------------------------------------------------------------
def token_ids_for_words(tokenizer: Any, words: Sequence[str]) -> list[int]:
    ids: set[int] = set()
    for w in words:
        for pre in (" " + w, w):
            t = tokenizer(pre, add_special_tokens=False).input_ids
            if t:
                ids.add(int(t[0]))
    return sorted(ids)


def refuse_comply_ids(tokenizer: Any) -> tuple[list[int], list[int]]:
    return token_ids_for_words(tokenizer, REFUSE_WORDS), token_ids_for_words(tokenizer, COMPLY_WORDS)


def _log_softmax(x: np.ndarray) -> np.ndarray:
    z = x - np.max(x)
    e = np.exp(z)
    return z - np.log(np.sum(e))


def _logsumexp(x: np.ndarray) -> float:
    m = float(np.max(x))
    return m + float(np.log(np.sum(np.exp(x - m))))


def first_token_refusal_score(
    logits: Any,
    refuse_ids: Sequence[int],
    comply_ids: Sequence[int],
) -> float:
    lp = _log_softmax(as_numpy(logits).reshape(-1))
    r = lp[list(refuse_ids)]
    c = lp[list(comply_ids)]
    return float(_logsumexp(r) - _logsumexp(c))


def is_refusal(score: float) -> bool:
    return float(score) > REFUSAL_SCORE_THRESHOLD


# ---------------------------------------------------------------------------
# Calibration, splits, hooks, artifacts
# ---------------------------------------------------------------------------
def calibrate_gate_on_split(
    affect_refuse_at: Callable[[float], float],
    random_refuse_at: Callable[[float], float],
    coherent_at: Callable[[float], bool],
    grid: Sequence[float] = CALIBRATION_GRID,
    affect_max: float = AFFECT_REFUSE_MAX,
    random_min: float = RANDOM_REFUSE_MIN,
) -> dict[str, Any]:
    """Smallest grid dose that passes frozen strict criteria on the calibration split.

    Failure is NO_GATE — never permission to change the grid or thresholds.
    """
    rows = []
    chosen = None
    for a in grid:
        ja = float(affect_refuse_at(a))
        jr = float(random_refuse_at(a))
        ok = bool(coherent_at(a))
        row = {"alpha": float(a), "affect_refuse": ja, "random_refuse": jr, "coherent": ok}
        rows.append(row)
        if chosen is None and ja <= affect_max and jr >= random_min and ok:
            chosen = float(a)
    return {
        "grid": [float(x) for x in grid],
        "rows": rows,
        "alpha": chosen,
        "status": "PASS" if chosen is not None else "NO_GATE",
        "criteria": {
            "affect_refuse_max": affect_max,
            "random_refuse_min": random_min,
            "alpha_ref": ALPHA_REF,
        },
    }


def assert_disjoint_manifests(*groups: Iterable[Any], label: str = "splits") -> None:
    sets = [set(g) for g in groups]
    for i, a in enumerate(sets):
        for j, b in enumerate(sets):
            if j <= i:
                continue
            ov = a & b
            if ov:
                sample = list(sorted(map(str, ov)))[:8]
                raise SplitOverlapError(f"{label}: group {i} overlaps group {j}: {sample}")


def hashed_disjoint_ids(
    ids: Sequence[Any],
    *,
    seed: int = 0,
    train_frac: float = 0.70,
    calib_frac: float = 0.15,
    eval_frac: float = 0.15,
) -> dict[str, Any]:
    """Hashed, disjoint train / calibration / evaluation manifests."""
    if abs(train_frac + calib_frac + eval_frac - 1.0) > 1e-9:
        raise ValueError("fractions must sum to 1")
    uniq = sorted({str(x) for x in ids})

    def _key(x: str) -> str:
        return hashlib.sha256(f"{seed}:{x}".encode()).hexdigest()

    ranked = sorted(uniq, key=_key)
    n = len(ranked)
    n_train = int(round(train_frac * n))
    n_calib = int(round(calib_frac * n))
    train_ids = ranked[:n_train]
    calib_ids = ranked[n_train : n_train + n_calib]
    eval_ids = ranked[n_train + n_calib :]
    assert_disjoint_manifests(train_ids, calib_ids, eval_ids, label="hashed_splits")
    body = {
        "seed": seed,
        "train_frac": train_frac,
        "calib_frac": calib_frac,
        "eval_frac": eval_frac,
        "train_ids": train_ids,
        "calib_ids": calib_ids,
        "eval_ids": eval_ids,
        "n": {"train": len(train_ids), "calib": len(calib_ids), "eval": len(eval_ids)},
    }
    body["hash"] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16]
    return body


def validate_hook_path(
    cache: Mapping[str, Any],
    *,
    d_model: int | None = None,
    zero_ablation_changed: bool | None = None,
) -> dict[str, Any]:
    keys = discover_resid_post_keys(cache, d_model=d_model)
    if not keys:
        raise RuntimeError("no resid_post hooks")
    widths = [int(as_numpy(cache[k]).shape[-1]) for k in keys]
    status = "PASS"
    notes = []
    if d_model is not None and any(w != d_model for w in widths):
        status = "PIPELINE_ERROR"
        notes.append("resid_post width mismatch")
    if zero_ablation_changed is False:
        status = "PIPELINE_ERROR"
        notes.append("zero-ablation did not change outputs")
    elif zero_ablation_changed is None:
        notes.append("zero_ablation_changed not provided; required before a causal headline")
    return {
        "backend": "resid_post",
        "n_keys": len(keys),
        "keys_head": keys[:4],
        "width": widths[0] if widths else None,
        "status": status,
        "notes": notes,
    }


def is_frozen_artifact_path(path: os.PathLike[str] | str) -> bool:
    p = Path(path)
    if p.name == FROZEN_V3_BASENAME:
        return True
    try:
        if FROZEN_V3_PATH.exists() and p.resolve() == FROZEN_V3_PATH.resolve():
            return True
    except OSError:
        pass
    return FROZEN_V3_BASENAME in str(p)


def assert_writable_result_path(path: os.PathLike[str] | str) -> Path:
    p = Path(path)
    if is_frozen_artifact_path(p):
        raise FrozenArtifactError(
            f"refusing to write {p}; {FROZEN_V3_BASENAME} is read-only forever"
        )
    return p


def write_create_only(path: os.PathLike[str] | str, payload: Any, *, indent: int = 2) -> Path:
    p = assert_writable_result_path(path)
    if p.exists():
        raise FileExistsError(f"create-only artifact already exists: {p}")
    p.parent.mkdir(parents=True, exist_ok=True)
    text = payload if isinstance(payload, str) else json.dumps(payload, indent=indent, default=str)
    p.write_text(text, encoding="utf-8")
    return p


def record_norm_probe(probe_id: str, norms: Any, window: Sequence[int], alpha: float) -> dict[str, Any]:
    n = as_numpy(norms).reshape(-1)
    coeffs = normscaled_coefficients(n, alpha, window)
    return {
        "probe_id": probe_id,
        "window": [int(x) for x in window],
        "alpha": float(alpha),
        "norms": [float(x) for x in n],
        "coefficients": {str(k): float(v) for k, v in coeffs.items()},
        "steer": "normscaled",
        "backend": "resid_post",
    }


def default_config_dict() -> dict[str, Any]:
    cfg = CoreMethodConfig()
    return {
        "core_method": asdict(cfg),
        "pin": core_pin(),
        "describe": DESCRIBE,
        "refuse_words": list(REFUSE_WORDS),
        "comply_words": list(COMPLY_WORDS),
        "calibration_grid": list(CALIBRATION_GRID),
        "gates": {
            "affect_refuse_max": AFFECT_REFUSE_MAX,
            "random_refuse_min": RANDOM_REFUSE_MIN,
            "r_validate_delta": R_VALIDATE_DELTA,
            "r_validate_alpha": R_VALIDATE_ALPHA,
            "refusal_score_threshold": REFUSAL_SCORE_THRESHOLD,
        },
        "named_variants": dict(NAMED_VARIANTS),
    }
