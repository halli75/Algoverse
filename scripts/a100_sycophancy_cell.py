# JupyterHub notebook cell for graded sycophancy × affect.
# Prints nvidia-smi, sets E2E_* env, execs scripts/a100_sycophancy_boot.py.
# [[sycophancy-affect-experiment]]
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ORIGINAL_PREREG_HASH = "051e1ea79cd116fce56edeb43848ae10526e2830efc49ab0df2cd7d904a20876"


def main() -> int:
    subprocess.run(["nvidia-smi"], check=False)
    root = Path(os.environ.get("E2E_ROOT", str(Path.home() / "algoverse_run"))).expanduser()
    root.mkdir(parents=True, exist_ok=True)
    os.environ["E2E_ROOT"] = str(root)
    os.environ.setdefault("E2E_TIER", os.environ.get("E2E_TIER", "smoke"))
    os.environ.setdefault("E2E_MODEL", "google/gemma-4-E4B-it")
    os.environ.setdefault("E2E_NO_FALLBACK", "1")
    os.environ.setdefault("E2E_PREREG_HASH", ORIGINAL_PREREG_HASH)
    os.environ.setdefault("E2E_OUT", str(root / "e2e_sycophancy_results.json"))
    os.environ.setdefault("E2E_HB", str(root / "e2e_sycophancy_heartbeat.json"))
    os.environ.setdefault("E2E_DIRS", str(root / "e2e_sycophancy_dirs.pt"))
    os.environ.setdefault("E2E_SPLIT", str(root / "emotic_split.json"))
    os.environ.setdefault("E2E_EMOTIC", str(root / "emotic_data"))
    os.environ.setdefault("E2E_DATA", str(root / "e2e_data"))
    print(
        "env ready",
        {
            "E2E_ROOT": os.environ["E2E_ROOT"],
            "E2E_TIER": os.environ["E2E_TIER"],
            "E2E_OUT": os.environ["E2E_OUT"],
            "E2E_HB": os.environ["E2E_HB"],
            "E2E_DIRS": os.environ["E2E_DIRS"],
            "E2E_SPLIT": os.environ["E2E_SPLIT"],
            "E2E_EMOTIC": os.environ["E2E_EMOTIC"],
            "E2E_DATA": os.environ["E2E_DATA"],
            "HF_TOKEN": bool(os.environ.get("HF_TOKEN")),
            "XAI_API_KEY": bool(os.environ.get("XAI_API_KEY")),
        },
        flush=True,
    )

    boot = None
    for cand in (
        Path(__file__).resolve().parent / "a100_sycophancy_boot.py" if "__file__" in globals() else None,
        Path.cwd() / "scripts" / "a100_sycophancy_boot.py",
        Path.home() / "Algoverse" / "scripts" / "a100_sycophancy_boot.py",
        Path.home() / "algoverse" / "scripts" / "a100_sycophancy_boot.py",
    ):
        if cand is not None and cand.exists():
            boot = cand
            break
    if boot is None:
        repo = Path(os.environ.get("E2E_REPO", str(Path.home() / "Algoverse"))).expanduser()
        if not (repo / "scripts" / "a100_sycophancy_boot.py").exists():
            subprocess.check_call(["git", "clone", "https://github.com/halli75/Algoverse.git", str(repo)])
        boot = repo / "scripts" / "a100_sycophancy_boot.py"
    print("boot", boot, flush=True)
    ns: dict = {"__name__": "a100_sycophancy_boot", "__file__": str(boot)}
    exec(boot.read_text(encoding="utf-8"), ns)
    return int(ns["main"]())


if __name__ == "__main__":
    raise SystemExit(main())
