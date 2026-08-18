from pathlib import Path

p = Path(__file__).with_name("e2e_local_pipeline.py")
c = p.read_text(encoding="utf-8")

# Normalize mojibake from prior PowerShell writes
for a, b in [
    ("Phase A â€”", "Phase A —"),
    ("Aâ†’J", "A→J"),
    ("Judge key â€”", "Judge key —"),
]:
    c = c.replace(a, b)

start = c.find('log("PHASE_A_INSTALL")')
end = c.find("model.eval()")
if start < 0 or end < 0:
    raise SystemExit(f"markers missing start={start} end={end}")

new_block = '''log("PHASE_A_INSTALL")
# Local deps assumed present (transformer_lens, bitsandbytes, dotenv).

from dotenv import load_dotenv  # noqa: E402
import torch  # noqa: E402
from huggingface_hub import login  # noqa: E402
from PIL import Image  # noqa: E402
from transformer_lens.model_bridge import TransformerBridge  # noqa: E402

load_dotenv(ROOT / ".env")
tok = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_HUB_TOKEN")
assert tok and len(tok) > 10, "HF_TOKEN missing in .env"
os.environ["HF_TOKEN"] = tok
login(tok)
assert os.environ.get("XAI_API_KEY"), "XAI_API_KEY missing in .env"
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

MODEL_ID = "google/gemma-3-4b-it"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
ALPHA_JB = 0.008
GATE_LO, GATE_HI = 8, 20
# Local RTX 3050 6GB: same protocol sizes as Colab T4 gist (32/24/16)
N_DIR, N_EVAL, N_IMG = 32, 24, 16
SEED = 0
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

log(f"device={DEVICE} gpu={torch.cuda.get_device_name(0) if DEVICE=='cuda' else None}")
RESULTS["runtime"] = {"host": "local_rtx3050", "protocol_n": [N_DIR, N_EVAL, N_IMG]}
if DEVICE == "cuda":
    torch.cuda.empty_cache()
    try:
        free, total = torch.cuda.mem_get_info()
        log(f"cuda_mem_before_load free_gb={free/1e9:.2f} total_gb={total/1e9:.2f}")
    except Exception as e:
        log(f"cuda_mem_info_failed={e}")

# 6GB cannot hold full bf16 Gemma-3-4b; use fp16 + accelerate offload.
log("load_strategy=fp16_device_map_auto_max5GiB")
try:
    model = TransformerBridge.boot_transformers(
        MODEL_ID,
        dtype=torch.float16,
        device_map="auto",
        max_memory={0: "5GiB", "cpu": "28GiB"},
    )
except Exception as e1:
    log(f"device_map_auto_failed={e1!r}; retry cpu fp16 then cuda")
    torch.cuda.empty_cache()
    model = TransformerBridge.boot_transformers(MODEL_ID, device="cpu", dtype=torch.float16)
    try:
        model = model.to(DEVICE)
    except torch.cuda.OutOfMemoryError:
        log("OOM_full_cuda_keep_cpu")
        DEVICE = "cpu"

'''

c = c[:start] + new_block + c[end:]

needle = "model.eval()\nfor p in model.parameters():\n    p.requires_grad = False\n"
insert = """model.eval()
for p in model.parameters():
    p.requires_grad = False
try:
    DEVICE = str(next(model.parameters()).device)
    if DEVICE.startswith("cuda"):
        DEVICE = "cuda"
except StopIteration:
    pass
log(f"primary_param_device={DEVICE}")
RESULTS["runtime"]["load"] = "fp16_device_map_auto"
"""
if "primary_param_device" not in c:
    if needle not in c:
        raise SystemExit("model.eval needle missing")
    c = c.replace(needle, insert, 1)

c = c.replace('"/content/e2e_dirs.pt"', 'str(DATA_ROOT / "e2e_dirs.pt")')
c = c.replace(
    '"reason": "T4_VRAM_skip_after_gemma; reload in overnight A100 run"',
    '"reason": "local_3050_VRAM_skip_after_gemma; reload in overnight A100 run"',
)
c = c.replace(
    'log("Qwen skipped on T4 (preserve session for Step7 + E2E_COMPLETE)")',
    'log("Qwen skipped on local 3050 (preserve VRAM for Step7 + E2E_COMPLETE)")',
)

if "google.colab" in c:
    raise SystemExit("google.colab still present")

p.write_text(c, encoding="utf-8")
print("patched", p, "load_dotenv", "load_dotenv" in c, "device_map", "device_map" in c)
