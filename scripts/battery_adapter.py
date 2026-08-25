# Shared A100 adapter for the affect battery. One Gemma-4 nf4 loader.
# Behavioral generate only (no TransformerLens unless need_hooks=True).
from __future__ import annotations

import json
import os
import time
from pathlib import Path

PRIMARY = "google/gemma-4-E4B-it"
STALE_S = 20 * 60
MAX_CONCURRENT = 4
EXPECTED_SPLIT = "1e8ea1c22144dd9d"


def e2e_root() -> Path:
    return Path(os.environ.get("E2E_ROOT", str(Path.home() / "algoverse_run"))).expanduser()


def load_env_file(path: Path) -> list[str]:
    """Load KEY=VALUE into os.environ if unset. Returns key names only."""
    loaded: list[str] = []
    if not path.is_file():
        return loaded
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v
            loaded.append(k)
    return loaded


def source_battery_env() -> list[str]:
    keys: list[str] = []
    for cand in (
        Path.home() / ".battery_env",
        Path(__file__).resolve().parents[1] / ".env",
    ):
        keys.extend(load_env_file(cand))
    xai = Path.home() / ".xai_api_key"
    if xai.is_file() and not os.environ.get("XAI_API_KEY"):
        os.environ["XAI_API_KEY"] = xai.read_text(encoding="utf-8").strip()
        keys.append("XAI_API_KEY")
    return keys


def plant_hf_token() -> str | None:
    source_battery_env()
    if os.environ.get("HF_TOKEN"):
        os.environ.setdefault("HUGGING_FACE_HUB_TOKEN", os.environ["HF_TOKEN"])
        return os.environ["HF_TOKEN"]
    for cand in (Path.home() / ".hf_token", Path.home() / ".cache" / "huggingface" / "token"):
        if cand.is_file():
            tok = cand.read_text(encoding="utf-8").strip()
            if tok:
                os.environ["HF_TOKEN"] = tok
                os.environ.setdefault("HUGGING_FACE_HUB_TOKEN", tok)
                return tok
    return None


def lock_dir() -> Path:
    alt = e2e_root() / "battery" / "A100.lock"
    if alt.exists() and alt.is_dir():
        return alt
    d = e2e_root() / "battery" / "locks"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def running_gpu_jobs() -> list[dict]:
    now = time.time()
    jobs = []
    for p in lock_dir().glob("gpu_*.json"):
        rec = _read_json(p)
        if not rec:
            continue
        rec["stale"] = now - float(rec.get("ts") or 0) > STALE_S
        jobs.append(rec)
    return jobs


def claim_gpu(exp: str, gpu: str) -> Path:
    path = lock_dir() / f"gpu_{gpu}.json"
    rec = _read_json(path)
    now = time.time()
    if rec and rec.get("exp") not in (None, exp):
        age = now - float(rec.get("ts") or 0)
        if age <= STALE_S:
            raise SystemExit(f"gpu {gpu} held by {rec.get('exp')} age={age:.0f}s")
    live = [j for j in running_gpu_jobs() if not j.get("stale") and j.get("exp") != exp]
    if len(live) >= MAX_CONCURRENT:
        raise SystemExit(f"max concurrent {MAX_CONCURRENT}: {[j.get('exp') for j in live]}")
    payload = {"gpu": gpu, "exp": exp, "pid": os.getpid(), "ts": now}
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(payload), encoding="utf-8")
    os.replace(tmp, path)
    return path


def refresh_lock(exp: str, gpu: str) -> None:
    path = lock_dir() / f"gpu_{gpu}.json"
    rec = _read_json(path) or {}
    rec.update({"gpu": gpu, "exp": exp, "pid": os.getpid(), "ts": time.time()})
    path.write_text(json.dumps(rec), encoding="utf-8")


def wait_for_first_download(exp: str, timeout_s: int = 1800) -> None:
    cache = Path.home() / ".cache" / "huggingface" / "hub"
    marker = e2e_root() / "battery" / "hf_gemma4.ready"
    if marker.exists():
        return
    hits = list(cache.glob("models--google--gemma-4-E4B-it/**/config.json")) if cache.exists() else []
    if hits:
        marker.write_text("cached\n", encoding="utf-8")
        return
    downloading = e2e_root() / "battery" / "hf_gemma4.downloading"
    if downloading.exists():
        rec = _read_json(downloading) or {}
        if rec.get("exp") != exp:
            t0 = time.time()
            while time.time() - t0 < timeout_s:
                if marker.exists():
                    return
                time.sleep(10)
            return
    downloading.write_text(json.dumps({"exp": exp, "ts": time.time()}), encoding="utf-8")


def mark_download_ready(exp: str) -> None:
    marker = e2e_root() / "battery" / "hf_gemma4.ready"
    marker.write_text("ok\n", encoding="utf-8")
    dl = e2e_root() / "battery" / "hf_gemma4.downloading"
    if dl.exists():
        try:
            rec = json.loads(dl.read_text(encoding="utf-8"))
            if rec.get("exp") == exp:
                dl.unlink()
        except Exception:
            pass


def load_gemma4_nf4(mid: str = PRIMARY):
    """Load google/gemma-4-E4B-it nf4 weights, bf16 compute. No fallback."""
    import torch
    from transformers import AutoModelForImageTextToText, AutoProcessor, BitsAndBytesConfig

    if mid != PRIMARY:
        raise SystemExit(f"fallback model forbidden: {mid}")
    plant_hf_token()
    token = os.environ.get("HF_TOKEN") or True
    bnb = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
    )
    model = AutoModelForImageTextToText.from_pretrained(
        mid,
        quantization_config=bnb,
        device_map={"": 0},
        torch_dtype=torch.bfloat16,
        token=token,
    )
    processor = AutoProcessor.from_pretrained(mid, token=token)
    model.eval()
    for p in model.parameters():
        p.requires_grad = False
    return model, processor


def build_inputs(processor, text: str, image=None):
    if image is not None:
        content = [{"type": "image"}, {"type": "text", "text": text}]
        prompt = processor.apply_chat_template(
            [{"role": "user", "content": content}], add_generation_prompt=True, tokenize=False
        )
        return processor(text=[prompt], images=[image], return_tensors="pt")
    prompt = processor.apply_chat_template(
        [{"role": "user", "content": [{"type": "text", "text": text}]}],
        add_generation_prompt=True,
        tokenize=False,
    )
    return processor(text=[prompt], return_tensors="pt")


def first_token_ids(tokenizer, s: str) -> list[int]:
    out = []
    for pre in (" " + s, s):
        t = tokenizer(pre, add_special_tokens=False).input_ids
        if len(t) == 1:
            out.append(int(t[0]))
    return sorted(set(out))


def generate_choice(model, processor, text: str, image=None, max_new: int = 8) -> dict:
    """Greedy A/B letter. Returns text, letter, ab_mass."""
    import torch

    device = next(model.parameters()).device
    tok = getattr(processor, "tokenizer", None) or processor
    inp = build_inputs(processor, text, image)
    packed = {k: (v.to(device) if hasattr(v, "to") else v) for k, v in inp.items()}
    with torch.no_grad():
        out = model.generate(
            **packed,
            max_new_tokens=max_new,
            do_sample=False,
            return_dict_in_generate=True,
            output_scores=True,
        )
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
        ids_a = first_token_ids(tok, "A")
        ids_b = first_token_ids(tok, "B")
        ma = float(torch.logsumexp(lp[ids_a], 0).exp()) if ids_a else 0.0
        mb = float(torch.logsumexp(lp[ids_b], 0).exp()) if ids_b else 0.0
        ab_mass = ma + mb
    return {"text": decoded[:200], "letter": letter, "ab_mass": ab_mass}


def discover_emotic() -> tuple[Path, Path]:
    root = e2e_root()
    split_cands = [
        Path(os.environ["E2E_SPLIT"]).expanduser() if os.environ.get("E2E_SPLIT") else None,
        root / "emotic_split.json",
        Path.home() / "Algoverse" / "data" / "emotic_split.json",
    ]
    emotic_cands = [
        Path(os.environ["E2E_EMOTIC"]).expanduser() if os.environ.get("E2E_EMOTIC") else None,
        root / "emotic_data",
        root / "emotic_images",
    ]
    split = next((p for p in split_cands if p is not None and p.exists()), None)
    emotic = None
    for p in emotic_cands:
        if p is None:
            continue
        if (p / "emotic").exists() and (p / "emotic_pre" / "train.csv").exists():
            emotic = p
            break
        if p.exists() and (p / "emotic_pre" / "train.csv").exists():
            emotic = p
            break
    if split is None or emotic is None:
        raise SystemExit(f"EMOTIC/split missing split={split} emotic={emotic}")
    return emotic, split
