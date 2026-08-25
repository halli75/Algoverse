# Host boot for exp01. Own process. CUDA_VISIBLE_DEVICES=0. No overseer-tab theft.
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path


def log(m: str) -> None:
    print(f"{time.strftime('%H:%M:%S')} {m}", flush=True)


def source_host_env() -> None:
    benv = Path.home() / ".battery_env"
    if benv.is_file():
        for raw in benv.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            if line.startswith("export "):
                line = line[7:].strip()
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and k not in os.environ:
                os.environ[k] = v
    if not os.environ.get("HF_TOKEN"):
        tokp = Path.home() / ".hf_token"
        if tokp.is_file():
            os.environ["HF_TOKEN"] = tokp.read_text(encoding="utf-8").strip()
    if os.environ.get("HF_TOKEN"):
        os.environ.setdefault("HUGGING_FACE_HUB_TOKEN", os.environ["HF_TOKEN"])
    if not os.environ.get("XAI_API_KEY"):
        xp = Path.home() / ".xai_api_key"
        if xp.is_file():
            os.environ["XAI_API_KEY"] = xp.read_text(encoding="utf-8").strip()


def main() -> int:
    source_host_env()
    root = Path(os.environ.get("E2E_ROOT", str(Path.home() / "algoverse_run"))).expanduser()
    run = root / "battery" / "exp01"
    run.mkdir(parents=True, exist_ok=True)
    os.environ["E2E_ROOT"] = str(root)
    os.environ["E2E_EXP01"] = str(run)
    os.environ["E2E_OUT"] = str(run / "results.json")
    os.environ["E2E_HB"] = str(run / "heartbeat.json")
    os.environ.setdefault("E2E_SPLIT", str(root / "emotic_split.json"))
    os.environ.setdefault("E2E_EMOTIC", str(root / "emotic_data"))
    os.environ.setdefault("E2E_MODEL", "google/gemma-4-E4B-it")
    os.environ.setdefault("E2E_NO_FALLBACK", "1")
    os.environ.setdefault("E2E_TIER", os.environ.get("EXP01_TIER", "full"))
    os.environ["CUDA_VISIBLE_DEVICES"] = os.environ.get("EXP01_GPU", "0")
    os.environ.setdefault("EXP01_LOTTERIES", str(Path.home() / "Algoverse" / "data" / "battery" / "exp01_lotteries.json"))

    repo = Path(os.environ.get("E2E_REPO", str(Path.home() / "Algoverse"))).expanduser()
    script = repo / "scripts" / "battery_exp01_run.py"
    if not script.exists():
        script = run / "battery_exp01_run.py"
    if not script.exists():
        raise SystemExit(f"missing {script}")

    for spec, mod in (
        ("pandas", "pandas"),
        ("pillow", "PIL"),
        ("accelerate", "accelerate"),
        ("bitsandbytes>=0.46.1", "bitsandbytes"),
        ("huggingface_hub", "huggingface_hub"),
        ("transformers", "transformers"),
        ("numpy", "numpy"),
    ):
        try:
            __import__(mod)
        except ImportError:
            log(f"pip install {spec}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", spec])

    env = os.environ.copy()
    log(f"boot exp01 gpu={env['CUDA_VISIBLE_DEVICES']} tier={env['E2E_TIER']} script={script}")
    return int(subprocess.call([sys.executable, "-u", str(script)], env=env))


if __name__ == "__main__":
    raise SystemExit(main())
