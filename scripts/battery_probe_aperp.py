"""Reusable frozen-v3 a_perp probe for the affect battery.

[[battery-campaign]] [[VA-subspace]]

Other experiment agents import this module. It never refits directions and
never writes artifacts/colab/e2e_mechanism_results_full_v3.json.

Primary mediator M is the window-mean a_perp projection at the last prompt
token during the *behavioral* forward (no DESCRIBE text). DESCRIBE-level
projection is a named diagnostic only.

Identification lock: artifacts/battery/exp10/ADVISOR_SPEC.md
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(_SCRIPTS))
import affect_core as ac

DESCRIBE = ac.DESCRIBE
EXPECTED_SPLIT = "1e8ea1c22144dd9d"
EXPECTED_MODEL = "google/gemma-4-E4B-it"
EXPECTED_N_LAYERS = 42
EXPECTED_D_MODEL = 2560
EXPECTED_GATE = (10, 25)
FROZEN_V3_JSON = ac.FROZEN_V3_PATH
DIRS_BASENAME = "e2e_dirs_mechanism.pt"
DIAGNOSTIC_LABEL = "DIAGNOSTIC_NOT_V3"
FROZEN_LABEL = "FROZEN_V3_EXACT"

# Frozen v3 reported mean |cos| (SOURCE_FACTS). Continuity check only.
V3_ABS_COS = {
    "abs_cos_a_text_r": 0.16912896931171417,
    "abs_cos_a_img_r": 0.1353452205657959,
    "abs_cos_a_text_a_img": 0.09839121252298355,
    "abs_cos_a_both_r": 0.18580281734466553,
}
V3_COS_TOL = 0.02
N_PAIRS_MIN = 64
FC_MASS_MIN = 0.8
N_BOOT_DEFAULT = 1000

_DIR_KEYS = (
    "r_dir",
    "a_text",
    "a_img",
    "a_both",
    "a_perp",
    "a_text_perp",
    "a_img_perp",
    "rand_perp",
    "j_dir",
    "j_perp",
)


@dataclass
class FrozenDirs:
    status: str
    path: str
    sha256: str
    model: str | None
    n_layers: int
    d_model: int
    window: list[int]
    arrays: dict[str, np.ndarray]
    notes: list[str] = field(default_factory=list)
    abs_cos: dict[str, float] = field(default_factory=dict)
    continuity_ok: bool | None = None

    @property
    def a_perp(self) -> np.ndarray:
        return self.arrays["a_perp"]

    @property
    def is_frozen_v3(self) -> bool:
        return self.status == FROZEN_LABEL


def _as_np(x: Any) -> np.ndarray:
    return ac.as_numpy(x)


def mean_abs_cos(a: np.ndarray, b: np.ndarray) -> float:
    aa = ac.unit(_as_np(a))
    bb = ac.unit(_as_np(b))
    if aa.ndim == 1:
        return float(abs(float(aa @ bb)))
    dots = np.abs(np.sum(aa * bb, axis=-1))
    return float(np.mean(dots))


def core_window(n_layers: int = EXPECTED_N_LAYERS) -> list[int]:
    return ac.gate_window(int(n_layers))


def project_aperp(
    acts: Any,
    dirs: Any,
    window: Sequence[int] | None = None,
) -> float:
    """Locked window-mean last-token projection onto a_perp."""
    h = _as_np(acts)
    d = _as_np(dirs)
    if window is None:
        window = core_window(h.shape[0])
    return float(ac.window_mean_projection(h, d, window))


def hidden_states_to_acts(hidden_states: Sequence[Any], n_layers: int | None = None) -> np.ndarray:
    """HF/TL hidden_states -> (n_layers, d) last-prompt residuals.

    If the first entry is embeddings (n_layers+1 tensors), it is dropped.
    """
    rows = [_as_np(h) for h in hidden_states]
    if not rows:
        raise ValueError("empty hidden_states")
    n = int(n_layers or EXPECTED_N_LAYERS)
    if len(rows) == n + 1:
        rows = rows[1:]
    elif len(rows) > n:
        rows = rows[-n:]
    out = []
    for arr in rows[:n]:
        if arr.ndim == 3:
            arr = arr[0]
        if arr.ndim != 2:
            raise ValueError(f"expected (seq, d), got {arr.shape}")
        out.append(arr[-1])
    return np.stack(out, axis=0)


def cache_to_acts(cache: Mapping[str, Any], d_model: int | None = None) -> np.ndarray:
    keys = ac.discover_resid_post_keys(cache, d_model=d_model)
    if not keys:
        raise RuntimeError("no resid_post keys in cache")
    return ac.extract_last_prompt_residuals(cache, keys)


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def candidate_dir_paths(extra: Iterable[os.PathLike[str] | str] | None = None) -> list[Path]:
    home = Path.home()
    root = Path(os.environ.get("E2E_ROOT", str(home / "algoverse_run"))).expanduser()
    repo = _SCRIPTS.parent
    raw = [
        os.environ.get("E2E_DIRS"),
        os.environ.get("EXP10_DIRS"),
        root / DIRS_BASENAME,
        root / "battery" / DIRS_BASENAME,
        root / "battery" / "exp10" / DIRS_BASENAME,
        root / "battery" / "exp10" / "dirs_frozen_v3.pt",
        Path("/content") / DIRS_BASENAME,
        repo / "artifacts" / "colab" / DIRS_BASENAME,
        home / "Algoverse" / "artifacts" / "colab" / DIRS_BASENAME,
    ]
    if extra:
        raw.extend(extra)
    out: list[Path] = []
    seen: set[str] = set()
    for item in raw:
        if not item:
            continue
        p = Path(item).expanduser()
        key = str(p)
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def find_dirs_file(extra: Iterable[os.PathLike[str] | str] | None = None) -> Path | None:
    for p in candidate_dir_paths(extra):
        if p.is_file() and p.stat().st_size > 1000:
            return p
    home = Path.home()
    root = Path(os.environ.get("E2E_ROOT", str(home / "algoverse_run"))).expanduser()
    search_dirs = [
        root,
        root / "battery",
        root / "battery" / "exp10",
        home / "Algoverse" / "artifacts" / "colab",
        Path("/content"),
    ]
    names = {DIRS_BASENAME, "dirs_frozen_v3.pt", "e2e_dirs.pt", "dirs_DIAGNOSTIC_NOT_V3.pt"}
    for folder in search_dirs:
        if not folder.is_dir() and not (folder.exists() and folder.is_file()):
            if folder.is_file() and folder.stat().st_size > 1000:
                return folder
            continue
        if not folder.is_dir():
            continue
        for p in folder.iterdir():
            if p.is_file() and p.name in names and p.stat().st_size > 1000:
                return p
    return None


def _torch_load(path: Path) -> dict[str, Any]:
    import torch

    return torch.load(str(path), map_location="cpu", weights_only=False)


def load_frozen_dirs(
    path: os.PathLike[str] | str | None = None,
    *,
    allow_diagnostic: bool = True,
) -> FrozenDirs:
    """Load a_perp pack. Does not refit. Refuses to treat a rebuild as v3."""
    p = Path(path).expanduser() if path else find_dirs_file()
    if p is None or not p.is_file():
        raise FileNotFoundError("frozen/diagnostic dirs.pt not found; rebuild only as DIAGNOSTIC_NOT_V3")
    if ac.is_frozen_artifact_path(p):
        raise ac.FrozenArtifactError(f"refusing to treat result JSON as dirs: {p}")
    blob = _torch_load(p)
    if not isinstance(blob, dict) or "a_perp" not in blob:
        raise ValueError(f"{p} has no a_perp")
    arrays = {k: _as_np(blob[k]) for k in _DIR_KEYS if k in blob and blob[k] is not None}
    a = arrays["a_perp"]
    if a.ndim != 2:
        raise ValueError(f"a_perp shape {a.shape} != (n_layers, d)")
    n_layers, d_model = int(a.shape[0]), int(a.shape[1])
    win = blob.get("win") or core_window(n_layers)
    window = [int(x) for x in win]
    model = blob.get("model")
    notes = []
    label = str(blob.get("status") or blob.get("provenance") or "")
    marked_diag = DIAGNOSTIC_LABEL in label or bool(blob.get("diagnostic"))
    shape_ok = n_layers == EXPECTED_N_LAYERS and d_model == EXPECTED_D_MODEL
    model_ok = (model is None) or (str(model) == EXPECTED_MODEL)
    abs_cos = {}
    if "a_text" in arrays and "r_dir" in arrays:
        abs_cos["abs_cos_a_text_r"] = mean_abs_cos(arrays["a_text"], arrays["r_dir"])
    if "a_img" in arrays and "r_dir" in arrays:
        abs_cos["abs_cos_a_img_r"] = mean_abs_cos(arrays["a_img"], arrays["r_dir"])
    if "a_text" in arrays and "a_img" in arrays:
        abs_cos["abs_cos_a_text_a_img"] = mean_abs_cos(arrays["a_text"], arrays["a_img"])
    if "a_both" in arrays and "r_dir" in arrays:
        abs_cos["abs_cos_a_both_r"] = mean_abs_cos(arrays["a_both"], arrays["r_dir"])
    continuity = True
    for k, exp in V3_ABS_COS.items():
        if k not in abs_cos:
            continuity = False
            notes.append(f"missing {k}")
            continue
        if abs(abs_cos[k] - exp) > V3_COS_TOL:
            continuity = False
            notes.append(f"{k} {abs_cos[k]:.4f} != v3 {exp:.4f}")
    frozen_claim = (
        not marked_diag
        and shape_ok
        and model_ok
        and blob.get("affect_axis", "a_perp=orth(unit(a_text+a_img), r)")
        and continuity
        and p.name in {DIRS_BASENAME, "dirs_frozen_v3.pt"}
    )
    if marked_diag or not frozen_claim:
        status = DIAGNOSTIC_LABEL
        if not allow_diagnostic:
            raise RuntimeError(f"{p} is not FROZEN_V3_EXACT")
        if not marked_diag:
            notes.append("loaded file failed frozen-v3 continuity; labeled DIAGNOSTIC_NOT_V3")
    else:
        status = FROZEN_LABEL
    return FrozenDirs(
        status=status,
        path=str(p),
        sha256=file_sha256(p),
        model=None if model is None else str(model),
        n_layers=n_layers,
        d_model=d_model,
        window=window,
        arrays=arrays,
        notes=notes,
        abs_cos=abs_cos,
        continuity_ok=continuity,
    )


def pack_diagnostic_dirs(
    arrays: Mapping[str, Any],
    *,
    path: os.PathLike[str] | str,
    model: str = EXPECTED_MODEL,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a DIAGNOSTIC_NOT_V3 payload. Caller writes it. Never writes v3 JSON."""
    ac.assert_writable_result_path(path)
    if Path(path).name == ac.FROZEN_V3_BASENAME:
        raise ac.FrozenArtifactError("refusing diagnostic pack named as v3 JSON")
    body: dict[str, Any] = {
        k: arrays[k] for k in _DIR_KEYS if k in arrays and arrays[k] is not None
    }
    a = _as_np(body["a_perp"])
    body.update(
        {
            "model": model,
            "status": DIAGNOSTIC_LABEL,
            "provenance": DIAGNOSTIC_LABEL,
            "diagnostic": True,
            "affect_axis": "a_perp=orth_span(unit(a_text+a_img), r)",
            "win": core_window(a.shape[0]),
            "core_method": dict(ac.CORE_METHOD),
            "core_pin": ac.core_pin(),
            "note": "Continuity rebuild from locked affect_core. Not the frozen v3 dirs.",
        }
    )
    if extra:
        body.update(dict(extra))
    return body


def pearson(x: Sequence[float], y: Sequence[float]) -> float | None:
    a = np.asarray(x, dtype=np.float64)
    b = np.asarray(y, dtype=np.float64)
    if a.size < 3 or b.size != a.size:
        return None
    if float(np.std(a)) < 1e-12 or float(np.std(b)) < 1e-12:
        return None
    return float(np.corrcoef(a, b)[0, 1])


def spearman(x: Sequence[float], y: Sequence[float]) -> float | None:
    a = np.asarray(x, dtype=np.float64)
    b = np.asarray(y, dtype=np.float64)
    if a.size < 3 or b.size != a.size:
        return None
    ra = a.argsort().argsort().astype(np.float64)
    rb = b.argsort().argsort().astype(np.float64)
    return pearson(ra, rb)


def _ols_b(x: np.ndarray, y: np.ndarray) -> float:
    xm = x - float(np.mean(x))
    ym = y - float(np.mean(y))
    den = float(np.dot(xm, xm))
    if den < 1e-12:
        return float("nan")
    return float(np.dot(xm, ym) / den)


def paired_product_of_coefficients(
    delta_m: Sequence[float],
    delta_y: Sequence[float],
) -> dict[str, float | None]:
    """Locked primary identification on paired ΔM, ΔY."""
    m = np.asarray(delta_m, dtype=np.float64)
    y = np.asarray(delta_y, dtype=np.float64)
    if m.size != y.size or m.size == 0:
        raise ValueError("delta_m/delta_y length mismatch")
    a = float(np.mean(m))
    c = float(np.mean(y))
    b = _ols_b(m, y)
    ab = float(a * b) if math.isfinite(b) else None
    c_prime = float(c - b * a) if math.isfinite(b) else None
    return {
        "n": int(m.size),
        "a_mean_dM": a,
        "b_dY_on_dM": b if math.isfinite(b) else None,
        "c_mean_dY": c,
        "c_prime": c_prime,
        "ab": ab,
        "var_dM": float(np.var(m, ddof=1)) if m.size > 1 else 0.0,
        "var_dY": float(np.var(y, ddof=1)) if y.size > 1 else 0.0,
        "pearson": pearson(m, y),
        "spearman": spearman(m, y),
    }


def bootstrap_ci(
    delta_m: Sequence[float],
    delta_y: Sequence[float],
    *,
    n_boot: int = N_BOOT_DEFAULT,
    seed: int = 10,
    keys: Sequence[str] = ("a_mean_dM", "b_dY_on_dM", "c_mean_dY", "ab"),
) -> dict[str, dict[str, float | None]]:
    m = np.asarray(delta_m, dtype=np.float64)
    y = np.asarray(delta_y, dtype=np.float64)
    rng = np.random.default_rng(seed)
    n = int(m.size)
    store = {k: [] for k in keys}
    for _ in range(int(n_boot)):
        idx = rng.integers(0, n, size=n)
        rec = paired_product_of_coefficients(m[idx], y[idx])
        for k in keys:
            v = rec.get(k)
            if v is not None and math.isfinite(float(v)):
                store[k].append(float(v))
    out: dict[str, dict[str, float | None]] = {}
    for k, vals in store.items():
        if len(vals) < max(20, int(0.5 * n_boot)):
            out[k] = {"lo": None, "hi": None, "n_boot": len(vals)}
            continue
        lo, hi = np.quantile(vals, [0.025, 0.975])
        out[k] = {"lo": float(lo), "hi": float(hi), "n_boot": len(vals)}
    return out


def holm_exclude_zero(pvals: Sequence[tuple[str, float]]) -> dict[str, bool]:
    """Holm step-down on two-sided 'CI excludes 0' p-values (already computed)."""
    ranked = sorted(pvals, key=lambda t: t[1])
    m = len(ranked)
    out = {name: False for name, _ in ranked}
    for i, (name, p) in enumerate(ranked):
        thr = 0.05 / (m - i)
        if p <= thr:
            out[name] = True
        else:
            break
    return out


def ci_excludes_zero(lo: float | None, hi: float | None) -> bool:
    if lo is None or hi is None:
        return False
    return (lo > 0.0 and hi > 0.0) or (lo < 0.0 and hi < 0.0)


def ci_entirely_above_zero(lo: float | None, hi: float | None) -> bool:
    return lo is not None and hi is not None and lo > 0.0


def domain_verdict(stats: Mapping[str, Any], ci: Mapping[str, Mapping[str, Any]], n: int) -> str:
    if n < N_PAIRS_MIN:
        return "INSUFFICIENT_POWER"
    var_m = float(stats.get("var_dM") or 0.0)
    var_y = float(stats.get("var_dY") or 0.0)
    if var_m < 1e-12:
        return "NO_MEDIATOR_MOVEMENT"
    if var_y < 1e-12:
        return "NO_BEHAVIOR_CHANGE"
    a_ok = ci_entirely_above_zero((ci.get("a_mean_dM") or {}).get("lo"), (ci.get("a_mean_dM") or {}).get("hi"))
    c_ok = ci_excludes_zero((ci.get("c_mean_dY") or {}).get("lo"), (ci.get("c_mean_dY") or {}).get("hi"))
    ab_ok = ci_excludes_zero((ci.get("ab") or {}).get("lo"), (ci.get("ab") or {}).get("hi"))
    b_ok = ci_excludes_zero((ci.get("b_dY_on_dM") or {}).get("lo"), (ci.get("b_dY_on_dM") or {}).get("hi"))
    ab = stats.get("ab")
    c = stats.get("c_mean_dY")
    sign_ok = (
        ab is not None
        and c is not None
        and math.isfinite(float(ab))
        and math.isfinite(float(c))
        and (float(ab) == 0.0 or float(c) == 0.0 or (float(ab) > 0) == (float(c) > 0))
    )
    if a_ok and c_ok and b_ok and ab_ok and sign_ok:
        return "CORRELATIONAL_MEDIATION_SUPPORTED"
    if ab_ok and not c_ok:
        return "INDIRECT_ASSOCIATION_ONLY"
    return "NO_EVIDENCE"


def mechanism_answer(
    direction_status: str,
    domains: Mapping[str, Mapping[str, Any]],
    passed: int,
    total: int,
) -> str:
    bits = []
    supported = 0
    valid = 0
    for name, rec in domains.items():
        v = rec.get("verdict")
        if v == "INSUFFICIENT_POWER":
            bits.append(f"{name} insufficient-power")
            continue
        valid += 1
        if v == "CORRELATIONAL_MEDIATION_SUPPORTED":
            supported += 1
            bits.append(f"{name} changed and mediation supported")
        elif v == "INDIRECT_ASSOCIATION_ONLY":
            bits.append(f"{name} indirect-only")
        elif v == "NO_BEHAVIOR_CHANGE":
            bits.append(f"{name} did not change")
        else:
            bits.append(f"{name} not supported")
    consistent = "consistent" if supported else "not consistent"
    return (
        f"Using {direction_status}, negative versus neutral images "
        f"{'; '.join(bits)}; the frozen task-context a_perp indirect association "
        f"was {'supported' if supported else 'not supported'} in {supported}/{max(valid, 1)} "
        f"valid domains ({passed}/{total} gates); this is {consistent} with "
        "correlational representation mediation but does not establish causal mediation."
    )


def refuse_v3_write(path: os.PathLike[str] | str) -> Path:
    return ac.assert_writable_result_path(path)


def write_json(path: os.PathLike[str] | str, payload: Any) -> Path:
    p = refuse_v3_write(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    os.replace(tmp, p)
    return p
