"""Charlotte notebook adapter for the locked shared core.

Notebooks should import this module (or `affect_core`) instead of copying
RL / add / st / rsc / aproj helper cells. Detector, clamp, lighting, and the
behavior battery remain Charlotte-only modules that call these primitives.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import affect_core as ac


def bind_model(model, tokenizer, *, device="cuda", n_layers=None, cache=None):
    """Return a small namespace that preserves Charlotte helper names on the core method."""
    import contextlib

    import torch

    n_layers = int(n_layers if n_layers is not None else model.cfg.n_layers)
    if cache is None:
        raise ValueError("pass a resid_post cache so layer keys can be discovered")
    lk = ac.discover_resid_post_keys(cache, d_model=int(model.cfg.d_model))
    win = ac.gate_window(n_layers, n_keys=len(lk))
    refuse_ids, comply_ids = ac.refuse_comply_ids(tokenizer)

    def split(inp):
        ids = inp["input_ids"].to(device)
        extra = {k: (v.to(device) if torch.is_tensor(v) else v) for k, v in inp.items() if k != "input_ids"}
        return ids, extra

    def RL(inp):
        ids, ex = split(inp)
        with torch.no_grad():
            _, c = model.run_with_cache(ids, names_filter=lambda n: "resid_post" in n, **ex)
        return torch.as_tensor(ac.extract_last_prompt_residuals(c, lk), dtype=torch.float32)

    def add(dv, coeff):
        return ac.make_add_hook(dv, coeff)

    def st(dirs, alpha, norms):
        return ac.make_normscaled_hooks(lk, dirs, norms, float(alpha), win)

    @contextlib.contextmanager
    def hk(fw):
        try:
            with model.hooks(fwd_hooks=list(fw)):
                yield
        except AttributeError:
            for n, f in fw:
                model.add_hook(n, f)
            try:
                yield
            finally:
                model.reset_hooks()

    def rsc(inp, fw=()):
        ids, ex = split(inp)
        with torch.no_grad(), hk(fw):
            lg = model(ids, **ex)
        return ac.first_token_refusal_score(lg[0, -1], refuse_ids, comply_ids)

    def aproj(inp, dirs, window=None):
        return ac.window_mean_projection(RL(inp), dirs, window if window is not None else win)

    def rproj(inp, r_dir, window=None):
        return aproj(inp, r_dir, window=window)

    return {
        "pin": ac.core_pin(),
        "CORE_METHOD": dict(ac.CORE_METHOD),
        "DESCRIBE": ac.DESCRIBE,
        "LK": lk,
        "WIN": win,
        "GATE": ac.fractional_gate_layers(n_layers),
        "RL": RL,
        "add": add,
        "st": st,
        "hk": hk,
        "rsc": rsc,
        "aproj": aproj,
        "rproj": rproj,
        "orth": ac.orthogonalize_span,
        "unit": ac.unit,
        "random_perp": ac.make_random_perp,
        "build_a_perp": ac.build_a_perp,
        "build_joint_affect": ac.build_joint_affect,
        "hashed_disjoint_ids": ac.hashed_disjoint_ids,
        "calibrate_gate_on_split": ac.calibrate_gate_on_split,
        "ALPHA_REF": ac.ALPHA_REF,
        "CALIBRATION_GRID": ac.CALIBRATION_GRID,
        "image_only_note": "construct a_img_perp as named variant image_only_a_perp; a_joint_perp is core primary",
    }
