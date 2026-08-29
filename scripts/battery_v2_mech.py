# Residual-stream probe. Native hidden_states, hooks fallback.
# Never writes frozen v3. Image-present dir from disjoint calib only.
from __future__ import annotations

from typing import Any

import numpy as np

import affect_core as ac
import battery_v2_config as cfg


MECH_PROMPT = (
    "You see a photo or nothing extra. Do not describe it. "
    "Which letter do you pick?\nA. continue\nB. stop\n\n" + cfg.FC_SUFFIX
)


def window_for(n_layers: int) -> list[int]:
    return ac.gate_window(n_layers)


def image_present_dir(photo_mean: np.ndarray, none_mean: np.ndarray) -> np.ndarray:
    """unit(mean(photo) - mean(no-image)). Built on calib, never eval."""
    return ac.unit(np.asarray(photo_mean, dtype=np.float64) - np.asarray(none_mean, dtype=np.float64))


def window_vec(acts: np.ndarray, window: list[int]) -> np.ndarray:
    h = np.asarray(acts, dtype=np.float64)
    if h.ndim != 2:
        raise ValueError(f"acts expected (n_layers, d), got {h.shape}")
    idx = [i for i in window if 0 <= i < h.shape[0]]
    if not idx:
        raise ValueError("empty window")
    return np.mean(h[idx], axis=0)


def layer_scores(resid_by_layer: dict[int, np.ndarray], direction: np.ndarray) -> dict[int, float]:
    d = ac.unit(np.asarray(direction, dtype=np.float64).reshape(-1))
    out = {}
    for i, vec in resid_by_layer.items():
        v = np.asarray(vec, dtype=np.float64).reshape(-1)
        out[int(i)] = float(np.dot(v, d[: v.size] if d.size != v.size else d))
    return out


def first_separate_layer(scores_a: dict[int, float], scores_b: dict[int, float], min_gap: float = 0.05) -> int | None:
    keys = sorted(set(scores_a) & set(scores_b))
    for k in keys:
        if abs(scores_a[k] - scores_b[k]) >= min_gap:
            return int(k)
    return None


def tracks_which(
    dy: np.ndarray,
    s_img: np.ndarray,
    s_aff: np.ndarray,
) -> dict[str, float]:
    """Pearson of choice-delta with image-present vs a_perp scores."""

    def _r(x, y):
        x = np.asarray(x, dtype=float).reshape(-1)
        y = np.asarray(y, dtype=float).reshape(-1)
        if x.size < 3 or np.std(x) < 1e-12 or np.std(y) < 1e-12:
            return float("nan")
        return float(np.corrcoef(x, y)[0, 1])

    r_img = _r(dy, s_img)
    r_aff = _r(dy, s_aff)
    more = None
    if np.isfinite(r_img) and np.isfinite(r_aff):
        more = bool(abs(r_img) > abs(r_aff))
    return {
        "r_choice_image_present": r_img,
        "r_choice_a_perp": r_aff,
        "tracks_image_present_more": more,
    }


def capture_last_prompt_resid(model, packed, window: list[int]) -> dict[int, np.ndarray]:
    """Best-effort native hooks. Raises if no layer modules found."""
    captured: dict[int, Any] = {}
    hooks = []

    def _layers(m):
        for name in ("model.language_model.layers", "model.layers", "language_model.layers", "layers"):
            cur = m
            ok = True
            for part in name.split("."):
                if not hasattr(cur, part):
                    ok = False
                    break
                cur = getattr(cur, part)
            if ok:
                return list(cur)
        raise RuntimeError("no transformer layers on model")

    layers = _layers(model)
    want = set(window)

    def make_hook(idx: int):
        def hook(_m, _i, out):
            h = out[0] if isinstance(out, tuple) else out
            captured[idx] = h.detach().float()[:, -1, :].cpu().numpy()[0]

        return hook

    for i, layer in enumerate(layers):
        if i in want:
            hooks.append(layer.register_forward_hook(make_hook(i)))
    try:
        import torch

        with torch.no_grad():
            model(**packed)
    finally:
        for h in hooks:
            h.remove()
    if not captured:
        raise RuntimeError("hooks captured nothing")
    return {i: np.asarray(v, dtype=np.float64) for i, v in captured.items()}


def pack_forward(model, processor, text: str, image=None) -> dict:
    import battery_v2_load as ld

    device = next(model.parameters()).device
    inp = ld.build_inputs(processor, text, image)
    return {k: (v.to(device) if hasattr(v, "to") else v) for k, v in inp.items()}


def capture_acts(model, processor, text: str, image, n_layers: int) -> np.ndarray:
    """(n_layers, d) last-prompt residuals. hidden_states first, hooks fallback."""
    import torch
    import battery_probe_aperp as probe

    packed = pack_forward(model, processor, text, image)
    try:
        with torch.no_grad():
            out = model(**packed, output_hidden_states=True)
        hs = getattr(out, "hidden_states", None)
        if hs:
            return probe.hidden_states_to_acts(hs, n_layers=n_layers)
    except Exception:
        pass
    by = capture_last_prompt_resid(model, packed, list(range(n_layers)))
    d = int(next(iter(by.values())).shape[-1])
    stacked = np.zeros((n_layers, d), dtype=np.float64)
    for i, v in by.items():
        stacked[int(i)] = np.asarray(v, dtype=np.float64).reshape(-1)[:d]
    return stacked


def score_task(model, processor, text: str, image, n_layers: int, dirs=None) -> dict[str, Any]:
    """One forward: last-token A/B masses + residual acts. No DESCRIBE."""
    import torch
    import battery_adapter as ba
    import battery_probe_aperp as probe

    packed = pack_forward(model, processor, text, image)
    tok = getattr(processor, "tokenizer", None) or processor
    with torch.no_grad():
        try:
            out = model(**packed, output_hidden_states=True)
        except TypeError:
            out = model(**packed)
    acts = None
    hs = getattr(out, "hidden_states", None)
    if hs:
        acts = probe.hidden_states_to_acts(hs, n_layers=n_layers)
    else:
        acts = capture_acts(model, processor, text, image, n_layers)
    logits = out.logits[0, -1]
    lp = torch.log_softmax(logits.float().reshape(-1), dim=-1)
    ids_a = ba.first_token_ids(tok, "A")
    ids_b = ba.first_token_ids(tok, "B")
    ma = float(torch.logsumexp(lp[ids_a], 0).exp()) if ids_a else 0.0
    mb = float(torch.logsumexp(lp[ids_b], 0).exp()) if ids_b else 0.0
    tot = ma + mb
    rec = {
        "acts": acts,
        "p_a": ma,
        "p_b": mb,
        "ab_mass": tot,
        "letter": "A" if ma >= mb else "B",
        "Y_risky_A": ma,
        "M": None,
    }
    if dirs is not None and getattr(dirs, "a_perp", None) is not None:
        try:
            rec["M"] = float(probe.project_aperp(acts, dirs.a_perp, dirs.window))
        except Exception:
            rec["M"] = None
    return rec


def try_load_dirs(model_key: str, corpus: str):
    """Frozen v3 dirs only valid for E4B+EMOTIC. Never writes v3."""
    import os

    if model_key != "e4b":
        return None, "DIAGNOSTIC_NOT_V3"
    import battery_probe_aperp as probe

    try:
        env_p = os.environ.get("E2E_DIRS") or os.environ.get("EXP10_DIRS")
        if env_p:
            d = probe.load_frozen_dirs(env_p)
        else:
            found = probe.find_dirs_file()
            d = probe.load_frozen_dirs(found) if found else None
        if d is None:
            return None, "DIAGNOSTIC_NOT_V3"
        if d.is_frozen_v3 and corpus == "emotic":
            return d, "FROZEN_V3_EXACT"
        return d, "DIAGNOSTIC_NOT_V3"
    except Exception:
        return None, "DIAGNOSTIC_NOT_V3"


def assert_not_v3_write(path) -> None:
    ac.assert_writable_result_path(path)
