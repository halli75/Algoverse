# Host launcher for exp02. Own nohup process on GPU 5. Do not touch JupyterLab UI.
# [[battery-campaign]]
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent


def main() -> int:
    os.environ.setdefault("E2E_ROOT", str(Path.home() / "algoverse_run"))
    os.environ.setdefault("CUDA_VISIBLE_DEVICES", os.environ.get("EXP02_GPU", "5"))
    os.environ.setdefault("E2E_MODEL", "google/gemma-4-E4B-it")
    os.environ.setdefault("E2E_NO_FALLBACK", "1")
    os.environ.setdefault("E2E_TIER", os.environ.get("E2E_TIER", "full"))
    os.environ["PYTHONUNBUFFERED"] = "1"
    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))
    log_dir = Path(os.environ["E2E_ROOT"]) / "battery" / "exp02"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "run.log"
    cmd = [sys.executable, "-u", str(HERE / "battery_exp02_run.py")]
    print(f"exec {' '.join(cmd)} gpu={os.environ['CUDA_VISIBLE_DEVICES']} log={log_path}", flush=True)
    with log_path.open("a", encoding="utf-8") as lf:
        lf.write(f"\n=== boot pid={os.getpid()} gpu={os.environ['CUDA_VISIBLE_DEVICES']} ===\n")
        lf.flush()
        return subprocess.call(cmd, stdout=lf, stderr=subprocess.STDOUT)


if __name__ == "__main__":
    raise SystemExit(main())
