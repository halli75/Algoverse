# bf16 dual-architecture loader. No BitsAndBytes. No nf4.
from __future__ import annotations

import os
from typing import Any

import battery_adapter as ba
import battery_v2_config as cfg


def load_model(model_key: str):
    """Load E4B-it or 12B-it in bf16. Thinking off. No quantization."""
    import torch

    meta = cfg.MODELS[model_key]
    mid = meta["id"]
    ba.plant_hf_token()
    token = os.environ.get("HF_TOKEN") or True
    kwargs = dict(
        torch_dtype=torch.bfloat16,
        device_map={"": 0},
        token=token,
    )
    if meta["hf_class"] == "AutoModelForMultimodalLM":
        from transformers import AutoModelForMultimodalLM, AutoProcessor

        model = AutoModelForMultimodalLM.from_pretrained(mid, **kwargs)
        processor = AutoProcessor.from_pretrained(mid, token=token)
    else:
        from transformers import AutoModelForImageTextToText, AutoProcessor

        model = AutoModelForImageTextToText.from_pretrained(mid, **kwargs)
        processor = AutoProcessor.from_pretrained(mid, token=token)
    model.eval()
    for p in model.parameters():
        p.requires_grad = False
    n_layers = int(getattr(model.config, "num_hidden_layers", meta["n_layers"]))
    d_model = int(getattr(model.config, "hidden_size", 0) or 0)
    return model, processor, {"n_layers": n_layers, "d_model": d_model, "id": mid, "key": model_key}


def apply_chat(processor, text: str, image=None) -> str:
    if image is not None:
        content = [{"type": "image"}, {"type": "text", "text": text}]
    else:
        content = [{"type": "text", "text": text}]
    kwargs: dict[str, Any] = {
        "add_generation_prompt": True,
        "tokenize": False,
    }
    # Gemma-4 thinking must stay off for forced-choice.
    try:
        return processor.apply_chat_template(
            [{"role": "user", "content": content}],
            enable_thinking=False,
            **kwargs,
        )
    except TypeError:
        return processor.apply_chat_template(
            [{"role": "user", "content": content}],
            **kwargs,
        )


def build_inputs(processor, text: str, image=None):
    prompt = apply_chat(processor, text, image)
    if image is not None:
        return processor(text=[prompt], images=[image], return_tensors="pt")
    return processor(text=[prompt], return_tensors="pt")


def generate_choice(model, processor, text: str, image=None, max_new: int = 8) -> dict:
    import torch

    device = next(model.parameters()).device
    tok = getattr(processor, "tokenizer", None) or processor
    inp = build_inputs(processor, text, image)
    packed = {k: (v.to(device) if hasattr(v, "to") else v) for k, v in inp.items()}
    gen_kw = dict(
        max_new_tokens=max_new,
        do_sample=False,
        return_dict_in_generate=True,
        output_scores=True,
    )
    with torch.no_grad():
        try:
            out = model.generate(**packed, enable_thinking=False, **gen_kw)
        except (TypeError, ValueError) as e:
            if "enable_thinking" in str(e) or isinstance(e, TypeError):
                out = model.generate(**packed, **gen_kw)
            else:
                raise
    gen_ids = out.sequences[0, packed["input_ids"].shape[1] :]
    decoded = tok.decode(gen_ids, skip_special_tokens=True).replace("\n", " ").strip()
    letter = None
    for ch in decoded.upper():
        if ch in ("A", "B"):
            letter = ch
            break
    ab_mass = None
    if out.scores:
        lp = torch.log_softmax(out.scores[0][0].float(), dim=-1)
        ids_a = ba.first_token_ids(tok, "A")
        ids_b = ba.first_token_ids(tok, "B")
        ma = float(torch.logsumexp(lp[ids_a], 0).exp()) if ids_a else 0.0
        mb = float(torch.logsumexp(lp[ids_b], 0).exp()) if ids_b else 0.0
        ab_mass = ma + mb
    return {"text": decoded[:400], "letter": letter, "ab_mass": ab_mass}


def generate_text(model, processor, text: str, image=None, max_new: int = 48) -> str:
    rec = generate_choice(model, processor, text, image, max_new=max_new)
    return rec["text"]
