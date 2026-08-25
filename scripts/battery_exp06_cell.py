"""Paste-into-Jupyter cell for exp06. Starts its own process — do not reuse overseer kernel."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    os.environ["CUDA_VISIBLE_DEVICES"] = os.environ.get("EXP06_GPU", "2")
    os.environ.setdefault("E2E_ROOT", str(Path.home() / "algoverse_run"))
    os.environ.setdefault("E2E_TIER", os.environ.get("E2E_TIER", "smoke"))
    os.environ.setdefault("E2E_MODEL", "google/gemma-4-E4B-it")
    os.environ.setdefault("E2E_NO_FALLBACK", "1")
    subprocess.run(["nvidia-smi", "-i", os.environ["CUDA_VISIBLE_DEVICES"]], check=False)
    boot = None
    for cand in (
        Path(__file__).resolve().parent / "battery_exp06_boot.py" if "__file__" in globals() else None,
        Path.cwd() / "scripts" / "battery_exp06_boot.py",
        Path.home() / "Algoverse" / "scripts" / "battery_exp06_boot.py",
        Path.home() / "algoverse" / "scripts" / "battery_exp06_boot.py",
    ):
        if cand is not None and cand.exists():
            boot = cand
            break
    if boot is None:
        raise SystemExit("battery_exp06_boot.py not found")
    print("boot", boot, flush=True)
    ns = {"__name__": "battery_exp06_boot", "__file__": str(boot)}
    exec(boot.read_text(encoding="utf-8"), ns)
    return int(ns["main"]())


if __name__ == "__main__":
    raise SystemExit(main())
