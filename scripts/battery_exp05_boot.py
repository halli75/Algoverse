# Host boot for exp05. Own process. CUDA_VISIBLE_DEVICES=1. No overseer-tab theft.
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path


def log(m: str) -> None:
    print(f"{time.strftime('%H:%M:%S')} {m}", flush=True)


def source_battery_env() -> None:
    p = Path.home() / ".battery_env"
    if not p.is_file():
        log("battery_env missing")
        return
    n = 0
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[7:]
        k, _, v = line.partition("=")
        k, v = k.strip(), v.strip().strip("'").strip('"')
        if k and k not in os.environ:
            os.environ[k] = v
            n += 1
    log(f"sourced battery_env keys={n}")
    for name, path in (("HF_TOKEN", Path.home() / ".hf_token"), ("XAI_API_KEY", Path.home() / ".xai_api_key")):
        if not os.environ.get(name) and path.is_file():
            os.environ[name] = path.read_text(encoding="utf-8").strip()
    if os.environ.get("HF_TOKEN"):
        os.environ.setdefault("HUGGING_FACE_HUB_TOKEN", os.environ["HF_TOKEN"])


def main() -> int:
    source_battery_env()
    root = Path(os.environ.get("E2E_ROOT", str(Path.home() / "algoverse_run"))).expanduser()
    run = root / "battery" / "exp05"
    run.mkdir(parents=True, exist_ok=True)
    os.environ["E2E_ROOT"] = str(root)
    os.environ["E2E_EXP05"] = str(run)
    os.environ["E2E_OUT"] = str(run / "results.json")
    os.environ["E2E_HB"] = str(run / "heartbeat.json")
    os.environ.setdefault("E2E_SPLIT", str(root / "emotic_split.json"))
    os.environ.setdefault("E2E_EMOTIC", str(root / "emotic_data"))
    os.environ.setdefault("E2E_MODEL", "google/gemma-4-E4B-it")
    os.environ.setdefault("E2E_NO_FALLBACK", "1")
    os.environ["CUDA_VISIBLE_DEVICES"] = "1"
    os.environ.setdefault("E2E_N", "32")

    if not os.environ.get("HF_TOKEN"):
        tokp = Path.home() / ".hf_token"
        if tokp.is_file():
            os.environ["HF_TOKEN"] = tokp.read_text(encoding="utf-8").strip()
            os.environ.setdefault("HUGGING_FACE_HUB_TOKEN", os.environ["HF_TOKEN"])

    repo = Path(os.environ.get("E2E_REPO", str(Path.home() / "Algoverse"))).expanduser()
    script = repo / "scripts" / "battery_exp05_run.py"
    if not script.exists():
        # fall back to a copy under the run dir
        script = run / "battery_exp05_run.py"
    if not script.exists():
        raise SystemExit(f"missing {script}")

    for spec, mod in (
        ("pandas", "pandas"),
        ("pillow", "PIL"),
        ("accelerate", "accelerate"),
        ("bitsandbytes>=0.46.1", "bitsandbytes"),
        ("huggingface_hub", "huggingface_hub"),
        ("transformers", "transformers"),
    ):
        try:
            __import__(mod)
        except ImportError:
            log(f"pip install {spec}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", spec])

    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = "1"
    log(f"boot exp05 gpu=1 script={script} out={env['E2E_OUT']}")
    return int(subprocess.call([sys.executable, "-u", str(script)], env=env))


if __name__ == "__main__":
    raise SystemExit(main())
