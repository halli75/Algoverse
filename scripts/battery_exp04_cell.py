# JupyterHub / nohup launcher for battery exp04. Own kernel. GPU 3.
# [[sycophancy-affect-experiment]]
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

GPU = "3"
PRIMARY = "google/gemma-4-E4B-it"


def main() -> int:
    os.environ["CUDA_VISIBLE_DEVICES"] = GPU
    root = Path(os.environ.get("E2E_ROOT", str(Path.home() / "algoverse_run"))).expanduser()
    run = root / "battery" / "exp04"
    run.mkdir(parents=True, exist_ok=True)
    os.environ["E2E_ROOT"] = str(root)
    os.environ.setdefault("E2E_MODEL", PRIMARY)
    os.environ.setdefault("E2E_NO_FALLBACK", "1")
    os.environ.setdefault("E2E_SPLIT", str(root / "emotic_split.json"))
    os.environ.setdefault("E2E_EMOTIC", str(root / "emotic_data"))
    os.environ.setdefault("E2E_DATA", str(run / "data"))
    os.environ["EXP04_ROOT"] = str(run)
    os.environ["EXP04_OUT"] = str(run / "results.json")
    os.environ["EXP04_HB"] = str(run / "heartbeat.json")
    os.environ["EXP04_CKPT"] = str(run / "checkpoint.jsonl")
    os.environ["EXP04_GPU"] = GPU
    benv = Path.home() / ".battery_env"
    if benv.is_file():
        sys.path.insert(0, str(Path(__file__).resolve().parent) if "__file__" in globals() else str(Path.cwd() / "scripts"))
        try:
            from battery_adapter import source_battery_env

            source_battery_env()
        except Exception:
            pass
    if not os.environ.get("HF_TOKEN"):
        for cand in (Path.home() / ".hf_token", Path.home() / ".cache" / "huggingface" / "token"):
            if cand.is_file():
                tok = cand.read_text(encoding="utf-8").strip()
                if tok:
                    os.environ["HF_TOKEN"] = tok
                    os.environ.setdefault("HUGGING_FACE_HUB_TOKEN", tok)
                    break
    subprocess.run(["nvidia-smi", "-i", GPU], check=False)
    script = None
    for cand in (
        Path(__file__).resolve().parent / "battery_exp04.py" if "__file__" in globals() else None,
        Path.cwd() / "scripts" / "battery_exp04.py",
        Path.home() / "Algoverse" / "scripts" / "battery_exp04.py",
        run / "battery_exp04.py",
    ):
        if cand is not None and cand.exists():
            script = cand
            break
    if script is None:
        raise SystemExit("battery_exp04.py not found")
    print("exec", script, flush=True)
    ns = {"__name__": "__main__", "__file__": str(script)}
    exec(script.read_text(encoding="utf-8"), ns)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
